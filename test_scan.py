from contrast.environment import runCommand
import time
import numpy as np
# =========================================================================

# energy interval with start, stop and number of points

# energies = np.linspace(920, 940, 40)

# =========================================================================

# energy interval with start, stop and step

# energies = np.arange(920, 930.5, 0.5)
# here, if you want the stop to be 930, make sure to add
# another step (i.e. 930.5)

# =========================================================================

# energy list with an offset
energies = [926.0, 928.0, 932.0, 933.3, 937.1, 940.8]

offset = 0.4 # uncomment this if you want an offset

for i in range(len(energies)):
    energies[i] += offset

# ==========energy stack===================================================
'''
energy_1 = np.arange(925, 929.8, 0.8)  # add an extra step at the stop point
energy_2 = np.arange(929.4, 935.3, 0.3)  # to make the list 'inclusive'
energy_3 = np.arange(935.4, 945.8, 0.8)

energies = [*energy_1, *energy_2, *energy_3]
'''
'''
offset = 0.4  # uncomment this if you want an offset

for i in range(len(energies)):
    energies[i] += offset
'''

# ========scan definition=============

scan = 'mesh finex -1 1 20 finey -1 1 20 0.02 jitter=0.01 ptycho=True'

# =======================================


for val in energies:
    try:
        print('mv beamline_energy', val)
        runCommand('mv beamline_energy '+str(val))  # changes beamline energy

        # zp.Defocus = 50.0 # changes Defocus

        print("mv zp_E too...")
        runCommand('mv zp_E_mot '+str(val))  # changes ZP energy

        runCommand(scan)  # run the scan

        print(f"runCommand({scan})")
        time.sleep(3)       
    
    except:
        print("Some error... Closing the shutter.")
        shutter0.Close()

