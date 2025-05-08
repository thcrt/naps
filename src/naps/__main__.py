import logging
from http import HTTPStatus

import typer
from requests import HTTPError
from rich.logging import RichHandler

from .client import ImmichClient
from .config import Config, load_config

app = typer.Typer()


logger = logging.getLogger("naps")
logger.addHandler(RichHandler(rich_tracebacks=True, tracebacks_code_width=None))  # type: ignore


def select_image(client: ImmichClient, config: Config):
    tag = client.get_tag_by_name(config.tag_name)
    return client.get_random(asset_type="IMAGE", tag_id=tag.id)


@app.command()
def main(log: str = "INFO") -> None:
    logger.setLevel(log)
    config = load_config()
    client = ImmichClient(config.base_url, config.api_key)

    logger.info(select_image(client, config))


if __name__ == "__main__":
    try:
        app()
    except HTTPError as e:
        match e.response.status_code:
            case HTTPStatus.UNAUTHORIZED:
                logger.error("Invalid API token!")
            case _:
                logger.error("Unexpected HTTP %s error!", e.response.status_code)
