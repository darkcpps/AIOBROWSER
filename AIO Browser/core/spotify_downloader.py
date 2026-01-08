# Spotify support removed. Monochrome downloader handles music sources now.
# Stubbed classes remain to provide clearer error messages if legacy code attempts to use them.

class SpotifyAPI:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Spotify support has been removed. Use Monochrome downloader instead.")

class SpotiDownloaderAPI:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Spotify support has been removed. Use Monochrome downloader instead.")

class MetadataEmbedder:
    @staticmethod
    def embed(*args, **kwargs):
        raise NotImplementedError("Spotify support has been removed. Use Monochrome downloader instead.")


class SpotifyAPI:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Spotify support has been removed. Use Monochrome downloader instead.")


class SpotiDownloaderAPI:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Spotify support has been removed. Use Monochrome downloader instead.")


class MetadataEmbedder:
    @staticmethod
    def embed(*args, **kwargs):
        raise NotImplementedError("Spotify support has been removed. Use Monochrome downloader instead.")

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
