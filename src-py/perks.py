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
import os

# PySFML
import sf

# My own stuff
import defaults
from game import Entity,Game
from tile import AnimTile,Tile,TileLoader
from player import Player
from renderer import Renderer,Drawable

class PerkOverlay(Tile):
    """The nice ASCII icon displayed in the lower status bar while
    a perk is active"""
    active = []
    
    def __init__(self,elems):
        self.orig_text = elems
        Tile.__init__(self,elems,len(elems) if elems.find("\n")==-1 else elems.find("\n"),max(1,elems.count("\n")),
            rsize=int(defaults.perks_overlay_letter_height*defaults.scale[1]))
        
        self.SetFormatters()
        
    def _GetHaloImage(self):
        return None
            
    def Enable(self):
        """Register the overlay and enable it for drawing."""
        self.game.AddSlaveDrawable(self)
        PerkOverlay.active.append(self)
        
    def Disable(self):
        """Must be called instead of Renderer.RemoveDrawable()"""
        self.game.RemoveSlaveDrawable(self)
        PerkOverlay.active.remove(self)
        
    def SetFormatters(self,d={}):
        """Set format() kwargs to substitute text variables, i.e.
        the remaining life time of the perk"""
        self.formatters = d
        try:
            self.text = self.orig_text.format(**d)
        except KeyError:
            self.text = self.orig_text
        
        self._Recache()
            
    def Draw(self):
        offset = 0
        for other in PerkOverlay.active:
            if other is self:
                break
            offset += other.dim[0]+defaults.perks_overlay_spacing
            
        height = self.game.GetLowerStatusBarHeight()
        coords = self.game.ToDeviceCoordinates((defaults.perks_overlay_start+offset, min(defaults.tiles[1] - self.dim[1]*1.2,  defaults.tiles[1] - 
            (height-(height-self.dim[1])/2))))
        
        # XXX add utilities to draw our 'shadowed' text to Renderer
        # to avoid code duplication
        for elem in self.cached:
            elem.SetPosition(coords[0]-1,coords[1]-1)
            elem.SetColor(sf.Color.Black)
            Renderer.app.Draw(elem)
        
        for elem in self.cached:
            elem.SetPosition(*coords)
            elem.SetColor(sf.Color.Yellow)
            Renderer.app.Draw(elem)
    
    def GetDrawOrder(self):
        return 100

class Perk(AnimTile):
    """Defines the interface for entities suitable to serve as perks,
    which are used to alter the original behaviour of the Player
    class slightly. Some perks can be accumulated (i.e. if the
    activates multiple of them at once, their effect sums up,
    other may not accept more than one of their kind to be active.)"""
    
    def __init__(self,overlay_file,*args,**kwargs):
        AnimTile.__init__(self,*args,**kwargs)
        self.players = {}
        self.overlay_file = overlay_file
        self.subs = []

    def EnablePerk(self,player,check_for_existing=True):
        """Apply the perk to a Player object. The perk
        is expected to be able to restore the current
        state later. The function checks if another perk
        of the same type is already active on the player
        and returns a reference to it if this is the
        case. Pass False for check_for_existing to disable
        this check (useful for perks which can be 
        accumulated, i.e. acquired multiple times) """
        self.players[player] = {}
        if check_for_existing is True:
            for perk in player.perks:
                if type(perk) == type(self):
                    perk.subs.append(self)
                    return perk

        player.perks.add(self)
        
        if not self.overlay_file is None:
            self.overlay = TileLoader.Load(self.overlay_file,self.game)
            self.overlay.Enable()
        return None

    def DisablePerk(self,player):
        """Recover the state prior to the EnablePerk()
        call. Properties not affected by the perk need
        not to be recovered. """
        try:
            player.perks.remove(self)
        except KeyError:
            pass
        del self.players[player]
        for sub in self.subs:
            del sub.players[player]
        self.subs = []
        
        if hasattr(self,"overlay"):
            self.overlay.Disable()

    def _SetAutoExpire(self,player,time,extend=False):
        """Automatically expire the perk for a specific player
        after a given time range has passed. If extend is True,
        the function will try to extend the perk if it is
        already running"""
        playerd = self.players[player]
        if extend is True:
            try:
                if self.game.GetTotalElapsedTime()-playerd["time_start"]-playerd["time"] > time:
                    return
                print("Extending lifetime of existing perk")
            except KeyError:
                pass
        
        playerd["time"] = time
        playerd["time_start"] = self.game.GetTotalElapsedTime()

    def _CheckIfExpired(self,player):
        """Called by Player during its Update() calls. We can'd do it
        from within our Update() callback because the perk position
        is static, and the player might leave its active range so
        Update() would not longer be called."""
        player_dict = self.players[player]
        
        try:
            remaining = player_dict["time"] - (self.game.GetTotalElapsedTime()-player_dict["time_start"])
            if hasattr(self,"overlay"):
                self.overlay.SetFormatters({"remaining":remaining})
                
            if remaining < 0:
                self.DisablePerk(player)
                return True
        except KeyError:
            pass
        return False

    def FindExisting(self,perks,cls):
        """Search a given list of perks for an instance of a particular
        class, but don't return *this* instance. If none is found,
        None is returned :-)"""
        for perk in perks:
            if not perk is self and isinstance(perk,cls):
                return perk
        return None

    def Interact(self,other):
        if isinstance(other,Player):
            if other in self.players:
                return Entity.ENTER    
            
            self.EnablePerk(other)
        return Entity.ENTER


class SuperSpeed(Perk):
    """The SuperSpeed perk enables the player to move
    much, much faster for a certain amount of time"""

    def __init__(self,text,height,frames,time=5.0,speed_multiplier=3.0,anim_speed=1.0):
        Perk.__init__(self,os.path.join(defaults.data_dir,"tiles_misc","superspeed.txt"),text,height,frames,anim_speed)
        self.speed_multiplier = speed_multiplier
        self.time = time

    def EnablePerk(self,player):
        if player in self.players:
            return
        
        print("Enable perk: SuperSpeed")
        other = Perk.EnablePerk(self,player)
        if other is None:
            player.speed_scale *= self.speed_multiplier
            self._SetAutoExpire(player,self.time)
            return

        other._SetAutoExpire(player,self.time,True)

    def DisablePerk(self,player):
        Perk.DisablePerk(self,player)
        print("Disable perk: SuperSpeed")

        player.speed_scale /= self.speed_multiplier


class MegaJump(Perk):
    """The MegaJump perk enables the player to jump
    much, much higher for a certain amount of time"""

    def __init__(self,text,height,frames,time=5.0,jump_multiplier=2.0,anim_speed=1.0):
        Perk.__init__(self,os.path.join(defaults.data_dir,"tiles_misc","megajump.txt"),text,height,frames,anim_speed)
        self.jump_multiplier = jump_multiplier
        self.time = time

    def EnablePerk(self,player):
        if player in self.players:
            return
        
        print("Enable perk: MegaJump")
        other = Perk.EnablePerk(self,player)
        if other is None:
            player.jump_scale *= self.jump_multiplier
            self._SetAutoExpire(player,self.time)
            return

        other._SetAutoExpire(player,self.time,True)

    def DisablePerk(self,player):
        Perk.DisablePerk(self,player)
        print("Disable perk: MegaJump")

        player.jump_scale /= self.jump_multiplier


class Unkillable(Perk):
    """The Unkillable perk enables the player to survive
    collisions with dangerous tiles for a specific
    duration. The player won't survive falling outside
    the level boundaries, however."""

    def __init__(self,text,height,frames,time=5.0,jump_multiplier=2.0,anim_speed=1.0):
        Perk.__init__(self,os.path.join(defaults.data_dir,"tiles_misc","unkillable.txt"),text,height,frames,anim_speed)
        self.time = time

    def EnablePerk(self,player):
        if player in self.players:
            return
        
        print("Enable perk: Unkillable")
        other = Perk.EnablePerk(self,player)
        if other is None:
            player.unkillable += 1
            self._SetAutoExpire(player,self.time)
            return

        other._SetAutoExpire(player,self.time,True)

    def DisablePerk(self,player):
        Perk.DisablePerk(self,player)
        print("Disable perk: Unkillable")

        player.unkillable -= 1
        assert player.unkillable>=0
    
