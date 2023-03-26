# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from melcloudmqtt import config as app

_log = logging.getLogger(__name__)


class Device:
    def __init__(self, device_conf: Dict[str, Any]):
        self._device_conf = device_conf
        self._values: Dict[str, Any] = {}
        self.__prev_last_update: Optional[datetime] = None

        self.device_id = device_conf.get("DeviceID")
        self.building_id = device_conf.get("BuildingID")
        self.mac = device_conf.get("MacAddress")
        self.serial = device_conf.get("SerialNumber")

        self._update_values()

    def update(self, device_confs: List[Dict[str, Any]]) -> bool:
        """
        Update properties if there is update for this, returns True if there
        is update for this. Update does not necessarily mean there is updated
        values, see values() for that.
        """
        try:
            self._device_conf = next(
                c for c in device_confs if c.get("DeviceID") == self.device_id and c.get("BuildingID") == self.building_id
            )
        except StopIteration:
            return False
        self._update_values()
        _log.info("device %s state updated", self.device_id)
        return True

    def _update_values(self) -> None:
        _log.debug("device %s prev / last update: %s / %s", self.device_id, self.__prev_last_update, self.last_update)
        if self.__prev_last_update == self.last_update:
            # no update - no new values
            self._values = {}
            _log.debug("device %s value collection cleared", self.device_id)
        else:
            self.__prev_last_update = self.last_update
            new_values = self._collect_values()
            if new_values == self._values:
                # identical - no new values
                self._values = {}
                _log.debug("device %s value collection cleared 2", self.device_id)
            else:
                _log.debug("device %s value collection updated", self.device_id)
                self._values = new_values

    @staticmethod
    def get_device_id(device_conf: Dict[str, Any]) -> Any:
        """Get device id from properties dictionary."""
        return device_conf.get("DeviceID")

    @property
    def name(self) -> Any:
        """Return device name."""
        return self._device_conf.get("DeviceName")

    @property
    def last_update(self) -> Optional[datetime]:
        """
        Return timestamp of the last update from MELCloud.
        This Does not equal to devices last report to MELCloud.
        The timestamp is in UTC.
        """
        ts = self.get_prop_value("LastTimeStamp")
        if ts:
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return None

    def get_prop_value(self, name: str) -> Optional[Any]:
        """Access device properties."""
        device = self._device_conf.get("Device", {})
        return device.get(name)

    def values(self) -> Dict[str, Any]:
        """Get values dictionary or empty one if there is no changes."""
        return self._values.copy()

    def _collect_values(self) -> Dict[str, Any]:
        values = {}
        device = self._device_conf.get("Device", {})
        for p in app.cfg.properties:
            if p.name in device:
                values[p.key] = self.get_prop_value(p.name)
        return values
