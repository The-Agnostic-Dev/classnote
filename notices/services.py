"""Notice board queries. The board is cached because parents hit it far more
often than teachers post to it."""

from datetime import date, datetime

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from reports.models import SchoolClass

from .models import Notice

BOARD_CACHE_KEY = "notices:board"


def active_notices(today: date | None = None) -> list[Notice]:
    today = today or timezone.localdate()
    queryset = (
        Notice.objects.filter(Q(expires_on__isnull=True) | Q(expires_on__gte=today))
        .select_related("author")
        .prefetch_related("audience")
    )
    return list(queryset.order_by("pinned", "-published_at"))


def board_notices() -> list[Notice]:
    return cache.get_or_set(BOARD_CACHE_KEY, active_notices, settings.NOTICE_BOARD_CACHE_SECONDS)


def invalidate_board() -> None:
    cache.delete(BOARD_CACHE_KEY)


def notices_for_class(notices: list[Notice], school_class: SchoolClass | None) -> list[Notice]:
    if school_class is None:
        return notices
    return [notice for notice in notices if school_class in notice.audience.all()]


def posted_label(published_at: datetime, today: date | None = None) -> str | None:
    """Friendly 'Today' / 'Yesterday' / 'N days ago' for recent notices."""
    today = today or timezone.localdate()
    days = (today - timezone.localdate(published_at)).days
    if days <= 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days} days ago"
    return None
