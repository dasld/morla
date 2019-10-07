# -*- coding: utf-8 -*-

from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Hashable,
    List,
    Optional,
    Set,
    Sequence,
    Tuple,
)

from functools import reduce, wraps
from itertools import chain

import os

# tk provides a re module
from tkinter import re

# from morla import *


# UTF8     = "utf-8"
COPYRIGHT = "\xa9"  # (c) symbol
SPACE = " "
UNDERSCORE = "_"
EOL = "\n" if os.name == "posix" else "\r\n"
COMMA = ", "
PERCENT = "%"
LDOTS = "..."
ELP = "[...]"
ARROW = chr(8594)  # right-pointing arrow

# languages
ENUS = "en-US"
PTBR = "pt-BR"

DEFAULT = "DEFAULT"
USER = "USER"


PREVIOUS = []


# OS functions -------------------------------------------------------------------------
class Cd:
    """Context manager for changing the current working directory.
    https://stackoverflow.com/a/13197763
    """

    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.old_path = os.getcwd()
        try:
            os.chdir(self.new_path)
        except OSError:
            print(f"> moving to {self.new_path} failed!")
            raise
        else:
            print("> moving to", self.new_path)

    def __exit__(self, etype, value, traceback):
        try:
            os.chdir(self.old_path)
        except OSError:
            print(f"> returning to {self.old_path} failed!")
            raise
        else:
            print("> returning to", self.old_path)


def get_extension(filename: str) -> str:
    if not os.path.isfile(filename):
        raise ValueError
    ext = os.path.splitext(filename)[1]  # filename.split(".")[-1]
    return ext.strip().lower() if ext else "*"


# str functions ------------------------------------------------------------------------
def print_sep() -> None:
    print("-" * 79)


def delete(x: str, y: str) -> str:
    # return re.sub(fr"^{y}", "", x).strip()
    return x.replace(y, "").strip()


def capitalize_first(s: str) -> str:
    """str.capitalize() capitalizes the first character of a string and converts the
    rest to lowercase. This function only capitalizes the first character.
    """
    if len(s) < 2:
        return s.upper()
    return s[0].upper() + s[1:]


def quote(s: str) -> str:
    return f'"{s}"'


def var_zfill(*args: int) -> Generator[str, None, None]:
    widest = max([len(str(i)) for i in args])
    for i in args:
        yield str(i).zfill(widest)


def make_end(start: str, end: str) -> str:
    """Returns a string that starts as start and ends as end. If start is shorter than
    end, end itself is returned.
    >>> make_end("foobar", "900")
    ... "foo900"
    :param str start: starting str
    :param str end: ending str
    :returns: a str that starts as start and ends as end
    """
    i = len(start) - len(end)
    if i <= 0:
        return end
    return start[:i] + end


def truncate(
    s: str,
    length: Optional[int] = 79,
    prefix: Optional[str] = None,
    suffix: Optional[str] = ELP,
    smart: Optional[int] = 1,
) -> str:
    """Returns prefix + s + suffix, if the total length of this is <length> characters
    at most.
    If not, then it removes characters from s, then from the prefix, then from the
    suffix, until an acceptable length is achieved.
    :param int length: maximum length of the resulting string
    :param str prefix: str to add right before s
    :param str prefix: str to append to s
    :param bool smart: 0: nothing;
                       1: double whitespace reduced to single whitespace, trailing
                       whitespace removed;
                       2: all whitespace removed
    :returns: prefix + s + suffix, possibly truncated
    """
    # ensure length is a non-negative integer
    if not isinstance(length, int):
        raise TypeError("length must be int.")
    if length < 0:
        raise ValueError("length must not be negative.")
    # check types of both prefix and suffix
    if prefix is not None and not isinstance(prefix, str):
        raise TypeError("prefix must be str or None.")
    if suffix is not None:
        if not isinstance(suffix, str):
            raise TypeError("suffix must be str or None.")
        elif len(suffix) >= length:
            # if the suffix alone exceeds the target window, simply truncate it
            return suffix[:length]
    # whitespace processing, if smart is 1 or 2
    if smart == 1:
        # remove trailing whitespace
        # s = re.sub(r"(^\s+|\s+$)", "", s)
        s = s.strip()
        # replace double whitespace with single whitespace
        s = re.sub(r"\s{2,}", SPACE, s)
    elif smart == 2:
        # remove all whitespace
        s = re.sub("\s+", "", s)
    elif smart != 0:  # not in (0, False):
        raise ValueError("smart must be either 0, 1 or 2.")
    # actual truncating
    trunc = prefix + s if prefix else s
    was_long = len(trunc) > length
    trunc = trunc[:length]
    if was_long and suffix:
        trunc = make_end(trunc, suffix)
    return trunc


def truncate2(
    s: str,
    length: Optional[int] = 79,
    prefix: Optional[str] = None,
    suffix: Optional[str] = ELP,
) -> str:
    """Returns prefix + s + suffix, if the total length of this is <length> characters
    at most.
    If it is too lengthy, then remove characters from s, then from the prefix, then from
    the suffix, until an acceptable length is achieved.
    :param int length: maximum length of the resulting string
    :param str prefix: str to add right before s
    :param str prefix: str to append to s
    :returns: prefix + s + suffix, possibly truncated
    """
    # ensure length is a non-negative number (integer or integer-like)
    if not isinstance(length, (int, float)):
        raise TypeError("length must be int or float.")
    elif length < 0:
        raise ValueError("length must not be negative.")
    elif int(length) != length:
        # even if length is a float, it must "look like" an integer
        raise ValueError("length must be an integer (int or float).")
    # check types of both prefix and suffix
    if prefix is not None and not isinstance(prefix, str):
        raise TypeError("prefix must be str or None.")
    if suffix is not None and not isinstance(suffix, str):
        raise TypeError("suffix must be str or None.")
    #
    trunc = [list(s)]  # [[s[0], s[1], ...]]
    trunc.insert(0, list(prefix) if prefix else [])
    trunc.append(list(suffix) if suffix else [])
    # empty lists are inserted so there's no IndexError in the for loop
    #
    cur_len = flat_len(trunc)
    for L in trunc[1], trunc[0], trunc[2]:
        # if anything must be removed, first chop the original string (trunc[1]), then
        # the prefix (trunc[0]), then the suffix (trunc[2])
        while cur_len > length:
            try:
                L.pop()
            except IndexError:
                break
            else:
                cur_len -= 1
    return "".join(["".join(L) for L in trunc])


def _truncate_test(simple: bool = True, reps: int = 1_000) -> None:
    if simple:
        t = truncate("oi, cara! " * 80, prefix=">>> ", suffix="$" * 3)
        print(len(t), quote(t))
    else:
        from timeit import timeit

        header = "from typing import Sequence, Optional; from __main__ import truncate, truncate2"
        test = quote("very long string " * 80)
        code1 = f"truncate({test})"
        code2 = f"truncate2({test})"
        t1 = timeit(setup=header, stmt=code1, number=reps)
        t2 = timeit(setup=header, stmt=code2, number=reps)
        print("t1:", t1)
        print("t2:", t2)
        winner, loser = min(t1, t2), max(t1, t2)
        print("winner is:", "t1" if t1 == winner else "t2")
        print(f"winner is ~{round(loser/winner, 2)}x better than loser!")


# dict functions -----------------------------------------------------------------------
def dict_diff(d1: dict, d2: dict, lazy: Optional[bool] = True) -> Set[Hashable]:
    """If lazy: return a singleton set with a key that occurs in exactly one of the two
    dictionaries.
    If not lazy: returns the set of all keys that occur in exactly one of the two
    dictionaries.
    """
    d1_keys, d2_keys = set(d1.keys()), set(d2.keys())
    # if not lazy:
    # XOR: a ^ b returns a new set with elements in either a or b but not both
    #    return d1_keys ^ d2_keys
    the_difference = set()
    pair = (d1_keys, d2_keys)
    for this, that in (pair, reversed(pair)):
        for k in this:
            if k not in that:
                the_difference.add(k)
                if lazy:
                    # a break statement would exit just the inner for-loop
                    return the_difference
    return the_difference


def dicts_diffs(L: Sequence[dict], lazy: Optional[bool] = True) -> List[Tuple[dict]]:
    if len(L) < 2:
        return []
    all_differences = []
    # the last dict doesn't need to be checked, for it will have already been checked
    # by then
    for i, d1 in enumerate(L[:-1]):
        # i + 1 can't raise an IndexError here because i will never be the last index
        after = L[i + 1 :]
        for d2 in after:
            diff = dict_diff(d1, d2)
            if diff:
                all_differences.append((d1, d2))
                if lazy:
                    # a break statement would exit just the inner for-loop
                    return all_differences
    return all_differences


def are_subdicts_invalid(D: Dict[Hashable, Dict], lazy: Optional[bool] = True) -> bool:
    dictionaries = tuple(D.values())
    return bool(dicts_diffs(dictionaries, lazy=lazy))
    if False:
        last = None
        all_differences = []
        for key, sub_d in D.items():
            if last is None:
                last = sub_d
                continue
            diff = dict_diff(last, sub_d)
            if not diff:
                continue
            if lazy:
                return (key, diff)
                # diff_str = COMMA.join(sorted(diff))
                # msg = truncate(f"Key mismatch in {key}: {diff_str}")
                # raise ValueError(msg)
            else:
                all_differences.append()
        return all_differences


# iterable's functions -----------------------------------------------------------------
def flat_len(L: Sequence) -> int:
    """Recursively looks for strings in L and returns the sum of their lengths.
    :param Sequence L: the container to be probed
    :returns: the added length of every string in L
    """
    # the following is not strictly necessary, but it's probably faster to just return
    # len(L) if L is a string than it is to do n += 1 for every character in L...
    if isinstance(L, str):
        return len(L)
    n = 0
    try:
        # iter(L) returns True if L is a string, but by now L certainly is not a string
        iter(L)
    except TypeError:
        print(f"{L} (type {type(L)}) is not iterable.")
    else:
        for x in L:
            n += flat_len(x)
    return n


def listDiff(m: Sequence, n: Sequence) -> list:
    return [x for x in m if x not in n]


def make_first(obj: Any, L: list) -> list:
    old_len = len(L)
    try:
        i = L.index(obj)
    except ValueError:
        pass
    else:
        del L[i]
        L.insert(0, obj)
    assert len(L) == old_len
    return L


# misc functions -----------------------------------------------------------------------
def _is_match(f: Callable, attr: str) -> None:
    def wrapper(f):
        @wraps(f)
        def wrapped(self, *f_args, **f_kwargs):
            if callable(_lambda) and re.search(pattern, (_lambda(self) or "")):
                f(self, *f_args, **f_kwargs)

        return wrapped

    return wrapper


def reveal(x: Any, D: dict = locals().copy()) -> str:
    global PREVIOUS
    current = []
    for k, v in D.items():
        if not k.startswith(UNDERSCORE):
            t = type(v)
            current.append(f"(locals) {k}: {v} {t}")
    for attr in dir(x):
        if not attr.startswith(UNDERSCORE):
            # y = x.__getattribute__(attr)
            y = getattr(x, attr)
            t = type(y)
            # if t not in terminal_classes:
            #    reveal(y)
            current.append(f"{repr(x)}.{attr}: {repr(y)} {t}")
    output = EOL.join(listDiff(current, PREVIOUS))
    PREVIOUS = current[:]
    return output


if __name__ == "__main__":
    from tkinter import sys

    #
    _truncate_test(False, 10_000)
    #
    sys.exit()
