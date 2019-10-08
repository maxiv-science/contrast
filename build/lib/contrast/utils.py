from .Gadget import Gadget
from collections import OrderedDict
from fnmatch import filter

def list_to_table(lst, titles, margins=3, sort=True):
    """
    Formats a table from a nested list, where the first index is the row.
    """
    if sort:
        lst = sorted(lst)
    result = ''
    margins = [margins,] * len(titles) if not hasattr(margins, '__iter__') else margins
    # establish column widths
    widths = []
    for i in range(len(titles)):
        widths.append(max([len(titles[i]),] + [len(row[i]) for row in lst]) + margins[i])
    # a base format string for every line
    linebase = ''
    for w in widths:
        linebase += ('%%-%ss'%w)
    # make the header
    result += linebase % tuple(titles) + '\n'
    result += '-' * sum(widths) + '\n'
    # add the table data
    for row in lst:
        result += linebase % tuple(row) + '\n'
    return result.strip()

def dict_to_table(dct, titles=('col1', 'col2'), margin=3, sort=True):
    """
    Formats a dict where key:val is str:str into a two column table.
    """
    if sort:
        dct = OrderedDict({key:dct[key] for key in sorted(dct.keys())})
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
    args_in = line.split()
    args_out = []
    gadget_lookup = {g.name: g for g in Gadget.getinstances()}
    for a in args_in:
        if ('*' in a) or ('?' in a):
            matching_names = filter(gadget_lookup.keys(), a)
            args_out += [gadget_lookup[name] for name in matching_names]
        elif a in gadget_lookup.keys():
            args_out.append(gadget_lookup[a])
        else:
            args_out.append(eval(a))
    return args_out

