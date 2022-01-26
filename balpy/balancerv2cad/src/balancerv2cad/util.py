from decimal import *


def mulUp(a: Decimal, b: Decimal) -> Decimal:
    getcontext().prec = 28
    getcontext().rounding = ROUND_UP
    return a*b


def divUp(a: Decimal, b: Decimal) -> Decimal:
    if a * b == 0:
        
        return Decimal(0)
    else:
        getcontext().prec = 28
        getcontext().rounding = ROUND_UP
        return a/b


def mulDown(a: Decimal, b: Decimal)-> Decimal:
    getcontext().prec = 28
    getcontext().rounding = ROUND_DOWN
    return a * b


def divDown(a: Decimal, b: Decimal)-> Decimal:
    getcontext().prec = 28
    getcontext().rounding = ROUND_DOWN
    result =  a/b
    return result


def complement(a: Decimal) -> Decimal:

    return Decimal(1 - a) if a < 1 else Decimal(0)


def powUp(a: Decimal,b:Decimal) -> Decimal:
    getcontext().prec = 28
    getcontext().rounding = ROUND_UP
    return a**b


def powDown(a: Decimal,b: Decimal)-> Decimal:
    getcontext().prec = 28
    getcontext().rounding = ROUND_DOWN
    return a**b
