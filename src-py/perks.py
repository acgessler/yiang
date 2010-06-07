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
import random

# PySFML
import sf

# My own stuff
import defaults
from game import Entity,Game,Tile,AnimTile
from player import Player

class Perk(AnimTile):
    """Sentinel base class, documents the expected
    interface for entities suitable to serve as
    perks, which are used to alter the original
    behaviour of the Player class slightly """
    
    def __init__(self,*args,**kwargs):
        AnimTile.__init__(self,*args,**kwargs)
        self.players = {} 

    def EnablePerk(self,player):
        """Apply the perk to a Player object. The perk
        is expected to be able to restore the current
        state later."""
        self.players[player] = {}

    def DisablePerk(self,player):
        """Recover the state prior to the EnablePerk()
        call. Properties not affected by the perk need
        not to be recovered. """
        del self.players[player]

    def Interact(self,other,game):
        if isinstance(other,Player):
            self.EnablePerk(other)
            
        return Entity.ENTER
    

class SuperSpeed(Perk):
    """The SuperSpeed perk enables the player to move
    much, much faster for a certain amount of time"""

    def __init__(self,text,height,frames,time=5.0,speed_multiplier=3.0,anim_speed=1.0):
        Perk.__init__(self,text,height,frames,anim_speed)
        self.speed_multiplier = speed_multiplier
        self.time = time

    def EnablePerk(self,player):
        pass

    def DisablePerk(self,player):
        pass


class MegaJump(Perk):
    """The MegaJump perk enables the player to jump
    much, much higher for a certain amount of time"""

    def __init__(self,text,height,frames,time=5.0,jump_multiplier=2.0,anim_speed=1.0):
        Perk.__init__(self,text,height,frames,anim_speed)
        self.jump_multiplier = jump_multiplier
        self.time = time

    def EnablePerk(self,player):
        pass

    def DisablePerk(self,player):
        pass


class Unkillable(Perk):
    """The Unkillable perk enables the player to survive
    collisions with dangerous tiles for a specific
    duration. The player won't survive falling outside
    the level boundaries, however."""

    def __init__(self,text,height,frames,time=5.0,jump_multiplier=2.0,anim_speed=1.0):
        Perk.__init__(self,text,height,frames,anim_speed)
        self.time = time

    def EnablePerk(self,player):
        pass

    def DisablePerk(self,player):
        pass

    
