#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [weapon.py]
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

# Python stuff
import os
import math

from stubs import *
from player import Player, InventoryItem

class ShootAnimStub(Tile):
    """Implements the text strings that are spawned whenever
    the player is killed."""

    def __init__(self,ttl=0.5):
        Tile.__init__(self, "", permute=False)

        self.ttl = ttl
         
    def _GetHaloImage(self):
        return Entity._GetHaloImage(self,"shootdrop1.png")     
    
    def GetBoundingBox(self):
        return None
    
    def GetBoundingBoxAbs(self):
        return None  

    def Update(self, time_elapsed, time_delta):
        Tile.Update(self,time_elapsed,time_delta)
        if not hasattr(self, "time_start"):
            self.time_start = time_elapsed
            return

        tdelta = time_elapsed - self.time_start
        if tdelta > self.ttl:
            self.game.RemoveEntity(self)
            return
    
        self.color = sf.Color(self.color.r,self.color.g,self.color.b,0xff-int(tdelta*0xff/self.ttl))


class Shot(Tile):
    """Utility class for weapons, wraps a single shot and
    handles any collision with entities"""
    def __init__(self,*args,**kwargs):
        Tile.__init__(self,*args,**kwargs)
        self.speed = 1.0
        self.onhit = lambda x:True
        self.protected = []
        self.dir = (1.0,0.0)
        
    def SetDirection(self,dir):
        """Set the target direction for the shot"""
        self.dir = dir
        
    def SetSpeed(self,speed):
        self.speed = speed
        
    def SetProtected(self,pro):
        self.protected = pro
        
    def GetBoundingBox(self):
        return None
    
    def GetBoundingBoxAbs(self):
        return None
        
    def Update(self,time_elapsed,time):
        oldpos = getattr(self,'oldpos',self.pos)

        for e in self._EnumCached():
            e.Rotate(time_elapsed * 500)
        
        self.SetPosition((self.pos[0] + self.dir[0]*time*self.speed, self.pos[1] + self.dir[1]*time*self.speed))
        lvdim = self.level.GetLevelSize()
        if self.pos[0] < 0 or self.pos[0] > lvdim[0] or self.pos[1] < 0 or self.pos[1] > lvdim[1]:
            self.game.RemoveEntity(self)
            return
        
        if (self.pos[0]-oldpos[0])**2 + (self.pos[1]-oldpos[1])**2 > 0.0040:
            st = ShootAnimStub()
            st.SetColor(self.color)
            st.SetPosition(self.pos)
            self.game.AddEntity(st)
            
            self.oldpos = self.pos
        
        ab = Tile.GetBoundingBoxAbs(self)
    
        # check for any collisions
        for collider in self.game.GetLevel().EnumPossibleColliders(ab):
            if collider in self.protected:
                continue
            
            cd = collider.GetBoundingBoxAbs()
            if cd is None:
                continue
            
            # XXX won't work for non horizontal movements
            if (self.dir[0] < 0 and self._HitsMyLeft(ab,cd) or self.dir[0] > 0 and self._HitsMyRight(ab,cd)):
                bl = collider.Interact(self) 
                if bl != Entity.ENTER:
                    self.game.RemoveEntity(self)
                
        Tile.Update(self,time_elapsed,time)
        

class Weapon(InventoryItem, Tile):
    """Defines the protocol for weapons and implements a default weapon,
    which shoots single shots in one direction and damages every entity
    to touch it. Weapon classes implement only logic and shot visuals, 
    they are not responsible for drawing the actual weapons"""
    
    def __init__(self, text="", width=Tile.AUTO,height = Tile.AUTO,shot_tile="shot1.txt",speed=10.0,halo_img=None):
        Tile.__init__(self,text,width,height,halo_img=halo_img,permute=False)
        InventoryItem.__init__(self)
        self.shot_tile= shot_tile
        self.speed= speed
    
    def GetItemName(self):
        return _("Hot-zoop's Steak'n'Slay Gun")
    
    def Interact(self, other):
        if isinstance(other,Player):
            self.TakeMe(other)
        
        return Entity.ENTER
    
    def Shoot(self,pos, dir,color=None,protected=[],speed=None,do_flash=False):
        from tileloader import TileLoader
        t = TileLoader.Load(os.path.join(defaults.data_dir,"tiles_misc",self.shot_tile),self.game)
                
        color = color or sf.Color(200,200,255)
        
        t.SetSpeed(speed or self.speed)
        t.SetDirection(dir)
        t.SetPosition(pos)
        t.SetColor(color)
        t.SetLevel(self.level)
        t.SetProtected(protected)
                
        if do_flash:
            from posteffect import FlashOverlay
            Renderer.AddDrawable(FlashOverlay(color,0.035,4))
                    
        self.game.AddEntity(t)
        
    def GetAmmoCode(self):
        return "AM"
    
    
class Flamethrower(Weapon):
    """A flamethrower does not require ammo, but it is terribly
    dangerous to use because the player dies immediately
    upon touching a flame."""
    
    def GetItemName(self):
        return _("The Rumpsteak Machine")
    
    def Shoot(self,dir,color,on_hit=lambda x: True):
        pass
    
    
class LaserWeapon(Weapon):
    """This is the player's default weapon - its shoots are reflected
    upon touching an entity, so it's a bit hard to use."""
    
    def GetItemName(self):
        return _("The Self-Reflecting Painless Chicken Slayer")
    
    def Shoot(self,dir,color,on_hit=lambda x: True):
        pass
    
    
class Ammo(AnimTile):
    """Ammo is ammo"""
    
    def __init__(self,*args,amount=5,**kwargs):
        AnimTile.__init__(self,*args,**kwargs)
        self.amount = amount
        
    def Interact(self, other):
        if isinstance(other,Player):
            
            if not hasattr(self,"ammo_taken"):
                other.AddAmmo(self.amount)
                self.game.RemoveEntity(self)
                self.ammo_taken = True
        
        return Entity.ENTER
    
    
    

# vim: ai ts=4 sts=4 et sw=4
