import argparse
import logging
import asyncio
import time
import socket
from pycec import cec, const, commands
from .driver.cambridge_cxa61 import cambridge_cxa61

logging.basicConfig(level=logging.INFO)

SYSTEM_AUDIO_MODE_REQUEST = 0x70
SET_SYSTEM_AUDIO_MODE = 0x72

CMD_AUDIO_MODE_STATUS_REQ, CMD_AUDIO_MODE_STATUS_REP = const.CMD_AUDIO_MODE_STATUS

class cec2rs232:

    def __init__(self, driver):
        self._loop = asyncio.new_event_loop()
        self._driver = driver
        self._adapter = cec.CecAdapter(driver.get_name(), device_type=const.TYPE_AUDIO, activate_source=False)
        self._adapter.set_event_loop(self._loop)
        self._adapter.set_command_callback(self._handle_command)
        self._address = None
        self._power = False
        
    def _init_callback(self, *args, **kwargs):
        self._address = self._adapter.get_logical_address()
        logging.info("ready")

    def _handle_keypress(self, att):
        if att == const.KEY_VOLUME_DOWN:
            self._driver.volume_down()
        elif att == const.KEY_VOLUME_UP:
            self._driver.volume_up()
        elif att == const.KEY_MUTE_TOGGLE:
            self._driver.toggle_mute()
        elif att == const.KEY_MUTE_ON:
            self._driver.mute_on()
        elif att == const.KEY_MUTE_OFF:
            self._driver.mute_off()
        else:
            logging.debug("unhandled keypress: {att}")

    def _handle_command(self, raw):
        cmd = commands.CecCommand(raw[3:])
        if cmd.src == const.ADDR_TV:
            if cmd.dst in (self._address, const.ADDR_BROADCAST):
                if cmd.cmd == const.CMD_KEY_PRESS:
                    self._handle_keypress(cmd.att[0])
                elif cmd.cmd == const.CMD_POWER_STATUS[0]:
                    power = self._driver.get_power_status()
                    reply = commands.CecCommand(const.CMD_POWER_STATUS[1], cmd.src, self._address, [0 if power else 1])
                    self._adapter.transmit(reply)
                elif cmd.cmd == SYSTEM_AUDIO_MODE_REQUEST:
                    self._driver.power_on()
                    reply = commands.CecCommand(SET_SYSTEM_AUDIO_MODE, cmd.src, self._address, [1])
                    self._adapter.transmit(reply)
                elif cmd.cmd == const.CMD_AUDIO_MODE_STATUS[0]:
                    reply = commands.CecCommand(const.CMD_AUDIO_MODE_STATUS[1], cmd.src, self._address, [1])
                    self._adapter.transmit(reply)
                elif cmd.cmd == const.CMD_AUDIO_STATUS[0]:
                    mute, volume = self._driver.get_audio_status()
                    reply = commands.CecCommand(const.CMD_AUDIO_STATUS[1], cmd.src, self._address, [(mute << 7 | volume)])
                    self._adapter.transmit(reply)
                elif cmd.cmd == const.CMD_STANDBY:
                    self._driver.power_off()
                else:
                    logging.debug(f"unhandled command: {raw} - 0x{cmd.cmd:02x} att: {cmd.att}")
    
    def run(self):
        task = self._adapter.init(self._init_callback)
        try:
            self._loop.run_forever()
        except Exception as e:
            logging.exception(e)
        self._loop.close()

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    driver = cambridge_cxa61("/dev/ttyUSB0", 4)
    cec2rs232(driver).run()
