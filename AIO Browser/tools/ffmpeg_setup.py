import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


def is_ffmpeg_installed():
    """Check if ffmpeg is available in the system PATH."""
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_urls():
    """Returns the download URL for ffmpeg essentials build."""
    # Using a reliable mirror for ffmpeg builds
    return "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def install_ffmpeg(progress_callback=None):
    """
    Downloads and sets up ffmpeg in the local tools directory.
    This avoids needing admin rights to change system PATH while keeping the app portable.
    """
    if is_ffmpeg_installed():
        return True, "FFmpeg is already installed."

    try:
        base_dir = Path(__file__).parent.parent.absolute()
        ffmpeg_dir = base_dir / "tools" / "ffmpeg"
        zip_path = base_dir / "tools" / "ffmpeg.zip"

        if not ffmpeg_dir.exists():
            ffmpeg_dir.mkdir(parents=True, exist_ok=True)

        # 1. Download
        if progress_callback:
            progress_callback("Downloading FFmpeg...", 0.1)
        url = get_ffmpeg_urls()

        # Simple download with progress
        def download_report(block_num, block_size, total_size):
            if progress_callback and total_size > 0:
                downloaded = block_num * block_size
                progress = 0.1 + (min(downloaded / total_size, 1.0) * 0.6)
                progress_callback(
                    f"Downloading FFmpeg: {int(progress * 100)}%", progress
                )

        urllib.request.urlretrieve(url, zip_path, reporthook=download_report)

        # 2. Extract
        if progress_callback:
            progress_callback("Extracting FFmpeg...", 0.75)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Find the bin folder inside the zip
            for member in zip_ref.namelist():
                if member.endswith("ffmpeg.exe") or member.endswith("ffprobe.exe"):
                    filename = os.path.basename(member)
                    source = zip_ref.open(member)
                    target = open(ffmpeg_dir / filename, "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)

        # 3. Cleanup
        if zip_path.exists():
            os.remove(zip_path)

        # 4. Verification
        ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
        if ffmpeg_exe.exists():
            # Add to current process path immediately
            os.environ["PATH"] += os.pathsep + str(ffmpeg_dir)
            if progress_callback:
                progress_callback("FFmpeg Setup Complete!", 1.0)
            return True, "FFmpeg installed successfully in tools folder."
        else:
            return False, "Failed to extract ffmpeg.exe"

    except Exception as e:
        return False, f"Installation error: {str(e)}"


def ensure_ffmpeg(progress_callback=None):
    """
    Main entry point to ensure ffmpeg is usable.
    Checks system path, then local tools path, then installs if missing.
    """
    # 1. System check
    if is_ffmpeg_installed():
        return True

    # 2. Local check
    base_dir = Path(__file__).parent.parent.absolute()
    local_ffmpeg = base_dir / "tools" / "ffmpeg"
    if (local_ffmpeg / "ffmpeg.exe").exists():
        if str(local_ffmpeg) not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + str(local_ffmpeg)
        return True

    # 3. Install if missing
    success, message = install_ffmpeg(progress_callback)
    return success


if __name__ == "__main__":
    # Test script
    print("Checking FFmpeg...")

    def simple_progress(text, p):
        print(f"[{int(p * 100)}%] {text}")

    if ensure_ffmpeg(simple_progress):
        print("FFmpeg is ready to use.")
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    else:
        print("Failed to setup FFmpeg.")
