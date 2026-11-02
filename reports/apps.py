from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reports"
    verbose_name = "Report cards"

    def ready(self) -> None:
        from . import signals  # noqa: F401
