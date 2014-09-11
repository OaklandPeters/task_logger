import pdb
import abc
import os
#----
from local_packages import rich_operator
from local_packages import rich_core
#----

from logger import JSONProgressLog, ProcessingAttempt, States, ProcessLogger
from data import read_dir, CompoundDataSet




    


class Reviewer(object):
    __metaclass__ = rich_operator.OperatorMeta
    
    def __call__(cls, **keywords):
        name, directory, logpath = cls.validate(**keywords)
        
        print("Reviewing log for {0},\n    at: {1}\n\n".format(name, logpath))

        with JSONProgressLog(logpath) as log:            
            pdb.set_trace()
            print('--')
        
        
    def validate(cls, name, directory, log, **extra):
        rich_core.AssertType(name, (basestring, ), name='name')
        AssertDirectory(directory, name='directory')
        AssertFile(log, name='log')
        return name, directory, log


def AssertDirectory(obj, name=None):
    rich_core.AssertKlass(obj, (basestring, ), name=name)
    assert(os.path.isdir(obj)), ("Directory path is invalid: "+obj)
    return obj

def AssertFile(obj, name=None):
    rich_core.AssertKlass(obj, (basestring, ), name=name)
    assert(os.path.isfile(obj)), ("File is invalid")
    return obj


def review(log, fields=None):
    if fields == None:
        fields = ('state','stopped','elapsed')
    rich_core.AssertType(fields, (collections.Sequence, ), name='fields')
    for i, elm in enumerate(fields):
        rich_core.AssertType(elm, (basestring, ), name='fields['+str(i)+']')
    
    
    for i,(key, attempt) in enumerate(log.items()):
        print("Attempt #{0}: {1}".format(i, key))
        msg = "    "
        field_msgs = [
            "{0}: {1}".format(field, attempt[field])
            for field in fields
            if field in attempt
        ]
        msg += ", ".join(field_msgs)
        print(msg)

def pluck(log, field):
    return [
        attempt[field]
        for attempt in log.values()
        if field in attempt
    ]



#--------------- Local Utility--------------
def _hasattr(subklass, attr):
    """Determine if subklass, or any ancestor class, has an attribute.
    Copied shamelessly from the abc portion of collections.py.
    """
    try:
        return any(attr in B.__dict__ for B in subklass.__mro__)
    except AttributeError:
        # Old-style class
        return hasattr(subklass, attr)





if __name__ == "__main__":

    #
    enami = {
        'name':'enami', 
        'directory':"/data/htdocs/cccid/build/compounds-db/data-files/enami/",
        'log':"/data/htdocs/cccid/build/compounds-db/data-files/enami/awk-sourcedata-insertion-log.json",
    }
    
    Reviewer(**enami)
    
    print("Left reviewer....")
    
    print("Left reviewer....")