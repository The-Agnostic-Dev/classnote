from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models

CA_MAX = 40
EXAM_MAX = 60


class SchoolClass(models.Model):
    name = models.CharField(max_length=40, unique=True)
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="form_classes",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "class"
        verbose_name_plural = "classes"

    def __str__(self) -> str:
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=60, unique=True)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Term(models.Model):
    name = models.CharField(max_length=60, unique=True)
    starts_on = models.DateField()
    ends_on = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-starts_on"]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def current(cls) -> "Term | None":
        return cls.objects.filter(is_current=True).first() or cls.objects.first()


class Student(models.Model):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    admission_no = models.CharField(max_length=20, unique=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name="students")

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Score(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="scores")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="scores")
    term = models.ForeignKey(Term, on_delete=models.PROTECT, related_name="scores")
    ca = models.PositiveSmallIntegerField("CA", validators=[MaxValueValidator(CA_MAX)])
    exam = models.PositiveSmallIntegerField(validators=[MaxValueValidator(EXAM_MAX)])
    total = models.PositiveSmallIntegerField(default=0, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "subject", "term"], name="one_score_per_subject_term"),
        ]
        ordering = ["subject__name"]

    def __str__(self) -> str:
        return f"{self.student} / {self.subject} / {self.term}: {self.total}"
