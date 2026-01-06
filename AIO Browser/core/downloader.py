# Core download logic. Handles file streaming, progress tracking, and pause/resume/stop functionality.
import requests
import os
import time
import re

# =========================================================================
# DOWNLOAD CORE ENGINE
# =========================================================================
def download_file(url, save_path, progress_callback, control_flags, session=None):
    """
    Downloads file with progress updates.
    progress_callback(status_text, progress_float)
    control_flags is a dict {'paused': bool, 'stopped': bool}
    session: optional requests.Session object to use for the download
    save_path: can be a full file path or a directory check.
    """
    try:
        progress_callback("Starting connection...", 0.0)
        
        if session:
            request_func = session.get
            kwargs = {
                "stream": True, 
                "allow_redirects": True
            }
        else:
            request_func = requests.get
            kwargs = {
                "stream": True, 
                "headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}, 
                "allow_redirects": True
            }
        
        with request_func(url, **kwargs) as r:
            content_type = r.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                progress_callback("Error: Resolved link is a webpage, not a file.", 0)
                return "IS_HTML"

            r.raise_for_status()
            
            # --- Determine Final Save Path ---
            final_path = save_path
            
            # Check if save_path is likely a directory (or existing dir).
            # The caller (GUI) might pass a specific path or a dir.
            # If user selected a directory, we need to append filename.
            
            if os.path.isdir(save_path):
                # Extract filename from headers
                filename = "downloaded_file.zip" # fallback
                cd = r.headers.get('Content-Disposition')
                if cd:
                    fnames = re.findall(r'filename\*?=([^;]+)', cd)
                    if fnames:
                        filename = fnames[0].strip().strip('"').strip("'")
                        if "UTF-8''" in filename:
                            filename = filename.split("UTF-8''")[-1]
                
                # If still no valid filename found or fallback triggered, try URL
                if filename == "downloaded_file.zip":
                     if url.endswith(".rar"): filename = "game.rar"
                     elif url.endswith(".zip"): filename = "game.zip"

                final_path = os.path.join(save_path, filename)
                progress_callback(f"Saving as: {filename}", 0.0)

            total_length = int(r.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()
            last_update_time = start_time
            last_downloaded = 0
            speed_samples = []  # For moving average
            
            def format_size(bytes_val):
                """Convert bytes to human readable format"""
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.2f} {unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.2f} TB"
            
            def format_time(seconds):
                """Convert seconds to human readable format"""
                if seconds < 60:
                    return f"{int(seconds)}s"
                elif seconds < 3600:
                    mins = int(seconds / 60)
                    secs = int(seconds % 60)
                    return f"{mins}m {secs}s"
                else:
                    hours = int(seconds / 3600)
                    mins = int((seconds % 3600) / 60)
                    return f"{hours}h {mins}m"
            
            with open(final_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536): # 64KB chunks
                    if control_flags['stopped']: break
                    
                    while control_flags['paused']:
                        if control_flags['stopped']: break
                        time.sleep(0.5)
                        # Reset timing after pause
                        start_time = time.time()
                        last_update_time = start_time
                        last_downloaded = downloaded
                        speed_samples.clear()

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        current_time = time.time()
                        
                        # Update progress every 0.5 seconds to avoid UI spam
                        if current_time - last_update_time >= 0.5:
                            elapsed = current_time - start_time
                            
                            # Calculate instantaneous speed
                            time_delta = current_time - last_update_time
                            bytes_delta = downloaded - last_downloaded
                            instant_speed = bytes_delta / time_delta if time_delta > 0 else 0
                            
                            # Moving average for smoother display (last 5 samples)
                            speed_samples.append(instant_speed)
                            if len(speed_samples) > 5:
                                speed_samples.pop(0)
                            avg_speed = sum(speed_samples) / len(speed_samples)
                            
                            if total_length > 0:
                                percent = downloaded / total_length
                                remaining = total_length - downloaded
                                
                                # Calculate ETA
                                if avg_speed > 0:
                                    eta_seconds = remaining / avg_speed
                                    eta_str = format_time(eta_seconds)
                                else:
                                    eta_str = "calculating..."
                                
                                # Format progress message
                                progress_msg = (
                                    f"{format_size(downloaded)} / {format_size(total_length)} "
                                    f"({int(percent*100)}%) • "
                                    f"{format_size(avg_speed)}/s • "
                                    f"ETA: {eta_str}"
                                )
                                progress_callback(progress_msg, percent)
                            else:
                                # If no content-length, show downloaded and speed
                                speed_str = format_size(avg_speed) if avg_speed > 0 else "0 B"
                                progress_callback(
                                    f"Downloaded {format_size(downloaded)} • {speed_str}/s", 
                                    0.5
                                )
                            
                            last_update_time = current_time
                            last_downloaded = downloaded
        
        if control_flags['stopped']:
            try: os.remove(final_path)
            except: pass
            progress_callback("Download Stopped & File Deleted.", 0)
            return "STOPPED"
        else:
            progress_callback("Download Complete!", 1.0)
            return "SUCCESS"

    except Exception as e:
        if control_flags['stopped']:
            try: 
                 if 'final_path' in locals(): os.remove(final_path)
            except: pass
            progress_callback("Download Stopped.", 0)
            return "STOPPED"
        else:
            progress_callback(f"Error: {e}", 0)
            return f"ERROR: {e}"
