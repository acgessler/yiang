#!echo "This file is not executable"
# -*- coding: UTF_8 -*-

#/////////////////////////////////////////////////////////////////////////////////
# Yet Another Jump'n'Run Game, unfair this time.
# (c) 2010 Alexander Christoph Gessler
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

# My own stuff
import defaults

class Log(io.IOBase):
    """Class to stream any print()'s calls to a separate on-disc
    log file as well. This is achieved by hijacking sys.stdout"""

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
                
            
        
        
    
    
