import logging
from http import HTTPStatus

from apscheduler.schedulers.blocking import (  # pyright: ignore[reportMissingTypeStubs]
    BlockingScheduler,
)
from requests import HTTPError, PreparedRequest

from .client import ImmichClient
from .config import config
from .sender import sender
from .utils import format_payload

logger = logging.getLogger(__name__)


def job():
    try:
        client = ImmichClient(config.immich.base_url, config.immich.api_key)
        tag = client.get_tag_by_name(config.immich.tag_name)

        image = client.get_random_unique(asset_type="IMAGE", tag_id=tag.id)
        data = client.download_asset(image.id)
        sender.send(image, data)
    except HTTPError as e:
        match e.response.status_code:
            case HTTPStatus.UNAUTHORIZED:
                logger.error("Invalid API token!")
            case _:
                logger.error(
                    """%(status)s %(method)s [ERR] %(url)s
Request:   %(req)s
Response:  %(res)s
            """,
                    {
                        "status": e.response.status_code,
                        "method": e.request.method,
                        "url": e.response.url,
                        "req": format_payload(
                            e.request.body
                            if isinstance(e.request, PreparedRequest)
                            else e.request.data
                        ),
                        "res": format_payload(e.response.text),
                    },
                )
    except Exception:
        logger.exception("Unexpected error in job!")


scheduler = BlockingScheduler()
_ = scheduler.add_job(job, "interval", seconds=30)  # pyright: ignore[reportUnknownMemberType]
