#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [log.py]
# (c) 2008-2011 Yiang Development Team
#
# HIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND 
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ///////////////////////////////////////////////////////////////////////////////////

# Python Core
import sys
import io
import os
import threading

# My own stuff
import defaults

class Log(io.IOBase):
    """Class to stream any print()'s calls to a separate on-disc
    log file as well. This is achieved by hijacking sys.stdout"""

    enabled = False
    old = sys.stdout
    nostdout = os.name == "posix"
 
    def __getattr__(self,name):
       return getattr(Log.old,name)

    def __init__(self,file,old):
        io.IOBase.__init__(self)
        
        self.file = open(file,"wt")
        self.old = old
        self.prev_arg = ""

    def write(self,what):
        # fixme: find out what's wrong here -- it does not filter the log messages
        """ 
        if len(args) == 1:

            if args[0] == self.prev_arg.replace("\n","").strip():
                
                # swallow duplicate log messages
                self.duplicates = True
                return
            self.prev_arg = args[0]
        
        if hasattr(self,"duplicates"):
            delattr(self,"duplicates")
            self.write("(last message was probably repeated several times)")
        """
               
        if len(what)>5:
            what = "t{0}: {1}".format(threading.current_thread().ident,what)
            
        try:
            if not self.file is None:
                self.file.write(what)
    
            if not self.old is None and not Log.nostdout:
                self.old.write(what)
        except:
            pass # swallow write exceptions, we don't want to die here ..

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
                
            
        
        
    
    

# vim: ai ts=4 sts=4 et sw=4