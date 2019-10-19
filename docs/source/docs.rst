Building this documentation
===========================

- make html to build from rst and code
- sphinx imports the code, so install first so the latest version is imported, or perhaps add some relative path to conf.py so the source code is used directly.
- new classes or changes in existing modules are caught, but
- if new modules (new source files) are added, they need to be added to the rst
