"""
Spotify Downloader Module
Integrates Spotify API and spotidownloader.com API for music downloading
"""
import requests
import json
import time
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TDRC, TRCK, TPOS, USLT, APIC, TSRC


class SpotifyAPI:
    """Handles Spotify Web API interactions for metadata fetching"""

    def __init__(self):
        self.client_id = "5f573c9620494bae87890c0f08a60293"  # From SpotiDownloader
        self.client_secret = "0a0e1c45c9f84d6ca38dc95d4d76e4f0"  # From SpotiDownloader
        self.access_token = None
        self.token_expires_at = 0
        self.session = requests.Session()

    def _get_access_token(self) -> str:
        """Get or refresh Spotify API access token"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        url = "https://accounts.spotify.com/api/token"
        data = {"grant_type": "client_credentials"}
        auth = (self.client_id, self.client_secret)

        response = self.session.post(url, data=data, auth=auth)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expires_at = time.time() + token_data["expires_in"] - 60

        return self.access_token

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make authenticated request to Spotify API"""
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        response = self.session.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    def parse_spotify_url(self, url: str) -> tuple[str, str]:
        """
        Parse Spotify URL to extract type and ID
        Returns: (type, id) - type can be 'track', 'album', 'playlist', 'artist'
        """
        patterns = [
            r'spotify\.com/(track|album|playlist|artist)/([a-zA-Z0-9]+)',
            r'open\.spotify\.com/(track|album|playlist|artist)/([a-zA-Z0-9]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)

        raise ValueError("Invalid Spotify URL")

    def get_track(self, track_id: str) -> Dict[str, Any]:
        """Get track metadata"""
        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        return self._make_request(url)

    def get_album(self, album_id: str) -> Dict[str, Any]:
        """Get album metadata with tracks"""
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        return self._make_request(url)

    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist metadata with tracks"""
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
        data = self._make_request(url)

        # Handle pagination for playlists with >100 tracks
        tracks = data["tracks"]["items"]
        next_url = data["tracks"]["next"]

        while next_url:
            next_data = self._make_request(next_url)
            tracks.extend(next_data["items"])
            next_url = next_data.get("next")

        data["tracks"]["items"] = tracks
        return data

    def get_artist(self, artist_id: str) -> Dict[str, Any]:
        """Get artist metadata"""
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        return self._make_request(url)

    def get_artist_albums(self, artist_id: str) -> List[Dict[str, Any]]:
        """Get all albums from an artist"""
        url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        params = {"limit": 50, "include_groups": "album,single"}

        albums = []
        while url:
            response = self._make_request(url + "?" + "&".join([f"{k}={v}" for k, v in params.items()]))
            albums.extend(response["items"])
            url = response.get("next")
            params = {}  # Clear params for subsequent requests

        return albums


class SpotiDownloaderAPI:
    """Handles spotidownloader.com API for music downloading"""

    API_BASE = "https://api.spotidownloader.com"

    def __init__(self, session_token: str):
        self.session_token = session_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {session_token}",
            "Content-Type": "application/json",
            "Origin": "https://spotidownloader.com",
            "Referer": "https://spotidownloader.com/"
        })

    def is_flac_available(self, track_id: str) -> bool:
        """Check if FLAC format is available for track"""
        url = f"{self.API_BASE}/isFlacAvailable"
        data = {"id": track_id}

        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json().get("available", False)
        except Exception as e:
            print(f"Error checking FLAC availability: {e}")
            return False

    def get_download_link(self, track_id: str) -> Dict[str, str]:
        """
        Get download links for a track
        Returns: {"link": mp3_url, "linkFlac": flac_url}
        """
        url = f"{self.API_BASE}/download"
        data = {"id": track_id}

        response = self.session.post(url, json=data)
        response.raise_for_status()

        result = response.json()
        if not result.get("success"):
            raise Exception("Download request failed")

        return {
            "link": result.get("link", ""),
            "linkFlac": result.get("linkFlac", "")
        }

    def download_file(self, download_url: str, output_path: Path,
                     progress_callback=None) -> None:
        """Download file with progress tracking"""
        headers = {
            "Referer": "https://spotidownloader.com/",
            "Origin": "https://spotidownloader.com"
        }

        response = self.session.get(download_url, headers=headers, stream=True)
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


class MetadataEmbedder:
    """Embeds metadata into audio files"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, ' ')

        # Remove control characters and extra spaces
        filename = ' '.join(filename.split())
        filename = filename.strip('. ')

        return filename or "Unknown"

    @staticmethod
    def build_filename(track_data: Dict[str, Any], format_str: str,
                      include_track_number: bool = True) -> str:
        """Build filename from track data"""
        title = track_data.get("name", "Unknown")
        artist = track_data["artists"][0]["name"] if track_data.get("artists") else "Unknown"
        album = track_data.get("album", {}).get("name", "Unknown")
        track_number = track_data.get("track_number", 0)

        # Sanitize components
        title = MetadataEmbedder.sanitize_filename(title)
        artist = MetadataEmbedder.sanitize_filename(artist)
        album = MetadataEmbedder.sanitize_filename(album)

        # Build filename based on format
        if "{" in format_str:
            # Template format
            filename = format_str
            filename = filename.replace("{title}", title)
            filename = filename.replace("{artist}", artist)
            filename = filename.replace("{album}", album)
            filename = filename.replace("{track}", f"{track_number:02d}" if track_number else "")
        else:
            # Legacy format
            if format_str == "artist-title":
                filename = f"{artist} - {title}"
            elif format_str == "title":
                filename = title
            else:  # "title-artist"
                filename = f"{title} - {artist}"

            if include_track_number and track_number:
                filename = f"{track_number:02d}. {filename}"

        return filename

    @staticmethod
    def embed_metadata_mp3(file_path: Path, track_data: Dict[str, Any],
                          cover_data: Optional[bytes] = None) -> None:
        """Embed metadata into MP3 file"""
        try:
            audio = MP3(file_path, ID3=ID3)

            # Add ID3 tag if not present
            try:
                audio.add_tags()
            except:
                pass

            # Basic metadata
            audio.tags.add(TIT2(encoding=3, text=track_data.get("name", "")))

            artists = ", ".join([a["name"] for a in track_data.get("artists", [])])
            audio.tags.add(TPE1(encoding=3, text=artists))

            album = track_data.get("album", {})
            if album:
                audio.tags.add(TALB(encoding=3, text=album.get("name", "")))

                album_artists = ", ".join([a["name"] for a in album.get("artists", [])])
                audio.tags.add(TPE2(encoding=3, text=album_artists))

                release_date = album.get("release_date", "")
                if release_date:
                    audio.tags.add(TDRC(encoding=3, text=release_date))

            # Track number
            track_number = track_data.get("track_number")
            total_tracks = album.get("total_tracks") if album else None
            if track_number:
                track_text = f"{track_number}/{total_tracks}" if total_tracks else str(track_number)
                audio.tags.add(TRCK(encoding=3, text=track_text))

            # Disc number
            disc_number = track_data.get("disc_number")
            if disc_number:
                audio.tags.add(TPOS(encoding=3, text=str(disc_number)))

            # ISRC
            isrc = track_data.get("external_ids", {}).get("isrc")
            if isrc:
                audio.tags.add(TSRC(encoding=3, text=isrc))

            # Cover art
            if cover_data:
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # Front cover
                    desc='Cover',
                    data=cover_data
                ))

            audio.save()
        except Exception as e:
            print(f"Error embedding MP3 metadata: {e}")

    @staticmethod
    def embed_metadata_flac(file_path: Path, track_data: Dict[str, Any],
                           cover_data: Optional[bytes] = None) -> None:
        """Embed metadata into FLAC file"""
        try:
            audio = FLAC(file_path)

            # Basic metadata
            audio["TITLE"] = track_data.get("name", "")

            artists = [a["name"] for a in track_data.get("artists", [])]
            audio["ARTIST"] = artists

            album = track_data.get("album", {})
            if album:
                audio["ALBUM"] = album.get("name", "")

                album_artists = [a["name"] for a in album.get("artists", [])]
                audio["ALBUMARTIST"] = album_artists

                release_date = album.get("release_date", "")
                if release_date:
                    audio["DATE"] = release_date

            # Track number
            track_number = track_data.get("track_number")
            if track_number:
                audio["TRACKNUMBER"] = str(track_number)

            total_tracks = album.get("total_tracks") if album else None
            if total_tracks:
                audio["TRACKTOTAL"] = str(total_tracks)

            # Disc number
            disc_number = track_data.get("disc_number")
            if disc_number:
                audio["DISCNUMBER"] = str(disc_number)

            # ISRC
            isrc = track_data.get("external_ids", {}).get("isrc")
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
        except Exception as e:
            print(f"Error embedding FLAC metadata: {e}")
