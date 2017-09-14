"""
Set of msipbias exceptions that can be raised
"""
from msipbias.logging import logger
logger.name = __name__

class Error(Exception):
    """
    Base class for all exceptions of msipbias
    """
    def __init__(self):
        pass

class MSIPBiasArgumentError(Error):
    """
    Exceptions raised when the argument to an msipbias
    function call is of the wrong type
    """
    def __init__(self, argname, reason):
        """
        @param argname: The argument name that triggered the exception.
        @type argname: String
        @param reason: An explanatory text that details the error
        @type reason: String
        """
        self.argname = argname
        self.reason = reason
        #self.message = self.reason
        self.args = (self.reason,)
        
    def __str__(self):
        return "%s : %s" % (self.argname, self.reason)

    
class MSIPGeneralError(Error):
    """
    Exceptions raised for some function in the msipbias library
    has some error
    """
    def __init__(self, errorname, reason):
        """
        @param errorname: The name of the error for exception.
        @type errorname: String
        @param reason: An explanatory text that details the error
        @type reason: String
        """
        self.errorname = errorname
        self.reason = reason
        self.args = (self.reason,)
        self.message = errorname
        self.message += ": "
        self.message += reason
        logger.error(self.message)
        
    def __str__(self):
        return self.message
