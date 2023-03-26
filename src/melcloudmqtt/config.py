# -*- coding: utf-8 -*-
import logging
from dataclasses import dataclass
from io import IOBase
from typing import Dict, List, Optional

from mashumaro.mixins.yaml import DataClassYAMLMixin

_log = logging.getLogger(__name__)


@dataclass
class DeviceProperty(DataClassYAMLMixin):
    """
    Configuration for device property.
    Value of matching property by its name will end to published message
    with given key.
    """

    name: str  # name of property as received from MELCloud
    key: str  # key in MQTT message


@dataclass
class MQTT(DataClassYAMLMixin):
    """Configuration for connecting to MQTT broker, topic settings etc."""

    topic_prefix: str  # publish each device under this topic
    host: str
    port: int
    username: str
    password: str

    qos: int = 0
    """MQTT Quality of Service (QoS)"""

    def client_clean_sessions(self) -> bool:
        """
        Should the broker remove all information about this client when it
        disconnects.

        Returns
        -------
        bool
        True if qos is 1 or 2. See MQTT Quality of Service (QoS).
        """
        return not bool(self.qos)


@dataclass
class MELCloud(DataClassYAMLMixin):
    """Configuration for connecting to MELCloud."""

    username: str
    password: str
    # TODO: read intervals


@dataclass
class Configuration(DataClassYAMLMixin):
    """Configuration for this application, persisted as YAML."""

    logging_config: str  # ok, being lazy in here and using just single magic string
    loop_time: int
    mqtt: MQTT
    melcloud: MELCloud
    properties: List[DeviceProperty]


cfg: Configuration  # pylint: disable=C0103


def load_configuration(io_stream: IOBase) -> None:
    """
    Load configuration from YAML formatted file and deserialize it into
    dictionary. An instance of Configuration will be created from this
    dictionary.
    """

    global cfg  # pylint: disable=C0103
    try:
        cfg = Configuration.from_yaml(io_stream.read())
    except Exception as e:  # noqa
        _log.exception("Failed to parse configuration. %s", repr(e))
    finally:
        io_stream.close()


@dataclass
class Url:
    BASE_URL: str = "https://app.melcloud.com/Mitsubishi.Wifi.Client"

    @staticmethod
    def get_login_url() -> str:
        return f"{Url.BASE_URL}/Login/ClientLogin"

    @staticmethod
    def get_list_devices_url() -> str:
        return f"{Url.BASE_URL}/User/ListDevices"

    @staticmethod
    def get_device_state_url(device_id: str, building_id: str) -> str:
        return f"{Url.BASE_URL}/Device/Get?id={device_id}&buildingID={building_id}"
