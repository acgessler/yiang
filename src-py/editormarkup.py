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

# PySFML
import sf

# Our stuff
import defaults

class MarkupHandler:
    """Base class for all markup handlers"""

    def __init__(self,editor,entity):
        self.editor = editor
        self.entity = entity
        
        assert editor and entity
        
        
from enemy import SmallTraverser
class MarkupHandler_SmallTraverser(MarkupHandler):
        
    @staticmethod
    def GetClasses():
        return (SmallTraverser,)

    def __call__(self):
        pass
    
    
from enemy import RotatingInferno
class MarkupHandler_RotatingInferno(MarkupHandler):
        
    @staticmethod
    def GetClasses():
        return (RotatingInferno,)

    def __call__(self):
        dim = self.entity.dim[0]*0.5,self.entity.dim[1]*0.5
        cpos = self.editor._TileToMouseCoords(self.entity.pos[0]+dim[0],self.entity.pos[1]+dim[1])
        rpos = self.editor._TileToMouseCoords(self.entity.real_pos[0]+dim[0],self.entity.real_pos[1]+dim[1])
        
        dist = getattr(self,"cached_dist",None) or self.__dict__.setdefault("cached_dist",
                ((rpos[1]-cpos[1])**2  + (rpos[0]-cpos[0])**2)**0.5
        )
        
        col = sf.Color(0xff,0xff,0x0,0xa0)
        self.editor.DrawSingle(sf.Shape.Line(cpos[0],cpos[1],rpos[0],rpos[1],1, col))
        self.editor.DrawSingle(sf.Shape.Circle(cpos[0],cpos[1],
            dist,sf.Color(0,0,0,0), 1 ,col
        ))
    

def GetHandlers():
    """Return a list of all known handler classes"""
    return [
        MarkupHandler_SmallTraverser,
        MarkupHandler_RotatingInferno
    ]
    
        