import re
from functools import wraps
from .helpers import http_bad_request

# Inspirted by reddit's validator code
# github.com/reddit/reddit/blob/master/r2/r2/controllers/validator/validator.py


def validated_form(*simple_vals, **param_vals):
    MISSING_ERROR = 'Missing parameter: {0}'

    def initial_wrap(function):
        @wraps(function)
        def wrapped(request):
            # Ensure the request body is json
            try:
                data = request.json_body
            except ValueError:
                return http_bad_request(request, 'Request body must be JSON.')
            # Validate each of the named parameters
            error_messages = []
            validated_params = {}
            for param, validator in param_vals.items():
                if param in data:
                    validator_errors = []
                    result = validator(data[param], validator_errors)
                    if validator_errors:
                        error_messages.extend(validator_errors)
                    else:
                        validated_params[param] = result
                else:
                    error_messages.append(MISSING_ERROR.format(param))
            if error_messages:
                return http_bad_request(request, error_messages)
            return function(request, **validated_params)
        return wrapped
    return initial_wrap


class Validator(object):
    def __init__(self, param):
        self.param = param

    def __call__(self, value, *args):
        return self.run(value, *args)

    def add_error(self, errors, message):
        errors.append('Validation error on param {0!r}: {1}'
                      .format(self.param, message))


class WhiteSpaceString(Validator):
    '''A validator for a generic string that allows whitespace on both ends.'''
    def __init__(self, param, invalid_re=None, min_length=0, max_length=None):
        super(WhiteSpaceString, self).__init__(param)
        self.min_length = min_length
        self.max_length = max_length
        if invalid_re and not hasattr(invalid_re, 'match'):
            self.invalid_re = re.compile(invalid_re)
        else:
            self.invalid_re = invalid_re

    def run(self, value, errors):
        if not isinstance(value, str):
            self.add_error(errors, 'must be a string')
            return value

        if self.min_length and len(value) < self.min_length:
            self.add_error(errors,
                           'must be >= {0} characters'.format(self.min_length))
        elif self.max_length and len(value) > self.max_length:
            self.add_error(errors,
                           'must be <= {0} characters'.format(self.max_length))

        if self.invalid_re and self.invalid_re.search(value):
            self.add_error(errors, 'contains invalid content')
        return value


class String(WhiteSpaceString):
    '''A validator that removes whitespace on both ends.'''
    def run(self, value, *args):
        return super(String, self).run(value.strip(), *args)
