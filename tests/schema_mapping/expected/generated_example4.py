from typedpy import *


class Example1(Structure):
    firstName = String()
    lastName = String()
    socialSecurity = String()
    ageYears = Integer()

    _required = ['ageYears', 'firstName', 'lastName', 'socialSecurity']
