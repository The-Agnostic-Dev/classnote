from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ScoreFormSet
from .models import CA_MAX, EXAM_MAX, SchoolClass, Score, Student, Subject, Term
from .services import class_positions, class_results, grade_for, report_lines, student_average


def selected_term(request) -> Term:
    term_id = request.GET.get("term")
    term = Term.objects.filter(pk=term_id).first() if term_id and term_id.isdigit() else None
    return term or Term.current()


@login_required
def class_list(request):
    classes = SchoolClass.objects.select_related("class_teacher").prefetch_related("students")
    return render(
        request,
        "reports/class_list.html",
        {"classes": classes, "subjects": Subject.objects.all(), "term": Term.current()},
    )


@login_required
def results(request, pk: int):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    term = selected_term(request)
    return render(
        request,
        "reports/results.html",
        {
            "school_class": school_class,
            "term": term,
            "terms": Term.objects.all(),
            "rows": class_results(school_class, term),
            "subjects": Subject.objects.all(),
        },
    )


@login_required
def enter_scores(request, pk: int, subject_pk: int):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    subject = get_object_or_404(Subject, pk=subject_pk)
    term = selected_term(request)
    students = list(school_class.students.all())
    existing = {
        score.student_id: score
        for score in Score.objects.filter(student__in=students, subject=subject, term=term)
    }

    if request.method == "POST":
        formset = ScoreFormSet(request.POST)
        if formset.is_valid():
            by_id = {student.pk: student for student in students}
            with transaction.atomic():
                for row in formset.cleaned_data:
                    student = by_id.get(row.get("student_id"))
                    if student is None or row.get("ca") is None:
                        continue
                    Score.objects.update_or_create(
                        student=student,
                        subject=subject,
                        term=term,
                        defaults={"ca": row["ca"], "exam": row["exam"]},
                    )
            messages.success(request, f"{subject.name} scores saved for {school_class.name}.")
            url = reverse("reports:enter_scores", args=[school_class.pk, subject.pk])
            return redirect(f"{url}?term={term.pk}")
    else:
        formset = ScoreFormSet(
            initial=[
                {
                    "student_id": student.pk,
                    "ca": getattr(existing.get(student.pk), "ca", None),
                    "exam": getattr(existing.get(student.pk), "exam", None),
                }
                for student in students
            ]
        )

    return render(
        request,
        "reports/scores.html",
        {
            "school_class": school_class,
            "subject": subject,
            "term": term,
            "rows": zip(students, formset.forms),
            "formset": formset,
            "ca_max": CA_MAX,
            "exam_max": EXAM_MAX,
        },
    )


@login_required
def report_card(request, pk: int):
    student = get_object_or_404(Student.objects.select_related("school_class__class_teacher"), pk=pk)
    term = selected_term(request)
    lines = report_lines(student, term)
    average = student_average(student, term)
    position = class_positions(student.school_class, term).get(student.pk) if lines else None
    return render(
        request,
        "reports/report_card.html",
        {
            "student": student,
            "term": term,
            "terms": Term.objects.all(),
            "lines": lines,
            "total_points": sum(line.total for line in lines),
            "average": average,
            "overall_grade": grade_for(average),
            "position": position,
            "class_size": student.school_class.students.count(),
        },
    )

