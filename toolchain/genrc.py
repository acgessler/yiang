#!echo /usr/bin/env python3
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
import random
import operator


import makepyc
makepyc.run()

ignore = []
basedir = os.path.join("..","src-py")
dirs = [".",os.path.join(".","updaters")]
outrc = os.path.join("..","vc9","yiang.rc")
outh = os.path.join("..","vc9","yiang.h")

files = {}

for dir in dirs:
    print("Enter directory {0}".format(dir))
    for file in os.listdir(os.path.join(basedir,dir)):
        path = os.path.join(os.path.join(basedir,dir),file)
        if os.path.splitext(file)[-1].lower() == ".pyc" and not (file in ignore or path in ignore):
            print("Slurp {0}".format(path))
            with open(path,"rb") as inp:
                files[os.path.join(dir,file)[2:].replace("/","\\").replace("\\","\\\\")] = inp.read()
    
indices = {}

with open(outrc,"wt") as outf:            
    for file,contents in files.items():
        index = random.randint(1,2**16 -1)
        indices[file] = index
        print("Write {0} as {1}".format(file,index))
        
        outf.write("""{0} RCDATA // {2}
        {{
            {1}
        }}
        
        
""".format(index, "L,\n".join( ["0x" + "".join( hex(c)[2:].zfill(2) 
        for c in reversed( contents[n:n+4] ) ) 
            for n in range(0,len(contents)+4,4) ] 
        )[:-3], file ))
        
        
with open(outh,"wt") as outf: 
    outf.write("""
#pragma once
    
namespace PyCacheTable {
struct Entry {
   const wchar_t* name;
   unsigned int index;
};
    
Entry entries[] = {
    
    """)
    for file,index in sorted( indices.items(), key=operator.itemgetter(0) ):
        
        outf.write(""" {{ L"{0}", {1} }},
        """.format(file,index));
        
        
    outf.write(""" 
       {{0,0}} // end sentinel
    }};
}}
    
#define NUM_PYCACHE_ENTRIES {0}
    """.format(len(indices)))
    print("Wrote auxiliary header file")
    
    
    
                  
