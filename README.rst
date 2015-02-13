======
BioDen
======

Requirements
============

BioDen has the following dependencies:

* `GTK+`_ (>=3.6)

* Python (>=2.7)

  * PyGObject_ (>=3.10)

  * xlrd

  * xlwt

On Debian (based) systems, the dependencies can be installed from the
software repository::

    sudo apt-get install python-gobject python-xlrd python-xlwt

More recent versions of some Python packages can be obtained via the Python
Package Index::

    pip install -r requirements.txt

Windows users first need to install `GTK+`_ and PyGObject_. Then use pip_
as described above to install the remaining dependencies.


Installation
============

From the GitHub repository::

    git clone https://github.com/figure002/bioden.git
    pip install bioden/

Or if you have a source archive file::

    pip install bioden-x.x.tar.gz


.. _`GTK+`: http://www.gtk.org/download/index.php
.. _PyGObject: https://wiki.gnome.org/action/show/Projects/PyGObject
.. _pip: https://pip.pypa.io/en/latest/installing.html
