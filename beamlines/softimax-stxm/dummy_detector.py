"""
This module contains code for generating fake STXM data from a stock
photo.
"""


from contrast.detectors import DummyDetector
import numpy as np
from scipy.misc import face


im = (1 - face() / 255) / 3  # absorption channels
im = np.flip(im, axis=0)


def get_stxm_signal(i, j, energy=None):
    """
    Returns the STXM signal from a stock photo at pixel (i, j). The
    energy can be used to generate a fake absorption edge at 700.
    """
    i = int(round(i))
    j = int(round(j))
    pix = 1 - np.sum(im[i, j, 0] + im[i, j, 2])  # red, blue
    if energy and (energy >= 700):
        pix -= im[i, j, 1]  # green
    return pix


class DummyStxmDetector(DummyDetector):
    """
    Mock STXM scanner which respects coarse and fine motors plus energy.
    There is an absorption edge around 700 eV.
    """
    def __init__(self, motors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.motors = motors

    def start(self):
        super().start()

    def read(self):
        fx, fy, cx, cy, en = self.motors  # fine, coarse, energy
        val = get_stxm_signal(cx.dial_position + fx.dial_position,
                              cx.dial_position + fx.dial_position,
                              en.dial_position)
        return val
