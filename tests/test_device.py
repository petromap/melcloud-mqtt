# -*- coding: utf-8 -*-
import json
import os

from pathlib import Path

from melcloudmqtt.config import load_configuration
from melcloudmqtt.device import Device

fixture_data_dir = Path(os.path.dirname(os.path.realpath(__file__))).parent / "tests" / "data"


class TestDeviceProperties:
    def test_device_update(self):
        cfg_file = "property_values.cfg.yaml"
        load_configuration(open(str(fixture_data_dir / cfg_file)))  # noqa

        with open(str(fixture_data_dir / "device_conf.json")) as file:
            conf_data = file.read()

        devices = []
        for device_conf in json.loads(conf_data):
            devices.append(Device(device_conf))

        assert devices[0].serial == "2234412110"

        old_serial = devices[0].serial
        alt_conf = devices[0]._device_conf
        alt_conf["SerialNumber"] = old_serial + "__xyz"
        assert devices[0].update([alt_conf])

        # 'serial' should not be touched (and SerialNumber should not change IRL)
        assert devices[0].serial == "2234412110"
        assert devices[0]._device_conf["SerialNumber"] == "2234412110__xyz"

        # now, the case device id doesn't match
        alt_conf["DeviceID"] = "abc"
        assert not devices[0].update([alt_conf])

    def test_collect_device_property_values(self):
        cfg_file = "property_values.cfg.yaml"
        load_configuration(open(str(fixture_data_dir / cfg_file)))  # noqa

        with open(str(fixture_data_dir / "device_conf.json")) as file:
            conf_data = file.read()

        expected_values = {"T-out": 6.0, "opmode": 5}

        # initial state when state is not read/received yet
        assert Device({}).values() == {}

        # initial state when state is already read/received
        devices = []
        device_confs = json.loads(conf_data)
        for device_conf in device_confs:
            device = Device(device_conf)
            devices.append(device)
            assert device.values() == expected_values

        # update with equal properties, no updated values
        devices[0].update(device_confs)
        assert devices[0].values() == {}
