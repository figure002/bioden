.. _installation:

=========================================
Installation
=========================================

:Release: |release|
:Date: |today|

Requirements
============

BioDen has the following dependencies:

* GTK+ (>=3.6)

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

Windows users can install the PyGObject_ Windows installer with Gtk3 support.
Then use ``pip`` as described above to install the remaining dependencies.

.. note::

  This step is not needed if you have the Windows installer for BioDen, which
  comes bundeled with all the requirements.


Installation
============

From the GitHub repository::

    git clone https://github.com/figure002/bioden.git
    pip install bioden/

Or if you have a source archive file::

    pip install bioden-x.x.tar.gz

Windows installers can be obtained from SourceForge_.

.. note::

  The Windows installer for BioDen comes bundled with third party dependencies.
  The third party tools bundled with BioDen are property of their individual
  authors and are governed by their individual applicable license.

.. _PyGObject: https://wiki.gnome.org/action/show/Projects/PyGObject
.. _SourceForge: http://sourceforge.net/projects/bioden/
.. _Sphinx: http://sphinx-doc.org/
