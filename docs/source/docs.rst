Building this documentation
===========================

How to maintain and build this documentation:

- Document all new code with docstrings. Classes are documented using reStructuredText, macros are better documented in plain text so that the IPython help is readable.

- The html documentation is built by from the ``contrast/docs`` directory::

    make html

- Sphinx build the documentation from docstrings by importing the code. The latest version therefore has to be installed first, from the root ``contrast`` directory::

    python3 setup.py install --user

- If new modules (new source files) are added, they need to be added to the ``docs/source/contrast.*.rst`` hierarchy so that ``autodoc`` can include them.

- macros.rst is a special case, it is assembled by ``make html`` per the code in ``conf.py``.