import logging
from enum import StrEnum, auto

import typer
from requests import HTTPError
from rich.logging import RichHandler

from .client import AuthenticationError, ImmichClient
from .config import load_config

app = typer.Typer()


logger = logging.getLogger("naps")
logger.addHandler(RichHandler(rich_tracebacks=True, tracebacks_code_width=None))  # type: ignore


class LogLevel(StrEnum):
    DEBUG = auto()
    INFO = auto()


@app.command()
def main(log: str = "INFO") -> None:
    logger.setLevel(log)

    config = load_config()

    client = ImmichClient(config.base_url, config.api_key)
    logger.info("Connected to %s", client.host)


if __name__ == "__main__":
    try:
        app()
    except AuthenticationError:
        logger.error("Invalid API token!")
    except HTTPError as e:
        logger.error("Unexpected HTTP %s error!", e.response.status_code)
