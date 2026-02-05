import hashlib
import json
import logging
import re
from dataclasses import dataclass
from typing import List, Optional

import httpx
import isodate
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from core.models import Genre, Playlist, Song
from fuminsho.settings import env

logger = logging.getLogger("fuminsho")


@dataclass(frozen=True)
class PlaylistItem:
    video_id: str
    title: str
    description: str
    thumbnails: str
    position: int
    video_owner_channel_title: str
    video_owner_channel_id: str


@dataclass(frozen=True)
class Track:
    artist: Optional[str]
    title: Optional[str]
    timestamp: Optional[str]


@dataclass(frozen=True)
class PlaylistMetadata:
    genres: Optional[List[str]]
    tracks: Optional[List[Track]]


class PlaylistManager:
    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
    OPENROUTER_API_BASE = "https://openrouter.ai/api/v1/chat/completions"
    BATCH_SIZE = 50
    FTP_DIRECTORY = "/"
    AI_MODEL = "mistralai/ministral-3b"

    def __init__(self, playlist_id: str):
        self.playlist_id = playlist_id
        self.playlist_last_video_id = env("PLAYLIST_LAST_VIDEO_ID")
        self.google_api_key = env("GOOGLE_API_KEY")
        self.openrouter_api_key = env("OPENROUTER_API_KEY")
        self.http_client = httpx.Client(timeout=60)
        logger.info(f"🚀 Starting PlaylistManager for 📂 Playlist ID: {playlist_id}")

    def fetch_playlist_items(self, page_token: Optional[str] = None) -> dict:
        logger.info(f"🔍 Fetching items for 📂 Playlist ID: {self.playlist_id}")
        params = {
            "key": self.google_api_key,
            "part": "snippet",
            "maxResults": self.BATCH_SIZE,
            "playlistId": self.playlist_id,
        }
        if page_token:
            params.update({"pageToken": page_token})

        endpoint = f"{self.YOUTUBE_API_BASE}/playlistItems"
        response = self.http_client.get(endpoint, params=params)
        return response.json()

    def parse_playlist_items(self, data: dict) -> List[PlaylistItem]:
        logger.info(f"🧩 Parsing items for 📂 Playlist ID: {self.playlist_id}")
        items = []
        for item in data["items"]:
            snippet = item["snippet"]
            if snippet["title"] in ("Deleted video", "Private video"):
                continue

            playlist_item = PlaylistItem(
                video_id=snippet["resourceId"]["videoId"],
                title=snippet["title"],
                description=snippet["description"],
                thumbnails=self.get_last_thumbnail(snippet["thumbnails"]),
                position=snippet["position"],
                video_owner_channel_title=snippet.get("videoOwnerChannelTitle", ""),
                video_owner_channel_id=snippet.get("videoOwnerChannelId", ""),
            )
            items.append(playlist_item)
        return items

    def bulk_update_db(self, playlist: List[PlaylistItem]):
        if not playlist:
            logger.info(
                f"📭 No new items to add for 📂 Playlist ID: {self.playlist_id}"
            )
            return

        video_ids = [video.video_id for video in playlist]
        existing_videos = Playlist.objects.filter(video_id__in=video_ids)
        existing_video_ids = set(existing_videos.values_list("video_id", flat=True))

        creates = []
        now = timezone.now()

        for video in playlist:
            key_args = {
                "video_id": video.video_id,
                "title": video.title,
                "description": video.description,
                "thumbnails": video.thumbnails,
                "position": video.position,
                "video_owner_channel_title": video.video_owner_channel_title,
                "video_owner_channel_id": video.video_owner_channel_id,
                "fetched_at": now,
            }

            if video.video_id in existing_video_ids:
                logger.info(f"🔄 Updating video 🆔 {video.video_id} in DB")
                existing_videos.filter(video_id=video.video_id).update(**key_args)
            else:
                logger.info(f"➕ Adding video 🆔 {video.video_id} to DB")
                creates.append(Playlist(**key_args))

        if creates:
            logger.info(f"📦 Bulk adding {len(creates)} videos to DB")
            Playlist.objects.bulk_create(creates)

    def generate_playlist(
        self, page_token: Optional[str] = None, full_scan: Optional[bool] = False
    ):
        logger.info(
            f"🛠️ Creating playlist for 📂 Playlist ID: {self.playlist_id} | Token: {page_token} | Full Scan: {full_scan}"
        )
        data = self.fetch_playlist_items(page_token)
        next_page_token = data.get("nextPageToken", None)
        playlist_items = self.parse_playlist_items(data)

        first_video_id = Playlist.objects.first() and Playlist.objects.first().video_id
        last_video_id = Playlist.objects.last() and Playlist.objects.last().video_id

        playlist_items_video_ids = [item.video_id for item in playlist_items]

        if (
            first_video_id in playlist_items_video_ids
            and not full_scan
            and last_video_id == self.playlist_last_video_id
        ):
            next_page_token = None

        self.bulk_update_db(playlist_items)
        self.update_comments(playlist_items)
        self.update_video_metadata(playlist_items)

        if next_page_token:
            self.generate_playlist(next_page_token)

    def fetch_comments(self, video_id: str) -> dict:
        logger.info(f"💬 Fetching comments for video 🆔 {video_id}")
        params = {
            "key": self.google_api_key,
            "part": "snippet",
            "maxResults": 5,
            "videoId": video_id,
            "order": "relevance",
        }
        endpoint = f"{self.YOUTUBE_API_BASE}/commentThreads"
        response = self.http_client.get(endpoint, params=params)
        return response.json()

    def parse_comments(self, data: dict) -> Optional[str]:
        log_data = (
            data["items"][0]["snippet"]["videoId"] if data.get("items", None) else None
        )
        logger.info(f"💬 Parsing comments for video 🆔 {log_data}")
        for item in data.get("items", []):
            content = item["snippet"]["topLevelComment"]["snippet"]
            is_author_youtube = content["authorDisplayName"] == "YouTube"
            contains_track_list = self.check_comment_for_track_list(
                content["textOriginal"]
            )
            if not is_author_youtube and contains_track_list:
                return content["textOriginal"]
        return None

    def check_comment_for_track_list(self, comment: str) -> bool:
        pattern = r"\w+ - \w"
        return len(re.findall(pattern, comment)) >= 3

    def update_comments(self, playlist: List[PlaylistItem]):
        logger.info(f"💬 Updating comments for 📂 Playlist ID: {self.playlist_id}")
        video_ids = [item.video_id for item in playlist]
        existing_videos = Playlist.objects.filter(
            video_id__in=video_ids, helpful_comment__isnull=True
        )

        for video in existing_videos:
            comments = self.fetch_comments(video.video_id)
            helpful_comment = self.parse_comments(comments)
            video.helpful_comment = helpful_comment or ""
            video.save(update_fields=["helpful_comment"])

    def fetch_video_metadata(self, video_id: str) -> dict:
        logger.info(f"⏳ Fetching video metadata for video 🆔 {video_id}")
        params = {
            "key": self.google_api_key,
            "part": "contentDetails,snippet",
            "id": video_id,
        }
        endpoint = f"{self.YOUTUBE_API_BASE}/videos"
        response = self.http_client.get(endpoint, params=params)
        return response.json()

    def update_video_metadata(self, playlist: List[PlaylistItem]):
        logger.info(
            f"⏳ Updating video metadata for 📂 Playlist ID: {self.playlist_id}"
        )
        video_ids = [item.video_id for item in playlist]
        existing_videos = Playlist.objects.filter(
            video_id__in=video_ids, duration__isnull=True
        )

        for video in existing_videos:
            response = self.fetch_video_metadata(video.video_id)
            duration = isodate.parse_duration(
                response["items"][0]["contentDetails"]["duration"]
            )
            published_at = isodate.parse_datetime(
                response["items"][0]["snippet"]["publishedAt"]
            )
            video.duration = duration
            video.published_at = published_at
            video.save(update_fields=["duration", "published_at"])

    def parse_metadata(self, response: dict) -> PlaylistMetadata:
        logger.info(f"📜 Parsing metadata for 📂 Playlist ID: {self.playlist_id}")
        genres = self.parse_metadata_genres(response)
        tracks = self.parse_metadata_tracks(response)
        return PlaylistMetadata(genres=genres, tracks=tracks)

    def parse_metadata_genres(self, response: dict) -> Optional[list[str]]:
        if not isinstance(response, (list, dict)):
            return None

        if isinstance(response, list):
            return [item for item in response if isinstance(item, str)] or None

        return response.get("genres", None)

    def parse_metadata_tracks(self, response: dict) -> Optional[list[Track]]:
        if not isinstance(response, (list, dict)):
            return None

        tracks_array = (
            response if isinstance(response, list) else response.get("tracks", None)
        )

        if not tracks_array or not isinstance(tracks_array, list):
            return None

        result = []

        for item in tracks_array:
            if not isinstance(item, dict):
                continue

            if " - " in item.get("title", ""):
                fallback_artist, title = item.get("title").split(" - ", 1)
            else:
                fallback_artist, title = None, item.get("title", None)

            artist = item.get("artist", None) or fallback_artist or None

            result.append(
                Track(
                    artist=artist,
                    title=title,
                    timestamp=item.get("timestamp", None),
                )
            )

        return result or None

    def fetch_metadata(self, playlist: Playlist) -> PlaylistMetadata:
        logger.info(f"📜 Fetching metadata for playlist {playlist.title}")

        prompt = f"""
        title: {playlist.title}
        description: {playlist.description}
        helpful comment: {playlist.helpful_comment}
        """

        context = """
        You are an AI designed to extract relevant information from playlist metadata. Your task is to extract song genres and track details from the provided playlist data. Follow these guidelines:

        1. **Genres:**
           - Extract or infer no more than 5 genres from the playlist.
           - Only include genres if you can confidently determine them.
           - If genre information is missing or unclear, omit the genre field.
        
        2. **Tracks:**
           - For each track, extract the song title, artist name, and timestamp (if available).
           - Use the following field names:
             - **title** for the song name.
             - **artist** for the artist name.
             - **timestamp** for the time at which the song appears in the playlist.
           - If any of these fields are missing or unclear, omit that specific field.
        
        3. **Response Format:**
           - Always return a valid minified JSON object.
           - The structure should match this format:
             ```json
             {
               "genres"?: string[],
               "tracks"?: [
                 {
                   "title"?: string,
                   "artist"?: string,
                   "timestamp"?: string
                 }
               ]
             }
             ```
        
        4. **Additional Guidelines:**
           - If you cannot extract any tracks or genres, exclude that field from the response.
           - Do not include more than 5 genres.
           - Ensure your output is always a valid minified JSON.
        """

        payload = {
            "model": self.AI_MODEL,
            "messages": [
                {"role": "system", "content": context},
                {"role": "user", "content": prompt},
            ],
            "provider": {"allow_fallbacks": False},
            "response_format": {"type": "json_object"},
            "top_p": 0.8,
            "temperature": 0.7,
            "frequency_penalty": 0.03,
            "presence_penalty": 0.2,
            "repetition_penalty": 1,
            "top_k": 0,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openrouter_api_key}",
        }

        try:
            response = self.http_client.post(
                self.OPENROUTER_API_BASE, headers=headers, json=payload, timeout=300
            )
            response.raise_for_status()

            message_data = json.loads(
                response.json()["choices"][0]["message"]["content"]
            )

            return self.parse_metadata(message_data)

        except (json.JSONDecodeError, KeyError) as e:
            raise Exception(
                f"Failed to parse response: {str(e)}. Response: {response.text.strip()}"
            )

        except httpx.HTTPStatusError as e:
            raise Exception(
                f"HTTP error occurred: {str(e)}. Response: {response.text.strip()}"
            )

        except Exception as e:
            raise Exception(
                f"Unexpected error: {str(e)}. Response: {response.text.strip()}"
            )

    def generate(self):
        logger.info(f"📈 Generating data for 📂 Playlist ID: {self.playlist_id}")
        playlists = (
            Playlist.objects.filter(Q(genres__isnull=True) | Q(songs__isnull=True))
            .order_by("-position")
            .distinct()
        )
        for playlist in playlists:
            if playlist.genres.exists() or playlist.songs.exists():
                logger.info(f"⏭️ Skipping existing video {playlist.title}")

                continue

            logger.info(f"🎬 Generating data for video {playlist.title}")
            metadata = self.fetch_metadata(playlist)

            if metadata.genres and not playlist.genres.exists():
                logger.info(
                    f"🎭 Updating genres for {playlist.title}: {', '.join(metadata.genres)}"
                )
                for genre in metadata.genres:
                    name_cleaned = (
                        genre.strip()
                        .lower()
                        .replace("#", "")
                        .replace("lofi", "lo-fi")
                        .replace("lo fi", "lo-fi")
                        .replace("hiphop", "hip-hop")
                        .replace("hip hop", "hip-hop")
                        .replace("r&b", "rnb")
                    )
                    genre_obj, _ = Genre.objects.update_or_create(
                        slug=slugify(name_cleaned)
                        or self.generate_hash(name_cleaned, 16),
                        defaults={"name": name_cleaned},
                    )
                    playlist.genres.add(genre_obj, through_defaults={})

            if metadata.tracks and not playlist.songs.exists():
                logger.info(
                    f"🎶 Updating tracks for {playlist.title}:\n  🎵 "
                    + "\n  🎵 ".join(
                        [f"{song.title} - {song.artist}" for song in metadata.tracks]
                    )
                )
                for song in metadata.tracks:
                    slug_base = f"{song.artist or ''} {song.title or ''}"
                    slug = slugify(slug_base) or self.generate_hash(slug_base, 16)
                    song_obj, _ = Song.objects.update_or_create(
                        slug=slug,
                        defaults={
                            "title": song.title,
                            "artist": song.artist,
                        },
                    )
                    playlist.songs.add(
                        song_obj, through_defaults={"position": song.timestamp}
                    )

    def get_last_thumbnail(self, thumbnails: dict) -> str:
        if not thumbnails.keys():
            return ""
        return thumbnails.get("default", {}).get("url", "")

    def generate_hash(self, input_string: str, length: int = 32) -> str:
        hash_object = hashlib.sha256(input_string.encode())
        hex_digest = hash_object.hexdigest()
        return hex_digest[:length]


def run(full_scan=False):
    playlist_manager = PlaylistManager(playlist_id=env("PLAYLIST_ID"))
    playlist_manager.generate_playlist(full_scan=full_scan)
    playlist_manager.generate()
