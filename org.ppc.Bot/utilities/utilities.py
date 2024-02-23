'''
Created on August 2, 2016

This file is subject to the terms and conditions defined in the
file 'LICENSE.txt', which is part of this source code package.

@author: David Moss
'''

# Time conversions to ms
ONE_MINUTE_MS = 60000
ONE_HOUR_MS = ONE_MINUTE_MS * 60
ONE_DAY_MS = ONE_HOUR_MS * 24
ONE_WEEK_MS = ONE_DAY_MS * 7
ONE_MONTH_MS = ONE_DAY_MS * 30

# Modes
MODE_HOME = "HOME"
MODE_AWAY = "AWAY"
MODE_STAY = "STAY"
MODE_TEST = "TEST"

MODE_ATTRIBUTE_SILENT = "SILENT"
MODE_ATTRIBUTE_DURESS = "DURESS"

# Occupancy status
OCCUPANCY_STATUS_PRESENT = "PRESENT"
OCCUPANCY_STATUS_ABSENT = "ABSENT"
OCCUPANCY_STATUS_H2S = "H2S"
OCCUPANCY_STATUS_SLEEP = "SLEEP"
OCCUPANCY_STATUS_S2H = "S2H"
OCCUPANCY_STATUS_H2A = "H2A"
OCCUPANCY_STATUS_A2H = "A2H"
OCCUPANCY_STATUS_VACATION = "VACATION"

# SMS Status
SMS_SUBSCRIBED = 1
SMS_OPT_OUT = 2


def celsius_to_fahrenheit(celsius):
    """
    Celsius to Fahrenheit
    :param celsius: Degrees Celsius
    :return: Fahrenheit
    """
    return float(celsius) * 9.0/5.0 + 32


def fahrenheit_to_celsius(fahrenheit):
    """
    Fahrenheit to Celsius
    :param celsius: Degrees Fahrenheit float
    :return: Fahrenheit float
    """
    return (float(fahrenheit) - 32) * 5.0/9.0


def relative_f_to_c_degree(fahrenheit_degree):
    """
    Convert relative degrees Fahrenheit to Celsius
    For example, if I want to increase the thermostat 3 degrees F, then I need to adjust it 1.66668 degrees C.
    :param fahrenheit_degree: relative number of degrees F
    :return: relative number of degrees C
    """
    return float(fahrenheit_degree) * 0.555556


def normalize_measurement(measure):
    """
    Transform a measurement's value, which could be a string, into a real value - like a boolean or int or float
    :param measure: a raw measurement's value
    :return: a value that has been corrected into the right type
    """
    try:
        return eval(measure, {}, {})

    except:
        if measure in ['true', 'True']:
            return True

        elif measure in ['false', 'False']:
            return False

        else:
            return measure

def iso_format(dt):
    """
    Returns an ISO formatted datetime that matches the format the server (Java) gives us, which is in milliseconds and not microseconds.
    :param dt: datetime to transform into an ISO formatted string
    :return: ISO formatted string
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S." + '%03d' % (dt.microsecond / 1000) + "%z")

def getsize(obj_0):
    """
    Recursively iterate to sum size of object & members.
    https://stackoverflow.com/questions/449560/how-do-i-determine-the-size-of-an-object-in-python
    """
    import sys
    from numbers import Number
    from collections import deque

    try: 
        from collections.abc import Mapping
        zero_depth_bases = (str, bytes, Number, range, bytearray)
        iteritems = 'items'
    except ImportError: # Python 2
        from collections import Mapping
        zero_depth_bases = (basestring, Number, xrange, bytearray)
        iteritems = 'iteritems'

    _seen_ids = set()
    def inner(obj):
        obj_id = id(obj)
        if obj_id in _seen_ids:
            return 0
        _seen_ids.add(obj_id)
        size = sys.getsizeof(obj)
        if isinstance(obj, zero_depth_bases):
            pass # bypass remaining control flow and return
        elif isinstance(obj, (tuple, list, Set, deque)):
            size += sum(inner(i) for i in obj)
        elif isinstance(obj, Mapping) or hasattr(obj, iteritems):
            size += sum(inner(k) + inner(v) for k, v in getattr(obj, iteritems)())
        # Check for custom object instances - may subclass above too
        if hasattr(obj, '__dict__'):
            size += inner(vars(obj))
        if hasattr(obj, '__slots__'): # can have __slots__ with __dict__
            size += sum(inner(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))
        return size
    return inner(obj_0)


class MachineLearningError(Exception):
    """
    Machine learning exception class
    """

    def __init__(self, message):
        """
        Constructor
        :param message: Message that describes what happened, for logging
        """
        self.message = message

