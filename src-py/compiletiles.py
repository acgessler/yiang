#!/usr/bin/env python3
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

import os
import defaults

dirs = [
    os.path.join(defaults.data_dir,"tiles"),
    os.path.join(defaults.data_dir,"tiles_misc"),
]

# Find all level-specific directories    
import re
reg = re.compile(r"^(\d+)\.txt$")
for file in os.listdir(os.path.join(defaults.data_dir,"levels")):
    m = re.match(reg,file)
    if m:
        dirs.append( os.path.join(defaults.data_dir,"levels", str( m.groups()[0] )))
        
reg = re.compile(r"[a-zA-Z0-9]+\.txt$")
for dir in dirs:
    print("Try enter directory: {0}".format(dir))
    try:
        matches = {}
        for e in os.listdir(dir):
            m = re.match(reg,e)
            if not m:
                continue
            
            print("Try to process: {0}".format(e))
            
            path = os.path.join(dir,e)
            try:
                with open(path,"rt") as file:
                    lines = file.read().split("\n",1)
                    if len(lines)==2:
                        replace = {
                            "<out>"  : "entity",
                            "<raw>"  : 'r"""'+lines[1].rstrip().replace('\"\"\"',
                                '\"\"\" + \'\"\"\"\' + \"\"\"') +' """',
                            "<game>" : "game"
                        }
                        
                        lines = lines[0]
                        for k,v in replace.items():
                            lines = lines.replace(k,v)
                            
                        try:
                            matches[path] = compile(lines,"<shebang-string>","exec")
                        except:
                            print("Failure compiling {0}; skipping".format(e))
                            pass
                    
            except IOError:
                print("Failure accessing {0}; skipping".format(e))
                pass
    except OSError:
        print("Failure accessing {0}; skipping".format(dir))
        continue
    
    if not matches:
        continue
    
    import marshal
    
    path = os.path.join(dir,"cooked")
    try:
        os.mkdir(path)
    except OSError:
        pass
    outf = os.path.join(path,"tiles.dat")
    with open(outf,"wb") as file:
        marshal.dump(matches,file)
    
    
    
    
    
    
    
    

