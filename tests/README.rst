Requirements
============

All the python requirements are enumerated in the ``dev`` dependency group of
pyproject.toml. You can install them with:

::
    uv sync --group dev


Apart from these requirements the following are required by plugins if you
choose to run the corresponding tests. Some of the comands use the Mac OS X
package manager `homebrew` - please use the package manager corresponding to
your operating system.


::
    # stylus
    npm install -g stylus

    #uglifyjs
    npm install -g uglify-js

    #asciidoc
    brew install asciidoc
    cd /usr/local/Cellar/asciidoc/8.6.8/bin
    curl -O https://asciidoc.googlecode.com/hg/asciidocapi.py

    #optipng
    brew install optipng


Ensure that `asciidoc`_ python api is available in the python path.

For example:

::
    export PYTHONPATH=/usr/local/Cellar/asciidoc/8.6.8/bin:$PYTHONPATH


Run the tests
=============

::
    nosetests tests
