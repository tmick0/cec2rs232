
class AbstractDevice (object):

    def get_name(self):
        raise NotImplementedError()

    def volume_up(self):
        raise NotImplementedError()

    def volume_down(self):
        raise NotImplementedError()

    def mute_on(self):
        raise NotImplementedError()

    def mute_off(self):
        raise NotImplementedError()

    def power_on(self):
        raise NotImplementedError()
        
    def power_off(self):
        raise NotImplementedError()
    
    def get_audio_status(self):
        raise NotImplementedError()
    
    def get_power_status(self):
        raise NotImplementedError()
    
    def toggle_mute(self):
        muted, _ = self.get_audio_status()
        if muted:
            self.mute_off()
        else:
            self.mute_on()
