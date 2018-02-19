from abc import ABCMeta
import collections
import inspect

from observable import Observable
from Editor.saveable.saveable import SaveableType
from Editor.saveable.saveableInt import saveable_int

from Editor.signal import Signal


class UnionMeta(ABCMeta):
    """
    Meta class that keeps track of an ordered list of class attributes to later be used by the Composite class.
    Adds all class attributes of type SaveableType to member __ordered__ of the class __dict__
    """
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(mcs, name, bases, classdict):
        for base in bases:
            if hasattr(base, '__ordered__'):
                for key in base.__ordered__:
                    classdict[key] = base.__dict__[key]
        classdict['__ordered__'] = [key for key in classdict.keys() if
                                    inspect.isclass(classdict[key]) and
                                    issubclass(classdict[key], SaveableType)]
        classdict['__typemap__'] = {key: classdict[key] for key in classdict['__ordered__']}
        classdict['__revtypemap__'] = {classdict[key]: key for key in classdict['__ordered__']}

        return type.__new__(mcs, name, bases, dict(classdict))


class Union(SaveableType, metaclass=UnionMeta):
    """
    A Saveable Composite type. This class is meant to be subclassed to easily create new SaveableType's made up of
    other SaveableTypes. For each type the object should hold, simply add a class attribute that is equal to that type.
    Every instance created will have a value of that type. No new instances attributes can be directly added. If the
    SaveableType has a 'get' method, then accessing that attribute will return its get method. If it has a 'set' method
    then setting that attribute will call its set method. Otherwise setting is disallowed

    The bytearray representation of a composite is each bytearray representation of the composite in the order they were
    declared, one after another

    Ex.
    class Composite1(Composite):
        val1 = saveable_int('u32')
        val2 = array('saveable_int('u32'))

        Every Composite1 that is created will have a val1 and val2 attributes of the specified types. val1 = 5 will call
        val1.set(5) but val2 does not have a set so val2 = [4] will cause an Exception


    """
    def __init__(self):
        """
        Creates an instance attribute for each type in the class attribute '__ordered__'.
        """
        SaveableType.__init__(self)
        self.signal_changed = Signal()
        self.__current__ = self.__typemap__[self.__ordered__[0]]()
        self.__current__.signal_changed.connect(self.signal_changed)

    def set(self, Type):
        if Type in self.__revtypemap__:
            self.__current__.signal_changed.disconnect(self.signal_changed)
            self.__current__ = Type()
            self.__current__.signal_changed.connect(self.signal_changed)
            self.signal_changed(Type)
            return
        raise ValueError('Invalid Type {}'.format(Type))

    def get(self):
        return type(self.__current__)

    def get_current(self):
        return self.__current__

    def __setattr__(self, key, value):
        """
        Catches all attribute setting. Only allows the setting if the attribute being set has a 'set' method. If it does
        calls attribute.set(value). Otherwise setting is disallowed
        """
        if key in self.__typemap__:
            Type = self.__typemap__[key]
            if not callable(getattr(Type, 'set', None)):
                raise ValueError("Cannot assign directly to '{}' ({})".format(key, type(Type)))
            if key != self.__revtypemap__[type(self.__current__)]:
                self.set(Type)
            self.__current__.set(value)
        else:
            SaveableType.__setattr__(self, key, value)

    def __getattribute__(self, item):
        """
        Catches all attribute getting. If the attribute defines a 'get' method returns that instead, otherwise just
        returns the attribute
        """
        get_attribute = lambda item: SaveableType.__getattribute__(self, item)
        if item not in get_attribute('__typemap__'):
            return get_attribute(item)
        current = get_attribute('__dict__')['__current__']
        SetType = get_attribute('__typemap__')[item]
        if type(current) != SetType:
            return None
        return current

    def load_in_place(self, byte_array):
        index = saveable_int('u8')()
        index.load_in_place(byte_array)
        index = index.get()
        if not (0 <= index < len(self.__ordered__)):
            raise ValueError('Union index {} is out of range'.format(index))
        Type = self.__typemap__[self.__ordered__[index]]
        self.set(Type)
        self.__current__.load_in_place(byte_array)

    def to_byte_array(self):
        if self.__current__ is None:
            raise ValueError('Union is null')
        ind = self.__ordered__.index(self.__revtypemap__[type(self.__current__)])
        array_ = bytearray()
        index = saveable_int('u8')()
        index.set(ind)
        array_ += index.to_byte_array()
        array_ += self.__current__.to_byte_array()
        return array_

    def __str__(self):
        return str(self.__current__)

    def __repr__(self):
        return self.__current__.__repr__


if __name__ == '__main__':
    from Editor.saveable.saveableArray import array
    from Editor.saveable.saveableString import SaveableString

    U32 = saveable_int('u32')
    U16 = saveable_int('u16')

    class Bar(Union):
        a = U32
        b = U16
        c = SaveableString
        d = array(U32)

    print()
    a = Bar()
    print(a.__dict__)
    a.set(U32)
    print(a)
    a.a = 5
    data = a.to_byte_array()
    print(data)
    a.c = 'HELLO'
    print(a.to_byte_array())
    b = Bar()
    b.load_in_place(data)
    print(b)
