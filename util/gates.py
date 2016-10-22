#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logical functions. Each logical function takes a one-argument predicate or a list of one-argument predicates.
Each logical function returns a one_argument predicate that is the chain of, or the negation of its arguments.
There are functions to chain predicates along NOT, AND, OR, NAND, NOR, XOR and XNOR.

The function 'gate' takes two lists of predicates, includes and excludes. Includes is the list of predicates that can
permit x through the gate; excludes is the list of predicates that can prevent x from passing the gate.

Each logical function, before returning the chained predicate, will check if the predicates in the argument list
are truly one-argument predicates. The behavior after detection of a wrong argument can be influenced by setting
    set_stop_on_creation_error(boolean)

The default behavior after detection of a wrong argument is to throw a GateCreationException.

"""
import inspect
import logging
from itertools import takewhile


def not_(predicate):
    """
    f(x) = not p(x)
    A negating predicate.
    :param predicate: the predicate to negate
    :return: a new predicate implementing not(p)
    """
    is_one_arg_predicate(predicate)
    return lambda x : not predicate(x)


def and_(*predicates):
    """
    f(x) = p_1(x) and p_2(x) and ... and p_n(x)
    The chain of predicates is True if all predicates are True, otherwise False
    :param predicates: predicates to chain in and.
    :return: a new predicate implementing p_1 and p_2 and ... and p_n
    """
    ps = [p for p in predicates if is_one_arg_predicate(p)]
    return lambda x : len(list(takewhile(lambda predicate : predicate(x), ps))) == len(ps)


def nor_(*predicates):
    """
    f(x) = not(p_1(x) or p_2(x) or ... or p_n(x))
    The chain of predicates is False if at least one predicate is True, otherwise True
    :param predicates: predicates to chain in nor.
    :return: a new predicate implementing not(p_1 or p_2 or ... or p_n)
    """
    ps = [p for p in predicates if is_one_arg_predicate(p)]
    return lambda x : len(list(takewhile(lambda predicate : not predicate(x), ps))) == len(ps)


def or_(*predicates):
    """
    f(x) = p_1(x) or p_2(x) or ... or p_n(x)
    The chain of predicates is True if at least one predicate is True, otherwise False
    :param predicates: predicates to chain in or.
    :return: a new predicate implementing p_1 or p_2 or ... or p_n
    """
    return not_(nor_(*predicates))


def nand_(*predicates):
    """
    f(x) = not(p_1(x) and p_2(x) and ... and p_n(x))
    The chain of predicates is False if all predicates are True, otherwise True
    :param predicates: predicates to chain in nand.
    :return: a new predicate implementing not(p_1 and p_2 and ... and p_n)
    """
    return not_(and_(*predicates))


def xor_(*predicates):
    """
    f(x) = p_1(x) xor p_2(x) xor ... xor p_n(x)
    Strictly speaking
        " A chain of XORs—a XOR b XOR c XOR d (and so on)—is true whenever an odd number of the inputs are true
        and is false whenever an even number of inputs are true." (https://en.wikipedia.org/wiki/Exclusive_or)
    Some definitions even deny that there can be more than two inputs:
        "a Boolean operator working on two variables that has the value one if one
        but not both of the variables is one." (https://www.google.nl/search?q=define+exclusive+OR)
    However, this implementation adheres to:
        The chain of predicates is True if one and only one predicate is True, otherwise False.

    :param predicates: predicates to chain with xor.
    :return: a new predicate implementing p_1 xor p_2 xor ... xor p_n
    """
    ps = [p for p in predicates if is_one_arg_predicate(p)]
    return lambda x : len([x for predicate in ps if predicate(x)]) == 1


def xnor_(*predicates):
    """
    f(x) = not(p_1(x) xor p_2(x) xor ... xor p_n(x))
    The chain of predicates is False if one and only one predicate is True, otherwise True.
    See also xor_(*predicates).
    :param predicates: predicates to chain with xnor.
    :return: a new predicate implementing not(p_1 xor p_2 xor ... xor p_n)
    """
    return not_(xor_(*predicates))


def gate(includes=list(), excludes=list()):
    """
    Chains including predicates and excluding predicates. The outcome of a gate for any x is
        g(x) = (i_1(x) or i_2(x) or ... or i_n(x)) and not(e_1(x) or e_2(x) or ... or e_n(x))
    Logical performance has been optimized. i.e. A or B or C is True if A is True; do not test B and C in this case.
    :param includes: predicates that permit x through gate
    :param excludes: predicates that restrict x from gate
    :return: a new predicate implementing (i_1 or i_2 or ... or i_n) and not(e_1 or e_2 or ... or e_n)
    """
    return and_(or_(*includes), nor_(*excludes))


LOG = logging.getLogger(__name__)

STOP_ON_CREATION_ERROR = True


def set_stop_on_creation_error(stop):
    global STOP_ON_CREATION_ERROR
    STOP_ON_CREATION_ERROR = stop


class GateCreationException(ValueError):
    pass


def is_one_arg_predicate(p):
    is_p = True
    msg = None
    if not inspect.isfunction(p):
        is_p = False
        msg = "not a function: %s" % p
    else:
        argspec = inspect.getargspec(p)
        if len(argspec.args) != 1:
            is_p = False
            msg = "more than one argument in %s: %s" % (p, argspec.args)
        elif argspec.varargs:
            is_p = False
            msg = "varargs in %s: %s" % (p, argspec.varargs)
        elif argspec.keywords:
            is_p = False
            msg = "keyword arguments in %s: %s" % (p, argspec.keywords)
    if not is_p:
        if STOP_ON_CREATION_ERROR:
            raise GateCreationException("Not a one-argument predicate: %s" % msg)
        else:
            LOG.error("Not a one-argument predicate: %s" % msg)
    return is_p