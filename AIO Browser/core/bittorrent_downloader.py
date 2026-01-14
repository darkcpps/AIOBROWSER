import time
import tempfile
from typing import Callable, Mapping, Sequence

try:
    import libtorrent as lt  # type: ignore
except Exception:  # pragma: no cover
    lt = None


def is_available() -> bool:
    return lt is not None


def list_torrent_files(
    source: str,
    status_callback: Callable[[str], None] | None = None,
    cancel_flags: Mapping[str, bool] | None = None,
    timeout_s: float = 60.0,
    poll_interval_s: float = 0.5,
) -> list[dict]:
    """
    Return torrent file entries as: {"index": int, "path": str, "size": int}

    For magnets, this waits for metadata (up to timeout_s). The temporary session is
    cleaned up before returning.
    """
    if lt is None:
        raise RuntimeError("libtorrent not installed")

    flags = cancel_flags or {}

    def _extract_files(info) -> list[dict]:
        files = info.files()
        try:
            count = int(files.num_files())
        except Exception:
            count = int(getattr(files, "num_files", 0) or 0)
        out: list[dict] = []
        for i in range(count):
            try:
                path = files.file_path(i)
            except Exception:
                path = ""
            try:
                size = int(files.file_size(i))
            except Exception:
                size = 0
            out.append({"index": i, "path": str(path), "size": size})
        return out

    def _get_info_from_handle(handle):
        for attr in ("torrent_file", "get_torrent_info"):
            try:
                fn = getattr(handle, attr, None)
                if callable(fn):
                    info = fn()
                    if info is not None:
                        return info
            except Exception:
                continue
        try:
            tf = getattr(handle, "torrent_file", None)
            if tf is not None:
                return tf
        except Exception:
            pass
        raise RuntimeError("Unable to read torrent metadata")

    src = (source or "").strip()
    if not src:
        raise ValueError("Missing torrent source")

    if src.startswith("magnet:?"):
        ses = lt.session({"listen_interfaces": "0.0.0.0:0"})
        params: dict = {"save_path": tempfile.gettempdir()}
        try:
            handle = lt.add_magnet_uri(ses, src, params)
            start = time.time()
            while True:
                if flags.get("stopped", False):
                    try:
                        ses.remove_torrent(handle, lt.session.delete_files)
                    except Exception:
                        pass
                    raise RuntimeError("Cancelled")

                if handle.has_metadata():
                    break

                if time.time() - start > timeout_s:
                    try:
                        ses.remove_torrent(handle, lt.session.delete_files)
                    except Exception:
                        pass
                    raise TimeoutError("Timed out waiting for magnet metadata")

                if status_callback:
                    status_callback("Fetching magnet metadata...")
                time.sleep(poll_interval_s)

            info = _get_info_from_handle(handle)
            entries = _extract_files(info)
        finally:
            try:
                if "handle" in locals():
                    ses.remove_torrent(handle, lt.session.delete_files)
            except Exception:
                pass
        return entries

    info = lt.torrent_info(src)
    return _extract_files(info)


def _apply_file_selection(handle, selected_file_indices: Sequence[int] | None) -> None:
    if lt is None or not selected_file_indices:
        return

    try:
        info = None
        for attr in ("torrent_file", "get_torrent_info"):
            fn = getattr(handle, attr, None)
            if callable(fn):
                try:
                    info = fn()
                    if info is not None:
                        break
                except Exception:
                    pass
        if info is None:
            try:
                info = handle.torrent_file()
            except Exception:
                info = None
        if info is None:
            return

        files = info.files()
        num_files = int(files.num_files())
        priorities = [0] * num_files
        for idx in selected_file_indices:
            try:
                i = int(idx)
            except Exception:
                continue
            if 0 <= i < num_files:
                priorities[i] = 1
        try:
            handle.prioritize_files(priorities)
        except Exception:
            try:
                handle.file_priorities(priorities)
            except Exception:
                pass
    except Exception:
        pass


def download_torrent(
    source: str,
    save_path: str,
    progress_callback: Callable[[str, float], None],
    control_flags: Mapping[str, bool] | None = None,
    selected_file_indices: Sequence[int] | None = None,
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
        ses = lt.session({"listen_interfaces": "0.0.0.0:0"})
        params: dict = {"save_path": save_path}

        if (source or "").startswith("magnet:?"):
            handle = lt.add_magnet_uri(ses, source, params)
            progress_callback("Fetching magnet metadata...", 0.0)
        else:
            info = lt.torrent_info(source)
            params["ti"] = info
            handle = ses.add_torrent(params)
            _apply_file_selection(handle, selected_file_indices)

        was_paused = False
        selection_applied = False

        while True:
            if flags.get("stopped", False):
                try:
                    # Pass delete_files to remove downloaded data from disk
                    ses.remove_torrent(handle, lt.session.delete_files)
                except Exception:
                    pass
                progress_callback("Stopped & Deleted", 0.0)
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

            if selected_file_indices and not selection_applied:
                _apply_file_selection(handle, selected_file_indices)
                selection_applied = True

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

