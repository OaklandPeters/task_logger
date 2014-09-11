"""
Import the virtual chemistry dataset, from files containing both 
(1) a range of chemoinformatic properties, and 
(2) sourcename / sourceid information
"""
from abc import ABCMeta, abstractmethod, abstractproperty
import collections
import datetime
import fnmatch
import os
#----
from local_packages.mysql import MySQL
# import local_packages.rich_core as rich_core
# import local_packages.vproperty as vproperty
# import local_packages.rich_collections as rich_collections
# import local_packages.rich_property as rich_property
from local_packages import rich_core
from local_packages import rich_collections
from local_packages import rich_property
#----
from cccid_setup import CCCIDConfiguration



jcman_examples = """
ALSO WORKS:
jcman c pre_cache_579c76r6m5c1jmnsjb3q191075 --bits 2 --coldefs "sourcename varchar(200), sourceid varchar(200), exactmass double(20,10), formula varchar(40), charge varchar(400), polarizability varchar(400), bondcount double(20,10), chiralcentercount double(20,10), molecularsurfacearea double(20,10), polarsurfacearea double(20,10), rotatablebondcount double(20,10), topologyanalysistable varchar(200), vdwsa double(20,10), wateraccessiblesurfacearea varchar(200), logd text, logp varchar(100), chargedistribution text, pi double(20,10), pka varchar(200), acceptorcount double(20,10), chargedensity varchar(200), donorcount double(20,10), electrondensity varchar(200), refractivity double(20,10), totalchargedensity varchar(200)" --fplength 1024 --bonds 8

cmd_parts = ['jcman', 'c', 'pre_cache_579c76r6m5c1jmnsjb3q191075', '--bits', '2', '--coldefs', '", sourcename varchar(200), sourceid varchar(200), exactmass double(20,10), formula varchar(40), charge varchar(400), polarizability varchar(400), bondcount double(20,10), chiralcentercount double(20,10), molecularsurfacearea double(20,10), polarsurfacearea double(20,10), rotatablebondcount double(20,10), topologyanalysistable varchar(200), vdwsa double(20,10), wateraccessiblesurfacearea varchar(200), logd text, logp varchar(100), chargedistribution text, pi double(20,10), pka varchar(200), acceptorcount double(20,10), chargedensity varchar(200), donorcount double(20,10), electrondensity varchar(200), refractivity double(20,10), totalchargedensity varchar(200)"', '--fplength', '1024', '--bonds', '8']
"""



class CompoundDataSetABC(collections.MutableSequence):
    __meta__ = ABCMeta
    name = abstractproperty()
    filepaths = abstractproperty()
    

class CompoundDataSet(CompoundDataSetABC, rich_collections.BasicMutableSequence):
#class CompoundDataSet(CompoundDataSetParent):
    __meta__ = ABCMeta
    
    def __init__(self, filepaths=None, name=None):
        self.name = name
        self.filepaths = filepaths

    #----------------------------------------------------------------
    #        Properties
    #----------------------------------------------------------------
    @rich_property.VProperty
    class filepaths(object):
        """(MutableSequence of basestring).
        The paths of all files in this dataset."""
        def getter(self):
            return self._filepaths
        def setter(self, filepaths):
            self._filepaths = filepaths
        def deleter(self):
            del self._filepaths
        def validator(self, filepaths):
            if filepaths == None:
                raise TypeError("'filepaths' can not be None.")
            rich_core.AssertKlass(filepaths, rich_core.NonStringSequence, name='filepaths')
            for i, elm in enumerate(filepaths):
                rich_core.AssertKlass(elm, basestring, name='filepaths[{0}]'.format(i))
                assert(os.path.exists(elm)), str.format(
                    "filepaths[{0}]=='{1}' does not exist.", i, elm
                )
                assert(os.path.isfile(elm)), str.format(
                    "filepaths[{0}]=='{1}' is not a file.", i, elm
                )
            return filepaths
    #----- Name property
    @rich_property.VProperty
    class name(object):
        """(basestring). Name for this dataset."""
        def getter(self):
            return self._name
        def setter(self, value):
            self._name = value
        def deleter(self):
            del self._name
        def validator(self, value):
            if value == None:
                value = ''
            rich_core.AssertKlass(value, basestring, name='name')
            return value
    data = filepaths

class CompoundDataFile(object):
    """
    Not yet sure what this should or be used for.
    PROBABLY holding the same information that should go into an 'attempt'
    in the progress-log-file.
    """
    pass


class SDFDataSet(CompoundDataSet):
    """
    CompoundDataSet customized to importing SDF files for the CCCID project.
    """
    #----------------------------------------------------------------
    #        Mixins
    #----------------------------------------------------------------
    def __enter__(self):
        self.cccid = CCCIDConfiguration()
        self.cccid.__enter__()
        
        self.cxn = MySQL(config=self.cccid.config['python_mysql_config'])
        self.cxn.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            self.cxn.__exit__(exc_type, exc_value, exc_traceback)
        except Exception as exc:
            #Should really throw a warning here
            pass
        try:
            self.cccid.__exit__(exc_type, exc_value, exc_traceback)
        except Exception as exc:
            #Should really throw a warning here
            pass
        
        
        if exc_traceback == None:
            # No exception
            return True
        else:
            # Exception -- re-raise it
            return False





#==============================================================================
#        Local Utility functions
#==============================================================================
def _get_default(mapping, key, default):
    # dict.get() except, also returns default if value is None
    rich_core.AssertKlass(mapping, collections.Mapping, name="mapping")
    if key not in mapping:
        return default
    elif mapping[key] == None:
        return default
    else:
        return mapping[key]

def read_dir(folder, match=None):
    """Return full path names for all files in 'folder', optionally
    which match a Unix-style wildcard string."""
    rich_core.AssertKlass(folder, basestring, name='folder')
    rich_core.AssertKlass(match, (type(None), basestring), name='match')
    
    names = os.listdir(folder)
    if match:
        names = fnmatch.filter(names, match)
    
    for name in names:
        yield folder+name

def make_data_set(name, directory, match, **kwargs):
    """kwargs are unused."""    
    return CompoundDataSet(
        name = name,
        filepaths = list(read_dir(
            directory,
            match=match
        ))
    )