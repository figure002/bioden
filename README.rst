======
BioDen
======

Requirements
============

BioDen has the following dependencies:

* GTK+ 2

* Python 2

    * pygtk

    * pygobject

    * xlrd

    * xlwt

On Debian (based) systems, most dependencies can be installed from the
software repository::

    sudo apt-get install python-gtk2 python-xlrd python-xlwt

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
