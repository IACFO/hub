from __future__ import annotations

from pathlib import Path

from hub.config import GCS_BUCKET, GOOGLE_CLOUD_PROJECT, MEDIA_DIR, ensure_dirs


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


def read_bytes(path: str) -> bytes:
    if path.startswith("gs://"):
        from google.cloud import storage

        _, rest = path.split("gs://", 1)
        bucket_name, blob_name = rest.split("/", 1)
        client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
        return client.bucket(bucket_name).blob(blob_name).download_as_bytes()
    return Path(path).read_bytes()
