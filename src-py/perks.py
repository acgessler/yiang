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
from game import Entity,Game
from tile import AnimTile
from player import Player

class Perk(AnimTile):
    """Sentinel base class, documents the expected
    interface for entities suitable to serve as
    perks, which are used to alter the original
    behaviour of the Player class slightly """
    
    def __init__(self,*args,**kwargs):
        AnimTile.__init__(self,*args,**kwargs)
        self.players = {}

    def EnablePerk(self,player,game):
        """Apply the perk to a Player object. The perk
        is expected to be able to restore the current
        state later. The function checks if another perk
        of the same type is already active on the player
        and returns a reference to it if this is the
        case. """
        self.players[player] = {}
        for perk in player.perks:
            if type(perk) == type(self):
                return perk

        player.perks.add(self)
        return None

    def DisablePerk(self,player,game):
        """Recover the state prior to the EnablePerk()
        call. Properties not affected by the perk need
        not to be recovered. """
        try:
            player.perks.remove(self)
        except KeyError:
            pass
        del self.players[player]

    def _SetAutoExpire(self,game,player,time,extend=False):
        """Automatically expire the perk for a specific player
        after a given time range has passed. If extend is True,
        the function will try to extend the perk if it is
        already running"""
        playerd = self.players[player]
        if extend is True:
            try:
                if game.GetTotalElapsedTime()-playerd["time_start"]-playerd["time"] > time:
                    return
                print("Extending lifetime of existing perk")
            except KeyError:
                pass
        
        playerd["time"] = time
        playerd["time_start"] = game.GetTotalElapsedTime()

    def _CheckIfExpired(self,game,player,):
        """Called by Player during its Update() calls. We can'd do it
        from within our Update() callback because the perk position
        is static, and the player might leave its active range so
        Update() would not longer be called."""
        player_dict = self.players[player]
        if game.GetTotalElapsedTime()-player_dict["time_start"] > player_dict["time"]:
            self.DisablePerk(player,game)

    def FindExisting(self,perks,cls):
        """Search a given list of perks for an instance of a particular
        class, but don't return ourselfes."""
        for perk in perks:
            if not perk is self and isinstance(perk,cls):
                return perk
        return None

    def Interact(self,other,game):
        if isinstance(other,Player):
            if other in self.players:
                return Entity.ENTER    
            
            self.EnablePerk(other,game)
        return Entity.ENTER


class SuperSpeed(Perk):
    """The SuperSpeed perk enables the player to move
    much, much faster for a certain amount of time"""

    def __init__(self,text,height,frames,time=5.0,speed_multiplier=3.0,anim_speed=1.0):
        Perk.__init__(self,text,height,frames,anim_speed)
        self.speed_multiplier = speed_multiplier
        self.time = time

    def EnablePerk(self,player,game):
        if player in self.players:
            return
        
        print("Enable perk: SuperSpeed")
        other = Perk.EnablePerk(self,player,game)
        if other is None:
            player.speed_scale *= self.speed_multiplier
            self._SetAutoExpire(game,player,self.time)
            return

        other._SetAutoExpire(game,player,self.time,True)

    def DisablePerk(self,player,game):
        Perk.DisablePerk(self,player,game)
        print("Disable perk: SuperSpeed")

        player.speed_scale /= self.speed_multiplier


class MegaJump(Perk):
    """The MegaJump perk enables the player to jump
    much, much higher for a certain amount of time"""

    def __init__(self,text,height,frames,time=5.0,jump_multiplier=2.0,anim_speed=1.0):
        Perk.__init__(self,text,height,frames,anim_speed)
        self.jump_multiplier = jump_multiplier
        self.time = time

    def EnablePerk(self,player,game):
        if player in self.players:
            return
        
        print("Enable perk: MegaJump")
        other = Perk.EnablePerk(self,player,game)
        if other is None:
            player.jump_scale *= self.jump_multiplier
            self._SetAutoExpire(game,player,self.time)
            return

        other._SetAutoExpire(game,player,self.time,True)

    def DisablePerk(self,player,game):
        Perk.DisablePerk(self,player,game)
        print("Disable perk: MegaJump")

        player.jump_scale /= self.jump_multiplier


class Unkillable(Perk):
    """The Unkillable perk enables the player to survive
    collisions with dangerous tiles for a specific
    duration. The player won't survive falling outside
    the level boundaries, however."""

    def __init__(self,text,height,frames,time=5.0,jump_multiplier=2.0,anim_speed=1.0):
        Perk.__init__(self,text,height,frames,anim_speed)
        self.time = time

    def EnablePerk(self,player,game):
        if player in self.players:
            return
        
        print("Enable perk: Unkillable")
        other = Perk.EnablePerk(self,player,game)
        if other is None:
            player.unkillable += 1
            self._SetAutoExpire(game,player,self.time)
            return

        other._SetAutoExpire(game,player,self.time,True)

    def DisablePerk(self,player,game):
        Perk.DisablePerk(self,player,game)
        print("Disable perk: Unkillable")

        player.unkillable -= 1
        assert player.unkillable>0
    
