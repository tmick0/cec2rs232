import piir
from .base import AbstractDevice


class IrDeviceMixin (object):
    def ir_init(self, config, gpio_pin):
        self._ir = piir.Remote(config, gpio_pin)

    def ir_send(self, command):
        res = self._ir.send(command)


class AbstractIrDevice (IrDeviceMixin, AbstractDevice):
    def __init__(self, config, gpio_pin):
        super().__init__(config, gpio_pin)
