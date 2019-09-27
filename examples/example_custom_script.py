"""
Shows an example of how python and macro syntax can be mixed when
writing custom scripts. Note that this is not a new macro, it's just a
simple script.

Execute this script with
%run example_custom_script.py

"""

from contrast.environment import runCommand

for i in range(5):
    new_y_pos = i * 1.5 + 2
    print('moving samy to %f' % new_y_pos)
    runCommand('mv samy %d' % new_y_pos)
    runCommand('ascan samx 0 1 5 .1')
