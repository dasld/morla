# -*- coding: utf-8 -*-

from typing import Any, ItemsView, KeysView, Optional, Union, ValuesView


from morla.utils import COMMA, dict_diff


class ConfigurationError(Exception):
    """An exception to be raised by Configuration objects.
    """

    pass


class Configuration:
    default = {
        "BAD_YEAR": "XXXX",
        "USO": "Uso:",
        "TAGS": "Tags:",
        "LABEL": "label",
        "ORIGIN": "origin",
        "BEGIN_QUESTION": r"\begin{Exercise}",
        "END_QUESTION": r"\end{Exercise}",
        "BEGIN_CHOICES": r"\begin{choices}",
        "END_CHOICES": r"\end{choices}",
        "CHOICE": r"\choice",
        "CORRECT": r"\CorrectChoice",
        "BEGIN_ANSWER": r"\begin{Answer}",
        "END_ANSWER": r"\end{Answer}",
    }

    def update(self, D: dict) -> None:
        # check whether D has only valid keys
        illegal = dict_diff(self.default, D)
        if not illegal:
            self.dict.update(D)
            # this ensures that every default (key, value) not overriden by D
            # is in D; self.dict = D.copy() wouldn't do.
        else:
            illegal = ", ".join(illegal)
            raise ConfigurationError(f"{illegal} are not valid configuration keys.")

    def __init__(self, D: Optional[Union[dict, "Configuration"]] = None) -> None:
        # del self.default
        if D is None or isinstance(D, dict):
            self._dict = Configuration.default.copy()
            if D:
                self.update(D)
                # this update attempt will raise a ConfigurationError if any
                # key in D is invalid
        elif isinstance(D, Configuration):
            self._dict = D._dict.copy()
        else:
            raise ValueError(f"{repr(D)} must be dict, Configuration or None!")

    @property
    def dict(self) -> dict:
        return self._dict

    def keys(self) -> KeysView:
        return self.dict.keys()

    def values(self) -> ValuesView:
        return self.dict.values()

    def items(self) -> ItemsView:
        return self.dict.items()

    def __len__(self) -> int:
        """(...) an object that doesn’t define a __bool__() method and whose __len__()
        method returns zero is considered to be false in a Boolean context.
        https://docs.python.org/3.6/reference/datamodel.html
        """
        return len(self.dict)

    def __getitem__(self, key) -> Any:
        """Implements the self["name"] syntax.
        """
        return self.dict[key]

    def __setitem__(self, key, value) -> None:
        """Implements the self[key] = value syntax.
        """
        if key not in self.keys():
            raise ValueError(f"{repr(key)} is not a valid configuration.")
        elif not isinstance(value, str):
            raise ValueError(f"{repr(value)} must be str.")
        else:
            self.dict[key] = value

    def __delitem__(self, key) -> ConfigurationError:
        """Implements (and prevents) the del self[key] syntax.
        """
        raise ConfigurationError("A configuration cannot not be deleted.")

    def __getattr__(self, name) -> Any:
        """Implements the self.name syntax.
        """
        try:
            # attempt normal attribute name syntax
            return self.__dict__[name]
        except KeyError:
            # attempt to access the inner dictionary
            D = self.__dict__["_dict"]
            return D[name]

    def __iter__(self) -> iter:
        """This method is called when an iterator is required for a container.
        This method should return a new iterator object that can iterate over
        all the objects in the container. For mappings, it should iterate over
        the keys of the container.
        """
        return iter(self.dict)

    def __contains__(self, item) -> bool:
        """Called to implement membership test operators. Should return true if
        item is in self, false otherwise. For mapping objects, this should
        consider the keys of the mapping rather than the values or the key-item
        pairs.
        """
        return item in self.dict

    def __eq__(self, other) -> bool:
        return self.dict == other.dict

    def __hash__(self) -> int:
        """dict is not hashable, so we need to hash a Configuration some other
        way.
        """
        # pair = (frozenset(self.keys()), frozenset(self.values()))
        # return hash(pair)
        return hash(tuple(self.items()))

    def __str__(self) -> str:
        """Outputs the dictionary as "k: v, k: v, k: v".
        """
        items = sorted(self.items())
        return COMMA.join([f"{k}: {v}" for k, v in items])


if __name__ == "__main__":
    print("This module should not be run alone.")
    from tkinter import sys

    sys.exit()

__trash = """
    def __setattr__(self, name, value) -> None:
        "Prevents self.name attribution if name is a self._dict key."
        if name in self.dict:
            raise ConfigurationError("nope")
        else:
            self.__dict__[name] = value
"""
