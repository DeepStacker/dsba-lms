from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

# Grade bands configuration (can be made configurable)
GRADE_BANDS = {
    "O": 10.0,
    "A+": 9.0,
    "A": 8.0,
    "B+": 7.0,
    "B": 6.0,
    "C": 5.0,
    "D": 4.0,
    "F": 0.0
}

def get_grade_point(percentage: float) -> float:
    """Convert percentage to grade point"""
    if percentage >= 90:
        return GRADE_BANDS["O"]
    elif percentage >= 80:
        return GRADE_BANDS["A+"]
    elif percentage >= 70:
        return GRADE_BANDS["A"]
    elif percentage >= 60:
        return GRADE_BANDS["B+"]
    elif percentage >= 50:
        return GRADE_BANDS["B"]
    elif percentage >= 40:
        return GRADE_BANDS["C"]
    elif percentage >= 35:
        return GRADE_BANDS["D"]
    else:
        return GRADE_BANDS["F"]

def calculate_sgpa(course_grades: List[Dict[str, Any]]) -> float:
    """
    Calculate SGPA from course grades
    course_grades: List of {"course_code": str, "grade_point": float, "credits": int}
    """
    total_credits = sum(course["credits"] for course in course_grades)
    if total_credits == 0:
        return 0.0

    weighted_sum = sum(
        course["grade_point"] * course["credits"]
        for course in course_grades
    )

    sgpa = weighted_sum / total_credits
    return float(Decimal(str(sgpa)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def calculate_cgpa(sgpa_list: List[float], semester_credits: List[int]) -> float:
    """
    Calculate CGPA from SGPA list and corresponding semester credits
    """
    if not sgpa_list or not semester_credits or len(sgpa_list) != len(semester_credits):
        return 0.0

    total_credits = sum(semester_credits)
    if total_credits == 0:
        return 0.0

    weighted_sum = sum(
        sgpa * credits
        for sgpa, credits in zip(sgpa_list, semester_credits)
    )

    cgpa = weighted_sum / total_credits
    return float(Decimal(str(cgpa)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def calculate_co_attainment(responses: List[Dict[str, Any]], co_id: int) -> float:
    """
    Calculate CO attainment percentage from responses
    responses: List of {"question_id": int, "score": float, "max_marks": float, "co_id": int}
    """
    co_responses = [r for r in responses if r.get("co_id") == co_id]
    if not co_responses:
        return 0.0

    total_max = sum(r["max_marks"] for r in co_responses)
    total_score = sum(r["score"] for r in co_responses)

    if total_max == 0:
        return 0.0

    return (total_score / total_max) * 100

def calculate_po_attainment(
    co_attainments: Dict[int, float],
    co_po_map: Dict[int, List[Dict[str, Any]]]
) -> Dict[int, float]:
    """
    Calculate PO attainment from CO attainments and CO-PO mapping
    co_attainments: {co_id: attainment_percentage}
    co_po_map: {co_id: [{"po_id": int, "weight": float}]}
    """
    po_attainments = {}

    for co_id, attainment in co_attainments.items():
        if co_id in co_po_map:
            for mapping in co_po_map[co_id]:
                po_id = mapping["po_id"]
                weight = mapping["weight"]

                if po_id not in po_attainments:
                    po_attainments[po_id] = 0.0

                po_attainments[po_id] += attainment * weight

    # Normalize PO attainments (assuming weights sum to 1 per PO)
    for po_id in po_attainments:
        po_attainments[po_id] = min(po_attainments[po_id], 100.0)

    return po_attainments

def get_grade_letter(percentage: float) -> str:
    """Get grade letter from percentage"""
    if percentage >= 90:
        return "O"
    elif percentage >= 80:
        return "A+"
    elif percentage >= 70:
        return "A"
    elif percentage >= 60:
        return "B+"
    elif percentage >= 50:
        return "B"
    elif percentage >= 40:
        return "C"
    elif percentage >= 35:
        return "D"
    else:
        return "F"