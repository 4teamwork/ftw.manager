
class Singleton(object):
    """
    Provides the singleton pattern for class inheriting the Singleton class.

    A normal class generates at every initialization a new object:
    >>> class NormalClass(object):
    ...     pass
    ... print NormalClass()==NormalClass()
    False

    A class inheriting from Singleton creates returns the same object at every
    initialization:
    >>> class SingletonClass(Singleton):
    ...    pass
    ... print SingletonClass()==SingletonClass()
    True

    You can also use multiple inheritance:
    >>> class MultiInheritanceClass(Singleton, NormalClass):
    ...    pass
    ... print MultiInheritanceClass()==MultiInheritanceClass()
    False
    """

    def __new__(cls, *args, **kwargs):
        if '__singleton_object__' not in dir(cls):
            obj = object.__new__(cls, *args, **kwargs)
            cls.__singleton_object__ = obj
        return cls.__singleton_object__

