==========================
Frequently Asked Questions
==========================

.. currentmodule:: typedpy

.. contents:: :local:

1. What is the equivalent of TypedDict (PEP-589) in Typedpy?

2. What is the equivalent of NamedTuple in Typedpy? or of TypedDict (PEP-589)?

Typedpy discourages things like NamedTuple, TypedDict, since they are thin wrappers around tuple, dict, with
limited dynamic check. Instead, use a Structure class. It gives you a lot more than NamedTuple, with some c
ost to speed.
You can still use NamedTuple to populate values in a typedpy Tuple field, btw, since a NamedTuple is a tuple.
Similarly, since any TypedDict is a dict, you can use it to populate a Map field.


3. What are the trade offs of using Typedpy?

* Support from the IDE is limited
* Performance (especially for immutables)
* Compile-time check


