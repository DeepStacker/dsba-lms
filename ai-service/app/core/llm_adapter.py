from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import random
import json
import openai

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
        pass

    @abstractmethod
    async def analyze_attainment(
        self,
        co_data: List[Dict[str, Any]],
        po_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
        score = min(10.0, len(answer) / 50)
        if "correct" in answer.lower():
            score += 2
        if "example" in answer.lower():
            score += 1
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

    async def analyze_attainment(self, co_data: List[Dict[str, Any]], po_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "co_attainments": {co["id"]: round(random.uniform(60, 95), 2) for co in co_data},
            "po_attainments": {po["id"]: round(random.uniform(65, 90), 2) for po in po_data},
            "insights": [
                "Overall attainment is good",
                "CO1 needs improvement",
                "PO2 shows strong performance"
            ]
        }


class OpenAIAdapter(LLMAdapter):
    """OpenAI GPT adapter that uses HTTP to call OpenAI's Chat Completions API.

    If no API key is provided, methods fall back to the Mock adapter.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model

    async def grade_descriptive_answer(self, answer: str, model_answer: str, rubric: Dict[str, Any], strictness: float = 0.5) -> Dict[str, Any]:
        if not self.api_key:
            return await MockLLMAdapter().grade_descriptive_answer(answer, model_answer, rubric, strictness)

        import httpx

        prompt = (
            f"Grade the student answer against the model answer.\nModel answer:\n{model_answer}\n\n"
            f"Student answer:\n{answer}\n\nRubric:\n{rubric}\n\nReturn a JSON object with fields: ai_score (0-10), per_criterion (dict), feedback_bullets (list), explanations (string)."
        )

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0, "max_tokens": 500}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers)
            if resp.status_code != 200:
                return await MockLLMAdapter().grade_descriptive_answer(answer, model_answer, rubric, strictness)

            data = resp.json()
            text = ""
            try:
                text = data["choices"][0]["message"]["content"]
            except Exception:
                return await MockLLMAdapter().grade_descriptive_answer(answer, model_answer, rubric, strictness)

            try:
                parsed = json.loads(text)
                return parsed
            except Exception:
                return {"ai_score": 0, "per_criterion": {}, "feedback_bullets": [text[:200]], "explanations": text}

    async def generate_questions(self, syllabus: str, topics: List[str], counts: Dict[str, int], difficulty_mix: Dict[str, float], types: List[str]) -> List[Dict[str, Any]]:
        if not self.api_key:
            return await MockLLMAdapter().generate_questions(syllabus, topics, counts, difficulty_mix, types)

        import httpx

        prompt = (f"Generate questions for the syllabus:\n{syllabus}\nTopics: {topics}\nTypes: {types}\nCounts: {counts}\n")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 800}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers)
            if resp.status_code != 200:
                return await MockLLMAdapter().generate_questions(syllabus, topics, counts, difficulty_mix, types)
            data = resp.json()
            text = data.get("choices", [])[0].get("message", {}).get("content", "")

            try:
                parsed = json.loads(text)
                return parsed.get("questions", parsed)
            except Exception:
                return await MockLLMAdapter().generate_questions(syllabus, topics, counts, difficulty_mix, types)

    async def analyze_attainment(self, co_data: List[Dict[str, Any]], po_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.api_key:
            return await MockLLMAdapter().analyze_attainment(co_data, po_data)

        return await MockLLMAdapter().analyze_attainment(co_data, po_data)


# Factory
def get_llm_adapter(provider: str = "mock", **kwargs) -> LLMAdapter:
    if provider == "mock":
        return MockLLMAdapter()
    if provider == "openai":
        return OpenAIAdapter(**kwargs)
                client = openai.AsyncOpenAI(api_key=self.api_key)

                prompt = (f"Analyze CO and PO attainment data and provide insights.\nCO Data:\n{json.dumps(co_data, indent=2)}\n\nPO Data:\n{json.dumps(po_data, indent=2)}\n\nReturn a JSON object with fields: co_attainments (dict), po_attainments (dict), insights (list).")

                try:
                    chat_completion = await client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=self.model,
                        temperature=0.0,
                        max_tokens=500,
                    )
                    text = chat_completion.choices[0].message.content
                    try:
                        parsed = json.loads(text)
                        return parsed
                    except json.JSONDecodeError:
                        print(f"Failed to parse JSON for attainment analysis. Raw text: {text[:500]}")
                        return {"co_attainments": {}, "po_attainments": {}, "insights": [text[:200]]}
                except Exception as e:
                    print(f"OpenAI API error during attainment analysis: {e}")
                    return await MockLLMAdapter().analyze_attainment(co_data, po_data)
    raise ValueError(f"Unknown provider: {provider}")