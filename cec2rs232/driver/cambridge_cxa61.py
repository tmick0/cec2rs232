import re
import serial
import logging
from .base_serial import SerialDeviceMixin
from .base_ir import IrDeviceMixin
from .base import AbstractDevice
from .registry import driver

logger = logging.getLogger(__name__)

# Serial protocol constants
# https://techsupport.cambridgeaudio.com/hc/en-us/article_attachments/360011247357/AP366462_CXA61_CXA81_Serial_Control_Protocol__1_.pdf

GROUP_ERROR = 0
GROUP_AMP_CMD = 1
GROUP_AMP_REP = 2
GROUP_SRC_CMD = 3
GROUP_SRC_REP = 4
GROUP_VER_CMD = 13
GROUP_VER_REP = 14

ERR_GROUP = 1
ERR_CMD = 2
ERR_DATA = 3
ERR_AVAIL = 4

SOURCE_A1 = "00"
SOURCE_A2 = "01"
SOURCE_A3 = "02"
SOURCE_A4 = "03"
SOURCE_D1 = "04"
SOURCE_D2 = "05"
SOURCE_D3 = "06"
SOURCE_MP3 = "10"
SOURCE_BT = "14"
SOURCE_USB = "16"
SOURCE_BAL = "20"

AMP_CMD_GET_PWR = 1
AMP_CMD_SET_PWR = 2
AMP_CMD_GET_MUT = 3
AMP_CMD_SET_MUT = 4
AMP_CMD_GET_VOL = 5
AMP_CMD_VOL_UP = 6
AMP_CMD_VOL_DN = 7

SRC_CMD_GET_SRC = 1
SRC_CMD_NEXT_SRC = 2
SRC_CMD_PREV_SRC = 3
SRC_CMD_SET_SRC = 4

SOURCE_MAP = {
    'A1': SOURCE_A1,
    'A2': SOURCE_A2,
    'A3': SOURCE_A3,
    'A4': SOURCE_A4,
    'A1 Balanced': SOURCE_BAL,
    'D1': SOURCE_D1,
    'D2': SOURCE_D2,
    'D3': SOURCE_D3,
    'MP3': SOURCE_MP3,
    'Bluetooth': SOURCE_BT,
    'USB': SOURCE_USB
}

# Serial message
class cambridge_cxa61_data (object):

    pattern = re.compile("#([0-9]{2}),([0-9]{2})(?:,([0-9]{1,2})?)\r")

    def __init__(self, group, number, data=None):
        self._group = group
        self._number = number
        self._data = data
    
    @classmethod
    def deserialize(cls, data):
        match = cls.pattern.fullmatch(data)
        if match is None:
            return None
        data = match.group(3)
        return cls(int(match.group(1)), int(match.group(2)), match.group(3))
    
    def serialize(self):
        res = f"#{self._group:02d},{self._number:02d}"
        if self._data is not None:
            res += f",{self._data:s}"
        res += "\r"
        return res.encode()
    
    @property
    def group(self):
        return self._group
    
    @property
    def number(self):
        return self._number

    @property
    def data(self):
        return self._data


# IR config
CXA61_IR_CONFIG = {
  "formats": [
    {
      "preamble": [1],
      "coding": "manchester",
      "zero": [1, 0],
      "one": [0, 1],
      "msb_first": True,
      "bits": 13,
      "timebase": 890,
      "gap": 89000,
      "carrier": 38000
    },
    {
      "coding": "ppm",
      "zero": [1, 1],
      "one": [2, 1],
      "bits": 7,
      "postamble": [1, 2, 2, 1, 1, 1, 1, 1, 1],
      "timebase": 890,
      "carrier": 38000
    }
  ],
  "keys": {
    "power": "B2 78",
    "volume_up": {
      "format": 1,
      "data": "08"
    },
    "volume_down": "A0 88",
    "mute": "A0 68",
    "d2": "61 50"
  }
}


@driver("cambridge_cxa61")
class cambridge_cxa61 (AbstractDevice, SerialDeviceMixin, IrDeviceMixin):

    def __init__(self, serial_port, ir_gpio_pin, tv_source=None):
        self.serial_init(serial_port,
                         baudrate=9600,
                         bytesize=serial.EIGHTBITS,
                         parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE)
        self.ir_init(CXA61_IR_CONFIG, ir_gpio_pin)
        self.tv_source = tv_source
        self.power_status = None

    def get_name(self):
        return "CXA61/81"

    def volume_up(self):
        self._clear()
        if not self.get_power_status(True):
            self.power_on()
        self.ir_send("volume_up")

    def volume_down(self):
        self._clear()
        if not self.get_power_status(True):
            self.power_on()
        self.ir_send("volume_down")

    def mute_on(self):
        self._clear()
        if not self.get_power_status(True):
            self.power_on()
        self._clear()
        self.serial_send(cambridge_cxa61_data(GROUP_AMP_CMD, AMP_CMD_SET_MUT, "1").serialize())
        self._read_message()

    def mute_off(self):
        self._clear()
        if not self.get_power_status(True):
            self.power_on()
        self._clear()
        self.serial_send(cambridge_cxa61_data(GROUP_AMP_CMD, AMP_CMD_SET_MUT, "0").serialize())
        self._read_message()

    def power_on(self):
        self._clear()
        self.serial_send(cambridge_cxa61_data(GROUP_AMP_CMD, AMP_CMD_SET_PWR, "1").serialize())
        while not self.get_power_status():
            pass
        if self.tv_source is not None:
            self.serial_send(cambridge_cxa61_data(GROUP_SRC_CMD, SRC_CMD_SET_SRC, SOURCE_MAP[self.tv_source]).serialize())
            self._read_message()

    def power_off(self):
        self._clear()
        self.serial_send(cambridge_cxa61_data(GROUP_AMP_CMD, AMP_CMD_SET_PWR, "0").serialize())
        self._read_message()
        self.power_status = False
    
    def get_audio_status(self):
        self._clear()
        if not self.get_power_status(True):
            self.power_on()
        self._clear()
        self.serial_send(cambridge_cxa61_data(GROUP_AMP_CMD, AMP_CMD_GET_MUT).serialize())
        reply = self._read_message()
        if reply is None or reply.group != GROUP_AMP_REP or reply.number != AMP_CMD_GET_MUT:
            return False, 64
        return (reply.data == "1"), 64
    
    def get_power_status(self, use_cache=False):
        if use_cache and self.power_status is not None:
            return self.power_status
        self._clear()
        self.serial_send(cambridge_cxa61_data(GROUP_AMP_CMD, AMP_CMD_GET_PWR).serialize())
        reply = self._read_message()
        if reply is None or reply.group != GROUP_AMP_REP or reply.number != AMP_CMD_GET_PWR:
            return False
        self.power_status = reply.data == "1"
        return self.power_status

    def _read_message(self):
        char = None
        while char != b'#':
            char = self.serial_recv(size=1)
        buffer = char
        while char != b'\r':
            char = self.serial_recv(size=1)
            buffer += char
        return cambridge_cxa61_data.deserialize(buffer.decode())
    
    def _process_background_message(self, message):
        if message.group == GROUP_AMP_REP and message.number == AMP_CMD_GET_PWR:
            logger.info(f"power status changed: {message.data}")
            self.power_status = message.data == "1"

    def _clear(self):
        while self._serial.in_waiting:
            self._process_background_message(self._read_message())
