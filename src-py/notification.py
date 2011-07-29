#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [notification.py]
# (c) 2008-2011 Yiang Development Team
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

from stubs import *
from entity import Entity,EntityWithEditorImage
from player import Player



def SimpleWrap(text,line_length):
    text_formatted = ""
    # XXX monospace is not the world, really -- this function should really take font metrics into account
    for paragraph in text.split("\n"):
        cnt = 0
        for word in paragraph.split(" "):
            if cnt + len(word) > line_length:
                text_formatted += "\n"
                cnt = 0
            text_formatted += word + " "
            cnt += len(word)
        
        text_formatted += "\n\n"
    return text_formatted


class MessageBox(Drawable):
    """Implements a reusable, generic message box that is drawn as overlay"""
    
    NO_FADE_IN, NO_FADE_OUT, NO_BLUR_IN, NO_BLUR_OUT = 0x10000,0x20000, 0x40000, 0x80000
    
    def __init__(self, text,
        fade_time=1.0,
        size=(550,120),
        auto_time=0.0,
        break_codes=(KeyMapping.Get("accept")),
        text_color=sf.Color.Red,
        on_close=lambda x:None,
        flags=0,
        bgtile='dialogbg.png'):
        
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
        self.tile =  TextureCache.GetFromTextures(bgtile) if bgtile else None
                
        from posteffect import FadeOutOverlay, BlurOutOverlay
        
        if self.flags & MessageBox.NO_FADE_IN == 0:
            self.fade = FadeOutOverlay(self.fade_time, on_close=lambda x:None)
            
        if self.flags & MessageBox.NO_BLUR_IN == 0:
            self.blur = BlurOutOverlay(self.fade_time, on_close=lambda x:None)
            
    def ProcessEvents(self):
        for event in Renderer.SwallowEvents():
            # break_codes == True serves as wildcard
            if event.Type == sf.Event.KeyPressed and (self.break_codes is True or event.Key.Code in self.break_codes):
                self.result.append(event.Key.Code)
                self._RemoveMe()
                
    def Draw(self):
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            
            if self.flags & MessageBox.NO_FADE_IN == 0:
                Renderer.AddDrawable(self.fade)
                
            if self.flags & MessageBox.NO_BLUR_IN == 0:
                Renderer.AddDrawable(self.blur)
 
                
        curtime = self.clock.GetElapsedTime() 
        if self.auto_time > 0.0 and curtime > self.auto_time:
            self.result.append(False)
            self._RemoveMe()
                    
        MessageBox._DrawStatusNotice(self.text, self.size, self.text_color, 
            min(1.0, curtime * 5 / self.fade_time
        ),tile=self.tile)
        return True
            
    def _RemoveMe(self):
        if hasattr(self,"fade"):
            Renderer.RemoveDrawable(self.fade)
        if hasattr(self,"blur"):
            Renderer.RemoveDrawable(self.blur)
            
        Renderer.RemoveDrawable(self)
      
        if self.flags & MessageBox.NO_FADE_OUT == 0:
            from posteffect import FadeInOverlay
            a,b = self.fade_time * 0.5, defaults.fade_stop if not hasattr(self, "fade") else self.fade.GetCurrentStrength()
            Renderer.AddDrawable(FadeInOverlay(a,b))
            
        if self.flags & MessageBox.NO_BLUR_OUT == 0:
            from posteffect import BlurInOverlay
            a,b = self.fade_time * 0.5, defaults.blur_stop if not hasattr(self, "blur") else self.blur.GetCurrentStrength()
            Renderer.AddDrawable(BlurInOverlay(a,b))
                
        if self.on_close:
            self.on_close(self.result[-1])
        raise NewFrame()
            
    def GetDrawOrder(self):
        return 1100
           
    @staticmethod
    def _DrawStatusNotice(text,size=(550,120),text_color=sf.Color.Red,alpha=1.0,auto_adjust=True,tile=None):
        """Utility to draw a messagebox-like status notice in the
        center of the screen."""
        
        # (hack) after adding translation support, most text boxes have changed their dimensions
        if auto_adjust:
            otext = text.GetText()
            x,y = size
            xbase,ybase = 20,10
            from fonts import FontCache
            face,height = FontCache.Find(text.GetFont())
            width = height/2
            
            cnt = 0 
            for n,line in enumerate(otext.split("\n")):
                x = max(x, len(line.strip()) * width + xbase) 
                if len(line.strip())==0:
                    cnt+=1
                else:
                    cnt = 0
            y = max(y,(n+1-cnt) * (height*1.09) + ybase)
            size = int(x),int(y)
        
        # FIX: avoid odd numbers to get pixel-exact font rendering
        size = (size[0]&~0x1,size[1]&~0x1)
        
        fg,bg = sf.Color(160,160,160,int(alpha*255)),sf.Color(50,50,45,int(alpha*255))
        
        r=defaults.resolution
        s=size
        
        bb = (r[0]-s[0])/2,(r[1]-s[1])/2,(r[0]+s[0])/2,(r[1]+s[1])/2
        if tile:
            Renderer.DrawTiled(tile,int(alpha*220),*bb)
        
        shape = sf.Shape()
        shape.AddPoint(bb[0], bb[1],fg,bg )
        shape.AddPoint(bb[2], bb[1],fg,bg )
        shape.AddPoint(bb[2], bb[3],fg,bg )
        shape.AddPoint(bb[0], bb[3],fg,bg )
        
        shape.SetOutlineWidth(4)
        shape.EnableFill(not tile)
        shape.EnableOutline(True)
        Renderer.app.Draw(shape)
        pos = ((defaults.resolution[0]-size[0]+30)/2,(defaults.resolution[1]-size[1]+18)/2)
        
        text.SetColor(sf.Color.Black if text_color != sf.Color.Black else sf.Color(220,220,220))
        text.SetPosition(pos[0]+1,pos[1]+1)
        Renderer.app.Draw(text)

        text.SetColor(text_color)
        text.SetPosition(pos[0],pos[1])
        Renderer.app.Draw(text)
        

class SimpleNotification(EntityWithEditorImage):
    """The SimpleNotification tile displays a popup box when the players
    enters its area. This is used extensively for story telling."""

    def __init__(self, text, desc=None, editor_image="notification_stub.png", bgtile='dialogbg.png',
        text_color=sf.Color.Red, 
        width=1, 
        height=1, 
        line_length=50, 
        format=True, 
        audio_fx=None, 
        only_once=True,
        no_blur=False
    ):
        EntityWithEditorImage.__init__(self,editor_image)
        self.text = text
        self.use_counter = 1 if only_once is True else 1000000000 
        self.dim = (width, height)
        self.text_formatted = ""
        self.line_length = line_length
        self.text_color = sf.Color(*text_color) if isinstance(text_color, tuple) else text_color
        self.desc = desc
        self.audio_fx = audio_fx
        self.bgtile = bgtile
        self.only_once = only_once
        self.blocked = False
        self.no_blur = no_blur
        
        if not self.desc:
            import uuid
            self.desc = str(uuid.uuid1())
        
        if format is True:
            try:
                self.text = self.text.format(enter=KeyMapping.GetString("escape"), \
                  accept=KeyMapping.GetString("accept"))
            except:
                print("format() failed, consider passing False for the 'format' parameter")
        
        # fix wrapping
        self.text_formatted = SimpleWrap(self.text,line_length)
        
        self.block_timer = sf.Clock()
        self.box_dim = (int(line_length *(defaults.letter_height_messagebox * 0.60) ), 
            int(self.text_formatted.count("\n") * defaults.letter_height_messagebox*1.0)
        )
        
    def Interact(self, other):
        inp = Renderer.app.GetInput()
        # note: the notification can always be activated by pressing interact,
        # regardless of the use counter.
        if isinstance(other, Player):
            if self.blocked:
                self.block_timer = sf.Clock()
        else:
            return Entity.ENTER
                
        if (self.game.__dict__.setdefault( "story_use_counter", {} )\
                .setdefault(self.desc,self.use_counter) > 0
                 or inp.IsKeyDown(KeyMapping.Get("interact")))\
            and not hasattr(self, "running")\
            and not self.game.GetGameMode() == Game.BACKGROUND and not self.blocked:
            
            print("Show notification '{0}', regular use counter: {1}".format(self.desc, self.use_counter))
            accepted = (KeyMapping.Get("escape"), KeyMapping.Get("accept"))
            
            # Fix: need to decrement the use counter immediately, or the player 
            # would be able to touch two adjacent bricks carrying the same
            # notification in a single frame, thus firing the popup
            # twice.
            self.game.story_use_counter[self.desc] -= 1
            self.blocked = True
            
            # closure to be called when the player has made his decision
            def on_close(key):
                delattr(self, "running")
                self.level.PopAutoScroll()
                
                if self.only_once and self.game.story_use_counter[self.desc] == 0:
                    #self.game.RemoveEntity(self)
                    print("Disable notification '{0}'".format(self.desc))
                elif not self.only_once:
                    self.block_timer = sf.Clock()
                    
            self.level.PushAutoScroll(0.0)
            self.running  = True
            
            if self.audio_fx:
                from audio import SoundEffectCache
                try:
                    SoundEffectCache.Get(self.audio_fx).SetVolume(4.0).Play()
                except: # be gratious (aka careless)
                    pass
            
            self.game._FadeOutAndShowStatusNotice( sf.String(self.text_formatted,
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
            )), defaults.game_over_fade_time, self.box_dim , 0.0, accepted, self.text_color, on_close, MessageBox.NO_BLUR_IN|MessageBox.NO_BLUR_OUT, bgtile=self.bgtile)
            
        return Entity.ENTER
    
    def Update(self,time,dtime):
        EntityWithEditorImage.Update(self,time,dtime)
        
        if not hasattr(self,'running') and self.blocked and self.block_timer.GetElapsedTime() > 1.0:
            self.blocked = False
    
    def GetBoundingBox(self):
        return (self.pos[0], self.pos[1], self.dim[0], self.dim[1])


    

# vim: ai ts=4 sts=4 et sw=4