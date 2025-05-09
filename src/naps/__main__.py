import logging

import typer
from rich import print as rich_print
from rich.logging import RichHandler

from .schedule import scheduler
from .state import state

logger = logging.getLogger("naps")
logging.getLogger().addHandler(
    RichHandler(
        rich_tracebacks=True,
        tracebacks_code_width=None,  # pyright: ignore[reportArgumentType]
    )
)

app = typer.Typer()


@app.callback()
def main(log: str = "WARNING") -> None:
    logger.setLevel(log)
    logger.info("Starting naps!")


@app.command()
def run() -> None:
    scheduler.start()  # pyright: ignore[reportUnknownMemberType]


@app.command()
def list_sent() -> None:
    for asset_id in state.list_sent():
        rich_print(asset_id)


if __name__ == "__main__":
    app()
