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
# import collections

# PySFML
import sf

# My own stuff
import defaults
from game import Entity, Game
from tile import AnimTile, Tile
from player import Player, InventoryItem
from renderer import Renderer
from keys import KeyMapping

class Door(AnimTile):
    """A door blocks the player unless he presents a key of the same color"""
    def __init__(self, text, height, frames, speed = 1.0, halo_img = None):
        AnimTile.__init__(self, text, height, frames, states=4, speed=speed, halo_img=halo_img)
        self.unlocked = False

    def Interact(self, other):
        if isinstance(other,Player) and self.unlocked is False and not hasattr( self, "during_interact" ):
            inv = other.EnumInventoryItems()
            
            try:
                while True:
                    item = inv.send(None)
                    if isinstance(item,Key) and item.color == self.color:
                        self.Unlock()
                        item = inv.send(item)
                        while inv.send(None): pass
            except StopIteration:
                pass
        
        return Entity.ENTER if self.unlocked else Entity.BLOCK
    
    def Update(self, time_elapsed, time):
        if hasattr( self, "during_interact" ):
            if self.Get() == self.GetNumFrames()-1:
                self.unlocked = self.target_state
                self.SetState(2 if self.unlocked else 0)
                self.Set(0)
                
                try:
                    delattr(self,"during_interact")
                except AttributeError:
                    pass
        AnimTile.Update(self,time_elapsed,time)
        
    def IsWorking(self):
        return hasattr( self, "during_interact" )
    
    def Unlock(self):
        """Unlock the door, does not alter the players inventory"""
        self.SetState(1)
        self.Set(0)
        
        self.target_state = True
        self.during_interact = True
        print("Unlocking door {0}".format(self))
        
    def Lock(self):
        """Lock the door again"""
        self.SetState(3)
        self.Set(0)
        
        self.target_state= False
        self.during_interact = True
        print("Locking door {0}".format(self))
        
        
class Bridge(Door):
    """A bridge is exactly the opposite of a door (really!):
    it blocks when it is opened."""
    
    def __init__(self, text, height, frames, speed = 1.0, halo_img = None):
        Door.__init__(self,text,height,frames,speed,halo_img)
    
    def Interact(self, other):
        return Entity.BLOCK
    
    
class BridgeControl(AnimTile):
    """A BridgeControl opens or closes the door which is next
    to it. """
    
    def __init__(self, text, height, frames, speed = 1.0, halo_img = None, initial_state=False):
        AnimTile.__init__(self, text, height, frames, states=2, speed=speed, halo_img=halo_img)
        self.initial_state = initial_state
    
    def Update(self,time,dtime):
        AnimTile.Update(self,time,dtime)
        if not hasattr(self,"did_init"):
            
            self.did_init = True
            self._UpdateBridge()
    
    def Interact(self, other):
        if isinstance(other,Player):
            if Renderer.app.GetInput().IsKeyDown(KeyMapping.Get("interact")):
                if not hasattr(self,"running"):
                    self.running = True
                    if not getattr(self,"last_bridge",None) or not self.last_bridge.IsWorking():
                        self._Toggle()
            else:
                try:
                    delattr(self,"running")
                except AttributeError:
                    pass
            
        return Entity.ENTER
    
    def _GetBridge(self):
        import mathutil
        p = [e for e in self.level.EnumAllEntities() if isinstance(e, Bridge) and e.color == self.color]
        if not p:
            print("Failure finding possible target for bridge controller: {0}".format(self))
            return None
        
        p = sorted(p,key=lambda e:(e.pos[0]-self.pos[0])**2 + (e.pos[1]-self.pos[1])**2)[0]
        return p
    
    def _Toggle(self):
        self.initial_state = not self.initial_state
        self._UpdateBridge()
        
    def _UpdateBridge(self):
        self.last_bridge = self._GetBridge()
        if not self.last_bridge:
            return
        
        print("Update bridge state: {0}".format(self.last_bridge))
        self.last_bridge.Unlock() if self.initial_state is True else self.last_bridge.Lock()
        self.SetState(1 if self.initial_state is True else 0)
        
    
class Key(Tile,InventoryItem):
    """A door blocks the player unless he presents a key of the same color"""
    
    def __init__(self,width=Tile.AUTO,height=Tile.AUTO):
        Tile.__init__(self,width,height)
        InventoryItem.__init__(self)
        
    def Interact(self, other):
        if isinstance(other,Player):
            other.AddToInventory(self)
            self.game.RemoveEntity(self)
        
        return Entity.ENTER
    
    def GetItemName(self):
    
        # XXX temporary solution
        def GetName(col):
            if col.a == 0:
                return "Invisible"
                
            if col.r > 60:
                if col.g > 60:
                    if col.b > 60:
                        return "Gray" if col.r+col.b+col.g!=255*3 else  "White"
                    else:
                        return "Yellow"
                else:         
                    if col.b > 60:
                        return "Pink"
                    else:
                        return "Red"
            else:
                if col.g > 60:
                    if col.b > 60:
                        return "Azure"
                    else:
                        return "Green"
                else:         
                    if col.b > 60:
                        return "Blue"
                    else:
                        return "Black"
            assert False
        
        return "{0} key".format(GetName( self.color ))
    
    
    
    
    
    
    
    
    
    
    
   

            