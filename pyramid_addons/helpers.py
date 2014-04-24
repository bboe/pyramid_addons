try:
    # Python 2.6+
    from ConfigParser import RawConfigParser
except ImportError:
    # Python 3
    # pylint: disable=F0401
    from configparser import RawConfigParser  # NOQA
    # pylint: enable=F0401
from datetime import datetime, timedelta, tzinfo
from pyramid.httpexceptions import (HTTPBadRequest, HTTPConflict, HTTPCreated,
                                    HTTPForbidden, HTTPGone, HTTPOk)


def http_bad_request(request, **kwargs):
    request.response.status = HTTPBadRequest.code
    kwargs.setdefault('error', 'Invalid request')
    return kwargs


def http_conflict(request, **kwargs):
    request.response.status = HTTPConflict.code
    return kwargs


def http_created(request, headers=None, **kwargs):
    request.response.status = HTTPCreated.code
    if headers:
        request.response.headerlist.extend(headers)
    return kwargs


def http_forbidden(request, **kwargs):
    request.response.status = HTTPForbidden.code
    kwargs.setdefault('error', 'Forbidden')
    return kwargs


def http_gone(request, headers=None, **kwargs):
    request.response.status = HTTPGone.code
    if headers:
        request.response.headerlist.extend(headers)
    return kwargs


def http_ok(request, **kwargs):
    request.response.status = HTTPOk.code
    return kwargs


def load_settings(config_file):
    config = RawConfigParser()
    if not config.read(config_file):
        raise Exception('Not a valid config file: {0!r}'.format(config_file))
    if config.has_section('app:main_helper'):
        settings = dict(config.items('app:main_helper'))
    else:
        settings = dict(config.items('app:main'))
    return settings


class UTC(tzinfo):
    """UTC tz

    From: http://docs.python.org/release/2.4.2/lib/datetime-tzinfo.html

    """
    def dst(self, _):
        return timedelta(0)

    def tzname(self, _):
        return 'UTC'

    def utcoffset(self, _):
        return timedelta(0)


def pretty_date(the_datetime):
    # Source modified from
    # http://stackoverflow.com/a/5164027/176978
    # If naive assume UTC for the_datetime
    if the_datetime.tzinfo:
        diff = datetime.now(UTC()) - the_datetime
    else:
        diff = datetime.utcnow() - the_datetime
    if diff.days > 7 or diff.days < 0:
        retval = the_datetime.strftime('%A %B %d, %Y')
    elif diff.days == 1:
        retval = '1 day ago'
    elif diff.days > 1:
        retval = '{0} days ago'.format(diff.days)
    elif diff.seconds <= 1:
        retval = 'just now'
    elif diff.seconds < 60:
        retval = '{0} seconds ago'.format(diff.seconds)
    elif diff.seconds < 120:
        retval = '1 minute ago'
    elif diff.seconds < 3600:
        retval = '{0} minutes ago'.format(diff.seconds / 60)
    elif diff.seconds < 7200:
        retval = '1 hour ago'
    else:
        retval = '{0} hours ago'.format(diff.seconds / 3600)
    return retval
