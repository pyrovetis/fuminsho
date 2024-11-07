import logging

import httpx


class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhook_url):
        super().__init__()
        self.webhook_url = webhook_url

    def emit(self, record):
        log_entry = self.format(record)
        try:
            httpx.post(self.webhook_url, json={"content": log_entry})
        except Exception as e:
            print(f"Failed to send log to Discord: {e}")


def generate_youtube_link(video_id):
    return f"https://youtu.be/{video_id}"
