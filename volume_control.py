import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class VolumeController:
    def __init__(self):
        self.devices = AudioUtilities.GetSpeakers()
        # In newer versions of pycaw/windows, .Activate is on the underlying _dev object
        if hasattr(self.devices, 'Activate'):
            self.interface = self.devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        else:
            self.interface = self.devices._dev.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            
        self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
        self.vol_range = self.volume.GetVolumeRange()  # (-96.0, 0.0, 0.03125)
        self.min_vol = self.vol_range[0]
        self.max_vol = self.vol_range[1]

    def set_volume_by_percentage(self, percentage):
        """
        Sets volume from 0 to 100.
        """
        # Map percentage (0-100) to range (min_vol - max_vol)
        vol = np.interp(percentage, [0, 100], [self.min_vol, self.max_vol])
        self.volume.SetMasterVolumeLevel(vol, None)

    def get_current_volume_percentage(self):
        """
        Returns master volume as a percentage (0-100).
        """
        current_vol = self.volume.GetMasterVolumeLevel()
        return np.interp(current_vol, [self.min_vol, self.max_vol], [0, 100])

    def change_volume(self, delta):
        """
        Delta is positive or negative percentage point change.
        """
        current = self.get_current_volume_percentage()
        new_vol = np.clip(current + delta, 0, 100)
        self.set_volume_by_percentage(new_vol)
