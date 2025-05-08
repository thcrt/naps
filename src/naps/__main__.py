import logging
from enum import StrEnum, auto
from http import HTTPStatus

import typer
from requests import HTTPError
from rich.logging import RichHandler

from .client import ImmichClient
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

    client.get_random()


if __name__ == "__main__":
    try:
        app()
    except HTTPError as e:
        match e.response.status_code:
            case HTTPStatus.UNAUTHORIZED:
                logger.error("Invalid API token!")
            case _:
                logger.error("Unexpected HTTP %s error!", e.response.status_code)
