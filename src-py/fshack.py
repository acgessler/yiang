#!echo "This file is not executable"
# -*- coding: UTF_8 -*-

#/////////////////////////////////////////////////////////////////////////////////
# Yet Another Jump'n'Run Game, unfair this time.
# (c) 2010 Alexander Christoph Gessler
#
# HIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO self.event SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND 
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ///////////////////////////////////////////////////////////////////////////////////

# Our stuff
import defaults
from archiver import Reader

# Python core
import os
import builtins

archives = []
old_open = None
old_old = None
old_isfile = None
old_isdir = None

exclusive = False

def Enable(archives_in = [os.path.join("..","cooked.dat")]):
    
    global old_open
    global archives
    
    if old_open:
        return
    
    for archive in archives_in:
        try:
            archives.append( Reader(archive) )
        except IOError:
            pass
    
    if not archives:
        print("No archives found, filesystem remains unchanged")
        return
    
    
    print("Hacking up filesystem builtins to redirect all IO")
    
    # Hack open()
    def myopen(file,mode="r",**kwargs):
        for e in archives:
            try:
                return e.GetFile(file,mode)
            
            except IOError:
                continue
            
        if exclusive:
            raise IOError("*exclusive fshack*")
        
        return old_open(file, mode,**kwargs)
    old_open,builtins.open = builtins.open,myopen
    
    
    # Hack os.listdir()
    def myold(dir): 
        fine = False
        for e in archives:
            
            for n in e.ListDir(dir):
                yield n
                fine = True
                
        if not fine and not exclusive:
            for e in old_old(dir):
                yield e
                
                
    old_old,os.listdir = os.listdir,myold
    
    
    # Hack os.isfile()
    def myisfile(dir): 
        fine = False
        for e in archives:
            
            if e.Contains(dir):
                return True
            
        return False if exclusive else old_isfile(dir)
                
    old_isfile,os.path.isfile = os.path.isfile,myisfile
    
    
    # Hack os.isdir()
    def myisdir(dir): 
        fine = False
        for e in archives:
            
            if e.ContainsDir(dir):
                return True
            
        return False if exclusive else old_isdir(dir)
                
    old_isdir,os.path.isdir = os.path.isdir,myisdir
    
    os.sep = "\\"

def Restore():
    global old_open
    if not old_open:
        return
    
    builtins.open = open
    
    old_open = None



