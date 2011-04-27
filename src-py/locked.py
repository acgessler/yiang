#!echo not intended for execution
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
import math

# PySFML
import sf

# My own stuff
from stubs import *
from player import Player, InventoryItem


class FloatingNotification:
    
    def __init__(self,alpha_scale=1.0):
        self.alpha_scale = alpha_scale
    
    def DrawNotification(self,text='(no text specified)',scale=1.0):
        scale = max(0,min(1,scale*self.alpha_scale))
        
        r,g,b = self.color.r,self.color.g,self.color.b
        fg = sf.Color(r//4,g//4,b//4,int(0xff*scale))
        bg = sf.Color(r//2,g//2,b//2,int(0xff*scale))
        
        pos = self.level.ToCameraDeviceCoordinates(self.pos)
        bb = pos[0]-200,pos[1]+5,pos[0],pos[1]+19
        shape = sf.Shape()
        shape.AddPoint(bb[0], bb[1],fg,bg )
        shape.AddPoint(bb[2], bb[1],fg,bg )
        shape.AddPoint(bb[2], bb[3],fg,bg )
        shape.AddPoint(bb[0], bb[3],fg,bg )
        
        shape.SetOutlineWidth(2)
        shape.EnableFill(True)
        shape.EnableOutline(True)
        Renderer.app.Draw(shape)
        
        rsize = 8
        text = sf.String(text,Font=FontCache.get(rsize),Size=rsize)
        text.SetPosition(bb[0]+10,bb[1]+3)
        text.SetColor(sf.Color(0xff,0xff,0xff,int(0xd0*scale)))
        Renderer.app.Draw(text)
        

class Door(AnimTile,FloatingNotification):
    """A door blocks the player unless he presents a key of the same color"""
    def __init__(self, text, height, frames, speed = 1.0, halo_img = None,draworder=2000):
        AnimTile.__init__(self, text, height, frames, speed*1.5, states=4, halo_img=halo_img, noloop=True,draworder=draworder) # balancing
        FloatingNotification.__init__(self)
        self.unlocked = False
        self.player_close = False
        self.notify = False
        self.force_flash = False

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
                self.notify = True
        
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
            
        elif self._CanFlash():
            old,self.player_close = self.player_close,not not self.level.IsPlayerClose(self.pos,5.0) or self.force_flash
            if self.player_close:  
                if not old:
                    self.pulse_timer = sf.Clock()
                                  
                time = self.pulse_timer.GetElapsedTime()
                self.dropshadow = True
                r,g,b = [int(min(0xff,c*3.0)) for c in (self.color.r,self.color.g,self.color.b)]
                self.dropshadow_color = sf.Color(r,g,b,int((0x1f*(math.sin(time*8.0)+1.0))))
            else:
                self.dropshadow = self.notify = False  
        else:
            self.dropshadow = self.player_close = self.notify = False      
                
        AnimTile.Update(self,time_elapsed,time)
        
    def _CanFlash(self):
        return not self.unlocked
        
    def Draw(self):
        AnimTile.Draw(self)
        
        if self.notify and self.player_close and not self.IsWorking():
            self.DrawNotification(text=_("Get a {0} key to speak to this door").format(defaults.GetColorName(self.color)),
                scale=self.pulse_timer.GetElapsedTime())
        
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
    
    def Draw(self):
        AnimTile.Draw(self)
        
    def _CanFlash(self):
        return True # bridges can flash in any state
    
    
class BridgeControl(AnimTile,FloatingNotification):
    """A BridgeControl opens or closes the door which is next
    to it. """
    
    def __init__(self, text, height, frames, speed = 1.0, halo_img = None, initial_state=False,draworder=2000):
        AnimTile.__init__(self, text, height, frames, states=2, speed=speed, halo_img=halo_img,draworder=draworder)
        FloatingNotification.__init__(self)
        self.initial_state = initial_state
        self.notify = False
        self.moved_once = False
        self.last_bridge = None
    
    def Update(self,time,dtime):
        AnimTile.Update(self,time,dtime)
        if not hasattr(self,"did_init"):
            self.did_init = True
            self._UpdateBridge()
 
    def Interact(self, other):
        if isinstance(other,Player):
            if Renderer.app.GetInput().IsKeyDown(KeyMapping.Get("interact")):
                self.notify = False
                self.moved_once = True
                if not hasattr(self,"running"):
                    self.running = True
                    if not getattr(self,"last_bridge",None) or not self.last_bridge.IsWorking():
                        self._Toggle()
            else:
                self.notify = True
                try:
                    delattr(self,"running")
                except AttributeError:
                    pass
            
        return Entity.ENTER

    
    def Draw(self):
        AnimTile.Draw(self)
        
        cl = self.level.IsPlayerClose(self.pos,4.0)
        
        doit = self.notify and cl and not self.moved_once
        if doit:
            self.DrawNotification(text=_("Press {0} to talk to the bridge").format(KeyMapping.GetString('interact')),scale=1-cl[1]/3)
            
        # highlight the corr. bridge as well
        if self.last_bridge:
            self.last_bridge.force_flash = doit
               
    def _GetBridge(self):
        p = self.level.FindClosestOfSameColor(self.pos,Bridge,self.color,exact_match=True)
        if not p:
            print("Failure finding possible target for bridge controller: {0}".format(self))
            return None
        
        return p
    
    def _Toggle(self):
        self.initial_state = not self.initial_state
        self._UpdateBridge(True)
        
    def _UpdateBridge(self,flash=False):
        self.SetState(1 if self.initial_state is True else 0)
        self._CacheBridge()
        if not self.last_bridge:
            return
        
        print("Update bridge state: {0}".format(self.last_bridge))
        (self.last_bridge.Unlock if self.initial_state is True else self.last_bridge.Lock)(flash)
        
    def _CacheBridge(self):
        if not self.last_bridge or self.game.GetGameMode() == Game.EDITOR:
            self.last_bridge = self._GetBridge()
        
    
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
        return _("{0} key").format(defaults.GetColorName( self.color ))
    
    
    
    
    
    
    
    
    
    
    
   

            

# vim: ai ts=4 sts=4 et sw=4