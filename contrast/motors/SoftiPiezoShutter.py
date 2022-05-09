from ..Gadget import Gadget
import PyTango

import time
from contrast.environment import runCommand, macro
# from contrast.scans import Mesh
# from contrast.environment import env


class SoftiPiezoShutter(Gadget):

    def __init__(self, device, **kwargs):
        super(SoftiPiezoShutter, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)

    def Open(self):
        self.proxy.Open()

    def Close(self):
        self.proxy.Close()


class SoftiPolarizationCtrl(Gadget):

    def __init__(self, device, **kwargs):
        super(SoftiPolarizationCtrl, self).__init__(**kwargs)
        self.proxy = PyTango.DeviceProxy(device)
        self.proxy.set_source(PyTango.DevSource.DEV)

    def set_polarization(self, val):
        self.proxy.polarizationmode = val

    def get_polarization(self):
        return self.proxy.polarizationmode


@macro
class night_scan(object):
    """ Does execution of a list of commands/macros
    """
    def __init__(self, shutter, pol_ctrl):
        self.lst = ["wa", ]
        self.shutter = shutter
        self.pol_ctrl = pol_ctrl

    def run(self):
        try:
            # print("Opening shutter...")
            # self.shutter.Open()
            # time.sleep(5)
            # print('Polarization is: ', self.pol_ctrl.polarization)

            # runCommand(i)

            # print("Closing shutter...")
            # self.shutter.Close()
            # time.sleep(5)

            # self.shutter.open()
            # self.pol_ctrl.polarizationmode = 'circularnegative'
            # runCommand('mv beamline_energy 776.2')
            # runCommand('mv zp_E_mot 776.2')
            # runCommand('mesh finex -2 -1.25 75 finey 1.75 2.25 50 0.02')
            # self.shutter.close()
            # self.pol_ctrl.polarizationmode = 'circularpositive'
            # runCommand('mv beamline_energy 776.2')
            # runCommand('mv zp_E_mot 776.2')
            # runCommand('mesh finex -2 -1.25 75 finey 1.75 2.25 50 0.02')
            # self.shutter.close()

            # self.shutter.Open()
            # =============== start 2 h roughly ==================
            #self.pol_ctrl.set_polarization('circularnegative')
            #print('self.pol_ctrl.polarizationmode', self.pol_ctrl.get_polarization())
            #runCommand('mv beamline_energy 776.2')
            # print('mv beamline_energy 776.0')
            # self.shutter.Close()

            runCommand('mesh finex 8.5 10 100 finey -0.8 -0.2 40 0.02')
            runCommand('mesh finex 8.5 10 100 finey -1.4 -0.8 40 0.02')

            self.pol_ctrl.set_polarization('circularpositive')
            print('self.pol_ctrl.polarizationmode', self.pol_ctrl.get_polarization())
            runCommand('mv beamline_energy 776.2')
            # print('mv zp_E_mot 776.0')
            # self.shutter.Close()

            runCommand('mesh finex 8.5 10 100 finey -0.8 -0.2 40 0.02')
            runCommand('mesh finex 8.5 10 100 finey -1.4 -0.8 40 0.02')

            

        except BaseException as e:
            print(e)
            print("Error, we have! Closing shutter...")
            self.shutter.Close()

            # print("This is the end of the script! Making sure the shutter is closed...")
            # shutter0.Close()
