from .Detector import Detector
from ..Gadget import Gadget
import string

def get_dict_recursive(dct, key):
    """
    Helper function to get the value corresponding to path/to/key from a nested
    dict.
    """
    if '/' in key:
        base, newkey = key.split('/', maxsplit=1)
        return get_dict_recursive(dct[base], newkey)
    else:
        try:
            ret = dct[key]
        except KeyError:
            # int keys would have been converted to strings
            ret = dct[int(key)]
        return ret

class PseudoDetector(Detector):
    """
    Derived detector which transforms signals from other Detector objects.
    Defines a dict of variables corresponding to detector labels, and
    one or more expressions to apply to these.

    Variables can be of the form detector/sub/value, where "detector" is
    interpreted as the basic gadget, and "sub/value" are components keys
    into the value dictionary.

    If 'expressions' is a string, the detector will return a single value,
    if it's a dict, the detector will return a corresponding dict of
    results.

    Example::

        r = PseudoDetector(variables={'x':'npointbuff/x', 'y':npointbuff/y'},
                           expressions={'r':np.sqrt(x**2+y**2)'},
                           name='r'')
    """
    def __init__(self, variables, expression, *args, **kwargs):
        self.variables = variables
        self.expression = expression
        super().__init__(*args, **kwargs)

    def initialize(self):
        """
        find our gadgets so we don't have to search every time
        """
        labels = [s.split('/')[0] for s in self.variables.values()]
        self.gadgets = {}
        for g in Gadget.getinstances():
            if g.name in labels:
                self.gadgets[g.name] = g

        for lbl in labels:
            if not lbl in self.gadgets.keys():
                print('WARNING! PseudoDetector "%s" cant find its constituent "%s"'%(self.name, lbl))

    def stop(self):
        pass

    def busy(self):
        return False

    def read(self):
        gadget_data = {g.name:g.read() for g in self.gadgets.values()}
        variable_data = {}
        for key, path in self.variables.items():
            gadget_name = path.split('/')[0]
            if '/' in path:
                subpath = path.split('/', maxsplit=1)[1]
                dat = get_dict_recursive(gadget_data[gadget_name], subpath)
            else:
                dat = gadget_data[gadget_name]
            variable_data[key] = dat
        if type(self.expression) == dict:
            ret = {}
            for name, exp in self.expression.items():
                ret[name] = eval(exp, {}, variable_data)
        else:
            ret = eval(self.expression, {}, variable_data)
        return ret
