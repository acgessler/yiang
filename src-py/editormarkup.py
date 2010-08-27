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

# Python
import random

# Our stuff
import defaults
import editor

class MarkupHandler:
    """Base class for all markup handlers"""

    def __init__(self,editor,entity):
        self.editor = editor
        self.entity = entity
        
        assert editor and entity
        
    def CenterInMouseCoords(self,entity=None):
        entity = entity or self.entity
        dim = entity.dim[0]*0.5,entity.dim[1]*0.5
        
        return self.editor._TileToMouseCoords(entity.pos[0]+dim[0],entity.pos[1]+dim[1])
    
    
    def ExtendsInMouseCoords(self,entity=None):
        entity = entity or self.entity
        
        # Don't use GetBoundingBox(), it may be overridden to do any bogus it likes to.
        dim = entity.dim
        return self.editor._TileToMouseCoords(*entity.pos) + self.editor._TileToMouseCoords(
            entity.pos[0]+dim[0],entity.pos[1]+dim[1]
        )
        
        
from enemy import SmallTraverser
class MarkupHandler_SmallTraverser(MarkupHandler):
        
    @staticmethod
    def GetClasses():
        return (SmallTraverser,)

    def __call__(self):
        pass
    
    
from materials import BackgroundLight
class MarkupHandler_BackgroundLight(MarkupHandler):
        
    @staticmethod
    def GetClasses():
        return (BackgroundLight,)

    def __call__(self):
        if self.editor.layer != editor.LAYER_BACKGROUND:
            return
    
        cpos = self.CenterInMouseCoords()
        dist = self.entity.dim[0]*0.5*defaults.tiles_size_px[0]
    
        col = self.__dict__.setdefault("cached_color",sf.Color(random.randint(0,0xff),
            random.randint(0,0xff),random.randint( 0,0xff ),0xa0
        ))
        self.editor.DrawSingle(sf.Shape.Circle(cpos[0],cpos[1],
            dist,sf.Color(0,0,0,0), 2 ,col
        ))
        
    
from enemy import RotatingInferno
class MarkupHandler_RotatingInferno(MarkupHandler):
        
    @staticmethod
    def GetClasses():
        return (RotatingInferno,)

    def __call__(self):
        if self.editor.layer != editor.LAYER_NORMAL:
            return
        
        dim = self.entity.dim[0]*0.5,self.entity.dim[1]*0.5
        rpos = self.editor._TileToMouseCoords(self.entity.real_pos[0]+dim[0],self.entity.real_pos[1]+dim[1])
        cpos = self.CenterInMouseCoords()
        
        dist = getattr(self,"cached_dist",None) or self.__dict__.setdefault("cached_dist",
                ((rpos[1]-cpos[1])**2  + (rpos[0]-cpos[0])**2)**0.5
        )
        
        col = sf.Color(0xff,0xff,0x0,0xa0)
        self.editor.DrawSingle(sf.Shape.Line(cpos[0],cpos[1],rpos[0],rpos[1],2, col))
        self.editor.DrawSingle(sf.Shape.Circle(cpos[0],cpos[1],
            dist,sf.Color(0,0,0,0), 2 ,col
        ))
    
    
from danger import Mine
class MarkupHandler_Mine(MarkupHandler):
        
    @staticmethod
    def GetClasses():
        return (Mine,)

    def __call__(self):
        if self.editor.layer != editor.LAYER_NORMAL:
            return
        
        cola = sf.Color(0xff,0x0,0x00,0x0a)
        colb = sf.Color(0xff,0x0,0x00,0x60)
        cpos = self.CenterInMouseCoords()
        self.editor.DrawSingle(sf.Shape.Circle(cpos[0],cpos[1],
            self.entity.radius*defaults.tiles_size_px[0],cola, 2 ,colb
        ))
        
        
from danger import FakeDangerousBarrel
class MarkupHandler_FakeDangerousBarrel(MarkupHandler):
        
    @staticmethod
    def GetClasses():
        return (FakeDangerousBarrel,)

    def __call__(self):
        if self.editor.layer != editor.LAYER_NORMAL:
            return
        
        colb = sf.Color(0xff,0xff,0xff,0xff)
        cpos = self.CenterInMouseCoords()
        
        x,y,xx,yy = self.ExtendsInMouseCoords()
        xx,yy = xx-1,yy-1
        self.editor.DrawSingle(sf.Shape.Rectangle(x,y,xx,yy,sf.Color(0,0,0,0), 1 ,colb ))
        self.editor.DrawSingle(sf.Shape.Line(x,y,xx,yy,1 ,colb ))
        self.editor.DrawSingle(sf.Shape.Line(xx,y, x,yy, 1 ,colb ))
    
    
class Connector(MarkupHandler):
    """Shared logic to automatically connect related,
    but different entities with lines, teleporters
     being an example."""
    
    def __init__(self,color,*args,**kwargs):
        MarkupHandler.__init__(self, *args, **kwargs)
        self.color = color
    
    def __call__(self):
        whichone = [e for e in self.GetClasses() if e != self.entity.__class__][0]
        
        if not hasattr(self,"partner") or self.clock.GetElapsedTime() > 2.0:
            self.partner = self.editor.GetLevel().FindClosestOfSameColor(
                self.entity.pos,whichone,self.entity.color
            )
            
            self.clock = sf.Clock()
            
        if not self.partner:
            return
        
        # Draw the line between the entities only once :-)
        if getattr(self.partner,"in_visible_set",False) and whichone == self.GetClasses()[0]:
            return
    
        cpos = self.CenterInMouseCoords()
        rpos = self.CenterInMouseCoords(self.partner)
        self.editor.DrawSingle(sf.Shape.Line(cpos[0],cpos[1],rpos[0],rpos[1],2, self.color))
        
    
from locked import BridgeControl,Bridge
class MarkupHandler_BridgeControl(Connector):
        
    def __init__(self,*args,**kwargs):
        Connector.__init__(self, sf.Color(0,0xff,0,0x80) , *args,**kwargs)
        
    @staticmethod
    def GetClasses():
        return (BridgeControl,Bridge,)
    
    def __call__(self):
        if self.editor.layer != editor.LAYER_NORMAL:
            return
        Connector.__call__(self)
        

from teleport import Sender, Receiver
class MarkupHandler_Teleport(Connector):
        
    def __init__(self,*args,**kwargs):
        Connector.__init__(self, sf.Color(0xff,0,0,0x80) , *args,**kwargs)
        
    @staticmethod
    def GetClasses():
        # Order matters here, because senders and receivers have 
        # a many to one relationship.
        return (Sender, Receiver,)
    
    
    def __call__(self):
        if self.editor.layer != editor.LAYER_NORMAL:
            return
        Connector.__call__(self)
    
    
def GetHandlers():
    """Return a list of all known handler classes"""
    return [
        MarkupHandler_SmallTraverser,
        MarkupHandler_RotatingInferno,
        MarkupHandler_BridgeControl,
        MarkupHandler_Teleport,
        MarkupHandler_BackgroundLight,
        MarkupHandler_Mine,
        MarkupHandler_FakeDangerousBarrel,
    ]
    
        