from __future__ import unicode_literals

import re
import unittest
from datetime import datetime
from pyramid.testing import DummyRequest
from pyramid_addons.helpers import UTC, pretty_date
from pyramid_addons.validation import (And, Enum, Equals, List, Or, String,
                                       TextNumber, RegexString, SOURCE_GET,
                                       WhiteSpaceString, validate)


class PrettyDateTest(unittest.TestCase):
    def test_naive(self):
        self.assertTrue(len(pretty_date(datetime.now())) > 1)
        self.assertEqual('just now', pretty_date(datetime.utcnow()))

    def test_tzenabled(self):
        self.assertEqual('just now', pretty_date(datetime.now(UTC())))


class AndTest(unittest.TestCase):
    def test_fail_all(self):
        validator = And('field', Equals('', 'yes'), Equals('', 'yes'))
        errors = []
        self.assertEqual('no', validator('no', errors, None))
        self.assertEqual(1, len(errors))

    def test_fail_first(self):
        validator = And('field', Equals('', 'yes'), Equals('', 'no'))
        errors = []
        self.assertEqual('no', validator('no', errors, None))
        self.assertEqual(1, len(errors))

    def test_fail_last(self):
        validator = And('field', Equals('', 'no'), Equals('', 'yes'))
        errors = []
        self.assertEqual('no', validator('no', errors, None))
        self.assertEqual(1, len(errors))

    def test_pass(self):
        validator = And('field', Equals('', 'yes'), Equals('', 'yes'))
        errors = []
        self.assertEqual('yes', validator('yes', errors, None))
        self.assertEqual(0, len(errors))


class DecoratorTest(unittest.TestCase):
    @staticmethod
    @validate(required=String('field_1'),
              optional=String('field_2', optional=True, default='foobar'),
              get=String('field_1', source=SOURCE_GET, optional=True))
    def dummy_function(_, **kwargs):
        return set(kwargs.values())

    def test_provide_all(self):
        json_body = {'field_1': 'json_data_1', 'field_2': 'json_data_2'}
        request = DummyRequest(GET={'field_1': 'get_data_1'},
                               json_body=json_body)
        # pylint: disable=E1120
        self.assertEqual(set(['get_data_1', 'json_data_1', 'json_data_2']),
                         self.dummy_function(request))
        self.assertEqual(200, request.response.status_code)

    def test_provide_none(self):
        json_body = {}
        request = DummyRequest(json_body=json_body)
        retval = self.dummy_function(request)  # pylint: disable=E1120
        self.assertEqual(400, request.response.status_code)
        self.assertEqual(['Missing json_body parameter: field_1'],
                         retval['messages'])

    def test_provide_required(self):
        json_body = {'field_1': 'data_1'}
        request = DummyRequest(json_body=json_body)
        # pylint: disable=E1120
        self.assertEqual(set([None, 'data_1', 'foobar']),
                         self.dummy_function(request))
        self.assertEqual(200, request.response.status_code)


class EnumTest(unittest.TestCase):
    def test_fail(self):
        validator = Enum('field', 1, 'true', 'TRUE')
        errors = []
        self.assertEqual(0, validator(0, errors, None))
        self.assertEqual(1, len(errors))

    def test_pass_first_value(self):
        validator = Enum('field', 1, 'true', 'TRUE')
        errors = []
        self.assertEqual(1, validator(1, errors, None))
        self.assertEqual(0, len(errors))

    def test_pass_last_value(self):
        validator = Enum('field', 1, 'true', 'TRUE')
        errors = []
        self.assertEqual('TRUE', validator('TRUE', errors, None))
        self.assertEqual(0, len(errors))


class EqualsTest(unittest.TestCase):
    def test_fail(self):
        validator = Equals('field', 'yes')
        errors = []
        self.assertEqual('no', validator('no', errors, None))
        self.assertEqual(1, len(errors))

    def test_pass(self):
        validator = Equals('field', 'yes')
        errors = []
        self.assertEqual('yes', validator('yes', errors, None))
        self.assertEqual(0, len(errors))


class ListTest(unittest.TestCase):
    def test_fail_all(self):
        validator = List('field', String(None, min_length=2), min_elements=3)
        errors = []
        data = ['a', 'b']
        self.assertEqual(data, validator(data, errors, None))
        self.assertEqual(3, len(errors))

    def test_fail_too_few_elements(self):
        validator = List('field', String(''), min_elements=3)
        errors = []
        data = ['a', 'b']
        self.assertEqual(data, validator(data, errors, None))
        self.assertEqual(1, len(errors))

    def test_fail_too_many_elements(self):
        validator = List('field', String(''), max_elements=3)
        errors = []
        data = ['a', 'b', 'c', 'd']
        self.assertEqual(data, validator(data, errors, None))
        self.assertEqual(1, len(errors))

    def test_successful(self):
        validator = List('field', String(''), min_elements=3, max_elements=3)
        errors = []
        data = [' a ', ' b ', ' c ']
        self.assertEqual([x.strip() for x in data], validator(data, errors,
                                                              None))
        self.assertEqual(0, len(errors))

    def test_successful_zero_elements(self):
        validator = List('field', String(''))
        errors = []
        data = []
        self.assertEqual([], validator(data, errors, None))
        self.assertEqual(0, len(errors))


class OrTest(unittest.TestCase):
    def test_fail_all(self):
        validator = Or('field', Equals('', 'yes'), Equals('', 'YES'))
        errors = []
        self.assertEqual('no', validator('no', errors, None))
        self.assertEqual(1, len(errors))

    def test_pass_first(self):
        validator = Or('field', Equals('', 'no'), Equals('', 'yes'))
        errors = []
        self.assertEqual('no', validator('no', errors, None))
        self.assertEqual(0, len(errors))

    def test_pass_second(self):
        validator = Or('field', Equals('', 'yes'), Equals('', 'no'))
        errors = []
        self.assertEqual('no', validator('no', errors, None))
        self.assertEqual(0, len(errors))

    def test_pass_all(self):
        validator = Or('field', Equals('', 'yes'), Equals('', 'yes'))
        errors = []
        self.assertEqual('yes', validator('yes', errors, None))
        self.assertEqual(0, len(errors))


class StringTests(unittest.TestCase):
    def test_fail_invalid_regex(self):
        validator = RegexString('field')
        errors = []
        validator('[a', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_invalid_whitespace(self):
        validator = String('field', invalid_re=' ')
        errors = []
        validator(' hello world ', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_type_bool(self):
        validator = String('field')
        errors = []
        validator(True, errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_type_int(self):
        validator = String('field')
        errors = []
        validator(1, errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_type_none(self):
        validator = String('field')
        errors = []
        validator(None, errors, None)
        self.assertEqual(1, len(errors))

    def test_pass_all(self):
        validator = String('field', invalid_re='foo', min_length=3,
                           max_length=3, lowercase=True)
        errors = []
        value = validator(' bAr ', errors, None)
        self.assertEqual(0, len(errors))
        self.assertEqual('bar', value)


class TextNumberTests(unittest.TestCase):
    def test_fail_alphanumeric1(self):
        validator = TextNumber('field')
        errors = []
        validator('1a', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_alphanumeric2(self):
        validator = TextNumber('field')
        errors = []
        validator('a1', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_empty_string(self):
        validator = TextNumber('field')
        errors = []
        validator('', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_float(self):
        validator = TextNumber('field')
        errors = []
        validator('1.1', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_not_digit(self):
        validator = TextNumber('field')
        errors = []
        validator('a', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_too_large(self):
        validator = TextNumber('field', max_value=0)
        errors = []
        validator('1', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_too_small(self):
        validator = TextNumber('field', min_value=0)
        errors = []
        validator('-1', errors, None)
        self.assertEqual(1, len(errors))

    def test_pass_all(self):
        validator = TextNumber('field', min_value=16, max_value=16)
        errors = []
        value = validator(' +0016 ', errors, None)
        self.assertEqual(0, len(errors))
        self.assertEqual(16, value)


class WhiteSpaceStringTests(unittest.TestCase):
    def test_fail_invalid_precomp_re(self):
        pre = re.compile('foo')
        validator = WhiteSpaceString('field', invalid_re=pre)
        errors = []
        validator('  foo ', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_invalid_re(self):
        validator = WhiteSpaceString('field', invalid_re='foo')
        errors = []
        validator('  foo ', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_max_length(self):
        validator = WhiteSpaceString('field', max_length=5)
        errors = []
        validator('  a   ', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_min_length(self):
        validator = WhiteSpaceString('field', min_length=5)
        errors = []
        validator(' a  ', errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_multiple(self):
        validator = WhiteSpaceString('field', invalid_re='foo', min_length=10)
        errors = []
        validator(' foo ', errors, None)
        self.assertEqual(2, len(errors))

    def test_fail_type_bool(self):
        validator = WhiteSpaceString('field')
        errors = []
        validator(True, errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_type_int(self):
        validator = WhiteSpaceString('field')
        errors = []
        validator(1, errors, None)
        self.assertEqual(1, len(errors))

    def test_fail_type_none(self):
        validator = WhiteSpaceString('field')
        errors = []
        validator(None, errors, None)
        self.assertEqual(1, len(errors))

    def test_pass_all(self):
        validator = WhiteSpaceString('field', invalid_re='foo', min_length=5,
                                     max_length=5)
        errors = []
        value = validator(' bar ', errors, None)
        self.assertEqual(0, len(errors))
        self.assertEqual(' bar ', value)


if __name__ == '__main__':
    unittest.main()
