======
BioDen
======

Requirements
============

BioDen has the following dependencies:

* GTK+ (>=3.6)

* Python (>=2.7)

  * PyGObject (>=3.10)

  * xlrd

  * xlwt

On Debian (based) systems, the dependencies can be installed from the
software repository::

    sudo apt-get install python-gobject python-xlrd python-xlwt

More recent versions of some Python packages can be obtained via the Python
Package Index::

    pip install -r requirements.txt


Installation
============

From the GitHub repository::

    git clone https://github.com/figure002/bioden.git
    pip install bioden/

Or if you have a source archive file::

    pip install bioden-x.x.tar.gz
