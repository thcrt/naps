import tomllib
from dataclasses import dataclass
from pathlib import Path

import tattl


@dataclass
class EmailSMTPConfig:
    host: str
    port: int
    username: str
    password: str
    start_tls: bool = False


@dataclass
class EmailConfig:
    smtp: EmailSMTPConfig
    sender: str
    recipient: str
    subject: str = "NAPS automatically sent media"
    text: str = "This email was automatically sent by NAPS."


@dataclass
class ImmichConfig:
    base_url: str
    api_key: str
    tag_name: str


@dataclass
class ScheduleConfig:
    days: int
    hours: int = 0
    minutes: int = 0
    seconds: int = 0


@dataclass
class Config:
    immich: ImmichConfig
    email: EmailConfig
    schedule: ScheduleConfig


def load_config(path: Path):
    with path.open("rb") as f:
        data = tomllib.load(f)
    return tattl.unpack_dict(data, Config)


config = load_config(Path("config.toml"))
