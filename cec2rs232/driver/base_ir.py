import lirc
from .base import AbstractDevice


class IrDeviceMixin (object):

    def ir_init(self, device):
        self._device = device
        self._ir = lirc.Client()

    def ir_send(self, command):
        self._ir.send_once(self._device, command)


class AbstractIrDevice (IrDeviceMixin, AbstractDevice):
    def __init__(self, device, **kwargs):
        super().__init__(device)
