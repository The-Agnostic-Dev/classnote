from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import SchoolClass, Score, Student, Subject, Term
from .services import class_positions, grade_for, rank, remark_for, round_average, student_average


class GradeTests(TestCase):
    def test_grade_bands(self):
        cases = {95: "A", 85: "A", 65: "B", 60: "B", 55: "C", 50: "C", 47: "D", 45: "D", 42: "E", 40: "E", 39: "F", 0: "F"}
        for score, grade in cases.items():
            with self.subTest(score=score):
                self.assertEqual(grade_for(score), grade)

    def test_missing_score(self):
        self.assertEqual(grade_for(None), "-")

    def test_remarks(self):
        self.assertEqual(remark_for("A"), "Excellent")
        self.assertEqual(remark_for("F"), "Fail")

    def test_round_average(self):
        self.assertEqual(round_average(470, 6), Decimal("78.3"))
        self.assertEqual(round_average(327, 6), Decimal("54.5"))
        self.assertIsNone(round_average(0, 0))

    def test_rank_orders_best_first(self):
        self.assertEqual(rank({1: Decimal("55"), 2: Decimal("71.5"), 3: Decimal("60")}), {2: 1, 3: 2, 1: 3})

    def test_rank_highest_average_is_first(self):
        self.assertEqual(rank({1: Decimal("78.3"), 2: Decimal("74.0")}), {1: 1, 2: 2})

    def test_rank_ties_share_position_and_skip_next(self):
        self.assertEqual(rank({1: Decimal("70.0"), 2: Decimal("70.0"), 3: Decimal("65.0")}), {1: 1, 2: 1, 3: 3})


class ReportDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = timezone.localdate()
        cls.teacher = get_user_model().objects.create_user("teacher", password="pass-12345")
        cls.term = Term.objects.create(name="First Term", starts_on=today, ends_on=today, is_current=True)
        cls.school_class = SchoolClass.objects.create(name="JSS 1A", class_teacher=cls.teacher)
        cls.maths = Subject.objects.create(name="Mathematics", code="MTH")
        cls.english = Subject.objects.create(name="English Language", code="ENG")
        cls.ada = Student.objects.create(first_name="Ada", last_name="Obi", admission_no="1", school_class=cls.school_class)
        cls.bayo = Student.objects.create(first_name="Bayo", last_name="Ade", admission_no="2", school_class=cls.school_class)
        for student, scores in ((cls.ada, [(30, 50), (35, 45)]), (cls.bayo, [(20, 30), (25, 35)])):
            for subject, (ca, exam) in zip((cls.maths, cls.english), scores):
                Score.objects.create(student=student, subject=subject, term=cls.term, ca=ca, exam=exam)


class ScoreModelTests(ReportDataTestCase):
    def test_new_score_gets_a_total(self):
        score = Score.objects.get(student=self.ada, subject=self.maths)
        self.assertEqual(score.total, 80)

    def test_student_average(self):
        self.assertEqual(student_average(self.ada, self.term), Decimal("80.0"))
        self.assertEqual(student_average(self.bayo, self.term), Decimal("55.0"))

    def test_class_positions(self):
        self.assertEqual(class_positions(self.school_class, self.term), {self.ada.pk: 1, self.bayo.pk: 2})

    def test_class_positions_with_reported_averages(self):
        term = Term.objects.create(name="Regression Term", starts_on=self.term.starts_on, ends_on=self.term.ends_on)
        school_class = SchoolClass.objects.create(name="JSS 1A Regression", class_teacher=self.teacher)
        chiamaka = Student.objects.create(first_name="Chiamaka", last_name="Obi", admission_no="3", school_class=school_class)
        tunde = Student.objects.create(first_name="Tunde", last_name="Bakare", admission_no="4", school_class=school_class)
        subjects = [Subject.objects.create(name=f"Subject {i}", code=f"SUB{i}") for i in range(3)]
        for subject, ca, exam in zip(subjects, [(40, 38), (40, 38), (40, 39)]):
            Score.objects.create(student=chiamaka, subject=subject, term=term, ca=ca, exam=exam)
        for subject, ca, exam in zip(subjects, [(40, 34), (40, 34), (40, 34)]):
            Score.objects.create(student=tunde, subject=subject, term=term, ca=ca, exam=exam)
        positions = class_positions(school_class, term)
        self.assertEqual(positions[chiamaka.pk], 1)
        self.assertEqual(positions[tunde.pk], 2)


class ReportViewTests(ReportDataTestCase):
    def setUp(self):
        self.client.force_login(self.teacher)

    def test_results_require_login(self):
        self.client.logout()
        response = self.client.get(reverse("reports:results", args=[self.school_class.pk]))
        self.assertEqual(response.status_code, 302)

    def test_results_page(self):
        response = self.client.get(reverse("reports:results", args=[self.school_class.pk]))
        self.assertContains(response, "Ada Obi")
        self.assertContains(response, "80.0")

    def test_report_card(self):
        response = self.client.get(reverse("reports:report_card", args=[self.ada.pk]))
        self.assertContains(response, "Report card")
        self.assertContains(response, "Mathematics")
        self.assertContains(response, "160")

    def test_entering_scores_for_a_new_subject(self):
        science = Subject.objects.create(name="Basic Science", code="BSC")
        url = reverse("reports:enter_scores", args=[self.school_class.pk, science.pk])
        response = self.client.post(
            url,
            {
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "2",
                "form-0-student_id": self.ada.pk,
                "form-0-ca": "32",
                "form-0-exam": "51",
                "form-1-student_id": self.bayo.pk,
                "form-1-ca": "",
                "form-1-exam": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        score = Score.objects.get(student=self.ada, subject=science)
        self.assertEqual((score.ca, score.exam, score.total), (32, 51, 83))
        self.assertFalse(Score.objects.filter(student=self.bayo, subject=science).exists())

    def test_exam_over_sixty_is_rejected(self):
        url = reverse("reports:enter_scores", args=[self.school_class.pk, self.maths.pk])
        response = self.client.post(
            url,
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-0-student_id": self.ada.pk,
                "form-0-ca": "30",
                "form-0-exam": "75",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Score.objects.get(student=self.ada, subject=self.maths).exam, 50)
