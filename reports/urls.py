from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("classes/", views.class_list, name="class_list"),
    path("classes/<int:pk>/results/", views.results, name="results"),
    path("classes/<int:pk>/scores/<int:subject_pk>/", views.enter_scores, name="enter_scores"),
    path("students/<int:pk>/report/", views.report_card, name="report_card"),
]
