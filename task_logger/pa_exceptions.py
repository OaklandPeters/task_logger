"""
Custom exceptions, used by ProcessingAttempt().
"""

class StopProcessingAttempt(Exception):
    """Parent class for Exceptions which have special interactions
    with the ProcessingAttempt() context-manager."""

class AttemptAlreadyInProgress(StopProcessingAttempt):
    pass

class AttemptPreviouslyCompleted(StopProcessingAttempt):
    pass

class NonSuppressedError(StopProcessingAttempt):
    """An error which will NOT be suppressed by the ProcessingAttempt()
    context manager.
    This Exception type can also 'wrap' another exception type."""
    def __init__(self, message, wrapped=None):
        """Can include another exception this is 'wrapped' around."""
        Exception.__init__(self, message)
        self.wrapped = wrapped
    def __repr__(self):
        if self.wrapped != None:
            return Exception.__repr__(self) + repr(self.wrapped)
        else:
            return Exception.__repr__(self)
    def __str__(self):
        if self.wrapped != None:
            return Exception.__str__(self) + str(self.wrapped)
        else:
            return Exception.__str__(self)

class AttemptCanceled(StopProcessingAttempt):
    pass