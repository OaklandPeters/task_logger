"""
Interfaces for classes in logger.py
"""
from abc import ABCMeta, abstractproperty, abstractmethod
import collections



class ProcessAttemptABC(collections.MutableMapping):
    __meta__ = ABCMeta
    __enter__ = abstractmethod(lambda *args, **kwargs: NotImplemented)
    __exit__ = abstractmethod(lambda *args, **kwargs: NotImplemented)
    close = abstractmethod(lambda *args, **kwargs: NotImplemented)
    summary = abstractmethod(lambda *args, **kwargs: NotImplemented)
class ProcessLoggerABC(collections.MutableMapping):
    __meta__ = ABCMeta
    attempt = abstractproperty()
    attempts = abstractproperty()
    __enter__ = abstractmethod(lambda *args, **kwargs: NotImplemented)
    __exit__ = abstractmethod(lambda *args, **kwargs: NotImplemented)
    summary = abstractmethod(lambda *args, **kwargs: NotImplemented)