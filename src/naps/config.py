import tomllib
from dataclasses import dataclass
from pathlib import Path

import tattl


@dataclass
class Config:
    base_url: str
    api_key: str


def load_config():
    with Path("config.toml").open("rb") as f:
        data = tomllib.load(f)
    return tattl.unpack_dict(data, Config)
