##'/mxn/home/softimax-user/Documents/IB_Doc/contrast'

##%run ./beamlines/softimax/softimax_beamline.py
##import numpy as np
umv beamline_energy 1300
print('ok')
for i in arrange(10):
	if i < 10:
		try:
 			umv beamline_energy 1300
			mesh finex -3.5 2.5 20 finey -1.5 4.5 20 0.1
			print('1300 eV went well, next \n')
		except:
			print('1300 eV crashed, lunching next one ... \n')

		try:
			umv beamline_energy 1309.
			mesh finex -3.5 2.5 20 finey -1.5 4.5 20 0.1
			print('1309 eV went well, next \n')
		except:
			print('1309 eV crashed, lunching next one ... \n')

		try:
			umv beamline_energy 1311.
			mesh finex -3.5 2.5 20 finey -1.5 4.5 20 0.1
			print('1311 eV went well, next \n')
		except:
			print('1311 eV crashed, lunching next one ... \n')

		try:
			umv beamline_energy 1319.
			mesh finex -3.5 2.5 20 finey -1.5 4.5 20 0.1
			print('1319 eV went well, next \n')
		except:
			print('1319 eV crashed, checking how many times it has been... \n')	

		print(f'RESTARTING, ITERATION NB: {i} of 10')

print(' function is happy' )

