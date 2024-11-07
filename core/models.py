from django.db import models
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from django.utils.text import slugify


class PlaylistManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                link=Concat(
                    Value("https://youtu.be/"),
                    "video_id",
                    output_field=CharField(),
                )
            )
        )


# Playlist Model
class Playlist(models.Model):
    video_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    thumbnails = models.URLField(max_length=500, blank=True, null=True)
    position = models.IntegerField(blank=True, null=True)
    video_owner_channel_title = models.CharField(max_length=255)
    video_owner_channel_id = models.CharField(max_length=255)
    duration = models.DurationField(blank=True, null=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    helpful_comment = models.TextField(blank=True, null=True)
    is_favorite = models.BooleanField(default=False)

    # Many-to-many relationships
    genres = models.ManyToManyField("Genre", through="PlaylistGenre")  # With Genre
    songs = models.ManyToManyField("Song", through="PlaylistSong")  # With Song

    objects = PlaylistManager()

    class Meta:
        ordering = ["position"]
        indexes = [models.Index(fields=["video_id", "position"])]

    def __str__(self):
        return self.title


# Song Model
class Song(models.Model):
    title = models.CharField(max_length=500, blank=True, null=True)
    artist = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=800, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:  # Only generate slug if it doesn't already exist
            slug_base = f"{self.artist or ''} {self.title or ''}"
            if slug_base:  # Ensure there's content to slugify
                self.slug = slugify(slug_base)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.artist}"


# Genre Model
class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:  # Only generate slug if it doesn't already exist
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# PlaylistSong (Intermediary Model for Playlist-Song Many-to-Many)
class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.CharField(
        max_length=20, blank=True, null=True
    )  # CharField for position

    class Meta:
        unique_together = ("playlist", "song")

    def __str__(self):
        return f"{self.song.title} in {self.playlist.title}"


# PlaylistGenre (Intermediary Model for Playlist-Genre Many-to-Many)
class PlaylistGenre(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("playlist", "genre")

    def __str__(self):
        return f"{self.playlist.title} - {self.genre.name}"
