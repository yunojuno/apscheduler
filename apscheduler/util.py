"""
This module contains several handy functions primarily meant for internal use.
"""

from datetime import date, datetime, timedelta
from time import mktime

__all__ = ('asint', 'asbool', 'convert_to_datetime', 'timedelta_seconds',
           'time_difference', 'datetime_ceil', 'obj_to_ref', 'ref_to_obj')


def asint(text):
    """
    Safely converts a string to an integer, returning None if the string
    is None.

    :type text: str
    :rtype: int
    """
    if text is not None:
        return int(text)


def asbool(obj):
    """
    Interprets an object as a boolean value.

    :rtype: bool
    """
    if isinstance(obj, str):
        obj = obj.strip().lower()
        if obj in ('true', 'yes', 'on', 'y', 't', '1'):
            return True
        if obj in ('false', 'no', 'off', 'n', 'f', '0'):
            return False
        raise ValueError('Unable to interpret value "%s" as boolean' % obj)
    return bool(obj)


def convert_to_datetime(dateval):
    """
    Converts a date object to a datetime object.
    If an actual datetime object is passed, it is returned unmodified.

    :type dateval: date
    :rtype: datetime
    """
    if isinstance(dateval, datetime):
        return dateval
    elif isinstance(dateval, date):
        return datetime.fromordinal(dateval.toordinal())
    raise TypeError('Expected date, got %s instead' % type(dateval))


def timedelta_seconds(delta):
    """
    Converts the given timedelta to seconds.

    :type delta: timedelta
    :rtype: float
    """
    return delta.days * 24 * 60 * 60 + delta.seconds + \
        delta.microseconds / 1000000.0


def time_difference(date1, date2):
    """
    Returns the time difference in seconds between the given two
    datetime objects. The difference is calculated as: date1 - date2.

    :param date1: the later datetime
    :type date1: datetime
    :param date2: the earlier datetime
    :type date2: datetime
    :rtype: float
    """
    later = mktime(date1.timetuple())
    earlier = mktime(date2.timetuple())
    return int(later - earlier)


def datetime_ceil(dateval):
    """
    Rounds the given datetime object upwards.

    :type dateval: datetime
    """
    if dateval.microsecond > 0:
        return dateval + timedelta(seconds=1,
                                   microseconds=-dateval.microsecond)
    return dateval


def subconfig(config, prefix):
    """
    Returns a subdictionary from keys and values of  ``config`` where the key
    starts with the given prefix. The keys in the subdictionary have the prefix
    removed.
    
    :type config: dict
    :type prefix: str
    :rtype: dict
    """
    prefixlen = len(prefix)
    subconf = {}
    for key, value in config.items():
        if key.startswith(prefix):
            key = key[:-prefixlen]
            subconf[key] = value
    return subconf


def obj_to_ref(obj):
    """
    Returns the path to the given object.
    """
    ref = '%s:%s' % (obj.__module__, obj.__name__)
    try:
        obj2 = ref_to_obj(ref)
    except AttributeError:
        pass
    else:
        if obj2 == obj:
            return ref

    raise ValueError('Only module level objects are supported')


def ref_to_obj(ref):
    """
    Returns the object pointed to by ``ref``.
    """
    modulename, rest = ref.split(':', 1)
    obj = __import__(modulename)
    for name in modulename.split('.')[1:] + rest.split('.'):
        obj = getattr(obj, name)
    return obj