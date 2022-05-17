from contrast.environment import MacroSyntaxError, env, macro, register_shortcut, runCommand
import requests
import time
import random


@macro
class Oamlight(object):
    """
    Macro for the control of the LED ring on the On-axis microscope.

    oamlight <on|off|disco>   Set all LEDs of the ring on, off, or to party mode
    oamlight <value>    Set the brightness of all LEDs, <value> is in percent [0-100]
    oamlight <left|top|right> <on|off>  Set the predefined LED group on or off
    oamlight <left|top|right> <value>   Set the brighntess of the predefined LED group to <value> (in percent [0-100])
    oamlight                            Show the current brighness settings for all LEDs
    
    Examples:
      oamlight off
          Switch all LEDs off
          
      oamlight top on left 70
          Set the LEDs in the top group on and the LEDs in the left goup to 70% brightness
          
      oamlight [1,2,3,4,5] 30 [6,7,8,9] off
          Set LEDs 1,2,3,4,5 to 30% brightness and switch LEDs 6,7,8,9 off
    """
    host = 'b-nanomax-ledcontrol-0.maxiv.lu.se'
    port = 8000
    # led number on illumination ring, starts at 1
    led_groups = {'all': [1,2,3,4,5,6,7,8,9],
                  'right': [1,2,3],
                  'top': [4,5,6],
                  'left': [7,8,9]}
    MAXBRIGHTNESS = 3800 # can be upto 4095, but this may burn out the LEDs too fast

    def __init__(self, *args):
        self.args = args
        self.session = requests.Session()
        self.session.trust_env = False

    def run(self):
        if len(self.args) == 0:
            self.show_led_status()
        # if only one argument is given, set the brighness of the leds in the 'all' led group
        elif len(self.args) == 1:
            if self.args[0] == 'disco':
                self.disco()
            else:
                group = 'all'
                brightness = self.to_raw(self.args[0])
                print(brightness, type(brightness))
                self.set_group(self.led_groups[group], brightness)
        # if an even number of arguments is given, it must be a pair of a LED group and brightness or a list of LEDs and brightness
        elif len(self.args)%2 == 0:
            for i in range(0, len(self.args), 2):
                # we can act on a list of LEDs
                if isinstance(self.args[i], list):
                    brightness = self.to_raw(self.args[i+1])
                    self.set_group(self.args[i], brightness)
                # or we act on a pre-definded led group
                elif self.args[i] in self.led_groups.keys():
                    group = self.args[i]
                    brightness = self.to_raw(self.args[i+1])
                    self.set_group(self.led_groups[group], brightness)
                else:
                    print(f"{self.args[i]} is not a valid LED identifier.")
        else:
            raise MacroSyntaxError("Wrong number of arguments")

    def show_led_status(self):
        # get raw data from the led controller
        led_status = self.get_leds()
        print(" LED  Brightness")
        i = 0
        for id,val in led_status.items():
            print(f"{int(id)+1:3d} {self.to_percent(val):8.1f}")
            i=i+1
            if i >= len(self.led_groups['all']):
                break           

    def to_raw(self, value):
        if value == 'on':
            brightness = self.MAXBRIGHTNESS
        elif value == 'off':
            brightness = 0
        elif isinstance(value, int) or isinstance(value, float):
            if 0<=value<=100:
                brightness = int(self.MAXBRIGHTNESS*value/100)
            else:
                raise ValueError(f'Brightness value must be between 0 and 100, not {value}.')
        else:
            raise ValueError(f"Wrong brightness value: {value}. Must be between 0 and 100.")
        
        return brightness
        
    def to_percent(self, value):
        return value/self.MAXBRIGHTNESS * 100
                    
    def set_group(self, group, brightness):
        payload = {}
        for led_chan in group:
            # led_chan is shifted by -1. The LED board starts counting at 0, but the LEDs on the LED-Ring start at 1
            payload[led_chan-1] = brightness
            
        self.set_leds(payload)

    def set_leds(self, payload:dict):
        key = "led"
        url = f'http://{self.host}:{self.port}/{key}'
        response = self.session.put(url,json=payload)

    def get_leds(self):
        key = "led"
        url = f'http://{self.host}:{self.port}/{key}'
        response = self.session.get(url)
        return response.json()

    def disco(self):
        try:
            while True:
                i0, i1 = random.sample(self.led_groups['all'], 2)
                self.set_group([i0], self.MAXBRIGHTNESS)
                self.set_group([i1], self.MAXBRIGHTNESS)
                time.sleep(.1)
                self.set_group([i0], 0)
                self.set_group([i1], 0)
        except KeyboardInterrupt:
            b = self.to_raw(30)
            self.set_group(self.led_groups['all'], b)
            print('party over!')

