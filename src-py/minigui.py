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

# Python Core
import math

# PySFML
import sf

# Our stuff
import defaults
from renderer import Renderer,Drawable,NewFrame
from fonts import FontCache

class Component(Drawable):
    """Base class for the minigui system, defines common container logic. 
    All metrics in use by the GUI system are in pixels, the upper-left
    window corner being the coordinate space origin."""
    
    STATE_NORMAL,STATE_ACTIVE,STATE_HOVER,STATE_DISABLED=range(4)
    COLORS = {
        STATE_NORMAL   : sf.Color(100,100,100),
        STATE_ACTIVE   : sf.Color(150,150,150),
        STATE_HOVER    : sf.Color(120,100,100),
        STATE_DISABLED : sf.Color(40,40,40),
    }
    
    
    def __init__(self,rect=None):
        Drawable.__init__(self)
        self.rect = rect or [0,0,0,0]
        self._state = Component.STATE_NORMAL
        
        self.font = FontCache.get(defaults.letter_height_gui,defaults.font_gui)
        
    def GetDrawOrder(self):
        # Make sure the GUI is on top fo everything else
        return 51000
    
    
    @property
    def rect(self):
        x,y,w,h = self._rect
        return (x if x>=0 else defaults.resolution[0]+x),(y if y>=0 else defaults.resolution[1]+y),w,h
    
    @rect.setter
    def rect(self,*args):
        self._rect = args if len(args)==4 else args[0]
    
    @property
    def pos(self):
        x,y = self._rect[:2] 
        return (x if x>=0 else defaults.resolution[0]+x),(y if y>=0 else defaults.resolution[1]+y)
    
    @pos.setter
    def pos(self,*args):
        self._rect[:2] = args if len(args)==2 else args[0]
        
    @property
    def x(self):
        x = self._rect[0]
        return x if x>=0 else defaults.resolution[0]+x
    
    @x.setter
    def x(self,x):
        self._rect[0] = x 
            
    @property
    def y(self):
        y = self._rect[1]
        return y if y>=0 else defaults.resolution[1]+y
    
    @y.setter
    def y(self,y):
        self._rect[1] = y 
        
    @property
    def size(self):
        return self._rect[2:]
    
    @size.setter
    def size(self,w,h):
        self._rect[2:] = w,h
        
    @property
    def w(self):
        return self._rect[2]
    
    @w.setter
    def w(self,x):
        self._rect[2] = x
        
    @property
    def h(self):
        return self._rect[3]
    
    @h.setter
    def h(self,y):
        self._rect[3] = y
    
    @property
    def state(self):
        return self._state
        
    @state.setter
    def state(self,state):
        self._state = state
        return self
        


    def _MkPos(self,*args):
        x,y = args if len(args)==2 else args[0]
        return math.floor(x+self.x),math.floor(y+self.y)

    def DrawMyRect(self):
        Component.DrawRect(self.rect,self.__class__.COLORS[self.state],sf.Color.Black)
        
    def Draw(self):
        inp = Renderer.app.GetInput()
        mx,my = inp.GetMouseX(),inp.GetMouseY()
        
        self.DrawMe(mx,my,(self.x+self.w>mx>self.x and self.y+self.h>my>self.y))
        
    @staticmethod
    def DrawRect(bb,color,color_outline = None):
        color_outline = color_outline or color
        shape = sf.Shape()

        bb = [bb[0],bb[1],bb[0]+bb[2],bb[1]+bb[3]]

        shape.AddPoint(bb[0],bb[1],color,color_outline)
        shape.AddPoint(bb[2],bb[1],color,color_outline)
        shape.AddPoint(bb[2],bb[3],color,color_outline)
        shape.AddPoint(bb[0],bb[3],color,color_outline)

        shape.SetOutlineWidth(2)
        shape.EnableFill(True)
        shape.EnableOutline(True)
        Renderer.app.Draw(shape)
        

class Button(Component):
    """A normal button control, enough said"""
    
    COLORS = {
        Component.STATE_NORMAL   : sf.Color(50,50,50),
        Component.STATE_ACTIVE   : sf.Color(75,75,75),
        Component.STATE_HOVER    : sf.Color(90,75,75),
        Component.STATE_DISABLED : sf.Color(40,40,40),
    }
    
    def __init__(self,text="No text specified",**kwargs):
        Component.__init__(self,**kwargs)
        self.text = text
        
    @property
    def text(self):
        return self._text
        
    @text.setter
    def text(self,text):
        self._text = text
        self._text_cached = sf.String(self._text,Font=self.font,Size=defaults.letter_height_gui)
        return self
        
    def DrawMe(self,mx,my,hit):
        
        if hit:
            self.state = Component.STATE_HOVER
        else:
            self.state = Component.STATE_NORMAL
        
        self.DrawMyRect()
        
        ts = self._text.split("\n")
        self._text_cached.SetPosition(*self._MkPos(self.w*0.5 - len(ts[0])*defaults.letter_height_gui*0.2,
            self.h*0.5 - len(ts)*defaults.letter_height_gui*0.5))
        
        Renderer.app.Draw(self._text_cached)
        
        
        
        
        
        
        
    
        
        
        