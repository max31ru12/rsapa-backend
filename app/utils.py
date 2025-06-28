from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


async def write_file(file: UploadFile) -> str:
    ext = file.filename.split(".")[-1]
    filename = f"{uuid4().hex}.{ext}"
    filepath = settings.MEDIA_STORAGE_PATH / filename

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    return f"media/{filename}"
