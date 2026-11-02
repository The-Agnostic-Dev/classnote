from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Classnote administration"

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("", include("reports.urls")),
    path("", include("notices.urls")),
]
