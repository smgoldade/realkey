from build123d import *
import abc

class Key(abc.ABC):
    """A class that all Keys should extend and define the methods of for a common key generation scheme"""

    _list = {}

    def __init_subclass__(cls, **kwargs):
        """Used to have a list of all current keys available for generation"""
        super().__init_subclass__(**kwargs)
        Key._list[cls.name()] = cls


    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        """Returns the name of this key"""

    @classmethod
    @abc.abstractmethod
    def profiles(cls) -> set[str]:
        """Returns the possible profiles for this key"""
    
    @classmethod
    @abc.abstractmethod
    def keyways(cls) -> set[str]:
        """Returns the possible keyways for this key"""

    @classmethod
    @abc.abstractmethod
    def blank(cls, profile: str, keyway: str) -> Part:
        """Returns a blank for the key with the given profile and keyway"""

    @classmethod
    @abc.abstractmethod
    def cut_definition(cls) -> str:
        """Provides an explanation for how the cut string should be interpreted"""

    @classmethod
    @abc.abstractmethod
    def key(cls, profile: str, keyway: str, cuts: str) -> Part:
        """Returns a cut key for the key with the given profile, keyway, and cuts"""