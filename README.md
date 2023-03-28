# melcloud-mqtt
MELCloud device reader and MQTT publisher.

This will periodically read properties, current state, of all devices from 
MELCloud. 
Then single MQTT message per device will be build and published with values 
of all properties listed in configuration.
Message format is fit to be handled by 
[this software](https://github.com/petromap/mqlcloud-mqtt).

## Install and run the package

Installing melcloudmqtt-mqtt package requires couple easy steps:
 * [Create virtual environment](https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-and-using-virtual-environments) 
for the software.
 * Download release and install the package into this virtual environment:
   * ```venv/bin/python3.11 -m pip install melcloudmqtt-*.whl```
 * Create a YAML configuration file, see [example](melcloudmqtt.cfg.example.yaml)
   * When running the program refer to that configuration file with program argument ```--config <config file>```

To test configuration and whether MELCloud can be read successfully:
```bash
venv/bin/python3.11 -m melcloudmqtt.app --config <config file>
```

### Configuration
See example configuration and comments in 
[melcloudmqtt.cfg.example.yaml](melcloudmqtt.cfg.example.yaml).

### Running as service

The program can be run long time ("infinitely") by configuration but unless 
just testing the package one may want to create a service for it.

## Developer's quick start
```bash
git clone git@github.com:petromap/melcloud-mqtt.git
cd melcloud-mqtt
pip install .
pip install .[dev]
pip install .[tests]

pytest

# bake the wheel
python -m build
```
