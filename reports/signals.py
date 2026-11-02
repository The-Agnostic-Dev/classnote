from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Score


@receiver(post_save, sender=Score)
def store_score_total(sender, instance: Score, created: bool, **kwargs) -> None:
    """Keep the denormalised total in step with CA + exam."""
    if created:
        total = instance.ca + instance.exam
        Score.objects.filter(pk=instance.pk).update(total=total)
        instance.total = total
