from django.urls import path

from core.views import (
    IndexView,
    PlaylistListView,
    SongListView,
    SongDetailView,
    GenreListView,
    GenreDetailView,
    DonateView,
    LogsView,
)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("playlists/", PlaylistListView.as_view(), name="playlists"),
    path("songs/", SongListView.as_view(), name="songs"),
    path("songs/<slug:slug>/", SongDetailView.as_view(), name="song"),
    path("genres/", GenreListView.as_view(), name="genres"),
    path("genres/<slug:slug>/", GenreDetailView.as_view(), name="genre"),
    path("donate/", DonateView.as_view(), name="donate"),
    path("logs/", LogsView.as_view(), name="logs"),
]
