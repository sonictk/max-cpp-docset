# Readme

This is a [Dash](http://kapeli.com/dash)-compatible docset for the 3ds max C++ SDK reference. It has been
built against the 2017 documentation, but should work for 2018 as well. 

## Status

**This is still a work-in-progress. The docset generation scripts are not ready to be used yet.**

## Usage

Place the ``max-2017-cpp.docset`` folder in your directory that is 
used by Zeal/Dash/Velocity to lookup docsets. Please refer to your respective
application's documentation for how to install such things.


## Building

### Dependencies

You will need to install the dependencies listed in ``requirements.txt``
through ``pip`` or have it available on your ``PYTHONPATH``.

### Generating the docset

The Python scripts for building the database and formatting the documentation
to work in standalone mode are located in the ``bin`` directory. The Autodesk
documentation should be placed in the directory:
``max-2017-cpp.docset/Contents/Resources/Documents``.  Once that is
done, you should be able to run ``python clean_html_documentation.py`` and 
``python generate_database_entries.py`` in order to re-generate the docset. The
formatted HTML output will be placed in
``maya-2017-cpp.docset/Contents/Resources/Documents/output``, which
you should move to the ``Documents`` directory instead.


## License

Except for the documentation itself (which belongs to Autodesk and is freely
available for download via their website), the license for the scripts in this
repository is viewable in the ``LICENSE`` file.


## Author

Siew Yi Liang
