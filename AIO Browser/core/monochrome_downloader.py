"""
Monochrome Downloader Module
Integrates with Monochrome API (monochrome-api.samidy.com) for music downloading
Supports searching and downloading from Tidal via Monochrome's API proxy
"""
import requests
import json
import base64
from pathlib import Path
from typing import Optional, Dict, List, Any, Literal
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TDRC, TRCK, TPOS, APIC


# Monochrome API Configuration
MONOCHROME_API_BASE = "https://monochrome-api.samidy.com"

# TIDAL API Mirrors (used by Monochrome)
TIDAL_API_ENDPOINTS = [
    "https://triton.squid.wtf",
    "https://wolf.qqdl.site",
    "https://maus.qqdl.site",
    "https://vogel.qqdl.site",
    "https://katze.qqdl.site",
    "https://hund.qqdl.site",
    "https://tidal.kinoplus.online",
    "https://tidal-api.binimum.org",
]

AudioQuality = Literal["LOW", "HIGH", "LOSSLESS", "HI_RES"]


class MonochromeAPI:
    """Handles Monochrome API interactions"""

    def __init__(self):
        self.api_base = MONOCHROME_API_BASE
        self.tidal_endpoints = TIDAL_API_ENDPOINTS.copy()
        print(f"[MONOCHROME] Initialized with API: {self.api_base}")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Monochrome API"""
        url = f"{self.api_base}{endpoint}"
        print(f"[MONOCHROME] Making request to: {url}")
        print(f"[MONOCHROME] Request params: {params}")

        try:
            response = self.session.get(url, params=params, timeout=30)
            print(f"[MONOCHROME] Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            print(f"[MONOCHROME] Response received successfully")
            return data
        except Exception as e:
            print(f"[MONOCHROME] Request failed: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")

    def search(self, query: str, search_type: str = "al") -> Dict[str, Any]:
        """
        Search Monochrome catalog
        search_type: al (albums), s (tracks), a (artists), p (playlists)
        """
        print(f"[MONOCHROME] Searching for '{query}' (type: {search_type})")
        endpoint = f"/search/"
        params = {search_type: query}
        result = self._make_request(endpoint, params)

        # Monochrome returns structure: {"version": "2.2", "data": {...}}
        return result.get("data", {})

    def get_track(self, track_id: str) -> Dict[str, Any]:
        """Get track metadata"""
        print(f"[MONOCHROME] Fetching track: {track_id}")
        endpoint = f"/track/"
        params = {"id": track_id}
        result = self._make_request(endpoint, params)

        # Return the data portion
        data = result.get("data", result)
        print(f"[MONOCHROME] Track fetched: {data.get('title', 'Unknown')}")
        return data

    def get_album(self, album_id: str) -> Dict[str, Any]:
        """Get album metadata with tracks"""
        print(f"[MONOCHROME] Fetching album: {album_id}")
        endpoint = f"/album/"
        params = {"id": album_id}
        result = self._make_request(endpoint, params)

        album_data = result.get("data", result)
        print(f"[MONOCHROME] Album fetched: {album_data.get('title', 'Unknown')}")

        # Extract tracks from the album - they are in items[] with structure {type: "track", item: {...}}
        raw_items = album_data.get("items", [])
        tracks = []
        for item_wrapper in raw_items:
            if item_wrapper.get("type") == "track":
                track = item_wrapper.get("item", {})
                tracks.append(track)

        album_data["tracks"] = tracks
        print(f"[MONOCHROME] Found {len(tracks)} tracks in album")

        return album_data

    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist metadata with tracks"""
        print(f"[MONOCHROME] Fetching playlist: {playlist_id}")
        endpoint = f"/playlist/"
        params = {"id": playlist_id}
        result = self._make_request(endpoint, params)

        playlist_data = result.get("data", result)

        # Extract tracks from playlist - they are in items[] with structure {type: "track", item: {...}}
        raw_items = playlist_data.get("items", [])
        tracks = []
        for item_wrapper in raw_items:
            if item_wrapper.get("type") == "track":
                track = item_wrapper.get("item", {})
                tracks.append(track)

        playlist_data["tracks"] = tracks
        print(f"[MONOCHROME] Found {len(tracks)} tracks in playlist")

        return playlist_data

    def get_artist(self, artist_id: str) -> Dict[str, Any]:
        """Get artist metadata"""
        print(f"[MONOCHROME] Fetching artist: {artist_id}")
        endpoint = f"/artist/"
        params = {"id": artist_id}
        result = self._make_request(endpoint, params)

        return result.get("data", result)

    def get_stream_url(self, track_id: str, quality: AudioQuality = "LOSSLESS") -> Dict[str, Any]:
        """
        Get streaming URL for a track using Tidal API mirrors
        Quality options: LOW (AAC 96kbps), HIGH (AAC 320kbps), LOSSLESS (FLAC 16-bit/44.1kHz), HI_RES (FLAC 24-bit/96kHz+)
        """
        print(f"[MONOCHROME] Getting stream URL for track {track_id} with quality: {quality}")

        # Try each Tidal endpoint until one works
        for endpoint_base in self.tidal_endpoints:
            try:
                url = f"{endpoint_base}/track/"
                params = {"id": track_id, "quality": quality}

                print(f"[MONOCHROME] Trying endpoint: {endpoint_base}")
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    print(f"[MONOCHROME] Successfully got stream URL from {endpoint_base}")
                    return data.get("data", data)

            except Exception as e:
                print(f"[MONOCHROME] Failed endpoint {endpoint_base}: {str(e)}")
                continue

        raise Exception("All Tidal API endpoints failed")

    def get_cover_image(self, cover_id: str, size: int = 1280) -> bytes:
        """Download cover image - size can be 160, 320, 640, 1280"""
        url = f"https://resources.tidal.com/images/{cover_id.replace('-', '/')}/{size}x{size}.jpg"
        response = self.session.get(url)
        response.raise_for_status()
        return response.content


class MonochromeDownloader:
    """Handles downloading tracks via Monochrome API"""

    def __init__(self, api: MonochromeAPI):
        self.api = api
        self.session = requests.Session()

    def download_file(self, url: str, output_path: Path, progress_callback=None) -> None:
        """Download file with progress tracking"""
        response = self.session.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress, downloaded, total_size)

    def download_track(
        self,
        track_data: Dict[str, Any],
        output_dir: Path,
        quality: AudioQuality = "LOSSLESS",
        progress_callback=None
    ) -> str:
        """Download a single track with metadata"""
        track_id = str(track_data["id"])
        track_title = track_data.get("title", "Unknown")
        print(f"[MONOCHROME] Starting download for track: {track_title} (ID: {track_id})")

        # Get stream URL
        stream_data = self.api.get_stream_url(track_id, quality)

        # Determine file extension based on quality
        if quality in ["LOW", "HIGH"]:
            file_ext = ".m4a"
        else:
            file_ext = ".flac"
        print(f"[MONOCHROME] File extension: {file_ext}")

        # Build filename
        filename = self._build_filename(track_data, file_ext)
        output_path = output_dir / filename
        print(f"[MONOCHROME] Output path: {output_path}")

        # Check if file already exists
        if output_path.exists():
            print(f"[MONOCHROME] File already exists, skipping download")
            return f"EXISTS:{output_path}"

        # Download the audio file
        download_url = stream_data.get("url")
        print(f"[MONOCHROME] Direct URL available: {download_url is not None}")

        if not download_url:
            # Handle manifest-based streaming (DASH/HLS)
            manifest = stream_data.get("manifest")
            print(f"[MONOCHROME] Manifest available: {manifest is not None}")
            if manifest:
                try:
                    # Try to decode manifest if it looks like base64 (Tidal BTS format)
                    decoded_manifest = base64.b64decode(manifest).decode('utf-8')
                    # Check if it is JSON
                    if decoded_manifest.strip().startswith('{') and decoded_manifest.strip().endswith('}'):
                        manifest_json = json.loads(decoded_manifest)
                        if "urls" in manifest_json:
                            urls = manifest_json["urls"]
                            print(f"[MONOCHROME] Found {len(urls)} URLs in decoded manifest")
                            download_url = urls[0] if urls else None
                except Exception as e:
                    print(f"[MONOCHROME] Failed to decode manifest: {e}")

                if not download_url:
                    urls = stream_data.get("urls", [])
                    print(f"[MONOCHROME] Found {len(urls)} URLs in manifest")
                    download_url = urls[0] if urls else None

        if not download_url:
            print(f"[MONOCHROME] ERROR: No download URL available")
            raise Exception("No download URL available")

        print(f"[MONOCHROME] Downloading from: {download_url[:100]}...")
        self.download_file(download_url, output_path, progress_callback)
        print(f"[MONOCHROME] Download complete")

        # Download cover art
        cover_data = None
        if track_data.get("album", {}).get("cover"):
            try:
                cover_id = track_data["album"]["cover"]
                print(f"[MONOCHROME] Downloading cover art: {cover_id}")
                cover_data = self.api.get_cover_image(cover_id)
                print(f"[MONOCHROME] Cover art downloaded: {len(cover_data)} bytes")
            except Exception as e:
                print(f"[MONOCHROME] Failed to download cover art: {str(e)}")

        # Embed metadata
        print(f"[MONOCHROME] Embedding metadata...")
        self._embed_metadata(output_path, track_data, cover_data, file_ext)
        print(f"[MONOCHROME] Metadata embedded successfully")

        return str(output_path)

    def _build_filename(self, track_data: Dict[str, Any], extension: str) -> str:
        """Build sanitized filename for track"""
        track_number = track_data.get("trackNumber", 0)
        title = track_data.get("title", "Unknown")
        artists = track_data.get("artists", [])
        artist_name = artists[0]["name"] if artists else "Unknown Artist"

        # Sanitize components
        title = self._sanitize_filename(title)
        artist_name = self._sanitize_filename(artist_name)

        # Build filename with track number
        if track_number:
            filename = f"{track_number:02d}. {title} - {artist_name}{extension}"
        else:
            filename = f"{title} - {artist_name}{extension}"

        return filename

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, ' ')
        filename = ' '.join(filename.split())
        filename = filename.strip('. ')
        return filename or "Unknown"

    def _embed_metadata(
        self,
        file_path: Path,
        track_data: Dict[str, Any],
        cover_data: Optional[bytes],
        file_ext: str
    ) -> None:
        """Embed metadata into audio file"""
        try:
            if file_ext == ".flac":
                self._embed_flac_metadata(file_path, track_data, cover_data)
            elif file_ext == ".m4a":
                self._embed_m4a_metadata(file_path, track_data, cover_data)
        except Exception as e:
            print(f"Warning: Failed to embed metadata: {e}")

    def _embed_flac_metadata(
        self,
        file_path: Path,
        track_data: Dict[str, Any],
        cover_data: Optional[bytes]
    ) -> None:
        """Embed metadata into FLAC file"""
        audio = FLAC(file_path)

        # Basic metadata
        audio["TITLE"] = track_data.get("title", "")

        artists = [a["name"] for a in track_data.get("artists", [])]
        if artists:
            audio["ARTIST"] = artists

        album = track_data.get("album", {})
        if album:
            audio["ALBUM"] = album.get("title", "")

            album_artists = [a["name"] for a in album.get("artists", [])]
            if album_artists:
                audio["ALBUMARTIST"] = album_artists

            release_date = album.get("releaseDate")
            if release_date:
                audio["DATE"] = release_date.split("-")[0]  # Year only

        # Track/disc numbers
        track_number = track_data.get("trackNumber")
        if track_number:
            audio["TRACKNUMBER"] = str(track_number)

        total_tracks = album.get("numberOfTracks")
        if total_tracks:
            audio["TRACKTOTAL"] = str(total_tracks)

        volume_number = track_data.get("volumeNumber")
        if volume_number:
            audio["DISCNUMBER"] = str(volume_number)

        # ISRC
        isrc = track_data.get("isrc")
        if isrc:
            audio["ISRC"] = isrc

        # Cover art
        if cover_data:
            from mutagen.flac import Picture
            picture = Picture()
            picture.type = 3  # Front cover
            picture.mime = 'image/jpeg'
            picture.desc = 'Cover'
            picture.data = cover_data
            audio.add_picture(picture)

        audio.save()

    def _embed_m4a_metadata(
        self,
        file_path: Path,
        track_data: Dict[str, Any],
        cover_data: Optional[bytes]
    ) -> None:
        """Embed metadata into M4A file"""
        audio = MP4(file_path)

        # Basic metadata
        audio["\xa9nam"] = track_data.get("title", "")

        artists = [a["name"] for a in track_data.get("artists", [])]
        if artists:
            audio["\xa9ART"] = ", ".join(artists)

        album = track_data.get("album", {})
        if album:
            audio["\xa9alb"] = album.get("title", "")

            album_artists = [a["name"] for a in album.get("artists", [])]
            if album_artists:
                audio["aART"] = ", ".join(album_artists)

            release_date = album.get("releaseDate")
            if release_date:
                audio["\xa9day"] = release_date.split("-")[0]

        # Track/disc numbers
        track_number = track_data.get("trackNumber", 0)
        total_tracks = album.get("numberOfTracks", 0) if album else 0
        if track_number:
            audio["trkn"] = [(track_number, total_tracks)]

        volume_number = track_data.get("volumeNumber", 0)
        if volume_number:
            audio["disk"] = [(volume_number, 0)]

        # Cover art
        if cover_data:
            from mutagen.mp4 import MP4Cover
            audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]

        audio.save()


class MetadataHelper:
    """Helper methods for track metadata"""

    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in seconds to MM:SS"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def get_quality_label(quality: AudioQuality) -> str:
        """Get human-readable quality label"""
        labels = {
            "LOW": "AAC 96kbps",
            "HIGH": "AAC 320kbps",
            "LOSSLESS": "FLAC 16-bit/44.1kHz",
            "HI_RES": "FLAC 24-bit/96kHz+"
        }
        return labels.get(quality, quality)

    @staticmethod
    def get_file_size_estimate(duration: int, quality: AudioQuality) -> str:
        """Estimate file size based on duration and quality"""
        # Approximate bitrates in kbps
        bitrates = {
            "LOW": 96,
            "HIGH": 320,
            "LOSSLESS": 1000,
            "HI_RES": 2500
        }

        bitrate = bitrates.get(quality, 1000)
        size_mb = (duration * bitrate * 1000) / (8 * 1024 * 1024)

        if size_mb >= 1000:
            return f"{size_mb / 1024:.1f} GB"
        return f"{size_mb:.1f} MB"
