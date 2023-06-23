import argparse
import logging
import asyncio
import json
from .driver.registry import driver_registry
from .cec import cec_interface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class cec2rs232:

    def __init__(self, driver):
        self._loop = asyncio.new_event_loop()
        self._driver = driver
        self._interface = cec_interface(driver, self._loop)
        
    def run(self):
        task = self._interface.init()
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
    
    driver = driver_registry[config["device"]["driver"]](**config["device"]["parameters"])
    cec2rs232(driver).run()
