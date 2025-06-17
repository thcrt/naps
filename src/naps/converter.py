from io import BytesIO
from logging import getLogger

import magic
from pi_heif import (  # pyright: ignore[reportMissingTypeStubs]
    register_heif_opener,  # pyright: ignore[reportUnknownVariableType]
)
from PIL import Image

from .client.models import ImmichAsset

logger = getLogger(__name__)

register_heif_opener()

ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
]
TARGET_FORMAT = "PNG"


def convert(image: ImmichAsset, image_data: bytes) -> tuple[ImmichAsset, bytes]:
    mime = magic.from_buffer(image_data, mime=True)
    if mime in ALLOWED_MIME_TYPES:
        logger.debug("Image is already %s", mime)
        return image, image_data
    with BytesIO(image_data) as data, BytesIO() as ret:
        logger.debug("Image is originally %s, converting to %s", mime, TARGET_FORMAT)
        im = Image.open(data)
        im.save(ret, format=TARGET_FORMAT)
        image.filename = f"{image.filename}.{TARGET_FORMAT}"
        return image, ret.getvalue()
