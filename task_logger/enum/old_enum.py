"""
Python 2.6 replacement for Enum() from Python 3.4+.
Essentially organizes name/alias classes.

"""
import copy
import collections
#----
import local_packages.rich_core as rich_core


#class StringEnum(object):
class Enum(collections.MutableMapping):
    """Basically, an enumerator (Enum: which only exist in Python 3.4).
    But provides access via mapping/keys, not methods.
    Stores data internally as a dict.

    See enum_test.py for example syntax.
    """
    def __init__(self, *states, **options):
        """Initialize groups, and apply possible options. Options
        simplifers:
        default:
        """
        self.groups = dict(states)

        self.simplifiers = options.get('simplifiers', Enum._simplifiers)
        if 'default' in options:
            self._default = options 
        
    #----------------------------------------------------------------
    #    Properties
    #----------------------------------------------------------------
    def _groups_getter(self):
        """Get all name/alias groups."""
        return self._groups
    def _groups_setter(self, mapping):
        """Set name/alias groups. Must be a mapping."""
        self._groups = self._validate_groups(mapping)
    _groups = []
    groups = property(_groups_getter, _groups_setter)
     
    def _names_getter(self):
        """Get names (~keys) for all groups."""
        return self.groups.keys()
    names = property(_names_getter)
    def name(self, key):
        """Find name for a group matching key."""
        return 
    
     
    def _aliases_getter(self):
        """Get aliases (~values) for all groups."""
        return self.groups.values()
    aliases = property(_aliases_getter)
    
    
    def _default_getter(self):
        return self._default
    def _default_setter(self, value):
        self._default = value
    def _default_deleter(self):
        del self._default
    default = property(_default_getter, _default_setter, _default_deleter)
    
#     _groups = []
#     @property
#     def groups(self):
#         """Get all name/alias groups."""
#         return self._groups
#     @groups.setter
#     def groups(self, mapping):
#         """Set name/alias groups. Must be a mapping."""
#         self._groups = self._validate_groups(mapping)
#     @property
#     def names(self):
#         return self.groups.keys()
#     @property
#     def aliases(self):
#         return self.groups.values()

    def items(self):
        return self.groups.items()
    def keys(self):
        return self.groups.keys()
    def values(self):
        return self.groups.values()
    #---------------------------------------------------------------- 
    #    MutableMapping Magic Methods
    #----------------------------------------------------------------
    def __getitem__(self, name):
        """Returns name (~key) if found, else raises key error.
        Note: UNLIKE normal dicts/mappings, this does NOT return the
        set of aliases (~values).
        """
        
        try:
            # Check group names (keys) - return aliases
            return self.check_names(name)[1]
        except KeyError:
            try:
                # Check group aliases (values) - return aliases
                return self.check_aliases(name)[1]
            except KeyError:
                try:
                    # Check for a default
                    return self.default
                except AttributeError:
                    raise KeyError(name)
        
#         if key in self.groups.keys():
#             return key
#         # Check group aliases (values)
#         else:
#             return self.__missing__(key)

    def __setitem__(self, key, value):
        self.groups[key] = self._validate_group(key, value)
    def __delitem__(self, key):
        del self.groups[key]
    def __iter__(self):
        return iter(self.groups)
    def __len__(self):
        return len(self.groups)
    #----------------------------------------------------------------
    #    More Magic Methods
    #----------------------------------------------------------------
    def __missing__(self, name):
        """ If self[name] not found by self.__getitem__(name).
        Simplifies name before comparing.
        
        @todo: Make this handle a self.default
        """
        
        raise KeyError(name)
        
#         if hasattr('default', self):
#             return self[self.default]
#         else:
#             raise KeyError(name)
    
    def __contains__(self, name):
        """ Magic method for 'in'/'not in': ('elm' in Enum())."""
        try:
            # Check group names (~keys)
            self.check_names(name)
            return True
        except KeyError:
            try:
                # Check group aliases (~values)
                self.check_aliases(name)
                return True
            except KeyError:
                return False
    def __repr__(self):
        return repr(self.groups)
    
    #----------------------------------------------------------------
    #    Private processing
    #----------------------------------------------------------------
    def _validate_groups(self, mapping):
        """Confirm that mapping is a valid groups mapping,
        and return the version with adjustments."""
        rich_core.AssertKlass(mapping, collections.Mapping, name='mapping')
        return dict(
            self._validate_group(key, value)
            for key, value in mapping.items()
        )
    def _validate_group(self, key, value):
        """Confirm that (key, value) for a single group is valid,
        and return (key,value) with any adjustements."""
        new_value = list(rich_core.ensure_tuple(value))
        if key not in new_value:
            new_value = new_value + list(rich_core.ensure_tuple(key))
        #Ensure all aliases are in simplified form:
        new_value = [self.simplify(elm) for elm in new_value]
        return (key, new_value)

    def find_group(self, name):
        """Find group matching 'name' (against names or simplified aliases).
        Then return as (name, aliases) pair.
        """
        try:
            # Check group names (keys) - return aliases
            return self.check_names(name)
        except KeyError:
            try:
                # Check group aliases (values) - return aliases
                return self.check_aliases(name)
            except KeyError:
                # Checking __missing__ may go here
                raise KeyError(name)
    def check_names(self, name):
        """Find and return name if contained in groups' names"""
        if name in self.groups.keys():
            return (name, self.groups[name])
        raise KeyError(name)
    def check_aliases(self, name):
        """Find and return name if contained in groups' aliases."""
        simplified_name = self.simplify(name)
        for group_name, group_aliases in self.groups.items():
            if simplified_name in group_aliases:
                return (group_name, group_aliases)
        raise KeyError(simplified_name)
    
    #----------------------------------------------------------------
    #    Simplifying Keys
    #----------------------------------------------------------------

    def _simplifiers_getter(self):
        """Retreive key simplifier functions."""
        if not hasattr(self, '_simplifiers'):
            self._simplifiers = Enum._simplifiers
        return self._simplifiers
    def _simplifiers_setter(self, value):
        """Validate and assign key simplifiers.
        Should be a Non-String Sequence of Callables."""
        value = rich_core.ensure_tuple(value)
        rich_core.AssertKlass(value, rich_core.NonStringSequence, name='value')
        for i, elm in enumerate(value):
            rich_core.AssertKlass(elm, collections.Callable,
                name="element #{0} of value.".format(i)
            )
        self._simplifiers = value
#     Default Simplifier functions.
#         Will be overridden by instance-specific version. Defaults:
#            1. Convert to lower case
#            2. Replace hyphens with underscores
#            3. Replace spaces with underscores
    _simplifiers = [
        lambda obj: obj if not isinstance(obj, basestring) else obj.lower(),
        lambda obj: obj if not isinstance(obj, basestring) else obj.replace('-','_'),
        lambda obj: obj if not isinstance(obj, basestring) else obj.replace(' ','_'),
    ]
    simplifiers = property(_simplifiers_getter, _simplifiers_setter)
    
#     @property
#     def simplifiers(self):
#         """Retreive key simplifier functions."""
#         if not hasattr(self, '_simplifiers'):
#             self._simplifiers = Enum._simplifiers
#         return self._simplifiers
#     @simplifiers.setter
#     def simplifiers(self, value):
#         """Validate and assign key simplifiers.
#         Should be a Non-String Sequence of Callables."""
#         value = rich_core.ensure_tuple(value)
#         rich_core.AssertKlass(value, rich_core.NonStringSequence, name='value')
#         for i, elm in enumerate(value):
#             rich_core.AssertKlass(elm, collections.Callable,
#                 name="element #{0} of value.".format(i)
#             )
#         self._simplifiers = value
    def simplify(self, key):
        """Simplify a key, using functions in self.simplifiers property."""
        newkey = copy.deepcopy(key)
        for _func in self.simplifiers:
            #old = copy.deepcopy(newkey)
            old = newkey
            try:
                newkey = _func(newkey)
            # Catch likely errors, while not catching Exceptions like
            # CTRL-C, StopIteration(), etc (which should pass through)
            except (AttributeError, TypeError, KeyError, IndexError):
                newkey = old
        return newkey





class StringEnum(Enum):
    """Enum() subclass which requires names and aliases to be strings."""
    def _validate_group(self, key, value):
        """Ensure that keys and values are basestrings, and invokes validation
        from parent (Enum._validate_group())."""
        rich_core.AssertKlass(key, basestring, name='key')
        rich_core.AssertKlass(value, rich_core.NonStringSequence, name='value')
        for i, elm in enumerate(value):
            rich_core.AssertKlass(elm, basestring, name='element #{0} of value'.format(i))

        return Enum._validate_group(self, key, value)
    

