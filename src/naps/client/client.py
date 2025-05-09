import logging
from http import HTTPMethod, HTTPStatus
from time import sleep
from typing import Any
from urllib.parse import urljoin

from requests import HTTPError, Session

from naps.state import state
from naps.utils import format_payload

from .models import ImmichAsset, ImmichAssetType, ImmichTag

DEFAULT_OK = [HTTPStatus.OK]
MAX_BACKOFF = 60 * 60 * 24 * 7  # 1 week

logger = logging.getLogger(__name__)


class ImmichClient:
    _session: Session
    host: str

    def __init__(self, host: str, api_key: str) -> None:
        logger.info("Initialising connection to host %s", host)
        self.host = host
        self._session = Session()
        self._session.headers.update({"x-api-key": api_key})
        self.validate_authentication()

    def _request(
        self,
        method: HTTPMethod,
        path: str,
        ok: list[HTTPStatus] = DEFAULT_OK,
        **kwargs: Any,
    ):
        res = self._session.request(
            method=method,
            url=urljoin(self.host, path),
            **kwargs,
        )
        if res.status_code not in ok:
            raise HTTPError(response=res)
        return res

    def request_json(
        self,
        method: HTTPMethod,
        path: str,
        ok: list[HTTPStatus] = DEFAULT_OK,
        **kwargs: Any,
    ) -> Any:
        res = self._request(method, path, ok, **kwargs)
        logger.debug(
            """%(status)s %(method)s [JSON] %(url)s
Request:   %(req)s
Response:  %(res)s
            """,
            {
                "status": res.status_code,
                "method": res.request.method,
                "url": res.url,
                "req": format_payload(res.request.body),
                "res": format_payload(res.text),
            },
        )
        return res.json()

    def request_bytes(
        self,
        method: HTTPMethod,
        path: str,
        ok: list[HTTPStatus] = DEFAULT_OK,
        **kwargs: Any,
    ) -> bytes:
        res = self._request(method, path, ok, **kwargs)
        logger.debug(
            """%(status)s %(method)s [BYTES] %(url)s
Request:   %(req)s
            """,
            {
                "status": res.status_code,
                "method": res.request.method,
                "url": res.url,
                "req": format_payload(res.request.body),
            },
        )
        return res.content

    def validate_authentication(self):
        logger.info("Validating authentication token")
        _ = self.request_json(HTTPMethod.POST, "api/auth/validateToken")
        logger.info("Authentication successful")

    def get_tags(self) -> list[ImmichTag]:
        logger.info("Looking up all tags")
        tags = [ImmichTag(**tag) for tag in self.request_json(HTTPMethod.GET, "api/tags")]
        logger.info("Found %d tags", len(tags))
        return tags

    def get_tag_by_name(self, name: str) -> ImmichTag:
        matches = list(filter((lambda tag: tag.full_name == name), self.get_tags()))
        if len(matches) != 1:
            logger.error(
                "Expected only one tag with name %(name)s, but %(matches)d were found!",
                {"name": name, "matches": len(matches)},
            )
        tag = matches[0]
        logger.info("Filtered tags by name, selected %s", repr(tag))
        return tag

    def download_asset(self, asset_id: str) -> bytes:
        logger.info("Downloading asset %s", asset_id)
        return self.request_bytes(HTTPMethod.GET, f"api/assets/{asset_id}/original")

    def get_random(
        self,
        number: int = 1,
        asset_type: ImmichAssetType | None = "IMAGE",
        tag_id: str | None = None,
    ):
        logger.info(
            "Requesting random assets [count: %(n)d, type: %(type)s, tag: %(tag)s]",
            {
                "n": number,
                "type": asset_type,
                "tag": tag_id,
            },
        )
        assets = [
            ImmichAsset(**asset)
            for asset in self.request_json(
                HTTPMethod.POST,
                "api/search/random",
                json={
                    "size": number,
                    "type": asset_type,
                    "tagIds": [tag_id] if tag_id else [],
                },
            )
        ]

        if len(assets) != number:
            logger.error("Requested %d assets, but %d assets were found!", number, len(assets))

        if len(assets) == 1:
            logger.info("Selected random asset %s", assets[0])
        else:
            logger.info("Selected %d random assets", len(assets))
            logger.debug(assets)

        return assets

    def get_random_unique(
        self,
        asset_type: ImmichAssetType | None = "IMAGE",
        tag_id: str | None = None,
    ):
        backoff_seconds = 1
        while True:
            image = self.get_random(asset_type=asset_type, tag_id=tag_id)[0]
            if not state.was_sent(image):
                break
            logger.info(
                "Chosen image %s has already been sent. Will choose another after %d seconds.",
                image.id,
                backoff_seconds,
            )
            sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2, MAX_BACKOFF)
        return image
