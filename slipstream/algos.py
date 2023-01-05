
def all_none(*args) -> bool:
    return all(x is None for x in args)


def any_none(*args) -> bool:
    return any(x is None for x in args)


def all_not_none(*args) -> bool:
    return all(x is not None for x in args)


def any_not_none(*args) -> bool:
    return any(x is not None for x in args)
