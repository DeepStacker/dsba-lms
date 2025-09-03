"""
AI Client for integrating with the AI service microservice
"""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
from .config import settings
import json
import logging

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    pass


class AIClientCircuitBreaker:
    """Simple circuit breaker pattern for AI service calls"""

    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.open = False

    def record_success(self):
        self.failures = 0
        self.open = False

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        if self.failures >= self.failure_threshold:
            self.open = True

    def can_attempt(self):
        if not self.open:
            return True

        # Check if recovery timeout has passed
        if self.last_failure_time:
            current_time = asyncio.get_event_loop().time()
            if current_time - self.last_failure_time > self.recovery_timeout:
                # Try a single test call
                self.open = False
                return True

        return False


class AIClient:
    """Client for calling the AI service microservice"""

    def __init__(self):
        self.base_url = getattr(settings, 'ai_service_url', 'http://localhost:8001')
        self.internal_token = getattr(settings, 'ai_service_token', 'internal_token_change_me')
        self.circuit_breaker = AIClientCircuitBreaker()
        self.timeout = httpx.Timeout(30.0)  # 30 second timeout

    async def _make_request(self, endpoint: str, payload: Dict[str, Any], retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request to AI service with retry logic"""

        if not self.circuit_breaker.can_attempt():
            raise AIClientError("Circuit breaker is open - AI service unreachable")

        headers = {
            'Content-Type': 'application/json',
            'X-Internal-Auth': self.internal_token
        }

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.info(f"Calling AI service: {endpoint} (attempt {attempt + 1})")
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        json=payload,
                        headers=headers
                    )

                    if response.status_code == 200:
                        self.circuit_breaker.record_success()
                        return response.json()

                    # Handle specific error codes
                    elif response.status_code in [429, 500, 502, 503, 504]:
                        logger.warning(f"AI service returned {response.status_code}, retrying...")
                        if attempt < retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            self.circuit_breaker.record_failure()
                            raise AIClientError(f"AI service returned {response.status_code}")

                    else:
                        # Immediate failure for 4xx errors (client errors)
                        self.circuit_breaker.record_failure()
                        logger.error(f"AI service client error: {response.status_code}, {response.text}")
                        raise AIClientError(f"AI service error: {response.status_code}")

            except httpx.TimeoutException:
                logger.warning(f"AI service timeout on attempt {attempt + 1}")
                self.circuit_breaker.record_failure()
                if attempt == retries - 1:
                    raise AIClientError("AI service timeout")

            except httpx.ConnectError:
                logger.warning(f"AI service connection error on attempt {attempt + 1}")
                self.circuit_breaker.record_failure()
                if attempt == retries - 1:
                    raise AIClientError("AI service unreachable")

            except Exception as e:
                logger.error(f"AI service error: {str(e)}")
                self.circuit_breaker.record_failure()
                if attempt == retries - 1:
                    raise AIClientError(f"AI service error: {str(e)}")

        raise AIClientError("Max retries exceeded")

    async def grade_descriptive_answer(self, answer: str, model_answer: str,
                                     rubric: Dict[str, Any],
                                     strictness: float = 0.5) -> Dict[str, Any]:
        """Grade a descriptive answer using AI"""

        payload = {
            "answer": answer,
            "model_answer": model_answer,
            "rubric_json": rubric,
            "strictness": strictness
        }

        try:
            result = await self._make_request("/grade/descriptive", payload)
            return result
        except AIClientError:
            # Return a fallback scoring structure if AI service is unavailable
            logger.warning("AI grading failed, using fallback")
            return self._fallback_grading(answer, model_answer, rubric, strictness)

    async def generate_questions(self, syllabus: str, topics: List[str],
                               counts: Dict[str, int], difficulty_mix: Dict[str, float],
                               types: List[str]) -> List[Dict[str, Any]]:
        """Generate questions using AI"""

        payload = {
            "syllabus": syllabus,
            "topics": topics,
            "counts": counts,
            "difficulty_mix": difficulty_mix,
            "types": types
        }

        try:
            result = await self._make_request("/generate/questions", payload)
            questions = result.get("questions", [])
            return questions
        except AIClientError:
            logger.warning("AI question generation failed")
            return []

    async def analyze_attainment(self, co_data: List[Dict[str, Any]],
                               po_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze CO/PO attainment using AI"""

        payload = {
            "co_data": co_data,
            "po_data": po_data
        }

        try:
            result = await self._make_request("/analyze/attainment", payload)
            return result
        except AIClientError:
            logger.warning("AI attainment analysis failed")
            return {"co_attainments": {}, "po_attainments": {}, "insights": []}

    def _fallback_grading(self, answer: str, model_answer: str,
                         rubric: Dict[str, Any], strictness: float) -> Dict[str, Any]:
        """Fallback grading when AI service is unavailable"""

        # Simple fallback logic based on string matching and length
        answer_length = len(answer.strip())
        model_length = len(model_answer.strip())

        # Very basic similarity scoring
        common_words = set(answer.lower().split()) & set(model_answer.lower().split())
        word_overlap = len(common_words) / max(len(set(answer.split())), 1)

        # Length similarity
        length_ratio = min(answer_length, model_length) / max(answer_length, model_length) if max(answer_length, model_length) > 0 else 0

        # Combined score
        base_score = (word_overlap + length_ratio) / 2
        adjusted_score = base_score * (2 - strictness)  # Less strict means higher scores

        # Clamp to reasonable range
        ai_score = max(0, min(10, adjusted_score * 10))  # Scale to 0-10

        return {
            "ai_score": ai_score,
            "per_criterion": self._calculate_per_criterion_fallback(ai_score, rubric),
            "feedback_bullets": [
                f"Estimated score based on content similarity ({word_overlap:.1%})",
                f"Answer length comparison: {answer_length} vs {model_length} characters"
            ],
            "explanations": "Fallback scoring due to AI service unavailability. Please review manually."
        }

    def _calculate_per_criterion_fallback(self, ai_score: float, rubric: Dict[str, Any]) -> Dict[str, float]:
        """Calculate per-criterion scores using fallback logic"""

        criterion_scores = {}
        total_score = 0
        num_criteria = 0

        # Since we don't have specific rubric criteria, distribute score evenly
        if isinstance(rubric, dict):
            for key, value in rubric.items():
                if isinstance(value, dict) and 'marks' in value:
                    criterion_scores[key] = min(value['marks'], ai_score * (value['marks'] / 10))
                    total_score += criterion_scores[key]
                    num_criteria += 1

        # If no specific criteria, create generic ones
        if not criterion_scores:
            criterion_scores = {
                "content_relevance": ai_score * 0.4,
                "completeness": ai_score * 0.3,
                "accuracy": ai_score * 0.3
            }

        return criterion_scores