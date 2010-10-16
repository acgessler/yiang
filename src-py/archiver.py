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
import io

verbose = True

class Base:

    def _Normalize(self,path):
        path = path.replace("/","\\").replace("\\\\","\\").strip()
        if path[:2] == ".\\":
            path = path[2:]
            
        return path
    
    def _NormalizeDir(self,dir):
        if dir[-1] != "\\":
            dir = dir + "\\"
            
        return self._Normalize(dir)
      
    

class Writer(Base):
    
    """Implements the archive logic to pack all the files prior to
    deployment."""
    
    def __init__(self,file,base=""):
        self.files = []
        self.base = base
        self.file = file
        self.final = False
    
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
            if filename[:2] == ".\\":
                filename = filename[2:]
            self.files.append([self._Normalize(filename),os.stat(filename2).st_size ])
    
    def Finalize(self):
        if self.final:
            return
        
        cnt = 0
        for e in self.files:
            m = e[1]
            e.append(cnt)
            cnt += e[1]
            
        with open(self.file,"wb") as outf:
            import marshal
            import struct
            s = marshal.dumps(self.files)
            outf.write(struct.pack("<I",len(s)))
            outf.write(s)
            
            for filename,size,ofs in self.files:
                filename2 = os.path.join(self.base,filename)
                with open(filename2,"rb") as inf:
                    outf.write(inf.read())
                    
        self.final = True
        print("Wrote {0}, totally {1} entries with {2} bytes".format(
            self.file,len(self.files),cnt))
        
        
class Reader(Base):
    
    """Used at runtime to access cooked files"""
    
    def __init__(self,filename):
        self.filename = filename
        self.file = open(filename,"rb")
        
        #import mmap
        #self.map = mmap.mmap(self.file.fileno(), 0)
        
        # need to keep marshal from pulling in the whole file
        import marshal
        import struct
        
        self.base_ofs, = struct.unpack("<I",self.file.read(4))
        self.files = marshal.loads(self.file.read(self.base_ofs))
        self.base_ofs += 4
        
        print("Reading {0}, got {1} entries".format(filename,len(self.files)))
        
    def __enter__(self):
        return self
        
    def __exit__(self,exc_type, exc_value, traceback):
        #self.map.close()
        self.file.close()
        return False
        
    def Read(self,filename):
        filename = self._Normalize(filename)
        try:
            filename,size,ofs = [e for e in self.files if e[0]==filename][0]
            
        except IndexError:
            raise IOError("File does not exist in archive: {0}".format(filename))
        
        self.file.seek(ofs+self.base_ofs)
        return self.file.read(size)
        
    def GetFile(self,filename,mode):
        data = self.Read(filename)
        
        if verbose:
            print("Get {0},{1}".format(filename,mode))
            
        return io.BytesIO(data) if not "t" in mode else \
            io.StringIO(data.decode("utf-8","ignore"), \
            None)
            
    def Contains(self,filename):
        filename = self._Normalize(filename)
        #print("Have {0}? {1}".format(filename,not not [e for e in self.files if e[0]==filename]))
        return not not [e for e in self.files if e[0]==filename]
    
    def ContainsDir(self,dir):
        dir = self._NormalizeDir(dir)
        return not not [e for e in self.files if e[0][:len(dir)]==dir]
    
    def ListDir(self,dir):
        dir = self._NormalizeDir(dir)      
        elems = [e[0][len(dir):] for e in self.files if e[0][:len(dir)]==dir]
        if not elems:
            return
        
        if verbose:
            print("List {0} -> {1}".format(dir,elems))
        return elems
        
        
        
def testReader():
     testfile = os.path.join("..","final","root","cooked.dat")
     with Reader(testfile) as reader:
         try:
             f = reader.Read( os.path.join( "..","data","tiles","cooked","tiles.dat"))
             print("Read entry, length {0}".format(len(f)))
         except IOError:
             print("Failure reading test entry!")
             assert False
         
 
if __name__ == "__main__":
    testReader()
    print("Test ok")
        
        
        
    
    
    
    
    
    
    
    