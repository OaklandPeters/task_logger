import unittest
import os
import random
import copy
import collections
#-----
from local_packages import rich_core
#-----
from logger import JSONProgressLog, ProcessingAttempt, States, ProcessLogger
from data import read_dir, CompoundDataSet








class JSONProgressLogTests(unittest.TestCase):
    def setUp(self):
        self.name = "json-test-log.json"
        #Delete values
        if os.path.exists(self.name):
            os.remove(self.name)
        
    def test_open_close(self):
        log = JSONProgressLog(self.name)
        log.open()
        log.close()
        self.assert_(not log.opened)
        
    def test_context_manager(self):
        with JSONProgressLog(self.name) as log:            
            log['mydata'] = 'things'
        self.assert_(not log.opened)
        self.assert_(isinstance(log.data, collections.Mapping))

    def test_insert(self):
        with JSONProgressLog(self.name) as log:
            log['testdata']= ['foo','bar']
        with JSONProgressLog(self.name) as otherlog:
            self.assertEquals(otherlog['testdata'],['foo','bar'])
    
    def test_remove(self):
        with JSONProgressLog(self.name) as log:
            log.data['testdata']= ['foo','bar']
            log.data['moredata'] = ['bababar']
        with JSONProgressLog(self.name) as otherlog:            
            self.assert_('testdata' in otherlog)
            self.assert_('moredata' in otherlog)
            del otherlog['moredata']
        with JSONProgressLog(self.name) as mylog:
            self.assert_('testdata' in mylog)
            self.assert_('moredata' not in mylog)

    def test_chaining(self):
        otherlog = JSONProgressLog(self.name).open()
        self.assert_(otherlog.opened)
        otherlog.close()



class ProcessAttemptTests(unittest.TestCase):
    def setUp(self):
        self.logpath = 'test-log.json'
        self.VC = CompoundDataSet(
            name = 'virtual_chemistry',
            filepaths = list(read_dir(
                "/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/",
                match="Virtual_Chemistry*.sdf.expanded"
            ))
        )
 
    def memoize_to_log(self, sequence_of_args, processing):        
        seq_of_seq = (rich_core.ensure_tuple(arguments) for arguments in sequence_of_args)
        with JSONProgressLog(self.logpath) as log:
            for arguments in seq_of_seq:
                with ProcessingAttempt(log, arguments) as attempt:
                    attempt['results'] = processing(*arguments)
            log_data = dict(log.data)
        return log_data
 
    def test_no_preexisting_log(self):
        if os.path.exists(self.logpath):
            os.remove(self.logpath)
         
        log = self.memoize_to_log(self.VC.filepaths, dummy_processing)
         
        self.assertEquals(
            log.keys()[0],
            ('/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/Virtual_Chemistry_10.sdf.expanded',)
        )
        self.assertEqual(len(log), len(self.VC.filepaths))
         
        states = [record['state'] for record in log.values()]
        self.assert_('errored' in states)
        self.assert_('completed' in states)
         
 
    def test_preexisting_log(self):
        if os.path.exists(self.logpath):
            os.remove(self.logpath)
        old_log = self.memoize_to_log(self.VC.filepaths, dummy_processing)
          
        log = self.memoize_to_log(self.VC.filepaths, dummy_processing)
          
          
        self.assertEquals(
            log.keys()[0],
            ('/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/Virtual_Chemistry_10.sdf.expanded',)
        )
        self.assertEqual(len(log), len(self.VC.filepaths))
          
        states = [record['state'] for record in log.values()]
        self.assert_('errored' in states)
        self.assert_('completed' in states)
 
    def test_erroring_log(self):
        if os.path.exists(self.logpath):
            os.remove(self.logpath)
          
        log = self.memoize_to_log(self.VC.filepaths, processing=erroring_processing)
          
        states = [record['state'] for record in log.values()]
        self.assert_('errored' in states)
        self.assert_('completed' not in states)
        errors = [state for state in states if state == 'errored']
        self.assertEqual(len(errors), len(self.VC.filepaths))




class ProcessLoggerTests(unittest.TestCase):
    def setUp(self):
        self.logpath = 'test-log.json'
        self.VC = CompoundDataSet(
            name = 'virtual_chemistry',
            filepaths = list(read_dir(
                "/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/",
                match="Virtual_Chemistry*.sdf.expanded"
            ))
        )
        if os.path.exists(self.logpath):
            os.remove(self.logpath)

    def memoize_to_log(self, sequence_of_args, processing):        
        seq_of_seq = (rich_core.ensure_tuple(arguments) for arguments in sequence_of_args)
        with ProcessLogger(self.logpath) as log:
            for arguments in seq_of_seq:
                with log.attempt(arguments) as attempt:
                    attempt['results'] = processing(*arguments)
            log_data = dict(log.data)
            
        return log_data

    def test_no_preexisting_log(self):
        log = self.memoize_to_log(self.VC.filepaths, dummy_processing)

        self.assertEquals(
            log.keys()[0],
            ('/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/Virtual_Chemistry_10.sdf.expanded',)
        )
        self.assertEqual(len(log), len(self.VC.filepaths))
        
        states = [record['state'] for record in log.values()]
        self.assert_('errored' in states)
        self.assert_('completed' in states)

    def test_time_record(self):
        log = self.memoize_to_log(self.VC.filepaths, dummy_processing)
        
        for arguments, record in log.items():
            self.assert_('started' in record)
            self.assert_('stopped' in record)
            self.assert_('elapsed' in record)

    def test_preexisting_log(self):
        old_log = self.memoize_to_log(self.VC.filepaths, dummy_processing)
        
        log = self.memoize_to_log(self.VC.filepaths, dummy_processing)
        
        
        self.assertEquals(
            log.keys()[0],
            ('/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/Virtual_Chemistry_10.sdf.expanded',)
        )
        self.assertEqual(len(log), len(self.VC.filepaths))
        
        states = [record['state'] for record in log.values()]
        self.assert_('errored' in states)
        self.assert_('completed' in states)

    def test_erroring_log(self):
        log = self.memoize_to_log(self.VC.filepaths, processing=erroring_processing)
         
        states = [record['state'] for record in log.values()]
        self.assert_('errored' in states)
        self.assert_('completed' not in states)
        errors = [state for state in states if state == 'errored']
        self.assertEqual(len(errors), len(self.VC.filepaths))


# class ReviewerTests(unittest.TestCase):
#     def setUp(self):
#         #self.logpath = 'test-log.json'
#         self.directory = "/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/" 
#         self.logpath = self.directory + 'import-sdf-log.json'
#         self.VC = CompoundDataSet(
#             name = 'virtual_chemistry',
#             filepaths = list(read_dir(
#                 self.directory,
#                 match="Virtual_Chemistry*.sdf.expanded"
#             ))
#         )
#     def test_basic(self):
#         import pdb
#         
#         with JSONProgressLog(self.logpath) as log:
#             pdb.set_trace()
#             print('--')


#------------------------------------------------------------------------------
#    Local Utility Functions
#------------------------------------------------------------------------------
def front(iterable, count=1):
    #Basically itertools.islice(iterable, stop)
    iterator = iter(iterable)
    for _ in range(count):
        yield iterator.next()


def dummy_processing(filepath):
    """Unit-test processing mock function.
    Reads the first few lines from the file
    """
    if random.random() < 0.5:
        fpath, fname = os.path.split(filepath)
            
        with open(filepath,'r') as sdf:
            accumulator = "".join(front(sdf, 6))
        return accumulator
    else:
        raise RuntimeError("Intentional dummy-processing error.")

def erroring_processing(filepath):
    """Always throws one of several errors KeyError."""
    myobj = object()
    mydict = {}
    myseq = range(10)
    
    rand = random.randint(1,5)
    
    if rand == 1:   #AttributeError
        return myobj.myvalue
    elif rand == 2: #KeyError
        return mydict['b']
    elif rand == 3: #ImportError
        import onamonapea
        return onamonapea
    elif rand == 4: #TypeError
        return "-".join(123)
    elif rand == 5: #IndexError
        return myseq[11]
        
    
    

if __name__ == "__main__":
    unittest.main()
