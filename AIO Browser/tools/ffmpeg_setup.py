import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path


def ffmpeg_binary_name():
    """Name of the ffmpeg binary on the current platform."""
    return "ffmpeg.exe" if os.name == "nt" else "ffmpeg"


def ffprobe_binary_name():
    """Name of the ffprobe binary on the current platform."""
    return "ffprobe.exe" if os.name == "nt" else "ffprobe"


def is_ffmpeg_installed():
    """Check if ffmpeg is available in the system PATH."""
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_urls():
    """Return a portable ffmpeg build URL for the current platform."""
    if os.name == "nt":
        # Reliable Windows mirror (essentials build).
        return "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    if sys.platform == "darwin":
        return "https://evermeet.cx/ffmpeg/getrelease/zip"
    # Linux: static amd64 build (no system packages required).
    return "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"


def _extract_binaries(archive_path, ffmpeg_dir):
    """Extract ffmpeg/ffprobe from a .zip or .tar.xz archive. Returns names."""
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    wanted = {ffmpeg_binary_name(), ffprobe_binary_name()}
    found = []

    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, "r") as archive:
            for member in archive.namelist():
                base = os.path.basename(member)
                if base in wanted:
                    with archive.open(member) as source:
                        with open(ffmpeg_dir / base, "wb") as target:
                            shutil.copyfileobj(source, target)
                    found.append(base)
    else:
        with tarfile.open(archive_path, "r:*") as archive:
            for member in archive.getmembers():
                base = os.path.basename(member.name)
                if member.isfile() and base in wanted:
                    source = archive.extractfile(member)
                    if source is None:
                        continue
                    with source:
                        with open(ffmpeg_dir / base, "wb") as target:
                            shutil.copyfileobj(source, target)
                    found.append(base)

    if os.name != "nt":
        for name in found:
            try:
                os.chmod(ffmpeg_dir / name, 0o755)
            except OSError:
                pass

    return found


def install_ffmpeg(progress_callback=None):
    """
    Download and set up a portable ffmpeg in the local tools directory.

    This avoids needing admin rights to change the system PATH while keeping
    the application portable. Works on Windows, Linux and macOS.
    """
    if is_ffmpeg_installed():
        return True, "FFmpeg is already installed."

    try:
        base_dir = Path(__file__).parent.parent.absolute()
        ffmpeg_dir = base_dir / "tools" / "ffmpeg"
        url = get_ffmpeg_urls()
        suffix = os.path.splitext(url.split("?")[0])[1] or ".zip"
        archive_path = base_dir / "tools" / ("ffmpeg_download" + suffix)

        # 1. Download
        if progress_callback:
            progress_callback("Downloading FFmpeg...", 0.1)

        def download_report(block_num, block_size, total_size):
            if progress_callback and total_size > 0:
                downloaded = block_num * block_size
                progress = 0.1 + (min(downloaded / total_size, 1.0) * 0.6)
                progress_callback(
                    "Downloading FFmpeg: %d%%" % int(progress * 100), progress
                )

        urllib.request.urlretrieve(url, archive_path, reporthook=download_report)

        # 2. Extract
        if progress_callback:
            progress_callback("Extracting FFmpeg...", 0.75)
        _extract_binaries(archive_path, ffmpeg_dir)

        # 3. Cleanup
        if archive_path.exists():
            os.remove(archive_path)

        # 4. Verification
        ffmpeg_exe = ffmpeg_dir / ffmpeg_binary_name()
        if ffmpeg_exe.exists():
            # Make it usable immediately in this process.
            os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
            if progress_callback:
                progress_callback("FFmpeg Setup Complete!", 1.0)
            return True, "FFmpeg installed successfully in tools folder."
        return False, "Failed to extract ffmpeg binary."

    except Exception as e:
        return False, "Installation error: %s" % str(e)


def ensure_ffmpeg(progress_callback=None):
    """
    Main entry point to ensure ffmpeg is usable.

    Checks the system PATH, then the local tools path, then installs if missing.
    """
    # 1. System check
    if is_ffmpeg_installed():
        return True

    # 2. Local check
    base_dir = Path(__file__).parent.parent.absolute()
    local_ffmpeg = base_dir / "tools" / "ffmpeg"
    if (local_ffmpeg / ffmpeg_binary_name()).exists():
        path_entries = os.environ.get("PATH", "").split(os.pathsep)
        if str(local_ffmpeg) not in path_entries:
            os.environ["PATH"] = str(local_ffmpeg) + os.pathsep + os.environ.get("PATH", "")
        return True

    # 3. Install if missing
    success, message = install_ffmpeg(progress_callback)
    return success


if __name__ == "__main__":
    # Test script
    print("Checking FFmpeg...")

    def simple_progress(text, p):
        print("[%d%%] %s" % (int(p * 100), text))

    if ensure_ffmpeg(simple_progress):
        print("FFmpeg is ready to use.")
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    else:
        print("Failed to setup FFmpeg.")
