import sys
import time
import ptypy
from ptypy import utils as u

from contrast.environment import macro, env
from contrast.recorders import active_recorders, RecorderHeader, RecorderFooter


@macro
class Dummy_Ptycho(object):
    """
    Dummy macro which produces data from ptypy's MoonFlowerScan.

    Does not use actual detectors or motors, but puts data in all active
    recorders.
    """

    def __init__(self):
        """
        The constructor should parse parameters.
        """

        self.scannr = env.nextScanID
        env.nextScanID += 1

        # for verbose output
        u.verbose.set_level(1)

        # create data parameter branch
        data = u.Param()
        data.shape = 256
        data.num_frames = 400
        data.density = .1
        data.min_frames = 1
        data.label = None
        data.psize = 172e-6
        data.energy = 6.2
        data.center = 'fftshift'
        data.distance = 7
        data.auto_center = None
        data.orientation = None

        # create PtyScan instance
        self.MF = ptypy.core.data.MoonFlowerScan(data)
        self.MF.initialize()

    def run(self):
        """
        This method does all the serious interaction with motors,
        detectors, and data recorders.
        """
        print('\nScan #%d starting at %s\n' % (self.scannr, time.asctime()))
        print('#     x          y          data')
        print('-----------------------------------------------')

        # send a header to the recorders
        snap = env.snapshot.capture()
        for r in active_recorders():
            r.queue.put(
                RecorderHeader(
                    scannr=self.scannr, path=env.paths.directory,
                    snapshot=snap, description=self._command
                )
            )

        try:
            n = 0
            while True:
                # generate the next position
                msg = self.MF.auto(1)
                if msg == self.MF.EOS:
                    break
                d = msg['iterable'][0]
                dct = {'x': d['position'][0],
                       'y': d['position'][1],
                       'diff': d['data']}

                # pass data to recorders
                for r in active_recorders():
                    r.queue.put(dct)

                # print spec-style info
                print('%-6u%-10.4f%-10.4f%10s'
                      % (n, dct['x'] * 1e6, dct['y'] * 1e6, dct['diff'].shape))
                n += 1
                time.sleep(.2)

        except KeyboardInterrupt:
            print('\nScan #%d cancelled at %s' % (self.scannr, time.asctime()))

        # tell the recorders that the scan is over
        for r in active_recorders():
            r.queue.put(RecorderFooter())
