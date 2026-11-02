from django.contrib import admin

from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "pinned", "published_at", "expires_on"]
    list_filter = ["pinned", "audience"]
    search_fields = ["title", "body"]
    filter_horizontal = ["audience"]
