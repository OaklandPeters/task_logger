"""
@todo: Refactor data, name, aliases
    --> name: getter, setter, deleter
    --> aliases: getter, setter, deleter
    --> data: getter only - returning [name] + aliases
    @todo: Requires changing the way validation determines whether to
        extract name from 'data'. I will have to carefully think about this case:
            state.data = ['attempting', 'attempt', 'attempted']
            #? Should this change the name? IE be the same as:
            state = EnumGroup(['attempting', 'attempt', 'attempted'])
        --YES--  hence,
        self.data = ['a','b','c'] 
            ==
        self.name, self.aliases = self._validate(data, name=name)
    @todo: EnumGroupInterface: self._validate_name, self._validate_aliases
        Difference between _validate(data, name=None) and _validate_data(data)
            is _validate_data *assumes* it will pop off the front to make a name
        _validate(data, name=None)
        _validate_data(data)
        _validate_aliases(aliases)
        _validate_name(name)


@todo: Allow EnumGroup __init__ to accept *args, **kwargs:
    EnumGroup('attempting', 'attempt', 'attempted')
@todo: Consider making (optional) hooks from EnumGroup back to it's parent.
    So each group would know it's .parent, and .index
@todo: Make EnumGroup count as child of it's parent somehow (to isinstance?)


------ Future: --------
@todo: RegexEnum() + RegexEnumGroup()
@todo: support 'simplify'ing functions (like str.lower()), via a callback mechanism.
    --> SmartEnum()/TransformEnum()
    Should maintain a list of callbacks that it applies before comparison.
    Will have to apply the callbacks on the 'name' and 'aliases' after updating callback list.
    @todo: Implement this via: self._keytransform(key) - used only inside
        __getitem__, __setitem__, __delitem__ (and maybe whatever sets the initial data) 
        

Hard issue:
    I would like States['attempting'] to be valid syntax.
    But... this gets complicated because what if the name or alias 
        for a group is an integer?
    (actually, this is a similar issue to atlas's)
    SOLUTION: (inelegant, but workable)
        (1) if isinstance(key, int):
            index = key
        (2) else:
            index = 
            #check alias
        (3) throw error if a name is ever an integer
"""

import collections
from abc import ABCMeta, abstractproperty, abstractmethod
#----
from local_packages import rich_collections
from local_packages import rich_core



#==============================================================================
#        Interfaces
#==============================================================================

class EnumInterface(collections.MutableSequence):
    __metaclass__ = ABCMeta
    
    groups = abstractproperty(lambda self: NotImplemented)
    names = abstractproperty(lambda self: NotImplemented)
    aliases = abstractproperty(lambda self: NotImplemented)
    
    _find_group = abstractmethod(lambda self, alias: NotImplemented) #returns EnumGroup()
    group = abstractmethod(lambda self, alias: NotImplemented) #returns EnumGroup(). Same as _find_group
    _find_all = abstractmethod(lambda self, alias: NotImplemented) #yields EnumGroup()
    index = abstractmethod(lambda self, alias: NotImplemented) #returns integer
    
    _make_group = abstractmethod(lambda self, data, name=None: NotImplemented) #constructor for groups
    
    keys = abstractmethod(lambda: NotImplemented)
    values = abstractmethod(lambda: NotImplemented)


class EnumGroupInterface(collections.Sequence):
    """
    Complication:
    self.data: returns self.name + self.alias
    self.alias: is stored in self._data (because of inheritance from BasicMutableSequence)
    
    
    @todo: Refactor data, name, aliases
        --> name: getter, setter, deleter
        --> aliases: getter, setter, deleter
        --> data: getter only - returning [name] + aliases
    
    """
    __metaclass__ = ABCMeta
    name = abstractproperty(lambda: NotImplemented)
    __eq__ = abstractmethod(lambda: NotImplemented)
    
    
    
    #--- Name property and validation
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        self._name = self._validate_name(value)
    @name.deleter
    def name(self):
        del self._name
    def _validate_name(self, value):
        if isinstance(value, int):
            raise TypeError(str.format(
                "{0} 'name' cannot be an integer, because it conflicts with Sequence indexes.",
                self.__class__.__name__
            ))
        return value
    #--- Aliases property and validation
    aliases = abstractproperty(lambda self: NotImplemented)
    #--- Data property and validation
    data = abstractproperty(lambda self: NotImplemented)



#==============================================================================
#        Concrete Classes
#==============================================================================


class Enum(EnumInterface, rich_collections.BasicMutableSequence):
    """
    A sequence of EnumGroups.
    
    
    Potentially complicated 'corner-case' error:
        If name of a group is an integer
        Since that integer could also be the index of a different group

    @todo: Consider moving the group validiation from EnumGroup._validate()
        into here (Enum._validate_group())
    """
    def __init__(self, data):
        self.data = self._validate(data)
    
    
    
    def _validate(self, data):
        """
        """
        rich_core.AssertKlass(data,
            (rich_core.NonStringSequence, collections.Mapping), name='data'
        )
        if isinstance(data, collections.Mapping):
            return [
                self._validate_group(group, name=name)
                for name, group in data.items()
            ]
        elif isinstance(data, rich_core.NonStringSequence):
            return [
                self._validate_group(group)
                for group in data
            ]
        else:
            raise TypeError("Switch error on type of 'data' ({0}).".format(type(data)))
    def _validate_group(self, group, name=None):
        """Ensure sequence is a valid group."""
        return self._make_group(group, name=name)

    def _make_group(self, data, name=None):
        """Constructor for a single group."""
        return EnumGroup(data, name=name)
    @property
    def groups(self):
        """Alias to self.data property."""
        return self.data
    @groups.setter
    def groups(self, value):
        """Alias to self.data property setter."""
        self.data = value
    @groups.deleter
    def groups(self):
        """Alias to self.data property deleter."""
        del self.data
    @property
    def names(self):
        return [group.name for group in self]
    @property
    def aliases(self):
        return [group.aliases for group in self]
    #--------------------------------------------------------------------------
    #        Problematic Item Getter/Setter functions
    #--------------------------------------------------------------------------
    #__getitem__, __setitem__, __delitem__
    #... these are best (partly) resolved, by first, resolving keys/aliases to
    #an index number, then calling the normal __getitem__ functions. Example:
    #def __getitem__(self, key):
    #    index = self.index(key)
    #    return self.data[index]
    
    def _resolve_index(self, key):
        if isinstance(key, int):
            return key
        else:
            return self.index(key)
    def __getitem__(self, key):
        return self.data[self._resolve_index(key)]
    def __setitem__(self, key, value):
        self.data[self._resolve_index(key)]
    def __delitem__(self, key):
        self.data[self._resolve_index(key)]
            
        
    
    
    def _find_group(self, alias):
        """Find first group matching alias.
        Primarily, this matches on name, but allows for the
        possibility of groups which accept alternatives."""
        return self._find_all(alias).next()
    def _find_all(self, alias):
        """Find all groups matching alias. Iterator."""
        for group in self:
            if alias in group:
                yield group
    def group(self, alias):
        """Find first group matching alias (~name)."""
        return self._find_group(alias)
    def keys(self):
        return self.names
    def values(self):
        return [elm for group in self.groups for elm in group]
    def items(self):
        return [(group.name, group.aliases) for group in self.groups]
    def index(self, alias):
        """Find index for alias."""
        for i, group in enumerate(self):
            if alias in group:
                return i
        raise ValueError("alias not contained in any group.")
    def __eq__(self, other):
        return (self.groups == other)




class EnumGroup(rich_collections.BasicMutableSequence, EnumGroupInterface):
    """
    
    Organization of data, names, aliases is confusing:
    
    @todo: Refactor data, name, aliases
        --> name: getter, setter, deleter
        --> aliases: getter, setter, deleter
        --> data: getter only - returning [name] + aliases
        @todo: Requires changing the way validation determines whether to
            extract name from 'data'. I will have to carefully think about this case:
                state.data = ['attempting', 'attempt', 'attempted']
                #? Should this change the name? IE be the same as:
                state = EnumGroup(['attempting', 'attempt', 'attempted'])
            --YES--  hence,
            self.data = ['a','b','c'] 
                ==
            self.name, self.aliases = self._validate(data, name=name)
            
            
    """
    def __init__(self, data, name=None):
        """Initialize groups contained in 
        If name == None, then first entry of data is used as name.
        """
        #self.name, self.aliases = self._validate(data, name=name)
        self.name, self.data = self._validate(data, name=name)
        
    def _validate(self, data, name=None):
        data = _ensure_list(data)
        rich_core.AssertKlass(data, collections.MutableSequence, name='data')
        
        # If name misisng, using the first entry in data
        if name == None:
            assert(len(data) > 0), "If 'name' not provided, data must be non-empty."
            name = data.pop(0)
        else:
            name = name
        
        # If name exists in data, remove it.
        try:
            data.pop(data.index(name))
        except ValueError:
            pass        
        
        return name, data
    
    def _validate_data(self, data, name=None):
        """
        Difference between _validate(data, name=None) and _validate_data(data)
            is _validate_data *assumes* it will pop off the front to make a name
        """
        #[] Process name - if not provided, extract from data
        #[] Assign remaining to aliases
        return self._validate_name(name), self._validate_aliases(aliases)
    
    
    #Special case for delitem: if length == 1, ie consists only of name    
    @property
    def data(self):
        return [self._name] + self._data
    @data.setter
    def data(self, value):
        self._data = value
    @data.deleter
    def data(self):
        del self._data
    @property
    def aliases(self):
        return self._data
    
    

class BasicEnumGroup(EnumGroupInterface, rich_collections.BasicSequence):
    """Very simple. Only consists of name."""
    #def __init__(self, data, name=None):
    def __init__(self, *data, **kwargs):
        """name is an unused keyword in BasicEnumGroup."""
        self.data = data
    def __eq__(self, other):
        return (self.data == other)


    #@todo: self._validate_name, self._validate_aliases
    #-- Getters
    @property
    def data(self):
        return tuple([self.name]) + self.aliases
    @data.setter
    def data(self, value):
        self.name, self.aliases = self._validate_data(value)
    @data.deleter
    def data(self):
        del self.name
        del self.aliases
    def _validate_data(self, data):
        rich_core.AssertKlass(data, rich_core.NonStringSequence, name='data')
        assert(len(data) == 1), "'data' must be length 1."
        return data[0], tuple() #name, aliases
    
    @property
    def aliases(self):
        return self._aliases
    @aliases.setter
    def aliases(self, value):
        self._aliases = self._validate_aliases(value)
    @aliases.deleter
    def aliases(self):
        del self._aliases
    def _validate_aliases(self, aliases):
        rich_core.AssertKlass(aliases, rich_core.NonStringSequence, name='aliases')
        return aliases
        

#------------------------------------------------------------------------------
#    Local Utility Functions
#------------------------------------------------------------------------------
def _ensure_list(value):
    """Return value as a list; if not a NonStringSequence, wraps in a list."""
    if isinstance(value, list):
        return value
    elif isinstance(value, rich_core.NonStringSequence):
        return list(value)
    else:
        return [value]





import unittest
import operator
class BasicEnumGroupTests(unittest.TestCase):
    constructor = BasicEnumGroup
    def setUp(self):
        self.g1a = self.constructor('attempting')
        self.g1b = self.constructor('attempting')
        self.g1c = self.constructor('attempting')
        self.g2  = self.constructor('attempt')
        
    def test_group_equality(self):

        
        self.assertEqual(self.g1a, self.g1b)
        self.assertEqual(self.g1a, self.g1c)
        self.assertEqual(self.g1b, self.g1c)
        self.assertNotEqual(self.g1a, self.g2)
        
        
        
    def test_contains(self):
        self.assert_(
            'attempt' not in self.g1a
        )
        self.assert_(
            'attempt' in self.g2
        )
        self.assert_(
            'non' not in self.g1a
        )
    def test_name(self):
        self.assertEqual(self.g1a.name, 'attempting')
        self.assertEqual(self.g1b.name, 'attempting')
        self.assertEqual(self.g2.name, 'attempt')
    def test_string_comparison(self):
        pass
    def test_errors(self):
        self.assertRaises(TypeError, lambda: self.g1a['attempting'])
        self.assertRaises(IndexError, lambda: self.g1b[1])
        self.assertRaises(TypeError, lambda: operator.delitem(self.g1c, 0) )


class EnumGroupTests(unittest.TestCase):
    constructor = EnumGroup
    def setUp(self):
        self.g1a = self.constructor(('attempting',))
        self.g1b = self.constructor(['attempting'])
        self.g1c = self.constructor('attempting',)
        self.g2  = self.constructor('attempt',)
    def test_group_equality(self):
        self.assert_(self.g1a == self.g1b)
        self.assert_(self.g1a == self.g1c)
        self.assert_(self.g1b == self.g1c)
        self.assert_(self.g1a != self.g2)
    def test_contains(self):
        self.assert_(
            'attempt' not in self.g1a
        )
        self.assert_(
            'attempt' in self.g2
        )
        self.assert_(
            'non' not in self.g1a
        )
    def test_name(self):
        self.assertEqual(self.g1a.name, 'attempting')
        self.assertEqual(self.g1b.name, 'attempting')
        self.assertEqual(self.g2.name, 'attempt')
    def test_string_comparison(self):
        pass
    def test_errors(self):
        self.assertRaises(TypeError, lambda: self.g1a['attempting'])
        self.assertRaises(IndexError, lambda: self.g1b[1])

        
class EnumTests(unittest.TestCase):
    def setUp(self):
        self.States = Enum((
            ('attempting', 'attempt','attempted'),
            ('errored', 'error'),
            ('completed', 'complete')
        ))
        self.expected = [
            ['attempting', 'attempt','attempted'],
            ['errored', 'error'],
            ['completed', 'complete']
        ]
        self.groups = [
            EnumGroup(['attempting', 'attempt','attempted']),
            EnumGroup(['errored', 'error']),
            EnumGroup(['completed', 'complete'])
        ]
    
    def test_getitem_repr(self):
        state = self.States['attempting']
        self.assert_(isinstance(state, EnumGroup), 
            "Is not instance of EnumGroup"
        )
        self.assertEqual(
            repr(state),
            "['attempting', 'attempt', 'attempted']",
            "States does not match repr of expectation."
        )

    
    def test_iter(self):
        names = ['attempting','errored','completed']
        for state, name, expected in zip(self.States,self.States.names, names):
            self.assert_(
                state.name == name == expected,
                "Inequality among: {0}, {1}, {2}".format(
                    state.name, name, expected
                )
            )
                
    def test_group_comparison(self):
        #For Enum
        self.assertEqual(
            self.States,
            self.groups,
            "States does not match expected groups"
        )
        
        #Group comparison
        self.assertEqual(
            self.States['attempting'],
            EnumGroup(['attempting', 'attempt','attempted']),
            "group comparison"
        ) 
    def test_string_comparison(self):
        #For Enum collection
        self.assertEqual(
            self.States,
            self.expected,
            "Enum() does not match expectation"
        )
        
        #For single groups
        compared = all(
            (exp == state)
            for exp, state in zip(self.expected, self.States)
        )
        
        self.assert_(compared, "Iterator failed.")       
        
        self.assertEqual(
            list(elm for elm in self.States),
            self.expected,
            "Groups from iter do not match expectations."
        )
        
        
        
        
    #def test_group_containment(self):
    #   States['attempting'] in States
    #def test_string_containment(self):
    #   'attempting' in States

#     def test_corner_case(self):
#         Problems = Enum([
#             (2,),
#             (1,),
#             ('c',)
#         ])
#         Problems['2']
#         print(Problems[1])
#         import pdb
#         pdb.set_trace()
#         print(Problems[1])

if __name__ == "__main__":
    unittest.main()