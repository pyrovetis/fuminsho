# Fuminshō

A Django application that automates the management of a YouTube playlist. Every 24 hours, a scheduled script fetches the
playlist details from YouTube, stores them in a database, and processes the data using an LLM (Large Language Model)
through the OpenRouter API to identify genres and track information.

The app also features a frontend designed with Tailwind CSS for a responsive and modern user experience.

---

## Features

- Automated daily YouTube playlist data fetching and storage
- Integration with OpenRouter for LLM-based genre and track analysis
- Logs sent to Discord or stored locally
- Optional FTP upload for playlist thumbnails
- Simple installation and setup

---

## Table of Contents

1. [Installation](#installation)
2. [Environment Variables](#environment-variables)
    - [Required Variables](#required-variables)
    - [Optional Variables](#optional-variables)
3. [Running the Project](#running-the-project)
4. [License](#license)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/pyrovetis/fuminsho.git
cd fuminsho
```

### 2. Install Django Dependencies

Ensure all necessary Python packages are installed by running:

```bash
pip install -r requirements.txt
```

### 3. Install Tailwind CSS

Tailwind CSS is installed and built using Bun:

```bash
bun install
bun tailwind
```

This will compile the file `static/src/css/tailwind.css` into `static/assets/css/style.css`.

### 4. Set Up Environment Variables

Copy the `.env.sample` file to `.env` in the project root and configure the necessary environment variables.
See [Environment Variables](#environment-variables) for detailed descriptions.

---

## Environment Variables

### Required Variables

These variables are essential for the app to function correctly.

```plaintext
DEBUG=True                              # Django debug mode (set to False in production)
SECRET_KEY=secret                       # Django secret key for encryption
STATIC_ROOT=/path/to/static             # Path for static files

PLAYLIST_ID=YourPlaylistID              # YouTube Playlist ID to fetch
PLAYLIST_LAST_VIDEO_ID=LastVideoID      # The last video ID in the playlist to avoid redundant scans

GOOGLE_API_KEY=YourGoogleAPIKey         # Key for accessing YouTube API
OPENROUTER_API_KEY=YourOpenRouterKey    # API key for OpenRouter LLM integration
```

### Optional Variables

These variables enable additional functionality and can enhance app performance. If not set, the app will use fallback
options.

```plaintext
# PostgreSQL Database Settings (optional; defaults to SQLite if not provided)
POSTGRES_DB=YourDatabase
POSTGRES_USER=YourUser
POSTGRES_PASSWORD=YourPassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Discord Webhook for logging (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook

# FTP Settings for Thumbnail Upload (optional)
FTP_HOST=ftp.example.com
FTP_USER=YourUsername
FTP_PASS=YourPassword
```

#### Obtaining API Keys

- **Google API Key**: Visit the [Google Cloud Console](https://console.cloud.google.com/), create a new project, and
  enable the YouTube Data API. Generate an API key in the API & Services section.
- **OpenRouter API Key**: Sign up at [OpenRouter](https://openrouter.ai) to obtain an API key. Note: To avoid response
  cuts, select an AI model with a high max output capacity (e.g., `mistralai/ministral-3b`, which supports up to 128,000
  tokens).

### Sample .env File

Refer to the `.env.sample` file in the project root for an example configuration, with brief comments on each variable’s
purpose.

---

## Running the Project

### 1. Start the Django Server

After configuring the environment, run the Django server:

```bash
python manage.py runserver
```

### 2. Scheduler and Playlist Manager

This project uses `django_extensions` to run scheduled scripts. Ensure this package is installed.

- To run the `PlaylistManager` script:
  ```bash
  python manage.py runscript main
  ```

- To run the scheduler, which triggers the script every 24 hours:
  ```bash
  python manage.py runscript scheduler
  ```

These scripts are located in `core/scripts`.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.