for val in np.arange(-471.8, -467.8,0.2):
	zp.zp_a0 = val;
	contrast.enviromen.runCommand('spiralscan finex finey 0.01 2 1');
	time.sleep(3)
	print('Scan finished, going to the next one')
	print('\n')

  GNU nano 2.3.1                                     New Buffer                                                                      Modified  

for val in np.arange(-1.5, 1.5, 0.1):
        zp.defocus = val;
	print('defoucs is' + str(val))
        contrast.environment.runCommand('loopscan 10 1');
        time.sleep(1)
        print('Scan finished, going to the next one')
        print('\n')





import time 

def beep():
	for i in range(6):
		print("\a")
		time.sleep(1)

beep()


def Trouble():
        for i in range(30):
                print("\a")
                time.sleep(0.3)


Trouble()

diffX = 0.0

diffY = 0.0

Xpos_i 
Xpos_f

Ypos_i 
Ypos_f

Xpos_i = 4.511
Xpos_f = Xpos_i +0.4

Ypos_i = 0.140
Ypos_f = Ypos_i + 0.4


Xpos_i += diffX
Xpos_f += diffX

Ypos_i += diffY
Ypos_f += diffY


mesh finex Xpos_i Xpos_f 10 finey Ypos_i Ypos_f 10 0.02

wm finex
umvr finex -0.4
wm finex

wm finey



contrast.environment.runCommand('umvr finex -0.4')

contrast.environment.runCommand('umvr finey -0.4')


print('mesh finex %s %s 10 finey %s %s 10 0.02'%(Xpos_i,Xpos_f,Ypos_i,Ypos_f))

contrast.environment.runCommand('mesh finex %s %s 10 finey %s %s 10 0.02'%(Xpos_i,Xpos_f,Ypos_i,Ypos_f))
beep()

### the above works fine


try :
	contrast.environment.runCommand('mesh finex %s %s 10 finey %s %s 10 0.02'%(Xpos_i,Xpos_f,Ypos_i,Ypos_f))
except:
	Trouble()
beep()

