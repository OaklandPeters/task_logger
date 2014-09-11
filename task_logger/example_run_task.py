import os
#----
import task_logger


def front(iterable, count=1):
    #Basically itertools.islice(iterable, stop)
    iterator = iter(iterable)
    for _ in range(count):
        yield iterator.next()


def fake_processing(filepath):
    """Unit-test processing mock function.
    Reads the first few lines from the file
    """
    fpath, fname = os.path.split(filepath)
    with open(filepath,'r') as sdf:
        for line in front(sdf, 6):
            print(line)
        print("Done simulating file: "+fname)
        print("-------------------")
        


VirtualChemistry = task_logger.CompoundDataSet(
    name = 'virtual_chemistry',
    filepaths = list(task_logger.read_dir(
        "/data/htdocs/cccid/build/compounds-db/data-files/virtual_chemistry/",
        match="Virtual_Chemistry*.sdf.expanded"
    ))
)





## NOTE: Alternate approach to this:
#    Memoization approach - log.attempt() is basically the memoization
#----------
def example_1():
    with task_logger.ProcessLogger("testlog.json", task='import-expanded') as log:
        for filepath in VirtualChemistry.filepaths:
            with log.attempt(filepath) as attempt:
                # log.attempt() returns ProcessingAttempt
                # the context manager on ProcessingAttempt initializes an attempt for task,filepath
                
                # load_data_file(filepath)  #would go here
                fake_processing(filepath)
            # ProcessingAttempt(): if error, will write 'errored' to state
            # else will write 'completed' to state if no error
example_1()


# --- Alternate, sugar-y interface with CompoundDataSet
def example_2():
    with task_logger.ProcessLogger("testlog.json", task='import-expanded', dataset=VirtualChemistry) as log:
        log.map(fake_processing)
        #log.map(func) sets up something like the loop in example_1()
        #    iterating over 'dataset', and feeding the results into func()
#--- Add this to ProcessLogger(), based on example_2
#    def map(self, callable, iterable=None):
#        #If iterable==None, then can use 'dataset' as specified in __init__


    