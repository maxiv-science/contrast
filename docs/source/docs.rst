Building this documentation
===========================

How to maintain and build this documentation:

- Document all new code with docstrings. Classes are documented using reStructuredText, macros are better documented in plain text so that the IPython help is readable.

- The html documentation is built by from the ``contrast/docs`` directory::

    make html

- Sphinx build the documentation from docstrings by importing the code. The latest version therefore has to be installed first, in the environment where you plan to build.

- If new modules (new source files) are added, they need to be added to the ``docs/source/contrast.*.rst`` hierarchy so that ``autodoc`` can include them.

- macros.rst is a special case, it is assembled by ``make html`` per the code in ``conf.py``.

---------------------------
Building on readthedocs.org
---------------------------

This documentation is hosted at https://contrast.readthedocs.io. The ``latest`` version is built automatically from new commits to the ``master`` branch at https://github.com/maxiv-science/contrast. The ``stable`` version is built from new tags (what github calls releases).
