
# Python Core
import sys
import io

# My own stuff
import defaults

class Log(io.IOBase):

    enabled = False
    old = sys.stdout

    def __init__(self,file,old):
        io.IOBase.__init__(self)
        
        self.file = open(file,"wt")
        self.old = old

    def write(self,*args,**kwargs):
        self.file.write(*args,**kwargs)
        self.old.write(*args,**kwargs)

        self.file.flush()

    @staticmethod
    def Enable(doit):
        Log.enabled = doit
        if Log.enabled is True:
            try:
                sys.stdout = Log(defaults.log_file,Log.old)
            except IOError as err:
                # this can happen if we have no write access in our working directory
                sys.stdout = Log.old
        else:
            sys.stdout = Log.old
                
            
        
        
    
    
