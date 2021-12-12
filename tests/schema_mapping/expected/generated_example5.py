from typedpy import *




# ********************


class Example1(Structure):
    NAME = String()
    A = Array()

    _required = ['A', 'NAME']
