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

# Python stuff
import os

# PySFML
import sf

# My own stuff
import defaults
from game import Entity, Game
from tile import AnimTile, Tile, TileLoader
from player import Player,InventoryItem

class Shot(Tile):
    """Utility class for weapons, wraps a single shot and
    handles any collision with entities"""
    def __init__(self,*args,**kwargs):
        Tile.__init__(self,*args,**kwargs)
        self.speed = 1.0
        self.onhit = lambda x:True
        
    def SetDirection(self,dir):
        """Set the target direction for the shot"""
        self.dir = dir
        
    def SetSpeed(self,speed):
        self.speed = speed
        
    def SetOnHit(self,oh):
        self.onhit = oh
        
    def Update(self,time_elapsed,time):
        self.pos = (self.pos[0] + self.dir[0]*time*self.speed, self.pos[1] + self.dir[1]*time*self.speed)
        rect = self.GetBoundingBox()
    
        # check for any collisions
        for collider in self.game.GetLevel().EnumPossibleColliders(rect):
            mycorner = collider.GetBoundingBox()
            if mycorner is None:
                continue
            
            tj = self._BBCollide_XYWH(rect, mycorner)
            if tj > 0 and collider.Interact(self) != Entity.ENTER and self.onhit(collider) is True:
                self.game.RemoveEntity(self)
                
        Tile.Update(self,time_elapsed,time)
        

class Weapon(InventoryItem, Tile):
    """Defines the protocol for weapons and implements a default weapon,
    which shoots single shots in one direction and damages every entity
    to touch it. Weapon classes implement only logic and shot visuals, 
    they are not responsible for drawing the actual weapons"""
    
    def __init__(self, text="", width=Tile.AUTO,height = Tile.AUTO,shot_tile="shot1.txt",speed=5.0,halo_img=None):
        Tile.__init__(self,text,width,height,halo_img=halo_img)
        InventoryItem.__init__(self)
        self.shot_tile= shot_tile
        self.speed= speed
    
    def GetItemName(self):
        return "Hot-zoop's Steak'n'Slay Gun"
    
    def Interact(self, other):
        if isinstance(other,Player):
            other.AddToInventory(self)
            self.game.RemoveEntity(self)
        
        return Entity.ENTER
    
    def Shoot(self,pos, dir,color,on_hit=lambda x: True):
        t = TileLoader.Load(os.path.join(defaults.data_dir,"tiles_misc",self.shot_tile),self.game)
                
        t.SetSpeed(self.speed)
        t.SetDirection(dir)
        t.SetPosition(pos)
        t.SetOnHit(on_hit)
        t.SetColor(color)
                
        self.game.AddEntity(t)
    
    
class Flamethrower(Weapon):
    """A flamethrower does not require ammo, but it is terribly
    dangerous to use because the player dies immediately
    upon touching a flame."""
    
    def GetItemName(self):
        return "The Rumpsteak Machine"
    
    def Shoot(self,dir,color,on_hit=lambda x: True):
        pass
    
    
class LaserWeapon(Weapon):
    """This is the player's default weapon - its shoots are reflected
    upon touching an entity, so it's a bit hard to use."""
    
    def GetItemName(self):
        return "The Self-Reflecting Painless Chicken Slayer"
    
    def Shoot(self,dir,color,on_hit=lambda x: True):
        pass
    
class Ammo(AnimTile):
    """Ammo is ammo"""
    
    def __init__(self,*args,amount=5,**kwargs):
        AnimTile.__init__(self,*args,**kwargs)
        self.amount = amount
        
    def Interact(self, other):
        if isinstance(other,Player):
            other.AddAmmo(self.amount)
            self.game.RemoveEntity(self)
        
        return Entity.ENTER