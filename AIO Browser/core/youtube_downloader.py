import os
import threading
import time
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class YoutubeDownloader:
    """
    Core logic for downloading YouTube videos or extracting audio using yt-dlp.
    """

    def __init__(self, progress_callback=None):
        """
        :param progress_callback: A function that accepts (status_text, progress_float)
        """
        self.progress_callback = progress_callback
        self.is_cancelled = False

    def _progress_hook(self, d):
        if self.is_cancelled:
            raise Exception("DOWNLOAD_STOPPED")

        if d["status"] == "downloading":
            p = d.get("_percent_str", "0%").replace("%", "")
            try:
                progress_float = float(p) / 100.0
            except:
                progress_float = 0.0

            speed = d.get("_speed_str", "N/A")
            eta = d.get("_eta_str", "N/A")
            downloaded = d.get("_downloaded_bytes_str", "N/A")
            total = d.get("_total_bytes_str", d.get("_total_bytes_estimate_str", "N/A"))

            status_text = (
                f"Downloading: {downloaded}/{total} ({p}%) • {speed} • ETA: {eta}"
            )
            if self.progress_callback:
                self.progress_callback(status_text, progress_float)

        elif d["status"] == "finished":
            if self.progress_callback:
                self.progress_callback("Processing / Finalizing...", 0.95)

    def download(self, url, save_path, mode="video", quality="Best Available"):
        """
        Downloads a video or audio from YouTube.

        :param url: YouTube URL
        :param save_path: Directory to save the file
        :param mode: 'video' or 'audio'
        :param quality: Resolution (e.g. '1080p') or bitrate (e.g. '320kbps')
        :return: 'SUCCESS', 'STOPPED', or 'ERROR: message'
        """
        self.is_cancelled = False

        # Ensure directory exists
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)

        if yt_dlp is None:
            return "ERROR: yt-dlp is not installed."

        # Explicitly point to local ffmpeg if it exists in the tools folder
        base_dir = Path(__file__).parent.parent.absolute()
        ffmpeg_dir = base_dir / "tools" / "ffmpeg"
        ffmpeg_location = str(ffmpeg_dir) if ffmpeg_dir.exists() else None

        ydl_opts = {
            "progress_hooks": [self._progress_hook],
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
            "ffmpeg_location": ffmpeg_location,
            "prefer_ffmpeg": True,
        }

        if mode == "audio":
            bitrate = quality.replace("kbps", "") if "kbps" in quality else "192"
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s"),
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": bitrate,
                        }
                    ],
                }
            )
        else:
            # Handle resolution selection
            res = quality.replace("p", "")
            if res.isdigit():
                f_string = f"bestvideo[vcodec^=avc1][height<={res}]+bestaudio[acodec^=mp4a]/best[ext=mp4][height<={res}]/best"
            else:
                f_string = (
                    "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[ext=mp4]/best"
                )

            ydl_opts.update(
                {
                    "format": f_string,
                    "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s"),
                    "merge_output_format": "mp4",
                    "postprocessors": [
                        {
                            "key": "FFmpegVideoConvertor",
                            "preferedformat": "mp4",
                        }
                    ],
                }
            )

        try:
            if self.progress_callback:
                self.progress_callback("Fetching video information...", 0.05)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if self.progress_callback:
                self.progress_callback("Download Complete!", 1.0)
            return "SUCCESS"

        except Exception as e:
            error_msg = str(e)
            if "DOWNLOAD_STOPPED" in error_msg:
                if self.progress_callback:
                    self.progress_callback("Download Stopped.", 0)
                return "STOPPED"

            if self.progress_callback:
                self.progress_callback(f"Error: {error_msg}", 0)
            return f"ERROR: {error_msg}"

    def cancel(self):
        self.is_cancelled = True


def get_video_info(url):
    """
    Helper to get title and thumbnail without downloading.
    """
    if yt_dlp is None:
        return None

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Unknown Title"),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", "Unknown"),
            }
    except Exception as e:
        print(f"Error fetching info: {e}")
        return None
