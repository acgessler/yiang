#!/echo not intended to be executed
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [title.py]
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

import time,random,os
from stubs import *

from player import Player
from tileloader import TileLoader

SPECIAL_LEVEL_TITLE = 80000


class TitlePlayer(Player):
    """Dummy player for the title menu"""
    
    def __init__(self, *args, draworder=10500, **kwargs):
        Player.__init__(self,*args,draworder=draworder,**kwargs)
        self.block_input = True
        self.unkillable = 0xffffffff
        self.splatter_cnt = 25
        
    def __str__(self):
        return "<TitlePlayer>"
        
    def _Shoot(self):
        return
    
    def Draw(self):
        time = self.clock.GetElapsedTime()
        if 5<time<6.2:
            Player.Draw(self)
    
    def Update(self, time_elapsed, timet):
        # don't update unless 3 seconds passed
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            
        time = self.clock.GetElapsedTime()
        if time > 5.0:
            Player.Update(self,time_elapsed,timet)
            
        # spawn MUCH blood
        if time > 5.95 and self.splatter_cnt>0:
            # spread the spawning across multiple frames to reduce lagging
            time *= 15
            if int(time)-int(time-timet*15)>0:
                self.splatter_cnt -= 1
                
                base = list(self.pos)
                base[0] += random.uniform(-1,1)*5
                base[1] += random.uniform(-1,1)*2
                
                self._SpreadSplatterAt(base)
            
    def _SpreadSplatterAt(self,pos):
        # specialized splatter spawner for the title screen
        name = "splatter1.txt"
        remaining = defaults.min_death_sprites_player*5
        
        for i in range(remaining):
            t = TileLoader.Load(os.path.join(defaults.data_dir,"tiles_misc",name),self.game)
            
            t.RandomizeSplatter()
            t.SetPosition(pos)
            self.game.AddEntity(t)
            
            
class FadeTile(Tile):
    """Special tile for the two title texts, which both
    fade in after a second."""
    
    def __init__(self,*args, fade_start=1.0, fade_time=2.0, **kwargs):
        Tile.__init__(self, *args,draworder=100000,**kwargs)
        self.fade_time = fade_time
        self.fade_start = fade_start
        
    def Update(self, time_elapsed, time):
        
        if not hasattr(self,"clock"):
            self.SetColor(sf.Color(self.color.r,self.color.g,self.color.b,0))
            self.clock = sf.Clock()
            
        time = self.clock.GetElapsedTime()
        if time>self.fade_start:
            time = (time-1.0)/self.fade_time
            self.SetColor(sf.Color(self.color.r,self.color.g,self.color.b,0xff if time > 1.0 else int(time*0xff)))
    

class Title(Drawable):
    """This class is responsible for displaying the title level (80000)"""

    def __init__(self,on_close):
        Drawable.__init__(self)
        
        print("Entering title")
        
        self.bggame = Game(mode=Game.BACKGROUND,undecorated=True)
        b = self.bggame.LoadLevel(SPECIAL_LEVEL_TITLE,no_loadscreen=True)
        assert b
        self.AddSlaveDrawable(self.bggame)
            
        from posteffect import FlashOverlay
        Renderer.AddDrawable(FlashOverlay(sf.Color(150,0,0),flash_length=10))
            
        self.on_close = on_close
        self.trigger_close = False
        
    def Draw(self):
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            
        time = self.clock.GetElapsedTime()
        
        if time > 8.2 or time > 1 and any(e for e in Renderer.SwallowEvents() if e.Type == sf.Event.KeyPressed): 
            
            if self.trigger_close:
                return
            
            self.trigger_close = True
            
            def next(old):
                Renderer.RemoveDrawable(self)
                Renderer.RemoveDrawable(old)
                self.on_close()
            
            from posteffect import FadeOutOverlay
            Renderer.AddDrawable(FadeOutOverlay(fade_time=2.0,fade_end=0.1,on_close=next))
            
# vim: ai ts=4 sts=4 et sw=4
