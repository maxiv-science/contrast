from .Gadget import Gadget
from collections import OrderedDict
from fnmatch import filter
import h5py
import numpy as np

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
    Handy function which splits a list of arguments and keyword
    arguments, translates names of Gadget instances to actual objects,
    evaluates expressions that can be evaluated, and accepts the rest as
    strings. For example,

    .. ipython::

        In [11]: from contrast.motors import DummyMotor

        In [12]: from contrast.utils import str_to_args

        In [13]: samx = DummyMotor(name='samx')

        In [14]: str_to_args("samx hej 1./20")
        Out[14]: [<contrast.motors.Motor.DummyMotor at 0x7efe164d4f98>, 'hej', 0.05]
    """
    args_in = line.split()
    args_out = []
    kwargs_out = {}
    gadget_lookup = {g.name: g for g in Gadget.getinstances()}
    for a in args_in:
        if '=' in a:
            key, val = a.split('=')
            if ('*' in val) or ('?' in val):
                matching_names = filter(gadget_lookup.keys(), val)
                kwargs_out[key] = [gadget_lookup[name] for name in matching_names]
            elif val in gadget_lookup.keys():
                kwargs_out[key] = gadget_lookup[val]
            else:
                kwargs_out[key] = eval(val)
        else:
            if ('*' in a) or ('?' in a):
                matching_names = filter(gadget_lookup.keys(), a)
                args_out += [gadget_lookup[name] for name in matching_names]
            elif a in gadget_lookup.keys():
                args_out.append(gadget_lookup[a])
            else:
                try:
                    args_out.append(eval(a))
                except NameError:
                    args_out.append(a)
    return args_out, kwargs_out

class SpecTable(object):
    """
    A dyamic table, for use when the column titles and one data row are
    known.
    """
    min_str_len = 12
    max_str_len = 12

    def format_pair(self, k, v):
        """
        Return two title strings and a format string corresponding to
        the k:v pair.
        """
        if isinstance(v, int):
            data_width = len(str(v)) + 1
            header_width = len(str(k))
            w = max(data_width, header_width)
            h = ('%% %us'%w)%k
            return ' '*len(h),  h, '%%%ud'%w
        elif k=='dt':
            fmt = '%6.3f'
            return 6*' ', '%6s'%k, fmt
        elif isinstance(v, float):
            fmt = '% .3e'
            data_width = len(fmt%1)
            header_width = len(str(k))
            w = max(data_width, header_width)
            spaces = ' '*(w-data_width)
            h = ('%%%us'%w)%k
            return ' '*len(h),  h, spaces+fmt
        elif isinstance(v, dict):
            results = [self.format_pair(k_, v_) for k_, v_ in v.items()]
            keys = '  '.join([str(r[-2]) for r in results])
            fmts = '  '.join([str(r[-1]) for r in results])
            h1 = ('%%.%us'%(len(keys))) % k
            pl = (len(keys)-len(h1)) // 2
            pr = (len(keys)-len(h1)) - pl
            h1 = '.' * pl + h1 + '.' * pr
            return h1, keys, fmts
        elif isinstance(v, h5py.ExternalLink):
            data_width = len('hdf5-link')
            header_width = len(str(k))
            w = max(data_width, header_width)
            h = ('%%%us'%w)%k
            return ' '*len(h), h, '%%%us'%w
        elif isinstance(v, h5py.VirtualLayout):
            data_width = len('hdf5-vds')
            header_width = len(str(k))
            w = max(data_width, header_width)
            h = ('%%%us'%w)%k
            return ' '*len(h), h, '%%%us'%w
        else:
            fmt = '%%%u.%us' % (self.min_str_len, self.max_str_len)
            w = len(fmt%v)
            h = ('%%%us'%w)%k
            return ' '*len(h), h, fmt

    def header_lines(self, dct):
        """
        Takes a dict of {header: value} pairs, and returns a header
        line. At the same time it calculates the format string for
        subsequent data lines.
        """
        headers1 = []
        headers2 = []
        formats = []
        for k, v in dct.items():
            h1, h2, f = self.format_pair(k, v)
            headers1.append(h1)
            headers2.append(h2)
            formats.append(f)
        self._line_format = '  '.join(formats)
        h1 = '  '.join(headers1)
        h2 = '  '.join(headers2)
        if h1.strip():
            return '\n'.join([h1, h2])
        else:
            return h2

    def fill_line(self, dct):
        """
        Takes a data dict and returns a data line.
        """
        return self._line_format % self.list_values(dct)

    def list_values(self, dct):
        if not hasattr(self, '_line_format'):
            self.header_lines(dct)
        vals = []
        for v in dct.values():
            if isinstance(v, dict):
                vals += list(self.list_values(v))
            elif isinstance(v, h5py.ExternalLink):
                vals += ['hdf5-link']
            elif isinstance(v, h5py.VirtualLayout):
                vals += ['hdf5-vds']
            elif isinstance(v, np.ndarray):
                vals += [np.array2string(v, threshold=4, edgeitems=1,
                            formatter={'float_kind':lambda x: "%.1e" % x},
                            separator=',',)]
            else:
                vals.append(v)
        return tuple(vals)

