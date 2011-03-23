#! /usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [locked.py]
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

# Python Core
# import collections

# PySFML
import sf

# My own stuff
from stubs import *
from player import Player, InventoryItem


class Door(AnimTile):
    """A door blocks the player unless he presents a key of the same color"""
    def __init__(self, text, height, frames, speed = 1.0, halo_img = None):
        AnimTile.__init__(self, text, height, frames, speed*1.5, states=4, halo_img=halo_img, noloop=True) # balancing
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
    
    def Flash(self):
        from posteffect import FlashOverlay
        Renderer.AddDrawable(FlashOverlay(self.color,0.045))
    
    def Unlock(self,flash=True):
        """Unlock the door, does not alter the players inventory"""
        self.SetState(1)
        self.Set(0)
        
        self.target_state = True
        self.during_interact = True
        print("Unlocking door {0}".format(self))
        
        if flash:
            self.Flash()
        
    def Lock(self,flash=True):
        """Lock the door again"""
        self.SetState(3)
        self.Set(0)
        
        self.target_state= False
        self.during_interact = True
        print("Locking door {0}".format(self))
        
        if flash:
            self.Flash()
        
        
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
        p = self.level.FindClosestOfSameColor(self.pos,Bridge,self.color)
        if not p:
            print("Failure finding possible target for bridge controller: {0}".format(self))
            return None
        
        return p
    
    def _Toggle(self):
        self.initial_state = not self.initial_state
        self._UpdateBridge(True)
        
    def _UpdateBridge(self,flash=False):
        self.SetState(1 if self.initial_state is True else 0)
        self.last_bridge = self._GetBridge()
        if not self.last_bridge:
            return
        
        print("Update bridge state: {0}".format(self.last_bridge))
        (self.last_bridge.Unlock if self.initial_state is True else self.last_bridge.Lock)(flash)
        
        
    
class Key(Tile,InventoryItem):
    """A door blocks the player unless he presents a key of the same color"""
    
    def __init__(self,width=Tile.AUTO,height=Tile.AUTO):
        Tile.__init__(self,width,height)
        InventoryItem.__init__(self)
        
    def Interact(self, other):
        if isinstance(other,Player):
            self.TakeMe(other)
            
            from posteffect import FlashOverlay
            Renderer.AddDrawable(FlashOverlay(self.color,0.075,0.5))
        
        return Entity.ENTER
    
    def GetItemName(self):
    
        # XXX temporary solution
        def GetName(col):
            if col.a == 0:
                return _("Invisible")
                
            if col.r > 60:
                if col.g > 60:
                    if col.b > 60:
                        return _("Gray") if col.r+col.b+col.g!=255*3 else _("White")
                    else:
                        return _("Yellow")
                else:         
                    if col.b > 60:
                        return _("Pink")
                    else:
                        return _("Red")
            else:
                if col.g > 60:
                    if col.b > 60:
                        return _("Azure")
                    else:
                        return _("Green")
                else:         
                    if col.b > 60:
                        return _("Blue")
                    else:
                        return _("Black")
            assert False
        
        return _("{0} key").format(GetName( self.color ))
    
    
    
    
    
    
    
    
    
    
    
   

            

# vim: ai ts=4 sts=4 et sw=4