import logging
import sqlite3
from pathlib import Path
from types import TracebackType

from .client.models import ImmichAsset

TABLE_SQL = (("sent_assets", "CREATE TABLE sent_assets(id)"),)

logger = logging.getLogger(__name__)


class Connection:
    _con: sqlite3.Connection

    def __init__(self, path: Path) -> None:
        logger.debug("Opening connection to database at %s", path)
        self._con = sqlite3.connect(path)
        self._con.set_trace_callback(logger.debug)

    def __enter__(self):
        return self._con

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        logger.debug("Closing database connection")
        self._con.close()


class StateManager:
    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path
        with self._connect() as con:
            cur = con.cursor()

            # create needed tables if they don't exist
            for table_name, table_sql in TABLE_SQL:
                if cur.execute(
                    "SELECT sql FROM sqlite_schema WHERE name = ?", (table_name,)
                ).fetchone() != (table_sql,):
                    logger.info("Initialising table %s", table_sql)
                    _ = cur.execute(table_sql)
                    con.commit()

    def _connect(self):
        return Connection(self.path)

    def was_sent(self, asset: ImmichAsset):
        with self._connect() as con:
            cur = con.cursor()
            res = cur.execute("SELECT id FROM sent_assets WHERE id = ?", (asset.id,)).fetchone()
            return res is not None

    def mark_sent(self, assets: list[ImmichAsset]):
        with self._connect() as con:
            cur = con.cursor()
            _ = cur.executemany(
                "INSERT INTO sent_assets VALUES(?)", [(asset.id,) for asset in assets]
            )
            con.commit()

    def list_sent(self):
        with self._connect() as con:
            cur = con.cursor()
            return [row[0] for row in cur.execute("SELECT id FROM sent_assets").fetchall()]


state = StateManager(Path("db.sqlite3"))
