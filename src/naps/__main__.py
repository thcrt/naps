import logging
from http import HTTPStatus

import typer
from apscheduler.schedulers.blocking import (  # pyright: ignore[reportMissingTypeStubs]
    BlockingScheduler,
)
from redmail.email.sender import EmailSender
from requests import HTTPError, PreparedRequest
from rich.logging import RichHandler

from .client import ImmichClient, format_payload
from .config import Config, load_config

app = typer.Typer()


logger = logging.getLogger("naps")
logger.addHandler(RichHandler(rich_tracebacks=True, tracebacks_code_width=None))  # pyright: ignore[reportArgumentType]


def send(client: ImmichClient, config: Config, sender: EmailSender):
    tag = client.get_tag_by_name(config.immich.tag_name)
    image = client.get_random(asset_type="IMAGE", tag_id=tag.id)[0]
    image_data = client.download_asset(image.id)

    logger.info('Sending email to "%s"', config.email.recipient)
    _ = sender.send(  # pyright: ignore[reportUnknownMemberType]
        subject=config.email.subject,
        sender=config.email.sender,
        receivers=[config.email.recipient],
        text=config.email.text,
        attachments={image.filename: image_data},
    )


@app.command()
def main(log: str = "INFO") -> None:
    logger.setLevel(log)
    config = load_config()
    client = ImmichClient(config.immich.base_url, config.immich.api_key)
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

    _ = scheduler.add_job(lambda: send(client, config, sender), "interval", seconds=30)  # pyright: ignore[reportUnknownMemberType]
    scheduler.start()  # pyright: ignore[reportUnknownMemberType]


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
