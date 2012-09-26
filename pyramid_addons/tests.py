import re
import unittest
from pyramid_addons import validation


class TextNumberTests(unittest.TestCase):
    def test_fail_alphanumeric1(self):
        validator = validation.TextNumber('field')
        errors = []
        validator('1a', errors)
        self.assertEqual(1, len(errors))

    def test_fail_alphanumeric2(self):
        validator = validation.TextNumber('field')
        errors = []
        validator('a1', errors)
        self.assertEqual(1, len(errors))

    def test_fail_empty_string(self):
        validator = validation.TextNumber('field')
        errors = []
        validator('', errors)
        self.assertEqual(1, len(errors))

    def test_fail_float(self):
        validator = validation.TextNumber('field')
        errors = []
        validator('1.1', errors)
        self.assertEqual(1, len(errors))

    def test_fail_not_digit(self):
        validator = validation.TextNumber('field')
        errors = []
        validator('a', errors)
        self.assertEqual(1, len(errors))

    def test_fail_too_large(self):
        validator = validation.TextNumber('field', max_value=0)
        errors = []
        validator('1', errors)
        self.assertEqual(1, len(errors))

    def test_fail_too_small(self):
        validator = validation.TextNumber('field', min_value=0)
        errors = []
        validator('-1', errors)
        self.assertEqual(1, len(errors))

    def test_pass_all(self):
        validator = validation.TextNumber('field', min_value=16, max_value=16)
        errors = []
        value = validator(' +0016 ', errors)
        self.assertEqual(0, len(errors))
        self.assertEqual(16, value)


class StringTests(unittest.TestCase):
    def test_fail_invalid_whitespace(self):
        validator = validation.String('field', invalid_re=' ')
        errors = []
        validator(' hello world ', errors)
        self.assertEqual(1, len(errors))

    def test_pass_all(self):
        validator = validation.String('field', invalid_re='foo',
                                      min_length=3, max_length=3)
        errors = []
        value = validator(' bar ', errors)
        self.assertEqual(0, len(errors))
        self.assertEqual('bar', value)


class WhiteSpaceStringTests(unittest.TestCase):
    def test_fail_invalid_precompiled_re(self):
        pre = re.compile('foo')
        validator = validation.WhiteSpaceString('field', invalid_re=pre)
        errors = []
        validator('  foo ', errors)
        self.assertEqual(1, len(errors))

    def test_fail_invalid_re(self):
        validator = validation.WhiteSpaceString('field', invalid_re='foo')
        errors = []
        validator('  foo ', errors)
        self.assertEqual(1, len(errors))

    def test_fail_max_length(self):
        validator = validation.WhiteSpaceString('field', max_length=5)
        errors = []
        validator('  a   ', errors)
        self.assertEqual(1, len(errors))

    def test_fail_min_length(self):
        validator = validation.WhiteSpaceString('field', min_length=5)
        errors = []
        validator(' a  ', errors)
        self.assertEqual(1, len(errors))

    def test_fail_multiple(self):
        validator = validation.WhiteSpaceString('field', invalid_re='foo',
                                                min_length=10)
        errors = []
        validator(' foo ', errors)
        self.assertEqual(2, len(errors))

    def test_pass_all(self):
        validator = validation.WhiteSpaceString('field', invalid_re='foo',
                                                min_length=5, max_length=5)
        errors = []
        value = validator(' bar ', errors)
        self.assertEqual(0, len(errors))
        self.assertEqual(' bar ', value)
