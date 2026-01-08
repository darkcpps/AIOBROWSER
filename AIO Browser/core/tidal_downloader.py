"""
Tidal Downloader Module
Integrates with HIFI API for high-quality music downloading from Tidal
Supports FLAC up to 24-bit/192kHz and AAC/MP3 formats
"""
import requests
import json
import random
from pathlib import Path
from typing import Optional, Dict, List, Any, Literal
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TDRC, TRCK, TPOS, APIC


# API Endpoints - using multiple mirrors for reliability
API_ENDPOINTS = [
    "https://triton.squid.wtf",
    "https://tidal.kinoplus.online",
    "https://tidal-api.binimum.org",
    "https://hund.qqdl.site",
    "https://katze.qqdl.site",
]

AudioQuality = Literal["LOW", "HIGH", "LOSSLESS", "HI_RES"]


class TidalAPI:
    """Handles Tidal API interactions via HIFI API mirrors"""

    def __init__(self, api_endpoint: Optional[str] = None):
        self.api_endpoint = api_endpoint or random.choice(API_ENDPOINTS)
        print(f"[TIDAL] Initialized with API endpoint: {self.api_endpoint}")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to HIFI API"""
        url = f"{self.api_endpoint}{endpoint}"
        print(f"[TIDAL] Making request to: {url}")
        print(f"[TIDAL] Request params: {params}")

        try:
            response = self.session.get(url, params=params, timeout=30)
            print(f"[TIDAL] Response status: {response.status_code}")

            # If 404, it might be that the content doesn't exist on this API
            # Don't try other endpoints for 404 - it likely won't exist on others either
            if response.status_code == 404:
                print(f"[TIDAL] Content not found (404) - this track/album may not be available")
                raise Exception(f"Content not found on Tidal. This track/album may not be available, region-restricted, or removed.")

            response.raise_for_status()
            data = response.json()
            print(f"[TIDAL] Response received successfully")
            return data
        except Exception as e:
            print(f"[TIDAL] Request failed: {str(e)}")

            # Check if it's a 404 error - don't retry for content that doesn't exist
            if "404" in str(e) or "not found" in str(e).lower():
                print(f"[TIDAL] Content not found - will not retry other endpoints")
                raise Exception(f"Content not found on Tidal. This album/track may be unavailable or region-restricted.")

            # Only try alternative endpoints for network/server errors
            if self.api_endpoint in API_ENDPOINTS:
                old_endpoint = self.api_endpoint
                API_ENDPOINTS.remove(old_endpoint)
                print(f"[TIDAL] Removed failed endpoint: {old_endpoint}")
                if API_ENDPOINTS:
                    self.api_endpoint = API_ENDPOINTS[0]
                    print(f"[TIDAL] Trying alternative endpoint: {self.api_endpoint}")
                    return self._make_request(endpoint, params)

            print(f"[TIDAL] All endpoints failed")
            raise Exception(f"API request failed: {str(e)}")

    def parse_tidal_url(self, url: str) -> tuple[str, str]:
        """
        Parse Tidal URL to extract type and ID
        Returns: (type, id) - type can be 'track', 'album', 'playlist', 'artist'
        """
        import re
        print(f"[TIDAL] Parsing URL: {url}")
        patterns = [
            r'tidal\.com/browse/(track|album|playlist|artist)/(\d+)',
            r'tidal\.com/(track|album|playlist|artist)/(\d+)',
            r'listen\.tidal\.com/(track|album|playlist|artist)/(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                tidal_type, tidal_id = match.group(1), match.group(2)
                print(f"[TIDAL] Parsed URL - Type: {tidal_type}, ID: {tidal_id}")
                return tidal_type, tidal_id

        print(f"[TIDAL] URL parsing failed - invalid format")
        raise ValueError("Invalid Tidal URL")

    def search(self, query: str, search_type: str = "al", limit: int = 50) -> Dict[str, Any]:
        """
        Search Tidal catalog
        search_type: al (albums), tr (tracks), ar (artists), pl (playlists)
        """
        endpoint = f"/search/"
        params = {search_type: query}
        return self._make_request(endpoint, params)

    def get_track(self, track_id: str) -> Dict[str, Any]:
        """Get track metadata"""
        print(f"[TIDAL] Fetching track: {track_id}")
        endpoint = f"/info/"
        params = {"id": track_id}
        data = self._make_request(endpoint, params)
        print(f"[TIDAL] Track fetched: {data.get('title', 'Unknown')}")
        return data

    def get_album(self, album_id: str) -> Dict[str, Any]:
        """Get album metadata with tracks"""
        print(f"[TIDAL] Fetching album: {album_id}")
        endpoint = f"/album/"
        params = {"id": album_id}
        album_data = self._make_request(endpoint, params)
        print(f"[TIDAL] Album fetched: {album_data.get('title', 'Unknown')}")

        # The album endpoint returns tracks directly
        tracks = album_data.get("tracks", {}).get("items", [])
        album_data["tracks"] = tracks
        print(f"[TIDAL] Found {len(tracks)} tracks in album")

        return album_data

    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist metadata with tracks"""
        endpoint = f"/playlist/"
        params = {"id": playlist_id}
        playlist_data = self._make_request(endpoint, params)

        # Playlist tracks should be included in response
        tracks = playlist_data.get("tracks", {}).get("items", [])
        playlist_data["tracks"] = tracks

        return playlist_data

    def get_artist(self, artist_id: str) -> Dict[str, Any]:
        """Get artist metadata"""
        endpoint = f"/artists/{artist_id}"
        return self._make_request(endpoint)

    def get_artist_albums(self, artist_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get albums from an artist"""
        endpoint = f"/artists/{artist_id}/albums"
        params = {"limit": limit}
        data = self._make_request(endpoint, params)
        return data.get("items", [])

    def get_artist_top_tracks(self, artist_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get artist's top tracks"""
        endpoint = f"/artists/{artist_id}/toptracks"
        params = {"limit": limit}
        data = self._make_request(endpoint, params)
        return data.get("items", [])

    def get_stream_url(self, track_id: str, quality: AudioQuality = "LOSSLESS") -> Dict[str, Any]:
        """
        Get streaming URL for a track
        Quality options: LOW (AAC 96kbps), HIGH (AAC 320kbps), LOSSLESS (FLAC 16-bit/44.1kHz), HI_RES (FLAC 24-bit/96kHz+)
        """
        print(f"[TIDAL] Getting stream URL for track {track_id} with quality: {quality}")
        endpoint = f"/tracks/{track_id}/stream"
        params = {"quality": quality}
        data = self._make_request(endpoint, params)
        print(f"[TIDAL] Stream data received: {list(data.keys())}")
        return data

    def get_cover_image(self, cover_id: str, size: int = 1280) -> bytes:
        """Download cover image - size can be 160, 320, 640, 1280"""
        url = f"https://resources.tidal.com/images/{cover_id.replace('-', '/')}/{size}x{size}.jpg"
        response = self.session.get(url)
        response.raise_for_status()
        return response.content


class TidalDownloader:
    """Handles downloading tracks from Tidal"""

    def __init__(self, api: TidalAPI):
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
        print(f"[TIDAL] Starting download for track: {track_title} (ID: {track_id})")

        # Get stream URL
        stream_data = self.api.get_stream_url(track_id, quality)

        # Determine file extension based on quality
        if quality in ["LOW", "HIGH"]:
            file_ext = ".m4a"
        else:
            file_ext = ".flac"
        print(f"[TIDAL] File extension: {file_ext}")

        # Build filename
        filename = self._build_filename(track_data, file_ext)
        output_path = output_dir / filename
        print(f"[TIDAL] Output path: {output_path}")

        # Check if file already exists
        if output_path.exists():
            print(f"[TIDAL] File already exists, skipping download")
            return f"EXISTS:{output_path}"

        # Download the audio file
        download_url = stream_data.get("url")
        print(f"[TIDAL] Direct URL available: {download_url is not None}")

        if not download_url:
            # Handle manifest-based streaming (DASH/HLS)
            manifest = stream_data.get("manifest")
            print(f"[TIDAL] Manifest available: {manifest is not None}")
            if manifest:
                # For simplicity, we'll just get the first URL from manifest
                # In production, you'd want to parse DASH/HLS properly
                urls = stream_data.get("urls", [])
                print(f"[TIDAL] Found {len(urls)} URLs in manifest")
                download_url = urls[0] if urls else None

        if not download_url:
            print(f"[TIDAL] ERROR: No download URL available")
            raise Exception("No download URL available")

        print(f"[TIDAL] Downloading from: {download_url[:100]}...")
        self.download_file(download_url, output_path, progress_callback)
        print(f"[TIDAL] Download complete")

        # Download cover art
        cover_data = None
        if track_data.get("album", {}).get("cover"):
            try:
                cover_id = track_data["album"]["cover"]
                print(f"[TIDAL] Downloading cover art: {cover_id}")
                cover_data = self.api.get_cover_image(cover_id)
                print(f"[TIDAL] Cover art downloaded: {len(cover_data)} bytes")
            except Exception as e:
                print(f"[TIDAL] Failed to download cover art: {str(e)}")

        # Embed metadata
        print(f"[TIDAL] Embedding metadata...")
        self._embed_metadata(output_path, track_data, cover_data, file_ext)
        print(f"[TIDAL] Metadata embedded successfully")

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
