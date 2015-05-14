======
BioDen
======

BioDen is a data transformer for files containing taxon biomass/density data for
ecotopes. In general the input file of BioDen includes a list of records that
give species name, an abundance measure (biomass and/or density), a sample code,
the surface sampled, and the ecotope. This list is transformed to a table in
which the rows represent species (names) and the columns represent samples. This
output table can serve as the input file for various software applications that
conduct species community analyses.

.. image:: https://img.shields.io/badge/license-GPLv3-red.svg
        :target: http://www.gnu.org/copyleft/gpl.html

.. image:: https://readthedocs.org/projects/bioden/badge/?version=latest
        :target: https://readthedocs.org/projects/bioden/?badge=latest
        :alt: Documentation Status

Requirements
============

BioDen has the following dependencies:

* GTK+ (>=3.6)

* Python (>=2.7)

  * appdirs

  * PyGObject_ (>=3.2)

  * xlrd

  * xlwt

On Debian (based) systems, the dependencies can be installed from the
software repository::

    sudo apt-get install python-appdirs python-gobject python-xlrd python-xlwt

More recent versions of some Python packages can be obtained via the Python
Package Index::

    pip install -r requirements.txt

Windows users can install the PyGObject_ Windows installer with Gtk3 support.
Then use ``pip`` as described above to install the remaining dependencies. Note
that this step is not needed if you have the Windows installer for BioDen, which
comes bundeled with the requirements.


Installation
============

From the GitHub repository::

    git clone https://github.com/figure002/bioden.git
    pip install bioden/

Or if you have a source archive file::

    pip install bioden-x.x.tar.gz

Windows installers can be obtained from SourceForge_.


Documentation
=============

The documentation can be found here:

http://bioden.readthedocs.org/

Alternatively, the same documentation can be built using Sphinx_::

    $ python setup.py build_sphinx

Then launch ``build/sphinx/html/index.html`` in your browser.


Contributing
============

Please follow the next steps:

1. Fork the project on github.com.
2. Create a new branch.
3. Commit changes to the new branch.
4. Send a `pull request`_.

First make sure that all dependencies are installed as described above. Then
follow the next steps to run and develop BioDen within a virtualenv_ isolated
Python environment::

    $ git clone https://github.com/figure002/bioden.git
    $ cd bioden/
    $ virtualenv --system-site-packages env
    $ source env/bin/activate
    (env)$ pip install -r requirements.txt
    (env)$ python setup.py develop
    (env)$ bioden

.. _PyGObject: https://wiki.gnome.org/action/show/Projects/PyGObject
.. _SourceForge: http://sourceforge.net/projects/bioden/
.. _Sphinx: http://sphinx-doc.org/
.. _virtualenv: https://virtualenv.pypa.io/
.. _`pull request`: https://help.github.com/articles/creating-a-pull-request/
