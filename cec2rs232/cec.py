import logging
from pycec import cec, const, commands

logger = logging.getLogger(__name__)

SYSTEM_AUDIO_MODE_REQUEST = 0x70
SET_SYSTEM_AUDIO_MODE = 0x72

CMD_AUDIO_MODE_STATUS_REQ, CMD_AUDIO_MODE_STATUS_REP = const.CMD_AUDIO_MODE_STATUS
CMD_AUDIO_STATUS_REQ, CMD_AUDIO_STATUS_REP = const.CMD_AUDIO_STATUS
CMD_POWER_STATUS_REQ, CMD_POWER_STATUS_REP = const.CMD_POWER_STATUS
CMD_PHY_ADDR_REQ, CMD_PHY_ADDR_REP = const.CMD_PHYSICAL_ADDRESS

KEYS_ACTIONS = {
    const.KEY_VOLUME_DOWN: "volume_down",
    const.KEY_VOLUME_UP: "volume_up",
    const.KEY_MUTE_TOGGLE: "toggle_mute",
    const.KEY_MUTE_ON: "mute_on",
    const.KEY_MUTE_OFF: "mute_off",
}


class cec_interface (object):

    def __init__(self, driver, loop, echo_device_keypress=False, ignore_device_keypress=False):
        self._driver = driver
        self._adapter = cec.CecAdapter(driver.get_name(), device_type=const.TYPE_AUDIO, activate_source=False)
        self._adapter.set_event_loop(loop)
        self._adapter.set_command_callback(self._handle_command)
        self._address = None
        self._echo_device_keypress = echo_device_keypress
        self._ignore_device_keypress = ignore_device_keypress
    
    def init(self):
        return self._adapter.init(self._init_callback)

    def _init_callback(self, *args, **kwargs):
        self._address = self._adapter.get_logical_address()
        logger.info("ready")
    
    def _is_recognized_keypress(self, att):
        return att in KEYS_ACTIONS

    def _handle_keypress(self, att):
        if self._is_recognized_keypress(att):
            getattr(self._driver, KEYS_ACTIONS[att])()
        else:
            logger.debug("unhandled keypress: {att}")

    def _handle_command(self, raw):
        try:
            cmd = commands.CecCommand(raw[3:])
            if cmd.src == const.ADDR_TV:
                if cmd.dst in (self._address, const.ADDR_BROADCAST):
                    if cmd.cmd == const.CMD_KEY_PRESS:
                        self._handle_keypress(cmd.att[0])
                    elif cmd.cmd == CMD_POWER_STATUS_REQ:
                        logger.info('cmd_power_status')
                        power = self._driver.get_power_status()
                        reply = commands.CecCommand(CMD_POWER_STATUS_REP, cmd.src, self._address, [0 if power else 1])
                        self._adapter.transmit(reply)
                    elif cmd.cmd == SYSTEM_AUDIO_MODE_REQUEST:
                        logger.info(f'system_audio_mode_request: {cmd.att}')
                        reply = commands.CecCommand(SET_SYSTEM_AUDIO_MODE, cmd.src, self._address, [1])
                        self._adapter.transmit(reply)
                        self._driver.power_on()
                    elif cmd.cmd == CMD_AUDIO_MODE_STATUS_REQ:
                        logger.info('cmd_audio_mode_status')
                        reply = commands.CecCommand(CMD_AUDIO_MODE_STATUS_REP, cmd.src, self._address, [1])
                        self._adapter.transmit(reply)
                    elif cmd.cmd == CMD_AUDIO_STATUS_REQ:
                        logger.info('cmd_audio_status')
                        mute, volume = self._driver.get_audio_status()
                        reply = commands.CecCommand(CMD_AUDIO_STATUS_REP, cmd.src, self._address, [(mute << 7 | volume)])
                        self._adapter.transmit(reply)
                    elif cmd.cmd == const.CMD_STANDBY:
                        logger.info('cmd_standby')
                        self._driver.power_off()
                    else:
                        logger.debug(f"unhandled command: {raw} - 0x{cmd.cmd:02x} att: {cmd.att}")
            elif cmd.src in (const.ADDR_PLAYBACKDEVICE1, const.ADDR_PLAYBACKDEVICE2, const.ADDR_PLAYBACKDEVICE3):
                if cmd.dst in (self._address, const.ADDR_BROADCAST):
                    if cmd.cmd == const.CMD_KEY_PRESS and self._is_recognized_keypress(cmd.att[0]):
                        if not self._ignore_device_keypress:
                            self._handle_keypress(cmd.att[0])
                        if self._echo_device_keypress:
                            reply = commands.CecCommand(const.CMD_KEY_PRESS, const.ADDR_TV, self._address, [cmd.att[0]])
                            self._adapter.transmit(reply)
        except Exception as e:
            logger.error("error in handle_command:")
            logger.exception(e)
