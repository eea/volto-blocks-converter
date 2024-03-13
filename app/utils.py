import random

urlAlphabet = "ModuleSymbhasOwnPr-0123456789ABCDEFGHNRVfgctiUvz_KqYTJkLxpZXIjQW"


def nanoid(size=5):
    return "".join(random.choices(urlAlphabet, k=size))
