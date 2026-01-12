import time
from typing import Callable, Mapping

try:
    import libtorrent as lt  # type: ignore
except Exception:  # pragma: no cover
    lt = None


def is_available() -> bool:
    return lt is not None


def download_torrent(
    source: str,
    save_path: str,
    progress_callback: Callable[[str, float], None],
    control_flags: Mapping[str, bool] | None = None,
    poll_interval_s: float = 1.0,
) -> str:
    """
    Download a torrent from a magnet link or .torrent file.

    Returns: "SUCCESS", "STOPPED", or "ERROR"
    """
    if lt is None:
        progress_callback("Error: libtorrent not installed", 0.0)
        return "ERROR"

    flags = control_flags or {"paused": False, "stopped": False}

    try:
        ses = lt.session({"listen_interfaces": "0.0.0.0:6881"})
        params: dict = {"save_path": save_path}

        if (source or "").startswith("magnet:?"):
            handle = lt.add_magnet_uri(ses, source, params)
            progress_callback("Fetching magnet metadata...", 0.0)
        else:
            info = lt.torrent_info(source)
            params["ti"] = info
            handle = ses.add_torrent(params)

        was_paused = False

        while True:
            if flags.get("stopped", False):
                try:
                    ses.remove_torrent(handle)
                except Exception:
                    pass
                progress_callback("Stopped", 0.0)
                return "STOPPED"

            paused = flags.get("paused", False)
            if paused and not was_paused:
                try:
                    handle.pause()
                except Exception:
                    pass
                was_paused = True
            elif not paused and was_paused:
                try:
                    handle.resume()
                except Exception:
                    pass
                was_paused = False

            if paused:
                current = 0.0
                try:
                    if handle.has_metadata():
                        current = float(handle.status().progress)
                except Exception:
                    current = 0.0
                progress_callback("Paused", current)
                time.sleep(poll_interval_s)
                continue

            if not handle.has_metadata():
                progress_callback("Fetching magnet metadata...", 0.0)
                time.sleep(poll_interval_s)
                continue

            s = handle.status()
            progress = float(getattr(s, "progress", 0.0) or 0.0)
            download_rate_kb = float(getattr(s, "download_rate", 0.0) or 0.0) / 1000.0
            peers = int(getattr(s, "num_peers", 0) or 0)
            state = getattr(s, "state", "")
            state_str = getattr(state, "name", None) or str(state)

            progress_callback(
                f"{state_str} | Peers: {peers} | {download_rate_kb:.1f} kB/s",
                progress,
            )

            if handle.is_seed():
                return "SUCCESS"

            time.sleep(poll_interval_s)
    except Exception as exc:
        progress_callback(f"Error: {exc}", 0.0)
        return "ERROR"

