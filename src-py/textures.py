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

import defaults
import sf

if defaults.no_threading:
    import dummy_threading as threading
else:
    import threading 

class TextureCache:
    """Centralized texture cache. Provides support for loading textures
    and works well with fs redirection internally."""

    cached = {}
    lock = threading.Lock()

    @staticmethod
    def Get(name=""):
        
        with TextureCache.lock:
        
            assert name
    
            tex = TextureCache.cached.get(name,None) 
            if not tex is None:
                return tex
            
            print("Loading texture {0}".format(name))
    
            tex = sf.Image()
            
            try:
                file = open(name,"rb").read()
                
                if not tex.LoadFromMemory(file) is True:
                    print("Failure creating texture {0} -> creation fails".format(name))
                    # XXX substitute default tex?
                
            except IOError:
                print("Failure creating tex {0} -> can't open file".format(face))
                tex = None
           
            TextureCache.cached[name] = tex
            return tex
        
        

    