from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from reports.models import SchoolClass


class Notice(models.Model):
    title = models.CharField(max_length=120)
    body = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="notices")
    audience = models.ManyToManyField(
        SchoolClass,
        blank=True,
        related_name="notices",
        help_text="Leave empty to post to the whole school.",
    )
    pinned = models.BooleanField(default=False, help_text="Pinned notices stay at the top of the board.")
    published_at = models.DateTimeField(default=timezone.now)
    expires_on = models.DateField(
        null=True,
        blank=True,
        help_text="Last day the notice is shown. Leave empty to keep it up.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("notices:detail", args=[self.pk])

    @property
    def audience_label(self) -> str:
        names = [school_class.name for school_class in self.audience.all()]
        return ", ".join(names) if names else "Whole school"
