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
import collections

# PySFML
import sf

# My own stuff
import defaults
from game import Entity, Game
from tile import AnimTile, Tile
from player import Player, InventoryItem

class Door(AnimTile):
    """A door blocks the player unless he presents a key of the same color"""
    def __init__(self, text, height, frames, speed = 1.0, halo_img = None):
        AnimTile.__init__(self, text, height, frames, states=2, speed=speed, halo_img=halo_img)
        self.unlocked = False

    def Interact(self, other):
        if isinstance(other,Player) and self.unlocked is False:
            inv = other.EnumInventoryItems()
            
            try:
                while True:
                    item = inv.send(None)
                    if isinstance(item,Key) and item.color == self.color:
                        self.Unlock()
                        item = inv.send(item)
                        break
            except StopIteration:
                pass
        
        return Entity.ENTER if self.unlocked else Entity.BLOCK
    
    def Unlock(self):
        """Unlock the door, does not alter the players inventory"""
        self.SetState(1)
        self.unlocked = True
        print("Unlocking door {0}".format(self))
        
    def Lock(self):
        """Lock the door again"""
        self.SetState(0)
        self.unlocked = False
        print("Locking door {0}".format(self))
    
    
class Key(Tile,InventoryItem):
    """A door blocks the player unless he presents a key of the same color"""
    
    color_names = collections.defaultdict(lambda : "colorful",{
        sf.Color.Red: "Red",
        sf.Color.Green: "Green",
        sf.Color.Blue: "Blue"
    })
    
    def __init__(self,width=Tile.AUTO,height=Tile.AUTO):
        Tile.__init__(self,width,height)
        InventoryItem.__init__(self)
        
    def Interact(self, other):
        if isinstance(other,Player):
            other.AddToInventory(self)
            self.game.RemoveEntity(self)
        
        return Entity.ENTER
    
    def GetItemName(self):
        return "{0} key".format(Key.color_names[ self.color ])
    
    
    
    
    
    
    
    
    
    
    
   

            