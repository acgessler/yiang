#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [filebot.py]
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


import os
import shutil

# Target directory to cpy all the files to.
target = os.path.join("..","final","root")
verbose = False

if verbose:
    import traceback
    
    
def clean():
    try:
        for f in os.walk(target,topdown=False):
            for ff in f[2]:
                os.remove(os.path.join(f[0],ff))
            
            for ff in f[1]:    
                os.rmdir(os.path.join(f[0],ff))
        print("Cleanup complete")
    except:
        print("Errors during cleanup")

def copy_files(files):
    for file in files:
        dst = os.path.join( target, file.replace("..\\","") )
        try:
            os.makedirs(os.path.split(dst)[0])
        except OSError:
            pass # exists already
        try:
            shutil.copy(file, dst)
            print("COPY {0} to {1}".format(file,dst))
        except:
            print("Failure copying {0} to {1}".format(file,dst))
            
            if verbose:
                traceback.print_exc()


def archive_files(files):
    from archiver import Writer
    
    af = os.path.join(target,"cooked.dat")
    with Writer(af) as archive:
        for file in files:
            try:
                archive.AddFile(file)
                print("ADD {0} to {1}".format(file,af))
            except:
                print("Failure adding {0} to archive {1}".format(file,af))
                
                if verbose:
                    traceback.print_exc()
        


def main(caches):
    
    clean()
    
    if "files" in caches:
        copy_files(caches["files"])
        
    if "archive_files" in caches:
        archive_files(caches["archive_files"])
         

# vim: ai ts=4 sts=4 et sw=4