from __future__ import annotations

from pathlib import Path

from hub.config import GCS_BUCKET, GOOGLE_CLOUD_PROJECT, MEDIA_DIR, ensure_dirs

STATIC_DEMO = Path(__file__).resolve().parent / "static" / "demo"


def save_bytes(filename: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    ensure_dirs()
    safe = filename.replace("..", "_").replace("/", "_").replace("\\", "_")
    dest = MEDIA_DIR / safe
    dest.write_bytes(data)
    if GCS_BUCKET:
        try:
            from google.cloud import storage

            client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
            blob = client.bucket(GCS_BUCKET).blob(f"media/{safe}")
            blob.upload_from_filename(str(dest), content_type=content_type)
            return f"gs://{GCS_BUCKET}/media/{safe}"
        except Exception as exc:  # noqa: BLE001
            print(f"[hub] GCS upload failed, keeping local file: {exc}")
    return str(dest)


def save_demo_asset(filename: str, data: bytes, content_type: str) -> str:
    """Persist week video/audio for the public demo (local + GCS demo/)."""
    ensure_dirs()
    safe = filename.replace("..", "_").replace("/", "_").replace("\\", "_")
    local = MEDIA_DIR / safe
    local.write_bytes(data)
    try:
        STATIC_DEMO.mkdir(parents=True, exist_ok=True)
        (STATIC_DEMO / safe).write_bytes(data)
    except Exception as exc:  # noqa: BLE001
        print(f"[hub] static/demo write skipped: {exc}")
    if GCS_BUCKET:
        try:
            from google.cloud import storage

            client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
            blob = client.bucket(GCS_BUCKET).blob(f"demo/{safe}")
            blob.upload_from_string(data, content_type=content_type)
            return f"gs://{GCS_BUCKET}/demo/{safe}"
        except Exception as exc:  # noqa: BLE001
            print(f"[hub] GCS demo upload failed: {exc}")
    return str(local)


def demo_asset_bytes(kind: str) -> tuple[bytes, str] | None:
    """Return (bytes, media_type) for baked week video/audio if available."""
    names = {
        "video": [("week_recap.mp4", "video/mp4"), ("week_video.mp4", "video/mp4"), ("recap.mp4", "video/mp4")],
        "audio": [
            ("week_theme.wav", "audio/wav"),
            ("week_theme.mp3", "audio/mpeg"),
            ("week_audio.wav", "audio/wav"),
            ("week_audio.mp3", "audio/mpeg"),
        ],
    }.get(kind, [])
    for name, media_type in names:
        local_static = STATIC_DEMO / name
        if local_static.is_file():
            return local_static.read_bytes(), media_type
        media_path = MEDIA_DIR / name
        if media_path.is_file():
            return media_path.read_bytes(), media_type
        if GCS_BUCKET:
            try:
                data = read_bytes(f"gs://{GCS_BUCKET}/demo/{name}")
                if data:
                    return data, media_type
            except Exception:  # noqa: BLE001
                pass
    return None


def demo_asset_exists(kind: str) -> bool:
    return demo_asset_bytes(kind) is not None


def delete_path(path: str) -> None:
    if not path:
        return
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            _, rest = path.split("gs://", 1)
            bucket_name, blob_name = rest.split("/", 1)
            client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
            client.bucket(bucket_name).blob(blob_name).delete()
            return
        local = Path(path)
        if local.exists():
            local.unlink()
    except Exception as exc:  # noqa: BLE001
        print(f"[hub] media delete skipped: {exc}")


def read_bytes(path: str) -> bytes:
    if path.startswith("gs://"):
        from google.cloud import storage

        _, rest = path.split("gs://", 1)
        bucket_name, blob_name = rest.split("/", 1)
        client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
        return client.bucket(bucket_name).blob(blob_name).download_as_bytes()
    return Path(path).read_bytes()
