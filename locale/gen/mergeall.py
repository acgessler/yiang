#!/usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# MGL Framework Python Scripting Interface (v0.1)
# [buildbot.py]
# (c) Alexander Gessler, 2009
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

outfile = "merged_master.txt"
folders = [os.path.join("..","..","data","tiles"), os.path.join("..","..","data","levels")]


def Stringify(string):
    return 'r"""' + string.rstrip().replace('\"\"\"','\"\"\" + \'\"\"\"\' + \"\"\"') + '"""' 

def ProcessFolder(folder,outf):
    for file in os.listdir(folder):
        path = os.path.join(folder,file)
        if os.path.isdir(path):
            ProcessFolder(path,outf)
            
        if not os.path.isfile(path):
            continue
        
        if os.path.splitext(path)[-1].lower() != ".txt":
            continue
        
        # try to get valid python expressions so pygettext can parse properly.
        with open(path,"rt") as inp:
            data = inp.read()
            data = data.split("\n",1)
        
            shebang = data[0].strip()
            shebang_words = shebang.split()
            if not "<out>" in shebang_words:
                continue
        
            eval_string = shebang.replace("<raw>", Stringify( data[1] ) if len(data) > 1 else "missing" )
            eval_string = eval_string.replace("<","").replace(">","").replace("\\","\\\\")
            if eval_string:
                
                try:
                    exec(eval_string)
                except (ImportError,NameError):
                    pass
                except:
                    print("check manually: ")
                    print(eval_string)
                
                #outf.write("# {0}\n".format(path))
                outf.write(eval_string + "\n"*5)
            
        
def Main():
    with open(outfile,"wt") as outf:
        for folder in folders:
            ProcessFolder(folder,outf)
        
    print("Done!")
    
    
if __name__ == "__main__":
    Main()