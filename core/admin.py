from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Genre,
    Playlist,
    PlaylistGenre,
    PlaylistSong,
    Song,
)

admin.site.register(Genre)
admin.site.register(PlaylistGenre)
admin.site.register(PlaylistSong)
admin.site.register(Song)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail_preview",
        "title",
        "published_at",
        "duration",
        "position",
        "is_favorite",
    )
    list_filter = ("is_favorite", "published_at")
    search_fields = ("title",)
    actions = ["mark_as_favorite", "remove_from_favorites"]
    list_editable = ["is_favorite"]
    list_per_page = 100

    def thumbnail_preview(self, obj):
        """Display thumbnail preview in admin list view"""
        if obj.thumbnails:
            return format_html(
                '<img src="{}" style="max-height: 48px;"/>', obj.thumbnails
            )
        return "No thumbnail"

    thumbnail_preview.short_description = "Thumbnail"

    def mark_as_favorite(self, request, queryset):
        """Action to mark selected items as favorite"""
        queryset.update(is_favorite=True)

    mark_as_favorite.short_description = "Mark selected items as favorite"

    def remove_from_favorites(self, request, queryset):
        """Action to remove selected items from favorites"""
        queryset.update(is_favorite=False)

    remove_from_favorites.short_description = "Remove selected items from favorites"

    def get_search_results(self, request, queryset, search_term):
        """Enhanced search functionality"""
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        return queryset, True
