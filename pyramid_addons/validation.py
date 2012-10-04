import re
import sys
from functools import wraps
from .helpers import http_bad_request

# Inspirted by reddit's validator code
# github.com/reddit/reddit/blob/master/r2/r2/controllers/validator/validator.py

# Configure text type
if sys.version_info < (3, 0):
    text_type = unicode
else:
    text_type = str


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
            for dst_param, validator in param_vals.items():
                src_param = validator.param
                if src_param in data:
                    validator_errors = []
                    result = validator(data[src_param], validator_errors)
                    if validator_errors:
                        error_messages.extend(validator_errors)
                    else:
                        validated_params[dst_param] = result
                elif validator.optional:
                    validated_params[dst_param] = validator.default
                else:
                    error_messages.append(MISSING_ERROR.format(src_param))
            if error_messages:
                return http_bad_request(request, error_messages)
            return function(request, **validated_params)
        return wrapped
    return initial_wrap


class Validator(object):
    '''A base validator that will accept any input.

    This class should be extended to implement real validators.'''
    def __init__(self, param, optional=False, default=None):
        self.param = param
        self.optional = optional
        self.default = default

    def __call__(self, value, *args):
        return self.run(value, *args)

    def add_error(self, errors, message):
        errors.append('Validation error on param \'{0}\': {1}'
                      .format(self.param, message))

    def run(self, value, errors):
        return value


class List(Validator):
    '''A validator that validates items within a list.'''
    def __init__(self, param, validator, min_elements=None, max_elements=None,
                 **kwargs):
        super(List, self).__init__(param, **kwargs)
        self.validator = validator
        self.min_elements = min_elements
        self.max_elements = max_elements

    def run(self, value, errors):
        if not isinstance(value, list):
            self.add_error(errors, 'must be a list')
            return value
        msg = 'must contain {0}= {1} elements'
        if self.min_elements is not None and len(value) < self.min_elements:
            self.add_error(errors, msg.format('>', self.min_elements))
        elif self.max_elements is not None and len(value) > self.max_elements:
            self.add_error(errors, msg.format('<', self.max_elements))
        for i, item in enumerate(value):
            self.validator.param = (self.param, i)
            value[i] = self.validator(item, errors)
        return value


class TextNumber(Validator):
    '''A validator that accepts only text that represents integers.'''
    def __init__(self, param, min_value=None, max_value=None, **kwargs):
        super(TextNumber, self).__init__(param, **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def run(self, value, errors):
        if not isinstance(value, text_type):
            self.add_error(errors, 'must be a unicode string')
            return value

        try:
            num = int(value)
        except ValueError:
            self.add_error(errors, 'must only contains digits')
            return value

        if self.min_value is not None and num < self.min_value:
            self.add_error(errors, 'must be >= {0}'.format(self.min_value))
        elif self.max_value is not None and num > self.max_value:
            self.add_error(errors, 'must be <= {0}'.format(self.max_value))
        return num


class WhiteSpaceString(Validator):
    '''A validator for a generic string that allows whitespace on both ends.'''
    def __init__(self, param, invalid_re=None, min_length=0, max_length=None,
                 **kwargs):
        super(WhiteSpaceString, self).__init__(param, **kwargs)
        self.min_length = min_length
        self.max_length = max_length
        if invalid_re and not hasattr(invalid_re, 'match'):
            self.invalid_re = re.compile(invalid_re)
        else:
            self.invalid_re = invalid_re

    def run(self, value, errors):
        if not isinstance(value, text_type):
            self.add_error(errors, 'must be a unicode string')
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
