from .Gadget import Gadget

def dict_to_table(dct, titles=('col1', 'col2'), margin=3):
    """
    Formats a dict where key:val is str:str into a two column table.
    """
    col1width = max([len(str(s)) for s in dct.keys()] + [len(titles[0])])
    col2width = max([len(str(s)) for s in dct.values()] + [len(titles[1])])
    width = col1width + col2width + margin
    baseline = ('%%-%ds' % col1width) + ' ' * margin + ('%%-%ds' % col2width)
    output = '\n' + baseline % titles + '\n' + '-' * width
    for key, val in dct.items():
        output += '\n' + (baseline % (key, val))
    return output

def str_to_args(line):
    """
    Handy function which splits a list of arguments, translates
    names of Gadget instances to actual objects, and evaluates
    other expressions. For example,

    In [11]: str_to_args("samx 'hej' 1./20")
    Out[11]: [<lib.motors.Motor.DummyMotor at 0x7f6b11b0ba90>, 'hej', 0.05]

    """
    args = line.split()
    gadget_lookup = {g.name: g for g in Gadget.getinstances()}
    for i, a in enumerate(args):
        if a in gadget_lookup.keys():
            args[i] = gadget_lookup[a]
        else:
            args[i] = eval(a)
    return args
