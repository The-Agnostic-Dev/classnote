"""Grades, averages and class positions for report cards."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, Sum

from .models import SchoolClass, Score, Student, Term

ONE_DP = Decimal("0.1")

REMARKS = {
    "A": "Excellent",
    "B": "Very good",
    "C": "Good",
    "D": "Fair",
    "E": "Pass",
    "F": "Fail",
}


def grade_for(score: Decimal | int | None) -> str:
    """WAEC-style letter grade for a score out of 100."""
    if score is None:
        return "-"
    if score > 70:
        return "A"
    if score >= 60:
        return "B"
    if score >= 50:
        return "C"
    if score >= 45:
        return "D"
    if score >= 40:
        return "E"
    return "F"


def remark_for(grade: str) -> str:
    return REMARKS.get(grade, "")


def round_average(points: int, subjects: int) -> Decimal | None:
    if not subjects:
        return None
    return (Decimal(points) / Decimal(subjects)).quantize(ONE_DP, rounding=ROUND_HALF_UP)


def student_average(student: Student, term: Term) -> Decimal | None:
    totals = Score.objects.filter(student=student, term=term).aggregate(points=Sum("total"), subjects=Count("id"))
    return round_average(totals["points"] or 0, totals["subjects"])


def rank(averages: dict[int, Decimal]) -> dict[int, int]:
    """Map student id to class position, best average first."""
    ordered = sorted(averages.items(), key=lambda item: item[1], reverse=True)
    return {student_id: index + 1 for index, (student_id, _average) in enumerate(ordered)}


def class_positions(school_class: SchoolClass, term: Term) -> dict[int, int]:
    rows = (
        Score.objects.filter(student__school_class=school_class)
        .values("student_id")
        .annotate(points=Sum("total"), subjects=Count("id"))
    )
    averages = {row["student_id"]: Decimal(row["points"]) / row["subjects"] for row in rows}
    return rank(averages)


@dataclass
class ResultRow:
    student: Student
    average: Decimal | None
    position: int | None
    grade: str


def class_results(school_class: SchoolClass, term: Term) -> list[ResultRow]:
    positions = class_positions(school_class, term)
    rows = []
    for student in school_class.students.all():
        average = student_average(student, term)
        rows.append(
            ResultRow(
                student=student,
                average=average,
                position=positions.get(student.pk) if average is not None else None,
                grade=grade_for(average),
            )
        )
    rows.sort(key=lambda row: (row.position is None, row.position or 0, row.student.last_name))
    return rows


@dataclass
class SubjectLine:
    subject: str
    ca: int
    exam: int
    total: int
    grade: str
    remark: str


def report_lines(student: Student, term: Term) -> list[SubjectLine]:
    scores = Score.objects.filter(student=student, term=term).select_related("subject")
    lines = []
    for score in scores:
        grade = grade_for(score.total)
        lines.append(
            SubjectLine(
                subject=score.subject.name,
                ca=score.ca,
                exam=score.exam,
                total=score.total,
                grade=grade,
                remark=remark_for(grade),
            )
        )
    return lines
