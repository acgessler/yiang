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
        self.minimap_offline = game.GetCookie("lv_{0}_minimap_offline".format(level),[])
        if defaults.world_draw_hud is True:
            self._LoadHUD()
        
    def Draw(self, time, dtime):
        Level.Draw(self,time,dtime)
        
        if defaults.world_draw_hud is True:
            self._DrawHUD()
            
    def _LoadHUD(self):
        self.minimap_img, self.minimap_vis, self.minimap_sprite = sf.Image(), sf.Image(), None
        if not self.minimap_img.LoadFromFile(os.path.join(defaults.data_dir, "levels", str(self.level), self.minimap )):
            print("Failure loading HUD minimap from {0}".format(self.minimap))
            return
        
        # the visible minimap is initially black and is uncovered as the player moves
        w,h = self.minimap_img.GetWidth(),self.minimap_img.GetHeight()
        b = bytearray(b'\x00\x00\x00')
        b.append(defaults.minimap_alpha)
        self.minimap_vis.LoadFromPixels(w,h, bytes(b) * (w*h))
        
        if len(self.minimap_offline) != h:
            for y in range(h):
                self.minimap_offline.append([0.0]*w)
      
        else: # recover the saved minimap
            for y in range(h):
                for x in range(w):
                    col,s = self.minimap_img.GetPixel(x,y),self.minimap_offline[y][x]
                    col.r *= s
                    col.g *= s
                    col.b *= s
                    col.a = max(defaults.minimap_alpha, col.a*s*0.5)
                    self.minimap_vis.SetPixel(x,y,col)
            
        self.minimap_sprite = sf.Sprite(self.minimap_vis)
        
        w = max(w, defaults.resolution[0]*defaults.minimap_size)
        h = max(h,w*self.minimap_img.GetWidth()/self.minimap_img.GetHeight())
        
        # -0.5 for pixel-exact mapping, seemingly SFML is unable to do this for us
        x,y = 100,defaults.resolution[1]-h-100
        self.minimap_sprite.SetPosition(x-0.5,y-0.5)
        self.minimap_sprite.Resize(w,h)
        
        self.minimap_sprite.SetColor(sf.Color(0xff,0xff,0xff,0xff))
        self.minimap_sprite.SetBlendMode(sf.Blend.Alpha)
        
        # finally, construct the rectangle around the minimap
        self.minimap_shape = sf.Shape()
        bcol = sf.Color(0x10,0x10,0x0,0xff)
        
        # interestingly, the 0.5px offset is not needed for
        # lines and other geometric shapes. Awesome.
        self.minimap_shape.AddPoint(x,y,bcol,bcol)
        self.minimap_shape.AddPoint(x+w,y,bcol,bcol)
        self.minimap_shape.AddPoint(x+w,y+h,bcol,bcol)
        self.minimap_shape.AddPoint(x,y+h,bcol,bcol)

        self.minimap_shape.SetOutlineWidth(3)
        self.minimap_shape.EnableFill(False)
        self.minimap_shape.EnableOutline(True)
        
    def UncoverMinimap(self,pos,radius=None):
        """Uncover all minimap pixels given a position on the map
        and a radius, in tile units as well."""
        radius = radius or (defaults.tiles[0]+defaults.tiles[1])*0.5
        
        # tiles map one by one to pixels on the minimap
        w,h = self.minimap_img.GetWidth(),self.minimap_img.GetHeight()
        rsq = radius**2
        for y in range(max(0, int(pos[1]-radius) ), min(h-1,int(pos[1]+radius ))):
            for x in range(max(0, int(pos[0]-radius) ), min(w-1,int(pos[0]+radius ))):
                dsq = (y-pos[1])**2 + (x-pos[0])**2
                if dsq > rsq:
                    continue
                
                if self.minimap_offline[y][x] >= 1.0:
                    continue
                
                col = self.minimap_img.GetPixel(x,y) 
                
                dsq = min(1.0, 1.7 - dsq*1.7/rsq)
                if dsq < self.minimap_offline[y][x]:
                    continue
                
                self.minimap_offline[y][x] = dsq
                col.r *= dsq
                col.g *= dsq
                col.b *= dsq
                col.a = max(defaults.minimap_alpha, col.a*dsq*0.5)
                    
                self.minimap_vis.SetPixel(x,y, col)
                
        ipos = (int(pos[0]),int(pos[1]))
               
        # draw a cross around the player's position
        crossdim = 6
        for i in range(-1,2):
            for y in range(max(0, int(pos[1]-crossdim) ), min(h-1,int(pos[1]+crossdim +1 ))):
                self.minimap_vis.SetPixel(ipos[0]+i,y,sf.Color(0xff,0,0,0xff))
                self.minimap_offline[y][ipos[0]+i] = False
            
            for x in range(max(0, int(pos[0]-crossdim) ), min(w-1,int(pos[0]+crossdim +1 ))):
                self.minimap_vis.SetPixel(x,ipos[1]+i,sf.Color(0xff,0,0,0xff))
                self.minimap_offline[ipos[1]+i][x] = False
                
            
    def _DrawHUD(self):
        if self.minimap_sprite is None:
            return
        
        self.game.DrawSingle(self.minimap_sprite)
        self.game.DrawSingle(self.minimap_shape)
        
    def Scroll(self,pos):
        # Center the viewport around the player (this completely
        # replaces the original implementation)
        self.SetOrigin((pos[0]-defaults.tiles[0]/2,pos[1]-defaults.tiles[1]/2))
        
        # (Hack) This ought to be in the player's logic, but
        # this way we can safe a custom Player-derived class.
        if hasattr(self,"oldpos"):
            if abs(pos[0]-self.oldpos[0])<1.0 and abs(pos[1]-self.oldpos[1])<1.0:
                return
            
        self.UncoverMinimap(pos)
        self.oldpos = pos
        

class LevelEntrance(AnimTile):
    """Only found on the campaign world map, marks the entrance
    to a particular level"""
    
    def __init__(self,text,height,frames,speed,states,next_level=5,draworder=15000,halo_img=None):
        AnimTile.__init__(self,text,height,frames,speed,states,draworder=draworder,halo_img=halo_img)
        self.next_level = next_level
        self.done = False
        
    def Interact(self,other):
        if isinstance(other,Player) and Renderer.app.GetInput().IsKeyDown(KeyMapping.Get("interact")) and not hasattr(self,"now_locked"):
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
        
        self.now_locked = True
        
        
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
                delattr( self, "now_locked" )
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






        

        