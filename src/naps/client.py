import logging
from http import HTTPMethod, HTTPStatus
from json import JSONDecodeError
from typing import Any, Literal, override
from urllib.parse import urljoin

from requests import HTTPError, Session
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


type ImmichAssetType = Literal["IMAGE", "VIDEO", "AUDIO", "OTHER"]


class ImmichAsset:
    id: str
    filename: str
    asset_type: ImmichAssetType

    def __init__(self, **kwargs: Any) -> None:
        self.id = kwargs["id"]
        self.filename = kwargs["originalFileName"]
        self.asset_type = kwargs["type"]

    @override
    def __repr__(self) -> str:
        return f'ImmichAsset(type="{self.asset_type}", id="{self.id}")'


class ImmichClient:
    _session: Session
    host: str

    def __init__(self, host: str, api_key: str) -> None:
        logger.info("Initialising connection to host %s", host)
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
    ) -> Any:
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
        logger.info("Validating authentication token")
        _ = self.request(HTTPMethod.POST, "api/auth/validateToken")
        logger.info("Authentication successful")

    def get_random(
        self,
        number: int = 1,
        asset_type: ImmichAssetType | None = "IMAGE",
        tag: str | None = None,
    ):
        logger.info(
            "Requesting random assets [count: %(n)d, type: %(type)s, tag: %(tag)s]",
            {
                "n": number,
                "type": asset_type,
                "tag": tag,
            },
        )
        res = self.request(
            HTTPMethod.POST,
            "api/search/random",
            json={
                "size": number,
                "type": asset_type,
                "tagIds": [tag] if tag else [],
            },
        )
        assets = [ImmichAsset(**asset) for asset in res]

        if len(assets) != number:
            logger.error("Requested %d assets, but %d assets were found!", number, len(assets))

        if len(assets) == 1:
            logger.info("Selected random asset %s", assets[0])
        else:
            logger.info("Selected %d random assets", len(assets))
            logger.debug(assets)

        return assets
