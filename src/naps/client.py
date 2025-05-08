import logging
from http import HTTPMethod, HTTPStatus
from json import JSONDecodeError
from typing import Any, Literal
from urllib.parse import urljoin

from requests import HTTPError, Response, Session
from rich.json import JSON

logger = logging.getLogger(__name__)
DEFAULT_OK = [HTTPStatus.OK]


def format_payload(data: str | bytes | None):
    if not data:
        return ""
    if isinstance(data, bytes):
        data = data.decode()
    try:
        return JSON(data).text
    except JSONDecodeError:
        return data


class ImmichClient:
    _session: Session
    host: str

    def __init__(self, host: str, api_key: str) -> None:
        self.host = host
        self._session = Session()
        self._session.headers.update({"x-api-key": api_key})
        self.validate_authentication()

    def request(
        self,
        method: HTTPMethod,
        path: str,
        ok: list[HTTPStatus] = DEFAULT_OK,
        **kwargs: Any,
    ) -> Response:
        url = urljoin(self.host, path)
        res = self._session.request(method=method, url=url, **kwargs)
        logger.debug(
            "%(status)s %(method)s %(url)s \nRequest: %(req)s \nResult: %(res)s",
            {
                "status": res.status_code,
                "method": res.request.method,
                "url": res.url,
                "req": format_payload(res.request.body),
                "res": format_payload(res.text),
            },
        )
        if res.status_code not in ok:
            raise HTTPError(response=res)
        return res.json()

    def validate_authentication(self):
        _ = self.request(HTTPMethod.POST, "api/auth/validateToken")
        logger.info("Authentication successful")

    def get_random(
        self,
        number: int = 1,
        asset_type: Literal["IMAGE", "VIDEO", "AUDIO", "OTHER"] = "IMAGE",
        tag: str | None = None,
    ):
        return self.request(
            HTTPMethod.POST,
            "api/search/random",
            json={
                "size": number,
                "type": asset_type,
                "tagIds": [tag] if tag else [],
            },
        )
