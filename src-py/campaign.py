#! /usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [campaign.py]
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

# Python core
import os
import random

from stubs import *
from player import Player


class CampaignLevel(Level):
    """Slightly adjust the default level behaviour to allow for the
    world's map to be rendered fluently."""
    
    def __init__(self, level, game, lines, 
        name="Map of the World", 
        minimap="map.bmp", 
        overlays=["extra_items.txt"], 
        color=(15,30,15),
        skip_validation=True
    ):
        Level.__init__(self,level,game, lines, 
            color=color,
            postfx=[("ingame2.sfx",())],
            name=name,
            gravity=0.0,
            autoscroll_speed=0.0,
            scroll=Level.SCROLL_ALL,
            distortion_params=(0,0,0),
            skip_validation=skip_validation)
        
        self.status_message = ""
        self.SetStatusMessage("")
        
        for elem in overlays:
            self._ReadOverlay(elem)
            
        # need to do this again, we might not have had a player the last time we tried
        self._UpdateEntityList()
        self._ComputeOrigin()
        
        self.minimap = minimap
        self.minimap_offline = game.GetCookie("lv_{0}_minimap_offline".format(level),[])
        if defaults.world_draw_hud is True:
            self._LoadHUD()
            
        
            
    def SetStatusMessage(self,msg,color=sf.Color.Yellow):
        self.status_color = color
        
        if not msg:
            self.status_msg_text = None
            return
        
        
        if self.status_message == msg:
            if self.status_msg_text:
                self.status_msg_text.SetColor(color)
            return
        
        self.status_message = msg
        
        height = defaults.letter_height_worldmap_status
        font = FontCache.get(height, face=defaults.font_status)
        
        self.status_msg_text = sf.String(msg,Font=font,Size=height)
        self.status_msg_pos = 35, defaults.resolution[1] - self.game.GetLowerStatusBarHeight()*defaults.tiles_size_px[1]/2 - height/2  
        #self.status_msg_text.SetPosition(*self.status_msg_pos)
        self.status_msg_text.SetColor(color)
        
        self.status_msg_fade = sf.Clock()
            
    def _ReadOverlay(self,filename):
        cnt = 0
        filename = os.path.join(self.lvbase, filename)
        with open(filename,"rt") as extra:
            lines = [l.split(" ") for l in extra.read().split("\n") if len(l) > 0 and not l[0] == "#"]
            for line in lines:
                if len(line) != 3:
                    print("Error reading overlay - each non-comment line must consist of three tokens, ignoring this line: {0}".format(line))
                    continue
                    
                x,y,e = line
                
                self._LoadSingleTile(e[1:3],e[0],int(x),int(y))
                cnt += 1
        print("Load level overlay {0}, got {1} tiles".format(filename,cnt))
        
    def Draw(self, time, dtime):
        self._GenToDeviceCoordinates()
        self._DoAutoScroll(dtime)
        
        self._UpdateEntities(time,dtime)
        self._UpdateDistortion(time,dtime)
        self._DrawEntities()
        self._UpdateEntityList()
        
        self.game._DrawHearts()
        
        #self.game.DrawStatusBar()
        
        # draw minimap
        if defaults.world_draw_hud is True:
            self._DrawHUD()
                
        # draw & update status message
        if not self.status_msg_text is None:
            c = self.status_color
            a = int(240.0 * (1.0 - min(1.0, abs((self.status_msg_fade.GetElapsedTime()*0.4+0.05) - 0.6) )))
            if a > 0:
                self.status_msg_text.SetColor(sf.Color( 60,60,60, a))
                self.status_msg_text.SetPosition(self.status_msg_pos[0]-1,self.status_msg_pos[1])
                self.game.DrawSingle(self.status_msg_text)
                
                self.status_msg_text.SetColor(sf.Color( c.r, c.g, c.b, a))
                self.status_msg_text.SetPosition(*self.status_msg_pos)
                self.game.DrawSingle(self.status_msg_text)
            else:
                self.status_msg_text = None
                self.status_message = ""
        #elif hasattr(self,"status_msg_fade") and self.status_msg_fade.GetElapsedTime() > 4.0:
        #    self.status_msg_text = ""
            
    def _GetImg(self,img):
        sprite = sf.Sprite(img)
        
        w,h = img.GetWidth(),img.GetHeight()
        w = max(w, defaults.resolution[0]*defaults.minimap_size)
        h = max(h,w*img.GetHeight()/img.GetWidth())
        
        # -0.5 for pixel-exact mapping, seemingly SFML is unable to do this for us
        x,y = 35,25 #defaults.resolution[1]-h-100
        sprite.SetPosition(x-0.5,y-0.5)
        sprite.Resize(w,h)
        
        sprite.SetColor(sf.Color(0xff,0xff,0xff,0xff))
        sprite.SetBlendMode(sf.Blend.Alpha)
        return sprite,w,h,x,y
    
    def _RebuildMinimap(self):
        w,h = self.minimap_img.GetWidth(),self.minimap_img.GetHeight()
        for y in range(h):
            for x in range(w):
                col,s = self.minimap_img.GetPixel(x,y),self.minimap_offline[y][x]
                col.r *= s
                col.g *= s
                col.b *= s
                col.a = max(defaults.minimap_alpha, col.a*s*0.5)
                self.minimap_vis.SetPixel(x,y,col)
            
    def _LoadHUD(self):
        self.minimap_vis, self.minimap_sprite = sf.Image(), None
        #if not self.minimap_img.LoadFromFile(os.path.join(defaults.data_dir, "levels", str(self.level), self.minimap )):
        self.minimap_img = TextureCache.Get(os.path.join(defaults.data_dir, "levels", str(self.level), self.minimap ))
        if not self.minimap_img:
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
            self._RebuildMinimap()
            
        self.minimap_sprite,self.sw,self.sh,self.sx,self.sy = self._GetImg(self.minimap_vis)
        
        # finally, construct the rectangle around the minimap
        self.minimap_shape = sf.Shape()
        bcol = sf.Color(0x10,0x10,0x0,0xff)
        
        # interestingly, the 0.5px offset is not needed for
        # lines and other geometric shapes. Awesome.
        self.minimap_shape.AddPoint(self.sx,self.sy,bcol,bcol)
        self.minimap_shape.AddPoint(self.sx+self.sw,self.sy,bcol,bcol)
        self.minimap_shape.AddPoint(self.sx+self.sw,self.sy+self.sh,bcol,bcol)
        self.minimap_shape.AddPoint(self.sx,self.sy+self.sh,bcol,bcol)

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
            try:
                for y in range(max(0, int(pos[1]-crossdim) ), min(h-1,int(pos[1]+crossdim +1 ))):
                    self.minimap_vis.SetPixel(ipos[0]+i,y,sf.Color(0xff,0,0,0xff))
                    self.minimap_offline[y][ipos[0]+i] = False
            
                for x in range(max(0, int(pos[0]-crossdim) ), min(w-1,int(pos[0]+crossdim +1 ))):
                    self.minimap_vis.SetPixel(x,ipos[1]+i,sf.Color(0xff,0,0,0xff))
                    self.minimap_offline[ipos[1]+i][x] = False
            except IndexError:
                # this happens if the player moves outside the map
                pass
                
    def _SetPlayerPos(self,mx,my):
        for entity in self.EnumAllEntities():
            if isinstance(entity,Player):
            
                entity.SetPosition((mx,my))
                self.Scroll((mx,my))
                
                # needed or the cross at the player position
                # remains sticky at its old place.
                self._RebuildMinimap()
                
                print("CampaignLevel: Move player to {0}\{1}".format(mx,my))
                raise NewFrame()
        else:
            assert False # we have a player there must be one!
            
    def _DrawHUD(self):
        if self.minimap_sprite is None:
            return
        
        if defaults.debug_godmode is True:
            if not hasattr(self,"minimap_debug_shape"):
                self.minimap_debug_shape,w,h,x,y = self._GetImg(self.minimap_img)
                
            inp = Renderer.app.GetInput()
            if inp.IsMouseButtonDown(sf.Mouse.Left):
                if not hasattr(self,"block_hud_click"):
                    self.block_hud_click = True
                    mx,my = inp.GetMouseX(),inp.GetMouseY()
                    if self.sx <= mx < self.sx+self.sw and self.sy <= my < self.sy+self.sh:
                        mx -= self.sx
                        my -= self.sy
                        
                        self._SetPlayerPos(mx,my)
            else:
                try:
                    delattr(self,"block_hud_click")
                except AttributeError:
                    pass
                    
            self.game.DrawSingle(self.minimap_debug_shape)
            
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
        
    def ToCameraCoordinates(self, coords):
        # This fixes small gaps between the tiles caused by ascii characters which 
        # are not as tall as they could be for their font size (i.e. 'a' leaves a
        # gap underneath)
        return ( (coords[0] - self.origin[0]), (coords[1] - self.origin[1])* 28.8/30.0)
    
    def _GenToDeviceCoordinates(self):
        def doit(coords):
            return self.game.ToDeviceCoordinates( self.ToCameraCoordinates(coords) )
        
        self.ToCameraDeviceCoordinates = doit
    
    def _UpdateEntities(self,time,dtime):
        # As a further optimization, we will only include visible entities
        # in our set of active entities. The normal implementation includes
        # near entities as well.
        self.entities_active = set()
        for n,window in self._EnumWindows():
            if n > 1:
                continue
            
            for entity in window:
                self.entities_active.add(entity)
                entity.in_visible_set = True
                
        self.entities_active.update(self.window_unassigned)
        for entity in self.EnumActiveEntities():
            entity.Update(time,dtime)
        
        
class CampaignPlayer(Player):
    """Slightly adjust the default player behaviour for the world map.
    For example, shooting does not work on the world map and the
    respective keys remain disabled"""
    
    def __init__(self, text, width, height, ofsx, move_freely=True, draworder=10500):
        Player.__init__(self,text,width,height,ofsx,move_freely,draworder)
        
    def _Shoot(self):
        return
    

class CampaignTile(Tile):
    """Tile for the campaign map, randomly permutes parts of
    its image to achieve greater realism"""
    
    def __init__(self,text, *args, permute=True, status_msg="" , **kwargs):
        # randomly permute every tile into 4 different display tiles.
        # if we made more, the number of different strings to be rendered
        # would get too high, so performance would potentially degrade.
        rand = random.random() 
        sp = list(("".join(reversed(n)) if rand>0.5 else n) for n in text.split("\n"))
        Tile.__init__(self, "\n".join(reversed(sp) if random.random()>0.5 and permute is True else sp), *args,double=True,permute=False,**kwargs)
        
        self.status_msg = status_msg
        
    def Interact(self,other):
        
        if self.status_msg:
            self.level.SetStatusMessage(self.status_msg)
            
        return Tile.Interact(self,other)
    
    
class CampaignAnimTile(AnimTile):
    """Tile for the campaign map, randomly permutes parts of
    its image to achieve greater realism"""
    
    def __init__(self,text, *args, permute=True, status_msg="" , **kwargs):
        # randomly permute every tile into 4 different display tiles.
        # if we made more, the number of different strings to be rendered
        # would get too high, so performance would potentially degrade.
        rand = random.random() 
        sp = list(("".join(reversed(n)) if rand>0.5 else n) for n in text.split("\n"))
        AnimTile.__init__(self, "\n".join(reversed(sp) if random.random()>0.5 and permute is True else sp), *args,double=True,**kwargs)
        
        
    def Interact(self,other):
        return AnimTile.Interact(self,other)
    

class LevelEntrance(AnimTile):
    """Only found on the campaign world map, marks the entrance
    to a particular level"""
    
    def __init__(self,text,height,frames,speed,states,next_level=5,draworder=15000,halo_img=None,dropshadow=True):
        AnimTile.__init__(self,text,height,frames,speed,states,draworder=draworder,halo_img=halo_img,dropshadow=dropshadow)
        self.next_level = next_level
        self.done = False
        
    def Interact(self,other):
        if isinstance(other,Player) and not hasattr(self,"now_locked"):
            if self.done is True and defaults.debug_godmode is False:
                self.level.SetStatusMessage(_("You completed this level!"),sf.Color.Green)
            else:
                self.level.SetStatusMessage(_("Press {0} to enter {1}").format(KeyMapping.GetString("accept"),self._GuessLevelName()))
                if Renderer.app.GetInput().IsKeyDown(KeyMapping.Get("accept")):
                    self._RunLevel()
        
        return Entity.ENTER
    
    def Update(self,time_elapsed,time):
        AnimTile.Update(self,time_elapsed,time)
        done = (self.next_level in self.game.GetDoneLevels())
        if done != self.done:
            self.done = done
            self.SetState(1)
            
    def _GuessLevelName(self):    
        return LevelLoader.GuessLevelName(self.next_level)
        
    def _RunLevel(self):
        if self.game.GetGameMode() in (Game.EDITOR,Game.EDITOR_HIDDEN) or hasattr(self,"now_locked"):
            return
        
        self.now_locked = True
        accepted = (KeyMapping.Get("accept"),KeyMapping.Get("escape"))
        def on_close(key):
            if key == accepted[0]:
                
                def pushit(x):
                    Renderer.RemoveDrawable(x)
                    
                    self.game.PopSuspend()
                    self.game.PushLevel(self.next_level)
                    
                    try:
                        delattr( self, "now_locked" )
                    except AttributeError:
                        pass
                    
                    #raise NewFrame()
                
                from posteffect import FadeOutOverlay
                Renderer.AddDrawable( FadeOutOverlay(defaults.enter_level_fade_time, fade_end=0.0, on_close=pushit) )
                return
            
            delattr( self, "now_locked" )
            self.game.PopSuspend()
        
        from notification import MessageBox
        self.game.FadeOutAndShowStatusNotice(_("""Enter '{1}'? 
You might die at this place, so be careful. 

Press {0} to risk it and {2} to leave.""").format(
                KeyMapping.GetString("accept"),
                self._GuessLevelName(),
                KeyMapping.GetString("escape")),
            defaults.messagebox_fade_time,(550,115),0.0,accepted,sf.Color.Black,on_close,flags=MessageBox.NO_FADE_OUT)
        
        self.game.PushSuspend()
        
        
class Blocker(Tile):
    """Blockers prevent the player from entering certain
    areas of the game world."""
    
    def __init__(self,text,width,height,draworder=15000,halo_img=None,need_levels=[],status_msg=None,dropshadow=True,opposite=False):
        Tile.__init__(self,text,width=width,height=height,draworder=draworder,halo_img=halo_img,dropshadow=dropshadow)
        self.need_levels = need_levels
        self.status_msg = status_msg or _("You cannot pass! I am a blocker of the ASCII world, wielder of the Fame of A-Dur.")
        self.opposite=self.nblocking=opposite
        self.old_color=sf.Color(0xff,0xff,0xff,0xff)
        if self.nblocking:
            self.color = sf.Color(0,0,0,0)

    def SetColor(self,color):

        Tile.SetColor(self,color)
        if self.nblocking:
            self.color = sf.Color(0,0,0,0)

        self.old_color = color

    def Interact(self,other):
        if isinstance(other, Player):
            self.level.SetStatusMessage(self.status_msg,sf.Color.Red)
        
        return Entity.ENTER if (defaults.debug_godmode or self.nblocking) else Entity.BLOCK
        
    def Update(self,time_elapsed,time):

        if not (set(self.need_levels ) - set(self.game.GetDoneLevels())):
            if self.opposite:
                self.color = self.old_color
                self.nblocking = False
            else:
                self.game.RemoveEntity(self)
            #raise NewFrame()
            
        Tile.Update(self,time_elapsed,time)
        
        




        

        

# vim: ai ts=4 sts=4 et sw=4
