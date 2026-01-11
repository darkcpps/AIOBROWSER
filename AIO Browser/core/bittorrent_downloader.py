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
        # Create a basic libtorrent session
        ses = lt.session()
        
        # Add DHT bootstrap nodes for peer discovery
        try:
            ses.add_dht_node(("dht.transmissionbt.com", 6881))
            ses.add_dht_node(("router.bittorrent.com", 6881))
        except Exception:
            pass
        
        params: dict = {"save_path": save_path}

        if (source or "").startswith("magnet:?"):
            handle = lt.add_magnet_uri(ses, source, params)
            progress_callback("Fetching magnet metadata...", 0.0)
        else:
            info = lt.torrent_info(source)
            params["ti"] = info
            handle = ses.add_torrent(params)

        was_paused = False
        peer_reconnect_timer = 0

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
                peer_reconnect_timer = 0
            elif not paused and was_paused:
                try:
                    handle.resume()
                except Exception:
                    pass
                was_paused = False
                peer_reconnect_timer = 0
                # Force DHT refresh on resume
                try:
                    ses.add_dht_node(("dht.transmissionbt.com", 6881))
                    ses.add_dht_node(("router.bittorrent.com", 6881))
                except Exception:
                    pass

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

            # Periodically refresh peer connections if peer count is low
            peer_reconnect_timer += poll_interval_s
            if peers < 3 and peer_reconnect_timer > 10:
                try:
                    ses.add_dht_node(("dht.transmissionbt.com", 6881))
                    ses.add_dht_node(("router.bittorrent.com", 6881))
                except Exception:
                    pass
                peer_reconnect_timer = 0

            progress_callback(
                f"{state_str} | Peers: {peers} | {download_rate_kb:.1f} kB/s",
                progress,
            )

            if handle.is_seed():
                return "SUCCESS"

            time.sleep(poll_interval_s)
    except Exception as exc:
        import traceback
        error_msg = f"Error: {exc}\n{traceback.format_exc()}"
        print(error_msg)  # Print to console for debugging
        progress_callback(f"Error: {exc}", 0.0)
        return "ERROR"

