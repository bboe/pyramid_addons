from pyramid.httpexceptions import HTTPNotFound
from pyramid_addons.validation import SOURCE_MATCHDICT, Validator


class DBThing(Validator):

    """An application-specific validator that converts ids into the object."""

    def __init__(self, param, cls, id_validator, **kwargs):
        super(DBThing, self).__init__(param, **kwargs)
        self.cls = cls
        self.id_validator = id_validator

    def run(self, value, errors, request):
        """Return the object if valid and available, otherwise None."""
        item_id = self.id_validator(value, errors, request)
        thing = None
        if not errors:  # the id passed validation
            thing = self.cls.fetch_by_id(item_id)
        if not thing and self.source == SOURCE_MATCHDICT:
            # If the id is part of the URL we should raise a not-found error.
            raise HTTPNotFound()
        elif not thing:
            self.add_error(errors, 'Invalid {0}'.format(self.cls.__name__))
        return thing
