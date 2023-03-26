# -*- coding: utf-8 -*-
import argparse
import asyncio
import json
import logging
import logging.config
import os
import time
import typing
from datetime import datetime
from pathlib import Path

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from paho.mqtt import client as mqtt

from melcloudmqtt import config as app
from melcloudmqtt.client import Client as MCClient
from melcloudmqtt.client import ClientLogin
from melcloudmqtt.device import Device

_log = logging.getLogger(__name__)


class MELCloud2MQTT:
    def __init__(self):
        self._mc_client: MCClient = type(None)()
        self._mqtt_client: mqtt.Client = type(None)()
        self._scheduler: BackgroundScheduler = type(None)()

        self._devices: typing.List[Device] = []

    def create_clients(self) -> bool:
        try:
            self._mc_client = asyncio.get_event_loop().run_until_complete(ClientLogin.login())
            self._mqtt_client = mqtt.Client(
                client_id="hemon", reconnect_on_failure=True, clean_session=app.cfg.mqtt.client_clean_sessions()
            )
            self._mqtt_client.username_pw_set(app.cfg.mqtt.username, app.cfg.mqtt.password)
            self._mqtt_client.on_log = _on_mqtt_log
            self._mqtt_client.on_connect = _on_mqtt_connect
            self._mqtt_client.connect(host=app.cfg.mqtt.host, port=app.cfg.mqtt.port, keepalive=180)

            self._scheduler = BackgroundScheduler()
        except Exception as e:
            logging.error("Error at %s", "create_clients", exc_info=e)
            return False
        return True

    def _tick_read(self) -> None:
        _log.debug("running read tick")
        asyncio.new_event_loop().run_until_complete(self._mc_client.fetch_device_confs())

        # update devices
        for device_conf in self._mc_client.device_confs:
            device = next((x for x in self._devices if x.device_id == Device.get_device_id(device_conf)), None)
            if device:
                device.update(self._mc_client.device_confs)
            else:
                device = Device(device_conf)
                self._devices.append(device)

        # build and send MQTT message for each device having updated values
        for device in self._devices:
            values = device.values()
            if len(values):
                result = {"node": device.name, "time": datetime.utcnow().timestamp(), "values": values, "read_status": 0}
                self._mqtt_client.publish(
                    topic=app.cfg.mqtt.topic_prefix + "/" + str(device.device_id), payload=json.dumps(result)
                )

    def _tick_refresh(self) -> None:
        _log.debug("running refresh token tick")
        asyncio.new_event_loop().run_until_complete(ClientLogin.refresh(self._mc_client))

    def run(self) -> None:
        self._scheduler.add_job(self._tick_read, "interval", seconds=50)
        #self._scheduler.add_job(self._tick_refresh, "interval", seconds=30)
        self._scheduler.start()

        try:
            if app.cfg.loop_time < 0:
                self._mqtt_client.loop_forever()
            elif app.cfg.loop_time == 0:
                self._mqtt_client.loop()
            else:
                self._mqtt_client.loop_start()
                time.sleep(app.cfg.loop_time)
                self._mqtt_client.loop_stop()
        except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            self._scheduler.shutdown()
            self._mqtt_client.disconnect()


def _on_mqtt_connect(client: mqtt.Client, userdata: typing.Any, flags: typing.Dict, rc: int) -> None:
    _log.info("connected to MQTT broker with result code %s", str(rc))


def _on_mqtt_log(client: mqtt.Client, userdata: typing.Any, level: int, buf: object) -> None:
    _log.log(level, buf)


def main() -> None:
    """Run the module app."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=argparse.FileType("r"))
    args = parser.parse_args()

    if not args.config:
        path = Path(os.getcwd()) / "melcloudmqtt.cfg.yaml"
        if not path.exists():
            raise ValueError("Missing configuration")
        args.config = open(str(path), "r", encoding="utf-8")  # pylint: disable=R1732

    app.load_configuration(args.config)
    if not hasattr(app, "cfg"):
        return

    _setup_logging(app.cfg.logging_config)
    _log.info("successfully read configuration from: %s", args.config.name)
    _log.debug(app.cfg)

    runner = MELCloud2MQTT()
    if runner.create_clients():
        runner.run()


def _setup_logging(cfg_yaml: str | None = None) -> None:
    if cfg_yaml and len(cfg_yaml) > 0:
        c = yaml.safe_load(cfg_yaml)
        logging.config.dictConfig(c)
        _log.info("log level set to: %s", logging.getLevelName(logging.getLogger().level))
    else:
        log_level_str = "INFO"
        log_level = logging.getLevelName(log_level_str)
        logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s")
        logging.getLogger().setLevel(log_level)
        logging.info("log level set to: %s", log_level_str)


if __name__ == "__main__":
    main()
