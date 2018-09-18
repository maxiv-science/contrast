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
    Handy function which splits a list of arguments, and translates
    names of Gadget instances to actual objects. Throws an error if one
    of the arguments cannot be evaluated.
    """
    args = line.split()
    gadget_lookup = {g.name: g for g in Gadget.getinstances()}
    for i, a in enumerate(args):
        if a in gadget_lookup.keys():
            args[i] = gadget_lookup[a]
        else:
            try:
                args[i] = eval(a)
            except NameError:
                args[i] = a
    return args