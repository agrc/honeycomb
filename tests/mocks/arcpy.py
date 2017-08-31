#!/usr/bin/env python
# * coding: utf8 *
'''
arcpy.py

A module that contains a mock for the arcpy library so that tests can be run without it.
'''


class env:
    workspace = None


class management:
    @staticmethod
    def Delete(arg):
        pass

    @staticmethod
    def Project(*args):
        pass

    @staticmethod
    def Copy(*args):
        pass


class SpatialReference:
    def __init__(self, arg):
        pass


def ListFeatureClasses():
    if env.workspace.endswith('.sde'):
        return ['SGID10.BOUNDARIES.CountyBoundaries', 'SGID10.LOCATION.Schools']
    else:
        return ['CountyBoundaries', 'Schools']
