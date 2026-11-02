from django.contrib import admin

from .models import SchoolClass, Score, Student, Subject, Term


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ["name", "class_teacher"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["admission_no", "last_name", "first_name", "school_class"]
    list_filter = ["school_class"]
    search_fields = ["first_name", "last_name", "admission_no"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ["name", "starts_on", "ends_on", "is_current"]


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ["student", "subject", "term", "ca", "exam", "total"]
    list_filter = ["term", "subject", "student__school_class"]
