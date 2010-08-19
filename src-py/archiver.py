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


import os

class Writer:
    
    def __init__(self,file,base=""):
        self.files = []
        self.base = base
        self.file = file
    
    def __enter__(self):
        return self
    
    def __exit__(self,exc_type, exc_value, traceback):
        self.Finalize()
        return False
    
    def AddFile(self,filename):
        filename2 = os.path.join(self.base,filename)
        # verify that we can read the file,
        # then cache its size.
        with open(filename2,"rt") as dummy:
            self.files.append([filename,os.stat(filename2).st_size ])
    
    def Finalize(self):
        cnt = 0
        for e in self.files:
            m = e[1]
            e[1] += cnt
            cnt += m
            
        with open(self.file,"wb") as outf:
            import marshal
            marshal.dump(self.files,outf)
            
            for filename,size in self.files:
                filename2 = os.path.join(self.base,filename)
                with open(filename2,"rb") as inf:
                    outf.write(inf.read())
                    
        print("Wrote {0}, totally {1} entries with {2} bytes".format(
            self.file,len(self.files),cnt))
        
        
class Reader:
    pass