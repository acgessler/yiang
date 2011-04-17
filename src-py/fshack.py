#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [fshack.py]
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
old_exists = None

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
        
        if "r" in mode:
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
        s = []
        for e in archives:
            s += [n for n in e.ListDir(dir)]
                
        if not exclusive:
            try:
                s += [e for e in old_old(dir) if not e in s]
            except OSError:
                if not s:
                    raise
                
        return s
                
                
    old_old,os.listdir = os.listdir,myold
    
    
    # Hack os.path.isfile()
    def myisfile(dir): 
        return not not ([e for e in archives if e.Contains(dir)] or\
            (False if exclusive else old_isfile(dir)))
                
    old_isfile,os.path.isfile = os.path.isfile,myisfile
    
    
    # Hack os.path.isdir()
    def myisdir(dir): 
        return not not ([e for e in archives if e.ContainsDir(dir)] or\
            (False if exclusive else old_isdir(dir)))
                
    old_isdir,os.path.isdir = os.path.isdir,myisdir
    
    
    # Hack os.path.exists()
    def myexists(dir): 
        return not not ( [e for e in archives if e.Contains(dir)] or\
            (False if exclusive else old_exists(dir)))
                
    old_exists,os.path.exists = os.path.exists,myexists
    
    
    # Add os.path.is_custom_fs()
    def icfs(dir):
        return not not [e for e in archives if e.Contains(dir)]
        
    os.path.is_archived =  icfs
    os.sep = "\\"

def Restore():
    global old_open
    if not old_open:
        return
    
    builtins.open = open
    os.listdir = old_old
    os.path.isdir = old_isdir
    os.path.isfile = old_isfile
    os.path.exists = old_exists
    delattr(os.path,"is_archived")
    
    old_open = None

# vim: ai ts=4 sts=4 et sw=4