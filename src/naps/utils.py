from json import JSONDecodeError

from rich.json import JSON


def format_payload(data: str | bytes | None):
    if not data:
        return ""
    if isinstance(data, bytes):
        data = data.decode()
    try:
        return JSON(data).text
    except JSONDecodeError:
        return data
