from io import BytesIO
from logging import getLogger

import magic
from pi_heif import (  # pyright: ignore[reportMissingTypeStubs]
    register_heif_opener,  # pyright: ignore[reportUnknownVariableType]
)
from PIL import Image

logger = getLogger(__name__)

register_heif_opener()

ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
]
TARGET_FORMAT = "PNG"


def convert(image: bytes) -> bytes:
    mime = magic.from_buffer(image, mime=True)
    if mime in ALLOWED_MIME_TYPES:
        logger.debug("Image is already %s", mime)
        return image
    with BytesIO(image) as data, BytesIO() as ret:
        logger.debug("Image is originally %s, converting to %s", mime, TARGET_FORMAT)
        im = Image.open(data)
        im.save(ret, format=TARGET_FORMAT)
        return ret.getvalue()
