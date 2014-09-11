"""

@TODO: ProcessLogger().attempts - update/interact based on __enter__/__exit__
@TODO: Review ProcessLoggerABC, and make ProcessLogger inherit from it
@TODO: ProcessingAttempt: make uncaught exception in switch_on_exit() cause parent
    to close all other attempts.

@TODO: Write ProcessLoggerABC in task_logger/. Then switch .validate()
    from checking if log is JSONProgressLog() to ProcessLoggerABC().
    ProcessLoggerABC() needs to be MutableMapping + ability to close attempts.
"""


import os
import collections
import json

import traceback
import datetime
#----
from local_packages import rich_core
from local_packages import rich_collections
from local_packages import rich_property
#---- Local Modules
import enum #local version of enum
import pa_exceptions


LOGGER_SUPPRESSES_ERRORS = True







class JSONProgressLog(rich_collections.BasicMutableMapping):
    """
    ~(1) MutableMapping 
    + (2) ability to read/write to file
    + (3) recursive getters/setters/deleters
    + (4) recursive setters should automatically create nested structure
        As in rich_misc.defaultlist
        ex. log = JSONProgressLog()
            log['import-expanded']['virtual-chemistry-01'][3] = AttemptRecord(...)
            --> will automatically create the structure for 
                self.data['import-expanded'] = {}
                self.data['import-expanded']['virtual-chemistry-01'] = []
                expand_list(self.data['import-expanded']['virtual-chemistry-01'], 3)
                self.data['import-expanded']['virtual-chemistry-01'][3] = AttemptRecord(...)

    """

    def __init__(self, logpath=None):
        if logpath == None:
            self.logpath = 'default-log.json'
        else:
            self.logpath = logpath

        self.data = None #Default until opened
        self.opened = False


    def open(self):
        try:
            self.data = self.read()
        except ValueError as exc:
            #File found, but 'No JSON object could be decoded'
            #Create and initialize the log file
            self.write({})
            self.data = self.read()
        except IOError as exc:
            #Usually: 'No such file or directory'
            #Create and initialize the log file
            self.write({})
            self.data = self.read()
        self.opened = True
        return self
        
    def close(self):
        #This should check that all attempts are closed
        self.write(self.data)
        #self.data = None
        self.opened = False
        return self
        
    def read(self):
        """Return dict of data in self.logpath:
        {
            (*args):{attempt-record},
            ...
        }
        """
        with open(self.logpath, mode='r') as fi:
            raw = json.load(fi)
        _unserialized = self.unserialize(raw)
        #Unpack nested structures
        return _convert_to_string(_unserialized)        
        
    def write(self, data=None):
        """Write 
        """ 
        if data == None:
            data = self.data
        with open(self.logpath, mode='w') as fi:
            json.dump(self.serialize(data), fi, indent=1)
            
        return self
    
    

    #-------- Context Manager
    def __enter__(self):
        self.open()
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()
    #----------- Serialization so it can be stored as JSON array
    def serialize(self, data=None):
        """Translate data dictionary into JSON object of array of key-value pairs."""
        if data == None:
            data = self.data
        rich_core.AssertKlass(data, collections.Mapping, name='data')
        return {
            'log': [[key, value] for key, value in data.items()]
        }
    def unserialize(self, raw):
        """Translate JSON array of key-value pairs into a dict."""
        rich_core.AssertKlass(raw, collections.Mapping, name='raw')
        rich_core.AssertKeys(raw, ['log'], name='raw')            
        rich_core.AssertKlass(raw['log'], collections.Sequence, name="raw['log']")
        return dict(
            #(rich_core.ensure_tuple(key), value)
            (seq2tuple(key), value)
            for key, value in raw['log']
        )
    
    #---- Overriding BasicMutableMapping
    @rich_collections.BasicMutableMapping.data.validator
    def data(self, data):
        rich_core.AssertKlass(data, (collections.MutableMapping, type(None)), name='data')
        return data
    def __getitem__(self, key):
        try:
            return self.data[key]
        except TypeError as exc:
            raise KeyError(
                "'{0}' not found, likely because log file is not open.".format(key))
    def __setitem__(self, key, value):
        try:
            self.data[key] = value
        except TypeError as exc:
            raise KeyError(
                "'{0}' not found likely because log file is not open.".format(key))
    def __delitem__(self, key):
        try:
            del self.data[key]
        except TypeError as exc:
            raise KeyError(
                "'{0}' not found likely because log file is not open.".format(key))












    
    



# States used to track state of ProcessingAttempt
States = enum.Enum([
    ('new','untried'),
    ('completed','complete','done','finished'),
    ('errored','error','exception','stopped'),
    ('attempting','attempted','in progress','in_progress','running')
])
    

class ProcessingAttempt(rich_collections.BasicMutableMapping):
    """
    Records and tracks a single attempt to apply processing to a single set
    of input arguments. Translates to a single record in the log.
    
    This class exists as a subject-class to ProcessLogger.
    
    
    @TODO: Consider whether initial data should be included. I suspect not.
    @TODO: Consider difficult issue: in switch_on_exit(): NonSuppressedError()
        - should it trigger an event in the parent log(), to close out of all
        other open attempts before raising that error?
    
    @TODO: Make the exception catching functionality ALSO catch on KeyboardInterrupt
    """
    def __init__(self, log, arguments, data=None):
        """Memoize on arguments.
        log should be a log, treatable as a MutableMapping
        data is initial values for the processing attempt's record
            self.data is copied back to self.log[self.arguments], upon __exit__
        """
        
        
        
        self.open = False
        self.started = datetime.datetime.now()
        (self.log,
        self.arguments,
        self.data) = self.validate(log, arguments, data)

    
    def validate(self, log, arguments, data):
        #rich_core.AssertKlass(log, task_logger.ProcessLoggerABC, name='log')
        rich_core.AssertKlass(log, collections.MutableMapping, name='log')
        
        # Revised: ensure that arguments are something Hashable
        #    But do not insist they are a tuple, allows for arguments being a string
        rich_core.AssertKlass(arguments, collections.Hashable, name='arguments')
        
        if data == None:
            #data = rich_core.defaults(self.data, self.new_record())
            data = {}
        else:
            rich_core.AssertKlass(data, collections.MutableMapping, name='data')
            
        return log, arguments, data
    
    def __enter__(self):
        """Entering 'with' context manager.
        Some initialization of keys handled here; however - initialization the Mapping
        (self ~ self.data) occurs in in the data property getter.
        """
        self.open = True
        
        #defs = rich_core.defaults(self.data, self.new_record())
        #self.update(defs)

        if 'state' not in self:
            self['state'] = States['new'].name
        self.switch_on_enter(self['state'])
          
        return self
         
    def __exit__(self, exc_type, exc_value, exc_traceback):
        """            
        """
        self.open = False
        self.elapsed()
        self.switch_on_exit(exc_type, exc_value, exc_traceback)
        return True     # Suppress exception
    #-------
    def elapsed(self):
        """Record time elapsed in processing."""
        self.stopped = datetime.datetime.now()
        self['started'] = str(self.started)
        self['stopped'] = str(self.stopped)
        self['elapsed'] = str(self.stopped - self.started)
    #------ Converting try_func(func, args, log)
    def switch_on_enter(self, state):         
        if state in States['new']:
            #Continue to processing
            pass
        elif state in States['attempting']:            
            #Interrupt processing
            raise pa_exceptions.AttemptAlreadyInProgress(state)
        elif state in States['completed']:            
            #Interrupt processing
            raise pa_exceptions.AttemptPreviouslyCompleted(state)
        elif state in States['errored']:
            #Continue to processing
            pass
        else:
            raise ValueError("Inappropriate state value. Should be: "+str(States.names))
            
    def switch_on_exit(self, exc_type, exc_value, exc_traceback):
        """
        Note: The parent's log is automatically updated by self/self.data's setter.
        """    
        if exc_type == None:            
            #No error encountered
            self['state'] = States['completed'].name
            return True     # Suppress exception in __exit__
        elif issubclass(exc_type, pa_exceptions.AttemptAlreadyInProgress):
            #Attempt already in progress for this combination of arguments
            self['state'] = States['attempting'].name
            return True     # Suppress exception in __exit__
        elif issubclass(exc_type, pa_exceptions.AttemptPreviouslyCompleted):
            #Attempt previous completed
            self['state'] = States['completed'].name
            return True     # Suppress exception in __exit__
        elif issubclass(exc_type, pa_exceptions.NonSuppressedError):
            #Record exception, and raise the exception
            self._original_close_errored(exc_type, exc_value, exc_traceback)
            
            # FUTURE: close all other attempts of parent-log
            #self.log.close_attempts()
            
            raise exc_type, exc_value, exc_traceback
        else:
            #Other exception type - record as error, and suppress the exception
            self._original_close_errored(exc_type, exc_value, exc_traceback)
            if LOGGER_SUPPRESSES_ERRORS:
                return True     # Suppress exception in __exit__
            else:
                raise exc_type, exc_value, exc_traceback    #re-raise error
    def _original_close_errored(self, exc_type=None,exc_value=None,exc_traceback=None):
        """Close as if an exception was thrown."""
        if exc_type == None:
            exc_type = pa_exceptions.AttemptCanceled
        if exc_value == None:
            exc_value = ""
        if exc_traceback == None:
            exc_traceback = traceback.print_stack()
        
        self['state'] = States['errored'].name
        self['exc_type'] = exc_type.__name__
        self['exc_value'] = str(exc_value)
        self['exc_traceback'] = '\n'.join(traceback.format_tb(exc_traceback))
    

    
    
    
    
    
            
    #==========================================================================
    #    Closer
    # --> Cancelled because of complexity and time-constraints
    #==========================================================================
    
#     def close(self, exc_type=None, exc_value=None, exc_traceback=None):
#         return _Close(self, exc_type, exc_value, exc_traceback)
#         
#     class _Close(object):
#         """Operator class, to organize functionality for closing.
#         ... which has become complicated."""
#         def __new__(cls, parent, exc_type=None, exc_value=None, exc_traceback=None):
#             cls.shared(parent)
#             func = self.dispatch(exc_type)
#             result = func(parent, exc_type, exc_value, exc_traceback)
#             return result
#         @classmethod
#         def shared(cls, parent):
#             pass
#         @classmethod
#         def dispatch(cls, exc_type):
#             pass
        
    
    
#     def close(self, exc_type=None,exc_value=None,exc_traceback=None):
#         """
#         @todo Handle possibility of:
#             attempt.close(ValueError('Invalid user id.'))
#         """
#         print(exc_type)
#         import pdb
#         pdb.set_trace()
#         print(exc_type)
#         
#         self._close_shared()
#         
#         close_func = self._close_dispatch(exc_type)
#         
#         print(close_func)
#         pdb.set_trace()
#         print('--')
#         
#         
#         result = close_func(exc_type, exc_value, exc_traceback)
#         
#         print(result)
#         import pdb
#         pdb.set_trace()
#         print(result)
#         
#         return result
#         
#         return close_func(exc_type, exc_value, exc_traceback)
# 
#     def _close_shared(self):
#         self.opened = False
#         self.stopped = datetime.datetime.now()
#         self['started'] = str(self.started)
#         self['stopped'] = str(self.stopped)
#         self['elapsed'] = str(self.stopped - self.started)
#     def _close_dispatch(self, exc_type):
#         #Dispatch on exc_type    
#         if exc_type == None:
#             self._close_completed
#         elif issubclass(exc_type, pa_exceptions.AttemptPreviouslyCompleted):
#             self._close_completed
#         elif issubclass(exc_type, pa_exceptions.AttemptAlreadyInProgress):
#             self._close_attempting
#         elif issubclass(exc_type, pa_exceptions.NonSuppressedError):
#             return self._close_nonsuppressed_error
#         else:
#             return self._close_suppressed_error
# 
# 
#         
#     def _close_errored(self, exc_type=None,exc_value=None,exc_traceback=None):
#         """Close as if an exception was thrown."""
#         self['state'] = States['errored'].name
#         self['exc_type'] = exc_type.__name__
#         self['exc_value'] = str(exc_value)
#         self['exc_traceback'] = '\n'.join(traceback.format_tb(exc_traceback))
#         
#     def _close_suppressed_error(self, exc_type, exc_value, exc_traceback):
#         # set record in log (~self)
#         self._close_errored(exc_type, exc_value, exc_traceback)
#         exc_type, exc_value, exc_traceback = self._validate_close_errored(
#             exc_type, exc_value, exc_traceback
#         )
#         if LOGGER_SUPPRESSES_ERRORS:
#             return True     # Suppress exception in __exit__
#         else:
#             raise exc_type, exc_value, exc_traceback    #re-raise error
#     def _close_nonsuppressed_error(self, exc_type, exc_value, exc_traceback):
#         """Always raises exception."""
#         # set record in log (~self)
#         self._close_errored(exc_type, exc_value, exc_traceback)
#         exc_type, exc_value, exc_traceback = self._validate_close_errored(
#             exc_type, exc_value, exc_traceback
#         )
#         raise exc_type, exc_value, exc_traceback    #re-raise error
#         
#     def _validate_close_errored(self, exc_type, exc_value, exc_traceback):
#         if exc_type == None:
#             exc_type = pa_exceptions.AttemptCanceled
#         elif isinstance(exc_type, Exception):
#             #If exc_type is an INSTANCE of Exception, rather than a type 
#             if exc_value == None:
#                 exc_value = str(exc_type)
#             exc_type = type(exc_type)
#         
# 
#         if exc_value == None:
#             exc_value = ""
#         if exc_traceback == None:
#             exc_traceback = traceback.print_stack()
#         return exc_type, exc_value, exc_traceback
# 
#     def _close_completed(self):
#         self['state'] = States['completed'].name
#         return True # Suppress exception in __exit__
#     def _close_attempted(self):
#         self['state'] = States['attempted'].name
#         return True # Suppress exception in __exit__
    
    #==========================================================================
    #---- Overriding BasicMutableMapping for .data
    @rich_property.VProperty
    class data(object):
        """(MutableMapping). Holds contents of attempt, via reference to 
        parent log. Over-rides BasicMutableMapping behavior for .data, thus all
        Mapping-like behavior references this."""
        def getter(self):
            """Reference's parent log, creating a new entry if necessary."""
            if self.arguments not in self.log:
                self.log[self.arguments] = self.new_record()
            return self.log[self.arguments]
        def setter(self, data):
            """Set corresponding value inside parent log."""
            self.log[self.arguments] = data
        def deleter(self):
            del self.log[self.arguments]
        def validator(self, data):
            if data == None:
                return {}
            else:
                rich_core.AssertKlass(data, collections.MutableMapping, name='data')
                return data
    
#     @vproperty.VProperty
#     def data(self):
#         #Create entry in parent log, if necessary
#         if self.arguments not in self.log:
#             self.log[self.arguments] = self.new_record()
#         return self.log[self.arguments]
#     @data.setter
#     def data(self, data):
#         self.log[self.arguments] = data
#     @data.deleter
#     def data(self):
#         del self.log[self.arguments]
#     @data.validator
#     def data(self, data):
#         if data == None:
#             return {}
#         else:
#             rich_core.AssertKlass(data, collections.MutableMapping, name='data')
#             return data
    def new_record(self):
        """Create a new record, with default keys set."""
        return {'state':States['new'].name}
    #----------
    def summary(self):
        """Print a summary of the state of this attempt."""
        return _summarize_attempt(self.log[self.arguments], self.arguments)
       







class ProcessLogger(JSONProgressLog):
    """
    ~ JSONProcessLog()
    + (1) functions dealing with the task/file/attempt structure
    + (2) interacts as a context manager
        + (2.1) automatically opens and reads the log-file on __enter__ing context manager
        + (2.2) automatically writes and closes the log-file on __exit__ing context manager
    + (3) embellishment functions like summary
    + (4) CAN Handle and launch processes for individual files, via a map() or apply()/call() functions
    + (5) processing functions operate INSIDE the context manager block
    + (6) ability to return an AttemptRecord(), via self.attempt(filepath)
                defaults should be drawn from properties of ProcessLogger()
                
    Depends on: 
        CompoundDataSet() from data.py
        ProcessingAttempt() from this file (logger.py)
        
    
    @TODO: Consider: should close() and close_attempts() be called together?
    @TODO: Closing an attempt should remove it from the list of active attempts.
    
    @TODO: Get default data working. Currently it causes bugs in self.attempt()
    @TODO: Allow setting default_data which is inherited by new attempts
    @TODO: Make the RuntimeError() in attempt() into a pa_exceptions.NonSuppressedError("Log file must be open")
    
    """
#     def __init__(self, logpath, task=None, dataset=None):
#         self.logpath = logpath
#         self.task = task
#         self.dataset = dataset
#         self.log = None
    def __init__(self, logpath, data=None):
        """
        with ProcessLogger(logpath) as log:
            log.mapper
            with log.attempt(
        """
        JSONProgressLog.__init__(self, logpath)
        
        self.default_data = self.validate(data)
        #self.default_data = {}
        
    
    def validate(self, data):
        if data == None:
            data = {}
        else:
            rich_core.AssertKlass(data, collections.MutableMapping, name='data')
        return data
        
    def attempt(self, arguments):
        """
        """
        if not self.opened:
            raise RuntimeError("Log file must be open.")
        
        #Trying to fix a bug:
        #return ProcessingAttempt(self, arguments)

        #Old code
        #attempt = ProcessingAttempt(self, arguments, data=self.default_data)
        attempt = ProcessingAttempt(self, arguments)
        self.attempts.append(attempt) 
        return attempt
    
    def __enter__(self):
        JSONProgressLog.__enter__(self)
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        Eventually, this will have to close out of the attempts.
        """
        JSONProgressLog.__exit__(self, exc_type, exc_value, exc_traceback)
        #Extra stuff...    
        #self.close_attempts()
    
    
    #----- Attempts property
    #Hook back from child attempts
    #Child attempts must be written on exiting the context manager
    
    
    _attempts = []
    @rich_property.VProperty
    def attempts(self):
        return self._attempts
    @attempts.setter
    def attempts(self, value):
        self._attempts = value
    @attempts.validator
    def attempts(self, attempts):
        rich_core.AssertKlass(attempts, rich_core.NonStringSequence, name='attempts')
        for attempt in attempts:
            rich_core.AssertKlass(attempt, ProcessingAttempt, name='attempt')
        return attempts
    def close_attempts(self):
        """Close all attempts."""
        for attempt in self.attempts:
            attempt.close()
    #------- default_data property
    @rich_property.VProperty
    class default_data(object):
        def getter(self):
            return self._default_data
        def setter(self, value):
            self._default_data = value
        def deleter(self):
            del self._default_data
        def validator(self, value):
            rich_core.AssertKlass(value, collections.MutableMapping, name='default_data')
            return value
    
    #-------
    def summary(self):
#         for arguments, record in self.items():
#             _summarize_attempt(record, arguments)
        return "\n\n".join(
            _summarize_attempt(record, arguments)
            for arguments, record in self.items()
        )

    #------ Advanced --- handle in the FUTURE
    def map(self, processing, iterable=None):
        """
        'callable' is the core processing.
        
        Mapper from example_2().
        with ProcessLogger("testlog.json", task='import-expanded', dataset=VirtualChemistry) as log:
            log.map(fake_processing)
        """
        if iterable==None:
            iterable = self.dataset
        
        for argument in iterable:
            with log.attempt(argument) as attempt:
                processing(*argument)
            
    def call(self, processing, argument):        
        with self.attempt(argument) as attempt:
            results = processing(argument)
        return attempt
            
                




def LoggerDecorator(logpath, arguments):
    """ Speculative attempt to make this usable as a decorator.
    Invoke in-line with:
        logger_as_decorator(log)(calculation(infiles))
    Invoke as decorator, with:
        @logger_as_decorator(log) #Probably requires log to be function to retrieve log
        def calculation(infiles):
        
    
    
    @todo: Revise this to use ProcessLogger() self, and match it's functionality
    @todo: Match this with ProcessLogger.map
        ProcessLogger(logname).map(processing)(arguments)
        OR
        @ProcessLogger(logname).map
        def processing(argument):
    @todo: Maybe: implement into ProcessLogger __new__, to handle the decorator step
    
    
    attempt['processing'] = str(processing)
    attempt['name'] = 'amend sdf'
    """
    
    raise RuntimeError("Unfinished function.")
    
    def outer(callable):
        """ """
        @functools.wraps(callable)
        def inner(arguments):
            """Arguments must be specified differently than normal.
            Must be a single argument, which is Iterable."""
            
            with ProcessLogger(logname) as log:
                for argument in arguments:
                    with log.attempt(argument) as attempt:
                        attempt['results'] = callable(argument)
                    # Print summary of attempt
                    print(attempt.summary())
                # Print summary of log
                print("\n\n==============================DONE:===========================")
                print(log.summary())
                print("\n\n==============================DONE:===========================\n")
            # Does not actually return anything
        return inner
    return outer


#==============================================================================
#    Local Utility Functions
#==============================================================================
def _convert_to_string(data):
    '''Converts potentially abstract objects to strings.
    Commonly used to convert JSON to dicts.'''
    #basestrings: convert directly to string
    if isinstance(data,basestring):
        return str(data)
    #Mappings: recurse on it's elements, and convert to a dict.
    elif isinstance(data, collections.Mapping):
        return dict(_convert_to_string(item) for item in data.iteritems())
        #return dict(map(_convert_to_string, data.iteritems()))
    #Iterables: recurse on it's elements, and preserve it's type.
    elif isinstance(data, collections.Iterable):
        return type(data)(_convert_to_string(elm) for elm in data)
        #return type(data)(map(_convert_to_string, data))
    #Others: no change
    else:
        return data
def seq2tuple(obj):
    if isinstance(obj, rich_core.NonStringSequence):
        return tuple(obj)
    else:
        return obj

def _summarize_attempt(record, arguments):
    """
    record = log[arguments]
    """
    try:
        message = "{0}: {1} <-- {2}".format(
            record['stopped'], record['state'], arguments
        )
    except KeyError:
        message = "{0} <-- {1}".format(
            record['state'], arguments
        )
        
    try:
        message += "\n{exc_traceback}{exc_type}: {exc_value}".format(**record)
    except KeyError:
        pass
    return message




#     print(record['state'] + " <-- " + str(arguments))
#     if 'exc_type' in record:
#         print("\t\t{exc_type}: {exc_value}".format(**record))
#         print(record['exc_traceback'])


# def summary(log, arguments=None):
#     if arguments == None:
#         for arguments, record in log.items():
#             _summarize_attempt(record, arguments)
#     else:
#         _summarize_attempt(log[arguments], arguments) 
