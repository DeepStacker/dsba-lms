from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import random
import json

class LLMAdapter(ABC):
    """Abstract base class for LLM adapters"""

    @abstractmethod
    async def grade_descriptive_answer(
        self,
        answer: str,
        model_answer: str,
        rubric: Dict[str, Any],
        strictness: float = 0.5
    ) -> Dict[str, Any]:
        """Grade a descriptive answer"""
        pass

    @abstractmethod
    async def generate_questions(
        self,
        syllabus: str,
        topics: List[str],
        counts: Dict[str, int],
        difficulty_mix: Dict[str, float],
        types: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate questions"""
        pass

    @abstractmethod
    async def analyze_attainment(
        self,
        co_data: List[Dict[str, Any]],
        po_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze CO/PO attainment"""
        pass

class MockLLMAdapter(LLMAdapter):
    """Mock LLM adapter for testing and development"""

    async def grade_descriptive_answer(
        self,
        answer: str,
        model_answer: str,
        rubric: Dict[str, Any],
        strictness: float = 0.5
    ) -> Dict[str, Any]:
        """Mock grading with deterministic but varied scores"""
        # Simple mock logic based on answer length and keywords
        score = min(10.0, len(answer) / 50)  # Base score on length
        if "correct" in answer.lower():
            score += 2
        if "example" in answer.lower():
            score += 1

        # Add some randomness
        score += random.uniform(-1, 1)
        score = max(0, min(10, score))

        return {
            "ai_score": round(score, 2),
            "per_criterion": {
                "content": round(score * 0.6, 2),
                "structure": round(score * 0.4, 2)
            },
            "feedback_bullets": [
                "Good understanding of the concept",
                "Could use more examples",
                "Well-structured response"
            ],
            "explanations": "Mock AI grading completed"
        }

    async def generate_questions(
        self,
        syllabus: str,
        topics: List[str],
        counts: Dict[str, int],
        difficulty_mix: Dict[str, float],
        types: List[str]
    ) -> List[Dict[str, Any]]:
        """Mock question generation"""
        questions = []
        question_id = 1

        for q_type in types:
            count = counts.get(q_type, 1)
            for i in range(count):
                question = {
                    "id": question_id,
                    "type": q_type,
                    "text": f"Mock {q_type} question {i+1} about {random.choice(topics)}",
                    "co_tags": [random.randint(1, 5)],
                    "difficulty": random.choice(["easy", "medium", "hard"]),
                    "confidence": round(random.uniform(0.7, 0.95), 2)
                }

                if q_type in ["mcq", "msq"]:
                    question["options"] = [
                        {"text": f"Option {j+1}", "is_correct": j == 0}
                        for j in range(4)
                    ]

                questions.append(question)
                question_id += 1

        return questions

    async def analyze_attainment(
        self,
        co_data: List[Dict[str, Any]],
        po_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Mock attainment analysis"""
        return {
            "co_attainments": {
                co["id"]: round(random.uniform(60, 95), 2)
                for co in co_data
            },
            "po_attainments": {
                po["id"]: round(random.uniform(65, 90), 2)
                for po in po_data
            },
            "insights": [
                "Overall attainment is good",
                "CO1 needs improvement",
                "PO2 shows strong performance"
            ]
        }

class OpenAIAdapter(LLMAdapter):
    """OpenAI GPT adapter"""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model

    async def grade_descriptive_answer(
        self,
        answer: str,
        model_answer: str,
        rubric: Dict[str, Any],
        strictness: float = 0.5
    ) -> Dict[str, Any]:
        # Implementation would call OpenAI API
        # Placeholder for now
        return await MockLLMAdapter().grade_descriptive_answer(
            answer, model_answer, rubric, strictness
        )

    async def generate_questions(
        self,
        syllabus: str,
        topics: List[str],
        counts: Dict[str, int],
        difficulty_mix: Dict[str, float],
        types: List[str]
    ) -> List[Dict[str, Any]]:
        # Implementation would call OpenAI API
        return await MockLLMAdapter().generate_questions(
            syllabus, topics, counts, difficulty_mix, types
        )

    async def analyze_attainment(
        self,
        co_data: List[Dict[str, Any]],
        po_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        # Implementation would call OpenAI API
        return await MockLLMAdapter().analyze_attainment(co_data, po_data)

# Factory function to get adapter
def get_llm_adapter(provider: str = "mock", **kwargs) -> LLMAdapter:
    if provider == "mock":
        return MockLLMAdapter()
    elif provider == "openai":
        return OpenAIAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")