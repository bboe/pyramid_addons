import re
import sys
from functools import wraps
from .helpers import http_bad_request

# Inspired by reddit's validator code
# https://github.com/reddit/reddit/blob/master/r2/r2/lib/validator/validator.py

# Configure text type
if sys.version_info < (3, 0):
    text_type = unicode  # pylint: disable=C0103
else:
    text_type = str  # pylint: disable=C0103


# Validator Sources
SOURCE_GET = 'GET'
SOURCE_JSON_BODY = 'json_body'
SOURCE_MATCHDICT = 'matchdict'
SOURCE_POST = 'POST'


def validate(**param_vals):
    MISSING_ERROR = 'Missing {0} parameter: {1}'  # pylint: disable=C0103

    def initial_wrap(function):
        @wraps(function)
        def wrapped(request):
            # Validate each of the named parameters
            error_messages = []
            validated_params = {}
            for dst_param, validator in param_vals.items():
                src_param = validator.param
                # Select the correct source to find the parameter in
                try:
                    data = getattr(request, validator.source)
                except (AttributeError, ValueError):
                    data = []
                # Look for the parameter
                if src_param in data:
                    validator_errors = []
                    try:
                        result = validator(data[src_param], validator_errors,
                                           request)
                    except ValidateAbort as exc:
                        # Return the desired abort response
                        request.override_renderer = 'json'  # Hack for now
                        return exc.response
                    if validator_errors:
                        error_messages.extend(validator_errors)
                    else:
                        validated_params[dst_param] = result
                elif validator.optional:
                    validated_params[dst_param] = validator.default
                else:
                    error_messages.append(MISSING_ERROR
                                          .format(validator.source, src_param))
            if error_messages:
                request.override_renderer = 'json'  # Hack for now
                return http_bad_request(request, messages=error_messages)
            # pylint: disable=W0142
            return function(request, **validated_params)
        return wrapped
    return initial_wrap


class ValidateAbort(Exception):

    """An exception that when raised will end all further validation."""

    def __init__(self, response):
        super(ValidateAbort, self).__init__()
        self.response = response


class Validator(object):

    """An abstract validator class."""

    default_source = SOURCE_JSON_BODY

    def __init__(self, param, optional=False, default=None, source=None):
        """Create a Validator instance

        :param param: The input, or source, parameter name.
        :param optional: When True, don't enforce a value to be provided.
            Note that if a value is provided, it will then need to pass the
            validation.
        :param default: The value to return when the parameter is optional and
            not provided.
        :param source: The source that param should be found in. Valid options
            are: SOURCE_MATCHDICT, SOURCE_GET, SOURCE_POST and
            SOURCE_JSON_BODY. When None, use the class's `default_source`
            selection.

        """
        if not optional and default is not None:
            raise TypeError('Cannot set default when optional is not True')

        self.param = param
        self.optional = optional
        self.default = default
        self.source = source if source is not None else self.default_source

    def __call__(self, value, *args):
        return self.run(value, *args)

    def add_error(self, errors, message):
        errors.append('Validation error on param \'{0}\': {1}'
                      .format(self.param, message))

    def run(self, value, errors, request):
        """Perform the validation using the validator.

        Subclasses must minimally define this function.

        :param value: The value send from the client of the request.
        :param errors: A list of errors that should be used in combination
            with add_error.
        :param request: The complete pyramid request object.
        :returns: The value returned will be passed to the function that this
            validator decorates. It can be altered, or returned as-is.

        """
        raise NotImplementedError('run must be defined in a subclass.')


class And(Validator):
    """Composes multiple validators with conjunction.
    It will also thread the value through.  An empty And
    simply returns without error."""

    def __init__(self, param, *validators, **kwargs):
        super(And, self).__init__(param, **kwargs)
        self.validators = validators

    def run(self, value, errors, request):
        for validator in self.validators:
            these_errors = []
            validator.param = self.param
            value = validator(value, these_errors, request)
            if these_errors:
                for error in these_errors:
                    self.add_error(errors, error)
                break
        return value


class Enum(Validator):

    """Validator that verifies the value is one of a few options."""

    def __init__(self, param, *values, **kwargs):
        super(Enum, self).__init__(param, **kwargs)
        self.values = values
        if len(values) < 2:
            raise TypeError('Expected at least two values.')
        # pylint: disable=W0142
        self.validator = Or(param, *[Equals('', x) for x in values])

    def run(self, value, errors, request):
        return self.validator(value, errors, request)


class Equals(Validator):
    """A validator that checks for object equality"""

    def __init__(self, param, compare, **kwargs):
        super(Equals, self).__init__(param, **kwargs)
        self.compare = compare

    def run(self, value, errors, _):
        if not value == self.compare:
            self.add_error(errors,
                           "must equal '{0}'".format(self.compare))
        return value


class List(Validator):
    """A validator that validates items within a list."""
    def __init__(self, param, validator, min_elements=None, max_elements=None,
                 **kwargs):
        super(List, self).__init__(param, **kwargs)
        self.validator = validator
        self.min_elements = min_elements
        self.max_elements = max_elements

    def run(self, value, errors, request):
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
            value[i] = self.validator(item, errors, request)
        return value


class Or(Validator):
    """Composes multiple validators with disjunction. An empty
    Or returns with an error."""

    def __init__(self, param, *validators, **kwargs):
        super(Or, self).__init__(param, **kwargs)
        self.validators = validators

    def run(self, value, errors, request):
        if not self.validators:
            self.add_error(errors, 'empty disjunction')
            return value

        all_errors = []
        for validator in self.validators:
            these_errors = []
            validator.param = self.param
            new_value = validator(value, these_errors, request)
            if not these_errors:
                return new_value
            all_errors.append(these_errors)

        msg = 'disjunction of evaluators failed: !({0})'
        error_groups = ['({0})'.format(', '.join(error_group))
                        for error_group in all_errors]
        self.add_error(errors,
                       msg.format(' || '.join(error_groups)))
        return value


class TextNumber(Validator):
    """A validator that accepts only text that represents integers."""
    def __init__(self, param, min_value=None, max_value=None, **kwargs):
        super(TextNumber, self).__init__(param, **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def run(self, value, errors, _):
        if not isinstance(value, text_type):
            self.add_error(errors, 'must be a unicode string')
            return value

        try:
            num = int(value)
        except ValueError:
            self.add_error(errors, 'must only contain digits')
            return value

        if self.min_value is not None and num < self.min_value:
            self.add_error(errors, 'must be >= {0}'.format(self.min_value))
        elif self.max_value is not None and num > self.max_value:
            self.add_error(errors, 'must be <= {0}'.format(self.max_value))
        return num


class WhiteSpaceString(Validator):
    """A validator for a generic string that allows whitespace on both ends."""
    def __init__(self, param, invalid_re=None, min_length=0, max_length=None,
                 trim_whitespace=False, lowercase=False, **kwargs):
        super(WhiteSpaceString, self).__init__(param, **kwargs)
        self.min_length = min_length
        self.max_length = max_length
        if invalid_re and not hasattr(invalid_re, 'match'):
            self.invalid_re = re.compile(invalid_re)
        else:
            self.invalid_re = invalid_re
        self.trim_whitespace = trim_whitespace
        self.lowercase = lowercase

    def run(self, value, errors, _):
        if not isinstance(value, text_type):
            self.add_error(errors, 'must be a unicode string')
            return value

        if self.trim_whitespace:
            value = value.strip()
        if self.lowercase:
            value = value.lower()

        if self.min_length and len(value) < self.min_length:
            self.add_error(errors,
                           'must be >= {0} characters'.format(self.min_length))
        elif self.max_length and len(value) > self.max_length:
            self.add_error(errors,
                           'must be <= {0} characters'.format(self.max_length))

        if self.invalid_re and self.invalid_re.search(value):
            self.add_error(errors, 'contains invalid content')
        return value


class RegexString(WhiteSpaceString):
    """A validator for strings that compile as regular expressions."""
    def run(self, value, errors, request):
        retval = super(RegexString, self).run(value, errors, request)
        try:
            re.compile(value)
        except re.error:
            self.add_error(errors, 'not a valid regular expression')
        return retval


class String(WhiteSpaceString):
    """A validator that removes whitespace on both ends."""
    def __init__(self, *args, **kwargs):
        super(String, self).__init__(*args, trim_whitespace=True, **kwargs)
