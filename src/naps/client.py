import logging
from http import HTTPMethod, HTTPStatus
from typing import Any
from urllib.parse import urljoin

from requests import HTTPError, Response, Session

from .errors import AuthenticationError

logger = logging.getLogger(__name__)
DEFAULT_OK = [HTTPStatus.OK]


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
        logger.debug("%s %s %s", res.status_code, res.request.method, res.url)
        if res.status_code not in ok:
            raise HTTPError(response=res)
        return res

    def validate_authentication(self):
        try:
            _ = self.request(HTTPMethod.POST, "api/auth/validateToken")
            logger.info("Authentication successful")
        except HTTPError as e:
            match e.response.status_code:
                case HTTPStatus.UNAUTHORIZED:
                    raise AuthenticationError from e
                case _:
                    raise
