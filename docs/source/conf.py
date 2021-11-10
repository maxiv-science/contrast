# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------

project = 'Contrast'
copyright = '2019, Alexander Björling'
author = 'Alexander Björling'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
        'sphinx.ext.autodoc',
        'sphinx.ext.viewcode',
        'sphinx.ext.inheritance_diagram',
#        'sphinx_automodapi.automodapi',
#        'sphinx.ext.autosectionlabel',
        'IPython.sphinxext.ipython_console_highlighting',
        'IPython.sphinxext.ipython_directive',
        ]

master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

autoclass_content = 'both' # docstring from both class and constructor
autodoc_mock_imports = ['PyTango']
autodoc_member_order = 'bysource' # in the source code order, not alphabetically
autodoc_inherit_docstrings = False

latex_elements = {
    'papersize': 'a4paper',
    }

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'classic' #'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Special handling of macro classes ---------------------------------------
def label_macros(app, what, name, obj, options, lines):
    """ Find macros and mark them as such in the docs. """
    from contrast.environment import env
    if what == 'class':
        name = obj.__name__.lower()
        if name in env.registeredMacros:
            lines.insert(0, '')
            lines.insert(0, '**This class generates the macro `%s`**' % name)

def setup(app):
    app.connect('autodoc-process-docstring', label_macros)

# -- Build a document listing the built-in macros ----------------------------
from contrast.environment import env
from collections import OrderedDict
dct = env.registeredMacros
dct = OrderedDict({key:dct[key] for key in sorted(dct.keys())})
with open('macros.rst', 'w') as fp:
    fp.write('Built-in macros\n')
    fp.write('===============\n\n')
    for name, macro in dct.items():
        fp.write('%s\n' % name)
        fp.write('-'*len(name) + '\n')
        fp.write(macro.__doc__)
        fp.write('\n\n')

# -- Infer the version numbers from git tags ---------------------------------
import re
# The full version, including git commit etc.
release = re.sub('^v', '', os.popen('git describe --tags').read().strip())
# The base version, corresponding to the latest release.
version = release.split('-')[0]
