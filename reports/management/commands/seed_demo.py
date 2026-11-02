"""Load Greenfield Model College demo data. Dates are relative to today."""

from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from notices.models import Notice
from reports.models import SchoolClass, Score, Student, Subject, Term

DEMO_PASSWORD = "classnote2026"

TEACHERS = [
    ("mrs.adeyemi", "Funke", "Adeyemi", False),
    ("mr.okafor", "Chinedu", "Okafor", False),
    ("principal", "Grace", "Bassey", True),
]

SUBJECTS = [
    ("English Language", "ENG"),
    ("Mathematics", "MTH"),
    ("Basic Science", "BSC"),
    ("Social Studies", "SOS"),
    ("Civic Education", "CVE"),
    ("Computer Studies", "CPS"),
]

# Totals out of 100 per subject, in SUBJECTS order: (current term, previous term)
STUDENTS = {
    "JSS 1A": [
        ("Chiamaka", "Obi", [82, 70, 85, 80, 78, 75], [45, 40, 50, 42, 48, 44]),
        ("Tunde", "Bakare", [75, 80, 72, 70, 74, 73], [76, 78, 74, 72, 75, 77]),
        ("Emeka", "Nwosu", [66, 68, 64, 70, 62, 66], [66, 68, 64, 70, 62, 66]),
        ("Ngozi", "Eze", [66, 68, 64, 70, 62, 66], [66, 68, 64, 70, 62, 66]),
        ("Aisha", "Bello", [60, 58, 63, 61, 59, 62], [61, 60, 62, 59, 60, 63]),
        ("Kelechi", "Uzo", [55, 52, 57, 54, 56, 53], [54, 53, 55, 52, 56, 54]),
        ("Folake", "Adebayo", [48, 45, 50, 47, 49, 46], [50, 47, 49, 48, 46, 45]),
        ("Ibrahim", "Musa", [40, 38, 44, 41, 39, 42], [42, 40, 41, 43, 39, 40]),
    ],
    "JSS 2B": [
        ("Zainab", "Lawal", [88, 84, 90, 79, 83, 86], [85, 82, 88, 80, 81, 84]),
        ("Segun", "Afolabi", [71, 65, 69, 74, 68, 72], [70, 66, 67, 73, 69, 71]),
        ("Blessing", "Okon", [64, 61, 59, 66, 63, 60], [62, 60, 58, 65, 61, 59]),
        ("Uche", "Nnaji", [57, 49, 52, 58, 55, 51], [56, 50, 53, 57, 54, 52]),
        ("Halima", "Sani", [46, 42, 48, 44, 47, 43], [45, 41, 47, 46, 44, 42]),
        ("David", "Etim", [35, 39, 33, 41, 37, 36], [38, 36, 35, 40, 34, 39]),
    ],
}


def split(total: int) -> tuple[int, int]:
    """Split a total into CA (out of 40) and exam (out of 60)."""
    ca = min(40, round(total * 0.4))
    return ca, total - ca


class Command(BaseCommand):
    help = "Reset the database to the Greenfield Model College demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        Notice.objects.all().delete()
        Score.objects.all().delete()
        Student.objects.all().delete()
        SchoolClass.objects.all().delete()
        Subject.objects.all().delete()
        Term.objects.all().delete()
        User.objects.filter(username__in=[t[0] for t in TEACHERS]).delete()

        users = {}
        for username, first, last, is_admin in TEACHERS:
            user = User(username=username, first_name=first, last_name=last, is_staff=is_admin, is_superuser=is_admin)
            user.set_password(DEMO_PASSWORD)
            user.save()
            users[username] = user

        today = timezone.localdate()
        current = Term.objects.create(
            name="2026/2027 First Term",
            starts_on=today - timedelta(days=60),
            ends_on=today + timedelta(days=40),
            is_current=True,
        )
        previous = Term.objects.create(
            name="2025/2026 Third Term",
            starts_on=today - timedelta(days=200),
            ends_on=today - timedelta(days=110),
        )

        subjects = [Subject.objects.create(name=name, code=code) for name, code in SUBJECTS]
        classes = {
            "JSS 1A": SchoolClass.objects.create(name="JSS 1A", class_teacher=users["mrs.adeyemi"]),
            "JSS 2B": SchoolClass.objects.create(name="JSS 2B", class_teacher=users["mr.okafor"]),
        }

        admission = 1000
        for class_name, rows in STUDENTS.items():
            for first, last, now_totals, before_totals in rows:
                admission += 1
                student = Student.objects.create(
                    first_name=first,
                    last_name=last,
                    admission_no=f"GMC/{admission}",
                    school_class=classes[class_name],
                )
                for term, totals in ((current, now_totals), (previous, before_totals)):
                    for subject, total in zip(subjects, totals):
                        ca, exam = split(total)
                        Score.objects.create(student=student, subject=subject, term=term, ca=ca, exam=exam)

        self.seed_notices(users, classes, today)
        self.stdout.write(self.style.SUCCESS(f"Demo data loaded. Teacher password: {DEMO_PASSWORD}"))

    def seed_notices(self, users, classes, today):
        def at(days_ago: int, hour: int = 8, minute: int = 0):
            day = today - timedelta(days=days_ago)
            return timezone.make_aware(datetime.combine(day, time(hour, minute)))

        notices = [
            dict(title="Welcome back: First Term timetable", author="principal", pinned=True, published_at=at(20),
                 body="Welcome back, everyone. The full First Term timetable is up in every classroom. "
                      "Lessons start at 7:45 sharp, assembly is on Mondays and Fridays."),
            dict(title="School fees deadline", author="principal", pinned=True, published_at=at(10),
                 expires_on=today + timedelta(days=20),
                 body="Second instalment of school fees is due by the end of the month. "
                      "Please bring the bank teller to the bursary."),
            dict(title="Mid-term break dates", author="principal", published_at=at(5, 14, 15),
                 body="Mid-term break runs from Thursday to the following Monday. School resumes on Tuesday."),
            dict(title="PTA meeting this evening", author="principal", published_at=at(3, 9, 30),
                 expires_on=today,
                 body="Parents and guardians are invited to the PTA meeting in the main hall at 5 pm today."),
            dict(title="Science fair projects", author="mrs.adeyemi", published_at=at(2, 13, 0),
                 classes=["JSS 1A"],
                 body="JSS 1A projects are due two weeks from today. Groups of three, one poster per group."),
            dict(title="Excursion consent forms", author="mr.okafor", published_at=at(1, 11, 45),
                 classes=["JSS 2B"], expires_on=today + timedelta(days=5),
                 body="Please return signed consent forms for the National Museum excursion by Friday."),
            dict(title="Inter-house sports: early start", author="mr.okafor", published_at=at(0, 0, 30),
                 body="Athletes should be on the field by 7 am in house colours. Spectators from 9 am."),
            dict(title="Library books overdue", author="mrs.adeyemi", published_at=at(12),
                 expires_on=today - timedelta(days=1),
                 body="Please return all library books borrowed last term."),
        ]
        for data in notices:
            class_names = data.pop("classes", [])
            data["author"] = users[data["author"]]
            notice = Notice.objects.create(**data)
            notice.audience.set([classes[name] for name in class_names])
