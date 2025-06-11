import logging
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import cast

from apscheduler.events import (  # pyright: ignore[reportMissingTypeStubs]
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_SCHEDULER_STARTED,
    JobEvent,
)
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
scheduled_job = scheduler.add_job(  # pyright: ignore[reportUnknownMemberType]
    job,
    "interval",
    days=config.schedule.days,
    hours=config.schedule.hours,
    minutes=config.schedule.minutes,
    seconds=config.schedule.seconds,
)


def log_next_run(_: JobEvent):
    next_run = cast("datetime", scheduled_job.next_run_time)  # pyright: ignore[reportUnknownMemberType]
    delta = next_run - datetime.now(tz=UTC)
    logger.info(
        "Next run scheduled for %s (in %d days, %s)",
        next_run,
        delta.days,
        timedelta(seconds=delta.seconds),
    )


scheduler.add_listener(  # pyright: ignore[reportUnknownMemberType]
    log_next_run, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED | EVENT_SCHEDULER_STARTED
)
