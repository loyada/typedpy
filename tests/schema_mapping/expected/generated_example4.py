from typedpy import *




# ********************


class Example1(Structure):
    firstName = String()
    lastName = String()
    socialSecurity = String()
    ageYears = Integer()

    _required = ['age_years', 'first_name', 'last_name', 'social_security']
