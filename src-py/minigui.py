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

class GUIManager:
    """GUIManager is responsible for holding a list of all GUI 
    components in the scene. GUIManager.Enable() must be
    called before any of its functions can be used. Note
    that the rest of the GUI can be used without 
    GUIManager. This is just an extra facility if a list
    of all components in the scene is of interest to
    you (and is not available elsewhere)"""
    
    components, components2 = set(), set()
    drawable = None
    
    @staticmethod
    def Enable():
        """Call this before you use any of the functions
        provided by the GUIManager"""
        
        class Cleaner(Drawable):
            def GetDrawOrder(self):
                return 100005
                
            def Draw(self):
                GUIManager.components2,GUIManager.components = GUIManager.components,GUIManager.components2
                GUIManager.components2 = set()
        
        GUIManager.drawable = Cleaner()
        Renderer.AddDrawable(GUIManager.drawable)
        
    @staticmethod
    def Disable(self):
        """Disable the GUI manager's functionality
        again."""
        Renderer.RemoveDrawable(GUIManager.drawable)
        GUIManager.drawable = None
    
    @staticmethod
    def EnumAllComponents():
        """Enumerate all controls in no special order"""
        return GUIManager.components
    
    @staticmethod
    def _IAmHere(entity):
        """For internal use by GUI components"""
        if GUIManager.drawable:
            GUIManager.components2.add(entity)
        

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
    
    
    def __init__(self,rect=None,bgcolor=None,fgcolor=None):
        Drawable.__init__(self)
        self.rect = rect or [0,0,0,0]
        self._state = Component.STATE_NORMAL
        self.handlers = {}
        
        self.bgcolor = bgcolor
        self.fgcolor = fgcolor
        
        self.font = FontCache.get(defaults.letter_height_gui,defaults.font_gui)
        self.draworder = 51000
        self.disabled = False
        
    def GetDrawOrder(self):
        # Make sure the GUI is on top of everything else
        return self.draworder
    
    
    @property
    def rect(self):
        x,y,w,h = self._rect
        return (((x if x < defaults.resolution[0] else x-defaults.resolution[0])
            if x>=0 else defaults.resolution[0]+x),
            ((y if y < defaults.resolution[1] else y-defaults.resolution[1]) 
                if y>=0 else defaults.resolution[1]+y),w,h)
    
    @rect.setter
    def rect(self,*args):
        self._rect = args if len(args)==4 else args[0]
    
    @property
    def pos(self):
        x,y = self._rect[:2] 
        return (((x if x < defaults.resolution[0] else x-defaults.resolution[0])
            if x>=0 else defaults.resolution[0]+x),
            ((y if y < defaults.resolution[1] else y-defaults.resolution[1]) 
                if y>=0 else defaults.resolution[1]+y))
    
    @pos.setter
    def pos(self,*args):
        self._rect[:2] = args if len(args)==2 else args[0]
        
    @property
    def x(self):
        x = self._rect[0]
        return (x if x < defaults.resolution[0] else x-defaults.resolution[0]) \
            if x>=0 else defaults.resolution[0]+x
    
    @x.setter
    def x(self,x):
        self._rect[0] = x 
            
    @property
    def y(self):
        y = self._rect[1]
        return (y if y < defaults.resolution[1] else y-defaults.resolution[1]) \
            if y>=0 else defaults.resolution[1]+y
    
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
        


    # Event handling
    def __add__(self,*args):
        event, handler = args if len(args)==2 else args[0]
        self.handlers.setdefault(event,[]).append(handler)
        return self
    
    
    
    def Fire(self,name,*args,**kwargs):
        """Fire a named events, forward arguments to handlers""" 
        try:
            for elem in self.handlers[name]:
                elem(*([self]+list(args)),**kwargs)
        except KeyError:
            pass

    def _MkPos(self,*args):
        x,y = args if len(args)==2 else args[0]
        return math.floor(x+self.x),math.floor(y+self.y)

    def _DrawMyRect(self):
        Component.DrawRect(self.rect,self.bgcolor if self.bgcolor else self.__class__.COLORS[self.state],sf.Color.Black)
        
    def Draw(self):
        GUIManager._IAmHere(self)
        
        inp = Renderer.app.GetInput()
        mx,my = inp.GetMouseX(),inp.GetMouseY()
        
        self.buttons = inp.IsMouseButtonDown(sf.Mouse.Left),inp.IsMouseButtonDown(sf.Mouse.Right)
        self.hit = (self.x+self.w>mx>self.x and self.y+self.h>my>self.y)

        self.Fire("update")
                
        # XXX we don't need to pass them as arguments, they are members ...
        self.DrawMe(mx,my,self.hit,self.buttons,
            self.__dict__.setdefault("prev_buttons",(False,False)),
            self.__dict__.setdefault("prev_hit",False))
        
        self.prev_buttons = self.buttons
        self.prev_hit = self.hit
        
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
        
        
class HasAText(Component):
    """ Internal base class for all GUI components which have a textual caption somewhere.
    The class defines also a tooltip, which is, however, not currently
    drawn automatically. """
    
    def __init__(self,text="No text specified",tip=None,**kwargs):
        Component.__init__(self,**kwargs)
        self.text = text
        self.tip = tip
        
    @property
    def text(self):
        return self._text
        
    @text.setter
    def text(self,text):
        self._text = text
        self._text_cached = sf.String(self._text,Font=self.font,Size=defaults.letter_height_gui)
        return self
    
    @property
    def tip(self):
        return self._tip
        
    @tip.setter
    def tip(self,tip):
        self._tip = tip
        return self
    
    def _DrawTextCentered(self):
        ts = self._text.split("\n")
        self._text_cached.SetPosition(*self._MkPos(self.w*0.5 - len(ts[0])*defaults.letter_height_gui*0.25,
            self.h*0.5 - len(ts)*defaults.letter_height_gui*0.55))
        
        self._text_cached.SetColor(self.fgcolor if self.fgcolor else sf.Color.White)
        Renderer.app.Draw(self._text_cached)


class Button(HasAText):
    """A normal button control, enough said"""
    
    COLORS = {
        Component.STATE_NORMAL   : sf.Color(50,50,50),
        Component.STATE_ACTIVE   : sf.Color(180,75,75),
        Component.STATE_HOVER    : sf.Color(90,75,75),
        Component.STATE_DISABLED : sf.Color(160,160,160),
    }
    
    def __init__(self,**kwargs):
        HasAText.__init__(self,**kwargs)

    def DrawMe(self,mx,my,hit,buttons,prev_buttons,prev_hit):
        if self.disabled:
            self.state = Component.STATE_DISABLED
        elif hit:
            if not prev_hit:
                self.Fire("mouse_enter")
            
            self.state = Component.STATE_ACTIVE if buttons[0] else Component.STATE_HOVER
            if buttons[0] and not prev_buttons[0]:
                self.Fire("click")
                
            if not buttons[0] and prev_buttons[0]:
                self.Fire("release")
        else:
            if prev_hit:
                self.Fire("mouse_leave")
            self.state = Component.STATE_NORMAL
         
        # XXX Draw tooltip somewhere?   
        #
        #if hit:
        #     tc = sf.String(self._text,Font=self.font,Size=defaults.letter_height_gui)
        #     tc.SetPosition(self.x+5,self.y+self.h+10)
        #     Renderer.app.Draw(tc)
            
        self._DrawMyRect()
        self._DrawTextCentered()

        
class ToggleButton(HasAText):
    """A persistent 2-state button, like a checkbox but easier to implement :-)"""
    
    COLORS = {
        Component.STATE_NORMAL   : sf.Color(150,50,50),
        Component.STATE_ACTIVE   : sf.Color(50,150,50),
        Component.STATE_HOVER    : sf.Color(90,75,75),
        Component.STATE_DISABLED : sf.Color(40,40,40),
    }
    
    def __init__(self,on=False,text="On\x00Off",**kwargs):
        HasAText.__init__(self,**kwargs)
        
        self.text_choices = text.split("\x00")
        self.text_choices = self.text_choices if len(self.text_choices)==2 else self.text_choices*2
        self.on = on
        
    @property
    def on(self):
        return self._on 
    
    @on.setter
    def on(self,on):
        self._on = on
        self.text = self.text_choices[0 if on else 1]
      
      
    def DrawMe(self,mx,my,hit,buttons,prev_buttons,prev_hit):
        
        if self.disabled:
            self.state = Component.STATE_DISABLED
        elif hit:
            if buttons[0] and not prev_buttons[0]:
                self.Fire("click")
                self.on = not self.on
                
                self.Fire("toggle",self.on)
                self.Fire("on" if self.on else "off")
                
            if not buttons[0] and prev_buttons[0]:
                self.Fire("release")
        
        self.state = Component.STATE_ACTIVE if self.on else Component.STATE_NORMAL
            
        self._DrawMyRect()
        self._DrawTextCentered()
        
        
        
        
        
        
        
        
    
        
        
        