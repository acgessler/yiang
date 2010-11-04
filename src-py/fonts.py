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
    

class FontCache:
    """Tiny utility to cache all fonts we're using to avoid creating redundant instances.
    I assume SFML caches internally as well, but this way we can safe some additional
    overhead, also fonts are easier to track."""

    cached = {}
    lock = threading.Lock()
    
    @staticmethod
    def Find(font_obj):
        for k,v in FontCache.cached.items():
            if v == font_obj:
                return k
        return None 
        

    @staticmethod
    def get(height,face=""):
        
        with FontCache.lock:
        
            if not face:
                face = defaults.font_monospace
    
            font = FontCache.cached.get((face,height),None) 
            if not font is None:
                return font
            
            print("Loading font {0} / {1}".format(face,height))
    
            font = sf.Font()
            
            try:
                file = open(face,"rb").read()
                
                if not font.LoadFromMemory(file,int(height)) is True:
                    print("Failure creating font {0},{1} -> creation fails".format(face,height))
                    # XXX substitute default font?
                
            except IOError:
                print("Failure creating font {0},{1} -> can't open file".format(face,height))
                font = None
           
    
            FontCache.cached[(face,height)] = font
            return font

    

    
