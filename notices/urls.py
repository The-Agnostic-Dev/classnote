from django.urls import path

from . import views

app_name = "notices"

urlpatterns = [
    path("", views.board, name="board"),
    path("notices/<int:pk>/", views.detail, name="detail"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("notices/new/", views.create, name="create"),
    path("notices/<int:pk>/edit/", views.edit, name="edit"),
    path("notices/<int:pk>/delete/", views.delete, name="delete"),
]
