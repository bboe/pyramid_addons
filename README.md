[![Build Status](https://travis-ci.org/bboe/pyramid_addons.png)](https://travis-ci.org/bboe/pyramid_addons)

## Suggested Alternative Packages

I created this package for use in two pyramid projects I was developing
simultaneously and the features were needed in both of them. I've since learned
about the following packages, and as such I will be removing functionality
provided by this package.

### [Pyramid Layout](http://pyramid_layout.readthedocs.org/en/latest/)

Pyramid Layout _should_ completely replace the need for the `site_layout`
decorator that `pyramid_addons` provides.

### [Colander](http://docs.pylonsproject.org/projects/colander/en/latest/)

Colander is a validation package that should replace the need for the
`validation` module provided by `pyramid_addons`. While its syntax appears to
be a bit different it is an official pyramid package so it _should_ be
utilized rather than a less actively developed package.

### Other notes

After discovering that pyramid supports view_configs that handle pyramid's HTTP
exceptions, the neccessity for the `http_` json response building functions
that this package provides are no longer necessary.

## Example Program

See the `example` directory for a sample Pyramid web application that utilizes
this package. The `run_example.py` script will start the web application, and
the `example_add_item.py` script is used to interface with the simple json API
the web application exposes.
