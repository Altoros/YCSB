""" Common functions and classes definitions for different types of
    plots.
"""
from cached_property import cached_property


# Add more colors to plot more than one figure in one window
COLORS = ['#008000',  # green
          '#0033FF',  # blue
          '#9933CC',  # purple
          '#FF3366',  # red
          '#FF6600',  # orange
          '#8B4513',  # saddle brown
          '#008080',  # teal
          '#EE82EE',  # violet
          '#6A5ACD',  # slate blue
          '#000000']  # black


class MetricUnit(object):

    def __init__(self, name, converter=lambda v: v):
        self._name = name
        self._converter = converter

    @property
    def name(self):
        return self._name

    @property
    def converter(self):
        return self._converter


class MetricInfo(object):

    def __init__(self, name, unit):
        self._name = name
        self._unit = unit

    @property
    def name(self):
        return self._name

    @property
    def unit(self):
        return self._unit

    @cached_property
    def full_name(self):
        return '%s (%s)' % (self._name, self._unit.name)
