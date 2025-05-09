import logging
from http import HTTPStatus
from pathlib import Path
from time import sleep

import typer
from apscheduler.schedulers.blocking import (  # pyright: ignore[reportMissingTypeStubs]
    BlockingScheduler,
)
from redmail.email.sender import EmailSender
from requests import HTTPError, PreparedRequest
from rich import print as rich_print
from rich.logging import RichHandler

from .client import ImmichClient, format_payload
from .config import Config, load_config
from .state import StateManager

app = typer.Typer()

MAX_BACKOFF = 60 * 60 * 24 * 7  # 1 week


config = load_config()
state = StateManager(Path("db.sqlite3"))

logger = logging.getLogger("naps")
logger.addHandler(RichHandler(rich_tracebacks=True, tracebacks_code_width=None))  # pyright: ignore[reportArgumentType]


def send(config: Config, sender: EmailSender):
    client = ImmichClient(config.immich.base_url, config.immich.api_key)

    tag = client.get_tag_by_name(config.immich.tag_name)

    backoff_seconds = 1
    while True:
        image = client.get_random(asset_type="IMAGE", tag_id=tag.id)[0]
        if not state.was_sent(image):
            break
        logger.info(
            "Chosen image %s has already been sent. Will choose another after %d seconds.",
            image.id,
            backoff_seconds,
        )
        sleep(backoff_seconds)
        backoff_seconds = min(backoff_seconds * 2, MAX_BACKOFF)

    image_data = client.download_asset(image.id)

    logger.info('Sending email to "%s"', config.email.recipient)
    _ = sender.send(  # pyright: ignore[reportUnknownMemberType]
        subject=config.email.subject,
        sender=config.email.sender,
        receivers=[config.email.recipient],
        text=config.email.text,
        attachments={image.filename: image_data},
    )
    state.mark_sent([image])


@app.command()
def run() -> None:
    scheduler = BlockingScheduler()

    logger.info(
        """Connecting to email server with following configuration:
  Host:     %(host)s
  Port:     %(port)d
  Username: %(username)s
  STARTTLS: %(start_tls)s""",
        {
            "host": config.email.smtp.host,
            "port": config.email.smtp.port,
            "username": config.email.smtp.username,
            "start_tls": config.email.smtp.start_tls,
        },
    )
    sender = EmailSender(
        host=config.email.smtp.host,
        port=config.email.smtp.port,
        username=config.email.smtp.username,
        password=config.email.smtp.password,
        use_starttls=config.email.smtp.start_tls,
    )

    _ = scheduler.add_job(lambda: send(config, sender), "interval", seconds=30)  # pyright: ignore[reportUnknownMemberType]
    scheduler.start()  # pyright: ignore[reportUnknownMemberType]


@app.command()
def list_sent() -> None:
    for asset_id in state.list_sent():
        rich_print(asset_id)


@app.callback()
def main(log: str = "WARNING") -> None:
    logger.setLevel(log)
    logger.info("Starting naps!")


if __name__ == "__main__":
    try:
        app()
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
