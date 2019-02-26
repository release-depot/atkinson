========
atkinson
========


.. image:: https://img.shields.io/pypi/v/atkinson.svg
        :target: https://pypi.python.org/pypi/atkinson

.. image:: https://img.shields.io/travis/release-depot/atkinson.svg
        :target: https://travis-ci.org/release-depot/atkinson

.. image:: https://readthedocs.org/projects/atkinson/badge/?version=latest
        :target: https://atkinson.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Python based release manager.


* Free software: MIT license
* Documentation: https://atkinson.readthedocs.io.


Features
--------

* TODO

Notes
-----

This application only supports python 3. Some features may still work with python 2.7 but not all of the
syntax and features my be compatible.

Development
-----------
atkinson uses the upcoming standard of Pipfiles via pipenv.  This is integrated
into our Makefile and once you have the above dependencies, you can simply run::

  make dev

This will install our dev environment for the package via pipenv.  It is installed
with --user, so it does not affect your site-packages.  Pipenv creates a unique virtualenv
for us, which you can activate via::

  pipenv shell

See the `pipenv documentation <https://docs.pipenv.org/>`_ for more detail.

Documentation
*************

To build the documentation on your checkout, simply run::

  make docs

We plan to get this published in the near future, and this README will be
updated when that happens.

Contributions
*************

All new code should include tests that excercise the code and prove that it
works, or fixes the bug you are trying to fix.  Any Pull Request without tests
will not be accepted.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
