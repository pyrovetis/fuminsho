import logging
import os
from typing import Optional

from django.core.cache import cache
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control

from core.models import Playlist, Genre, Song
from fuminsho import settings

logger = logging.getLogger(__name__)


class BaseView(View):
    template_name: str = None
    cache_timeout: int = 600

    @method_decorator(cache_control(max_age=600))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def render(self, context: Optional[dict] = None) -> HttpResponse:
        return render(self.request, self.template_name, context)


class IndexView(BaseView):
    template_name = "pages/index.html"

    def get(self, request):
        stats = cache.get("index_stats")
        if stats is None:
            stats = {
                "playlists_count": Playlist.objects.count(),
                "genres_count": Genre.objects.count(),
                "songs_count": Song.objects.count(),
            }
            cache.set("index_stats", stats, 24 * 60 * 60)  # Cache for 1 day

        context = {
            "stats": stats,
            "recent_playlists": Playlist.objects.values(
                "title", "link", "thumbnails"
            ).values("title", "link", "thumbnails")[:2],
        }
        return self.render(context)


class PlaylistListView(BaseView):
    template_name = "pages/playlists.html"

    def get(self, request):
        is_favorite = request.GET.get("favorite")
        all_playlists = Playlist.objects.prefetch_related(
            "genres", "songs", "playlistsong_set", "playlistsong_set__song"
        ).select_related()
        if is_favorite:
            all_playlists = all_playlists.filter(is_favorite=True)

        context = {"all_playlists": all_playlists}
        return self.render(context)


class SongListView(BaseView):
    template_name = "pages/songs.html"

    def get(self, request):
        all_songs = (
            Song.objects.annotate(count_playlists=Count("playlist"))
            .select_related()
            .order_by("-count_playlists")
        )

        context = {"all_songs": all_songs}
        return self.render(context)


class SongDetailView(BaseView):
    template_name = "pages/song.html"

    def get(self, request, slug):
        song = get_object_or_404(Song.objects.select_related(), slug=slug)
        playlists = song.playlist_set.prefetch_related(
            "genres", "songs", "playlistsong_set", "playlistsong_set__song"
        ).select_related()

        context = {
            "playlists": playlists,
            "song": song,
        }
        return self.render(context)


class GenreListView(BaseView):
    template_name = "pages/genres.html"

    def get(self, request):
        genres = (
            Genre.objects.annotate(count_playlists=Count("playlist"))
            .select_related()
            .order_by("-count_playlists")
            .all()
        )
        context = {"genres": genres}
        return self.render(context)


class GenreDetailView(BaseView):
    template_name = "pages/genre.html"

    def get(self, request, slug):
        genre = get_object_or_404(Genre, slug=slug)
        playlists = Playlist.objects.filter(genres=genre).prefetch_related(
            "genres", "songs", "playlistsong_set", "playlistsong_set__song"
        )

        context = {
            "genre": genre,
            "playlists": playlists,
        }
        return self.render(context)


class DonateView(BaseView):
    template_name = "pages/donate.html"

    def get(self, request):
        return self.render()


class LogsView(BaseView):
    template_name = "pages/logs.html"

    def get(self, request):
        log_file_path = os.path.join(settings.BASE_DIR, "logs.log")
        try:
            with open(log_file_path, "r", encoding="utf-8") as log_file:
                log_content = log_file.read()[-200_000:]

            context = {"log_content": log_content}
            return self.render(context)
        except FileNotFoundError:
            logger.error(f"Log file not found at {log_file_path}")
            return HttpResponse("Log file not found.", status=404)
        except Exception as e:
            logger.error(f"Error reading log file: {str(e)}")
            return HttpResponse("Error reading log file.", status=500)
