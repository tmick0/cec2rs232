import argparse
import logging
import asyncio
import json
from .driver.registry import driver_registry
from .cec import cec_interface
from .mqtt import mqtt_interface

logger = logging.getLogger(__name__)


def init_logs(level="INFO"):
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARN,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    logging.basicConfig(level=levels[level])


class cec2rs232:

    def __init__(self, loop, driver, cec, mqtt):
        self._loop = loop
        self._driver = driver
        self._cec = cec
        self._mqtt = mqtt
        
    def run(self):
        tasks = []
        tasks.append(self._cec.init())
        if self._mqtt:
            tasks.append(self._loop.create_task(self._mqtt.run()))
        try:
            self._loop.run_forever()
        except Exception as e:
            logger.exception(e)
        self._loop.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file', default='/etc/cec2rs232/cec2rs232.json')
    args = parser.parse_args()

    with open(args.config_file, 'r') as fh:
        config = json.load(fh)
    
    init_logs(**config.get("logging", {}))
    
    loop = asyncio.new_event_loop()
    driver = driver_registry[config["device"]["driver"]](**config["device"]["parameters"])
    cec = cec_interface(driver, loop, **config.get("cec", {}))

    if "mqtt" in config:
        mqtt = mqtt_interface(driver, loop, **config["mqtt"])
    else:
        mqtt = None

    cec2rs232(loop, driver, cec, mqtt).run()
