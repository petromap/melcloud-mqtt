# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession

from melcloudmqtt import config as app
from melcloudmqtt.config import Url as ServiceUrl

_log = logging.getLogger(__name__)


class Client:
    """Client to read MELCloud."""

    def __init__(self, token: str):
        """Initialize the client."""
        self._token = token
        self._device_confs: List[Dict[str, Any]] = []

    @staticmethod
    def _headers(token: str) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/110.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "X-MitsContextKey": token,
            "X-Requested-With": "XMLHttpRequest",
        }

    @property
    def device_confs(self) -> List[Dict[Any, Any]]:
        """Return device configurations."""
        return self._device_confs

    async def fetch_device_confs(self) -> None:
        """Fetch all configured devices."""
        _session = ClientSession()
        async with _session.get(
            ServiceUrl.get_list_devices_url(), headers=Client._headers(self._token), raise_for_status=True
        ) as resp:
            entries = await resp.json()
            new_devices = []
            _log.debug("response(list_devices): %s", resp)
            _log.debug("response_data(list_devices): %s", entries)

            for entry in entries:
                new_devices.extend(entry["Structure"]["Devices"])

                for area in entry["Structure"]["Areas"]:
                    new_devices.extend(area["Devices"])

                for floor in entry["Structure"]["Floors"]:
                    new_devices.extend(floor["Devices"])

                    for area in floor["Areas"]:
                        new_devices.extend(area["Devices"])

            self._device_confs = new_devices
        await _session.close()

    async def fetch_device_state(self, device) -> Optional[Dict[Any, Any]]:
        """Fetch state information of a device."""
        device_id = device.device_id
        building_id = device.building_id
        _session = ClientSession()
        try:
            async with _session.get(
                ServiceUrl.get_device_state_url(device_id, building_id),
                headers=Client._headers(self._token),
                raise_for_status=True,
            ) as resp:
                state = await resp.json()
                _log.debug("response(device_state): %s", resp)
                _log.debug("response_data(device_state): %s", state)
                return state
        finally:
            await _session.close()

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str):
        self._token = value


class ClientLogin:
    """MELCloud client auth handler."""

    @staticmethod
    async def _do_login(_session: ClientSession) -> Any:
        body = {
            "AppVersion": "1.26.2.0",
            "CaptchaResponse": None,
            "Email": app.cfg.melcloud.username,
            "Language": 0,
            "Password": app.cfg.melcloud.password,
            "Persist": True,
        }

        async with _session.post(ServiceUrl.get_login_url(), json=body, raise_for_status=True) as resp:
            return await resp.json()

    @staticmethod
    async def login() -> Client:
        async with ClientSession() as _session:
            response = await ClientLogin._do_login(_session)
        _log.debug("response(login): %s", response)

        return Client(response.get("LoginData").get("ContextKey"))

    @staticmethod
    async def refresh(client: Client) -> None:
        async with ClientSession() as _session:
            response = await ClientLogin._do_login(_session)
        _log.debug("response(refresh): %s", response)
        client.token = response.get("LoginData").get("ContextKey")
