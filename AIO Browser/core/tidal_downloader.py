# Tidal support removed. Monochrome downloader handles music sources now.
# Stubbed classes remain to provide clearer error messages if legacy code attempts to use them.

class TidalAPI:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Tidal support has been removed. Use Monochrome downloader instead.")

class TidalDownloader:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Tidal support has been removed. Use Monochrome downloader instead.")

class MetadataHelper:
    @staticmethod
    def parse(*args, **kwargs):
        raise NotImplementedError("Tidal support has been removed. Use Monochrome downloader instead.")

AudioQuality = str


# API Endpoints - using multiple mirrors for reliability
API_ENDPOINTS = [
    "https://triton.squid.wtf",
    "https://tidal.kinoplus.online",
    "https://tidal-api.binimum.org",
    "https://hund.qqdl.site",
    "https://katze.qqdl.site",
]

AudioQuality = Literal["LOW", "HIGH", "LOSSLESS", "HI_RES"]


# Tidal module removed. Functionality replaced by Monochrome downloader.
# Keeping minimal stubs to avoid import errors in other modules.

class TidalAPI:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Tidal support has been removed. Use Monochrome downloader instead.")

class TidalDownloader:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Tidal support has been removed. Use Monochrome downloader instead.")

class MetadataHelper:
    @staticmethod
    def format_duration(*args, **kwargs):
        raise NotImplementedError("Tidal support has been removed. Use Monochrome downloader instead.")

AudioQuality = str


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
