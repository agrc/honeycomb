#!/usr/bin/env python
# * coding: utf8 *
"""
arcpy.py

A module that contains a mock for the arcpy library so that tests can be run without it.
"""


class env(object):
    workspace = None


class management(object):
    @staticmethod
    def Delete(arg):
        pass

    @staticmethod
    def Project(*args):
        pass

    @staticmethod
    def Copy(*args):
        pass

    @staticmethod
    def GetCount(*args):
        return [15]


class _cursor(object):
    def __enter__(self, *args):
        return self

    def __exit__(*args):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration


class da(object):
    @staticmethod
    def SearchCursor(*args):
        return _cursor()


class SpatialReference(object):
    def __init__(self, arg):
        pass


class analysis(object):
    @staticmethod
    def Intersect(in_features, out_features, join_attributes):
        pass


def ListFeatureClasses():
    if env.workspace.endswith(".sde"):
        return ["SGID10.BOUNDARIES.CountyBoundaries", "SGID10.LOCATION.Schools"]
    else:
        return ["CountyBoundaries", "Schools"]


def GetMessages():
    return "GetMessages mock response"


def ExecuteError(Exception):
    pass
