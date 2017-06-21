# Readme

This is a [Dash](http://kapeli.com/dash)-compatible docset for the 3ds max C++
SDK reference. It has been built against the 2017 documentation, but should work
for 2018 as well. 


## Building


### Dependencies

You will need to install the dependencies listed in ``requirements.txt``
through ``pip`` or have it available on your ``PYTHONPATH``.

Due to the size of the 3ds max SDK reference, the documentation sources are not
included in this repository. You will need to download it yourself from
[Autodesk's website](https://www.autodesk.com/me-sdk-docs). 


### Generating the docset

The Python scripts for building the database and formatting the documentation to
work in standalone mode are located in the ``bin`` directory. 

By default, you can copy the offline documentation to the a folder called
``resources/2017`` in the root directory. 

Once that is done, you should be able to run ``python
clean_html_documentation.py`` and ``python generate_database_entries.py`` in
order to re-generate the docset. Both scripts will attempt to create the docset
in default locations; these can be specified manually with command-line flags to
output to different locations should you so choose. Please refer to the
documentation included with each command-line script by adding the flag
``--help`` , like so: 

``python clean_html_documention.py --help``
``python generate_database_entries.py --help``

Both scripts support multi-threading in order to speed up generation of the
docsets with the ``-mt`` flag.


## License

Except for the documentation itself (which belongs to Autodesk and is freely
available for download via their website) along with the 3ds max logo, the
license for the scripts in this repository is viewable in the ``LICENSE`` file.


## Author

Siew Yi Liang
