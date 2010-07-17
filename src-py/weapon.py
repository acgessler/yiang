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

# PySFML
import sf

# My own stuff
import defaults
from game import Entity, Game
from tile import AnimTile, Tile
from player import Player,InventoryItem

class Weapon(InventoryItem):
    """Defines the protocol for weapons and implements a default weapon,
    which shoots single shots in one direction and damages every entity
    to touch it. Weapon classes implement only logic and shot visuals, 
    they are not responsible for drawing the actual weapons"""
    def __init__(self):
        pass
    
    def GetItemName(self):
        return "Hot-zoop's Steak'n'Slay Gun"
    
    def Shoot(self,dir,color):
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