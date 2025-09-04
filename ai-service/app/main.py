from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import random
import time
from datetime import datetime

app = FastAPI(title="DSBA LMS AI Service", version="1.0.0")

# Simple token validation
def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    if token != "internal_token_change_me":  # Should match backend config
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return token

# Request/Response models
class QuestionGenerationRequest(BaseModel):
    course_id: int
    course_title: str
    course_code: str
    topics: List[str]
    question_types: List[str]
    difficulty_distribution: Dict[str, int]
    total_questions: int
    total_marks: float
    available_cos: List[Dict[str, Any]]
    co_mappings: Dict[str, int]

class GradingRequest(BaseModel):
    question_text: str
    model_answer: Optional[str]
    student_answer: str
    max_marks: float
    rubric: Optional[Dict[str, Any]]
    strictness: str
    question_type: str

class ContentAnalysisRequest(BaseModel):
    course_id: int
    course_title: str
    content_text: str
    analysis_type: str

class COMappingRequest(BaseModel):
    course_id: int
    question_texts: List[str]
    available_cos: List[Dict[str, Any]]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "DSBA LMS AI Service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/generate-questions")
async def generate_questions(
    request: QuestionGenerationRequest,
    token: str = Depends(verify_token)
):
    """Mock AI question generation"""
    
    # Simulate processing time
    time.sleep(random.uniform(1, 3))
    
    questions = []
    marks_per_question = request.total_marks / request.total_questions
    
    for i in range(request.total_questions):
        topic = random.choice(request.topics)
        question_type = random.choice(request.question_types)
        difficulty = random.choices(
            list(request.difficulty_distribution.keys()),
            weights=list(request.difficulty_distribution.values())
        )[0]
        
        # Generate mock question based on type
        if question_type == "mcq":
            question = {
                "type": "mcq",
                "text": f"Mock MCQ question {i+1} about {topic} in {request.course_title}",
                "options": [
                    {"text": "Option A", "is_correct": True},
                    {"text": "Option B", "is_correct": False},
                    {"text": "Option C", "is_correct": False},
                    {"text": "Option D", "is_correct": False}
                ],
                "max_marks": marks_per_question,
                "difficulty": difficulty,
                "topic": topic,
                "co_id": request.available_cos[i % len(request.available_cos)]["id"] if request.available_cos else None,
                "confidence": random.uniform(0.7, 0.95)
            }
        elif question_type == "descriptive":
            question = {
                "type": "descriptive",
                "text": f"Mock descriptive question {i+1}: Explain the concept of {topic} in {request.course_title}",
                "model_answer": f"Sample answer for {topic} concept explanation...",
                "max_marks": marks_per_question,
                "difficulty": difficulty,
                "topic": topic,
                "co_id": request.available_cos[i % len(request.available_cos)]["id"] if request.available_cos else None,
                "rubric_json": {
                    "criteria": [
                        {"name": "Conceptual Understanding", "weight": 0.4, "max_score": marks_per_question * 0.4},
                        {"name": "Clarity of Explanation", "weight": 0.3, "max_score": marks_per_question * 0.3},
                        {"name": "Examples and Applications", "weight": 0.3, "max_score": marks_per_question * 0.3}
                    ]
                },
                "confidence": random.uniform(0.6, 0.9)
            }
        else:
            question = {
                "type": question_type,
                "text": f"Mock {question_type} question {i+1} about {topic}",
                "max_marks": marks_per_question,
                "difficulty": difficulty,
                "topic": topic,
                "co_id": request.available_cos[i % len(request.available_cos)]["id"] if request.available_cos else None,
                "confidence": random.uniform(0.5, 0.8)
            }
        
        questions.append(question)
    
    return {
        "questions": questions,
        "model_used": "mock-ai-v1.0",
        "processing_time": random.uniform(2, 5)
    }

@app.post("/grade")
async def grade_response(
    request: GradingRequest,
    token: str = Depends(verify_token)
):
    """Mock AI grading"""
    
    # Simulate processing time
    time.sleep(random.uniform(0.5, 2))
    
    # Mock grading logic
    if request.question_type == "descriptive":
        # Simple keyword matching for mock
        model_words = set(request.model_answer.lower().split()) if request.model_answer else set()
        student_words = set(request.student_answer.lower().split())
        
        overlap = len(model_words.intersection(student_words))
        total_model_words = len(model_words) if model_words else 1
        
        similarity_score = min(overlap / total_model_words, 1.0)
        
        # Adjust based on strictness
        if request.strictness == "strict":
            score = similarity_score * 0.8
        elif request.strictness == "lenient":
            score = min(similarity_score * 1.2, 1.0)
        else:  # standard
            score = similarity_score
        
        final_score = score * request.max_marks
        
        feedback = []
        if score >= 0.8:
            feedback.append("Excellent understanding demonstrated")
        elif score >= 0.6:
            feedback.append("Good grasp of concepts with room for improvement")
        else:
            feedback.append("Needs more detailed explanation and examples")
        
        return {
            "score": round(final_score, 2),
            "feedback": feedback,
            "confidence": random.uniform(0.7, 0.9),
            "model_used": "mock-nlp-grader-v1.0",
            "processing_time": random.uniform(1, 3)
        }
    
    else:
        # For other question types, return random score
        score = random.uniform(0.3, 1.0) * request.max_marks
        return {
            "score": round(score, 2),
            "feedback": ["Automated grading completed"],
            "confidence": random.uniform(0.8, 0.95),
            "model_used": "mock-auto-grader-v1.0",
            "processing_time": random.uniform(0.1, 0.5)
        }

@app.post("/analyze-content")
async def analyze_content(
    request: ContentAnalysisRequest,
    token: str = Depends(verify_token)
):
    """Mock content analysis"""
    
    time.sleep(random.uniform(1, 2))
    
    if request.analysis_type == "topics":
        # Extract mock topics
        topics = [
            "Programming Fundamentals",
            "Data Structures",
            "Algorithms",
            "Object-Oriented Programming",
            "Database Concepts"
        ]
        return {
            "topics": random.sample(topics, min(3, len(topics))),
            "confidence": random.uniform(0.8, 0.95)
        }
    
    elif request.analysis_type == "learning_objectives":
        objectives = [
            "Understand basic programming concepts",
            "Apply problem-solving techniques",
            "Analyze algorithmic complexity",
            "Design efficient data structures",
            "Evaluate different programming paradigms"
        ]
        return {
            "learning_objectives": random.sample(objectives, min(3, len(objectives))),
            "confidence": random.uniform(0.7, 0.9)
        }
    
    else:
        return {
            "analysis_result": f"Mock analysis for {request.analysis_type}",
            "confidence": random.uniform(0.6, 0.8)
        }

@app.post("/suggest-co-mappings")
async def suggest_co_mappings(
    request: COMappingRequest,
    token: str = Depends(verify_token)
):
    """Mock CO mapping suggestions"""
    
    time.sleep(random.uniform(0.5, 1))
    
    suggestions = []
    confidence_scores = []
    reasoning = []
    
    for i, question_text in enumerate(request.question_texts):
        # Random CO suggestion
        suggested_co = random.choice(request.available_cos)
        confidence = random.uniform(0.6, 0.9)
        
        suggestions.append(suggested_co["id"])
        confidence_scores.append(confidence)
        reasoning.append(f"Question {i+1} aligns with {suggested_co['code']} based on content analysis")
    
    return {
        "suggestions": suggestions,
        "confidence_scores": confidence_scores,
        "reasoning": reasoning
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)