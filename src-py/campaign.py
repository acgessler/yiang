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

# Python core
import os

# PySFML
import sf

# My own stuff
import defaults
from game import Entity
from renderer import NewFrame, Renderer
from tile import AnimTile
from player import Player
from keys import KeyMapping
from level import Level

class CampaignLevel(Level):
    """Slightly adjust the default level behaviour to allow for the
    world's map to be rendered fluently."""
    
    def __init__(self, level, game, lines, name="Map of the World", minimap="map.bmp"):
        Level.__init__(self,level,game, lines, 
            color=(15,30,15),
            postfx=[("ingame2.sfx",())],
            name=name,
            gravity=0.0,
            autoscroll_speed=0.0,
            scroll=Level.SCROLL_ALL)
        
        self.minimap = minimap
        if defaults.world_draw_hud is True:
            self._LoadHUD()
        
    def Draw(self, time, dtime):
        Level.Draw(self,time,dtime)
        
        if defaults.world_draw_hud is True:
            self._DrawHUD()
            
    def _LoadHUD(self):
        self.minimap_img, self.minimap_sprite = sf.Image(), None
        if not self.minimap_img.LoadFromFile(os.path.join(defaults.data_dir, "levels", str(self.level), self.minimap )):
            print("Failure loading HUD minimap from {0}".format(self.minimap))
            return
            
        self.minimap_sprite = sf.Sprite(self.minimap_img)
        
        x = defaults.resolution[0]*defaults.minimap_size
        y = x*self.minimap_img.GetWidth()/self.minimap_img.GetHeight()
        self.minimap_sprite.SetPosition(100,defaults.resolution[1]-y-100)
        
        self.minimap_sprite.Resize(x,y)
        self.minimap_sprite.SetColor(sf.Color(0xff,0xff,0xff,0x90))
        self.minimap_sprite.SetBlendMode(sf.Blend.Alpha)
            
    def _DrawHUD(self):
        if self.minimap_sprite is None:
            return
        
        Renderer.app.Draw(self.minimap_sprite)
        
    def Scroll(self,pos):
        # Center the viewport around the player (this completely
        # replaces the original implementation)
        self.SetOrigin((pos[0]-defaults.tiles[0]/2,pos[1]-defaults.tiles[1]/2))
        

class LevelEntrance(AnimTile):
    """Only found on the campaign world map, marks the entrance
    to a particular level"""
    
    def __init__(self,text,height,frames,speed,states,next_level=5,draworder=15000):
        AnimTile.__init__(self,text,height,frames,speed,states,draworder=draworder)
        self.next_level = next_level
        self.done = False
        
    def Interact(self,other):
        if isinstance(other,Player) and Renderer.app.GetInput().IsKeyDown(KeyMapping.Get("interact")):
            self._RunLevel()
        
        return Entity.ENTER
    
    def Update(self,time_elapsed,time):
        AnimTile.Update(self,time_elapsed,time)
        done = (self.next_level in self.game.GetDoneLevels())
        if done != self.done:
            self.done = done
            self.SetState(1)
        
    def _RunLevel(self):
        if self.done is True:
            return
        
        # try to obtain the written name of the level by
        # skimming through its shebang line looking
        # for name="..."
        file = os.path.join(defaults.data_dir, "levels", str(self.next_level)+".txt")
        name = "Level {0}".format(self.next_level)
        try:
            with open(file,"rt") as file:
                import re
                look = re.search(r"name=\"(.+?)\"",file.read(250))
                if not look is None:
                    name = look.groups()[0]
                    print("Guess level name for {0}: {1}".format(self.next_level,name))
        except IOError:
            # LevelLoader will take care of this error, we don't bother for now
            pass
        
        accepted = (KeyMapping.Get("accept"),KeyMapping.Get("escape"))
        def on_close(key):
            if key == accepted[0]:
                self.game.PushLevel(self.next_level)
                raise NewFrame()
            
        self.game.FadeOutAndShowStatusNotice("""Enter '{1}'? 
You might die at this place, so be careful. 

Press {0} to risk it and {2} to leave.""".format(
                KeyMapping.GetString("accept"),
                name,
                KeyMapping.GetString("escape")),
            defaults.game_over_fade_time,(550,85),0.0,accepted,sf.Color.White,on_close)
        
        
class Blocker(AnimTile):
    pass






        

        