"""
A collection of functions for colorful terminal output using ANSI escape codes
to be used for a homogeneous appearance thoughout the rest of the code.
"""

def make_color_code(style='none', text_color='black', background_color='white'):
    dict_style = {'none':'0', 'bold':'1', 'underline':'2', 'negative1':'3', 'negative2':'5'}
    dict_c = {'black':'30',  'k':'30', 
              'red':'31',    'r':'31',
              'green':'32',  'g':'32',
              'yellow':'33', 'y':'33',
              'blue':'34',   'b':'34',
              'purple':'35', 'm':'35',
              'cyan':'36',   'c':'36',
              'gray':'37',   'gr':'37',
              'orange':'D0', 'o':'D0',
              'white':'38',  'w':'38'} 
    return f'\033[{dict_style[style]};{dict_c[text_color]};4{dict_c[background_color][1]}m'

def str_scannumber(scan_number):
    """
    color highlighting of the scan #XYZ number with an orange background
    """
    string = '\033[48;5;172m' + f'#{scan_number}' + '\033[0m'
    return string


def str_position(string):
    """
    color highlighting of printed positions with a green background
    taking an already formatted strings.
    """
    string = '\033[48;5;82m' + string + '\033[0m'
    return string

def str_path(string):
    """
    color highlighting of printed path with a turquoise background
    taking an already formatted strings.
    """
    string = '\033[48;5;87m' + string + '\033[0m'
    return string

