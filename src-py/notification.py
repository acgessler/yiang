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

# My own stuff
import defaults
from game import Entity, NewFrame
from player import Player
from keys import KeyMapping
from fonts import FontCache
from renderer import Drawable, Renderer

class MessageBox(Drawable):
    """Implements a reusable, generic message box that is drawn as overlay"""
    
    NO_FADE_IN, NO_FADE_OUT = 0x10000,0x20000
    
    def __init__(self, text,
        fade_time=1.0,
        size=(550,120),
        auto_time=0.0,
        break_codes=(KeyMapping.Get("accept")),
        text_color=sf.Color.Red,
        on_close=lambda x:None,
        flags=0):
        
        """Create a message box.
        XXX document parameters
        """
        Drawable.__init__(self)
        self.result = []
        self.break_codes = break_codes
        self.fade_time = fade_time
        self.text_color = text_color
        self.auto_time = auto_time
        self.text = text
        self.on_close = on_close
        self.size = size
        self.flags |= flags
                
        from posteffect import FadeOutOverlay
        
        if self.flags & MessageBox.NO_FADE_IN == 0:
            self.fade = FadeOutOverlay(self.fade_time, on_close=lambda x:None)
                
    def Draw(self):
        
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            
            if self.flags & MessageBox.NO_FADE_IN == 0:
                Renderer.AddDrawable(self.fade)
                
        curtime = self.clock.GetElapsedTime() 
        if self.auto_time > 0.0 and curtime > self.auto_time:
            self.result.append(False)
            self._RemoveMe()
                
        for event in Renderer.GetEvents():
            if event.Type == sf.Event.KeyPressed and event.Key.Code in self.break_codes:
                self.result.append(event.Key.Code)
                self._RemoveMe()
                    
        MessageBox._DrawStatusNotice(self.text, self.size, self.text_color, min(1.0, curtime * 5 / self.fade_time))
        return True
            
    def _RemoveMe(self):
        if self.flags & MessageBox.NO_FADE_IN == 0:
            Renderer.RemoveDrawable(self.fade)
            
        Renderer.RemoveDrawable(self)
      
        if self.flags & MessageBox.NO_FADE_OUT == 0:
            from posteffect import FadeInOverlay
            Renderer.AddDrawable(FadeInOverlay(self.fade_time * 0.5, defaults.fade_stop if not hasattr(self, "fade") else self.fade.GetCurrentStrength()))
                
        self.on_close(self.result[-1])
        raise NewFrame()
            
    def GetDrawOrder(self):
        return 1100
        
        
    @staticmethod
    def _DrawStatusNotice(text,size=(550,120),text_color=sf.Color.Red,alpha=1.0):
        """Utility to draw a messagebox-like status notice in the
        center of the screen."""
        
        # FIX: avoid odd numbers to get pixel-exact font rendering
        size = (size[0]&~0x1,size[1]&~0x1)
        
        fg,bg = sf.Color(160,160,160,int(alpha*255)),sf.Color(50,50,50,int(alpha*255))
        
        shape = sf.Shape()
        shape.AddPoint((defaults.resolution[0]-size[0])/2,(defaults.resolution[1]-size[1])/2,fg,bg )
        shape.AddPoint((defaults.resolution[0]+size[0])/2,(defaults.resolution[1]-size[1])/2,fg,bg )
        shape.AddPoint((defaults.resolution[0]+size[0])/2,(defaults.resolution[1]+size[1])/2,fg,bg )
        shape.AddPoint((defaults.resolution[0]-size[0])/2,(defaults.resolution[1]+size[1])/2,fg,bg )
        
        shape.SetOutlineWidth(4)
        shape.EnableFill(True)
        shape.EnableOutline(True)
        Renderer.app.Draw(shape)
        pos = ((defaults.resolution[0]-size[0]+30)/2,(defaults.resolution[1]-size[1]+18)/2)
        
        text.SetColor(sf.Color.Black if text_color != sf.Color.Black else sf.Color(220,220,220))
        text.SetPosition(pos[0]+1,pos[1]+1)
        Renderer.app.Draw(text)

        text.SetColor(text_color)
        text.SetPosition(pos[0],pos[1])
        Renderer.app.Draw(text)
        

class SimpleNotification(Entity):
    """The SimpleNotification tile displays a popup box when the players
    enters its area. This is used extensively for story telling."""

    def __init__(self, text, desc="<unnamed>", text_color=sf.Color.Red, only_once=True, width=1, height=1, line_length=50, format=True):
        Entity.__init__(self)
        self.text = text
        self.use_counter = 1 if only_once is True else 1000000000 
        self.dim = (width, height)
        self.text_formatted = ""
        self.line_length = line_length
        self.text_color = sf.Color(*text_color) if isinstance(text_color, tuple) else text_color
        self.desc = desc
        
        if format is True:
            try:
                self.text = self.text.format(enter=KeyMapping.GetString("escape"), \
                  accept=KeyMapping.GetString("accept"))
            except:
                print("format() failed, consider passing False for the 'format' parameter")
        
        # format the text nicely
        # XXX monospace is not everything, really
        for paragraph in self.text.split("\n"):
            cnt = 0
            for word in paragraph.split(" "):
                if cnt + len(word) > line_length:
                    self.text_formatted += "\n"
                    cnt = 0
                self.text_formatted += word + " "
                cnt += len(word)
            
            self.text_formatted += "\n\n"
        
        self.box_dim = (line_length * 11, self.text_formatted.count("\n") * 16)
        
    def Interact(self, other):
        if isinstance(other, Player) and self.use_counter > 0 and not hasattr(self, "running"):
            
            print("Show notification '{0}', use counter: {1}".format(self.desc, self.use_counter))
            accepted = (KeyMapping.Get("escape"), KeyMapping.Get("accept"))
            
            # closure to be called when the player has made his decision
            def on_close(key):
                delattr(self, "running")
                self.use_counter -= 1
                self.level.PopAutoScroll()
                
                if self.use_counter == 0:
                    self.game.RemoveEntity(self)
                    print("Disable notification '{0}'".format(self.desc))
                    
            self.level.PushAutoScroll(0.0)
            
            self.running  = True
            self.game._FadeOutAndShowStatusNotice( sf.String(self.text_formatted,
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
            )), defaults.game_over_fade_time, self.box_dim , 0.0, accepted, self.text_color, on_close)
            
        return Entity.ENTER
    
    def GetBoundingBox(self):
        return (self.pos[0], self.pos[1], self.dim[0], self.dim[1])


    
