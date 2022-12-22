import serial
from .base import AbstractDevice


class SerialDeviceMixin (object):

    def serial_init(self, device, **kwargs):
        self._serial = serial.Serial(device, **kwargs)

    def serial_send(self, data):
        self._serial.write(data)
    
    def serial_recv(self, size=1):
        self._serial.read(size)


class AbstractSerialDevice (SerialDeviceMixin, AbstractDevice):
    def __init__(self, device, **kwargs):
        super().__init__(device, **kwargs)
