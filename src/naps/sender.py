import logging

from redmail.email.sender import EmailSender

from .client.models import ImmichAsset
from .config import config
from .state import state

logger = logging.getLogger(__name__)


class Sender:
    _sender: EmailSender

    def __init__(self) -> None:
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
        self._sender = EmailSender(
            host=config.email.smtp.host,
            port=config.email.smtp.port,
            username=config.email.smtp.username,
            password=config.email.smtp.password,
            use_starttls=config.email.smtp.start_tls,
        )

    def send(self, image: ImmichAsset, data: bytes):
        logger.info('Sending email to "%s"', config.email.recipient)
        _ = self._sender.send(  # pyright: ignore[reportUnknownMemberType]
            subject=config.email.subject,
            sender=config.email.sender,
            receivers=[config.email.recipient],
            text=config.email.text,
            attachments={f"{image.filename}.jpg": data},
        )
        state.mark_sent([image])


sender = Sender()
