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

# Python core
import math
import random
import os
import operator

# PySFML
import sf

# My own stuff
import defaults
import mathutil
from game import Entity, Game
from renderer import NewFrame, Drawable, Renderer
from tile import Tile
from keys import KeyMapping
from level import Level

class InventoryItem:
    """Base class for inventory items.
    Such items are collected by the player and are subsequently
    reused to perform specific actions, i.e. open doors."""
    
    
    def GetItemName(self):
        """Return a descriptive item name to be displayed to the user"""
        return "an unnamed inventory item"

class Player(Entity):
    """Special entity which responds to user input and moves the
    player tiles accordingly. Multiple player's can coexist in
    a single level."""

    ANIM_WALK, ANIM_JUMP, ANIM_SHOOT = range(3)
    MAX_ANIMS = 3
    
    LEFT,RIGHT=range(2)

    def __init__(self, text, width, height, ofsx, move_freely=False, draworder=1000):
        Entity.__init__(self)

        self.pwidth = width / defaults.tiles_size[0]
        self.pheight = height / defaults.tiles_size[1]
        self.pofsx = ofsx / defaults.tiles_size[0]
        
        # XXX get rid of pwith and pheight
        self.dim = self.pwidth,self.pheight
        self.draworder = draworder

        lines = text.split("\n")
        height = len(lines) // (Player.MAX_ANIMS*2)

        from weapon import Weapon
        self.inventory = []
        self.ordered_respawn_positions = []
        self.ammo = 0
        self.move_freely = move_freely

        # XXX use AnimTile instead
        self.tiles = []
        for i in range(0, (len(lines) // height) * height, height):
            self.tiles.append(Tile("\n".join(lines[i:i + height]),halo_img=None))
            self.tiles[-1].SetDim(self.dim)
            self.tiles[-1].SetPosition((0, 0))

        assert len(self.tiles) == (Player.MAX_ANIMS*2)
        
    def SetLevel(self,level):
        Entity.SetLevel(self,level)
        self._Reset()

    def _Reset(self):
        """Reset the state of the player instance, this is needed
        for proper respawning"""
        self.vel = [0, 0]
        self.in_jump = self.block_jump = self.level.gravity > 0
        self.block_shoot, self.moved_once, self.setup_autoscroll = False, False, False
        self.cur_tile = Player.ANIM_WALK
        self.dir = Player.RIGHT
        
        self.level.PushAutoScroll(0.0)

        # disable all perks
        if hasattr(self, "perks"):
            for perk in self.perks.copy():
                perk.DisablePerk(self)
        self.perks = set()

        # these are used and modified by the various 'upgrades' in perks.py
        self.jump_scale = 1.0
        self.speed_scale = 1.0
        
        # unkillable is used by Protect() as well
        self.unkillable = 0
        
        # self.draw is set to False while the player is death and 
        # his body is therefore not visible.
        self.draw = True
        
    def Protect(self,time=None):
        """Protect the player from being killed for a specific
        amount of time. The player is shown with a bright
        halo during this time."""
        
        time = time or defaults.respawn_protection_time
        
        outer = self
        class Proxy(Drawable):
            def __init__(self):
                Drawable.__init__(self)
                self.time = time
                self.timer = sf.Clock()
            
            def Draw(self):
                if self.timer.GetElapsedTime()>self.time:
                    outer.unkillable -= 1
                    try:
                        delattr( outer, "flash_halo" )
                    except AttributeError:
                        pass
                    
                    print("End respawn protection on {0}".format(outer))
                    Renderer.RemoveDrawable(self)
        
        print("Set respawn protection on {0}".format(self))
        self.unkillable += 1
        
        img = self._GetHaloImage("halo_protect.png")
        if not img is None:
            self.flash_halo = sf.Sprite(img)
            self.flash_halo.Resize(self.pwidth * defaults.tiles_size_px[0],self.pheight * defaults.tiles_size_px[1])
            self.flash_halo.SetColor(sf.Color(255,255,0,160))
            
        Renderer.AddDrawable(Proxy())
        
    def SetGame(self, game):
        self.game = game
        for tile in self.tiles:
            tile.SetGame(self.game)

    def SetPosition(self, pos):
        Entity.SetPosition(self,pos)

        # (HACK) keep the original position, for we need it to implement respawning
        if not hasattr(self, "respawn_positions"):
            self.respawn_positions = []
            self._AddRespawnPoint(pos)
            
    def EnumInventoryItems(self):
        """Yields all inventory items in unspecified order.
        use send(item) to mark a specific item for deletion"""
        erase = []
        for item in self.inventory:
            assert isinstance(item,InventoryItem)
            
            item = ( yield item )
            if not item is None:
                erase.append(item)
                
        for item in erase:
            self.inventory.remove(item)
            self.game.AddEntity(InventoryChangeAnimStub("-- "+item.GetItemName(),self.pos,color=sf.Color.Red))
            
    def AddToInventory(self,item):
        """Adds an item to the player's inventory. The same
        item can be added multiple times."""
        assert isinstance(item,InventoryItem)
        self.inventory.append(item)
        self.game.AddEntity(InventoryChangeAnimStub("++ "+item.GetItemName(),self.pos))
        
    def AddAmmo(self,ammo):
        """Add a specific amount of ammo to the player's inventory.
        One shoot consumes one unit of ammo.""" 
        assert ammo > 0
        self.ammo += ammo
        self.game.AddEntity(InventoryChangeAnimStub("++ {0}x ammo".format(ammo),
            self.pos,color=sf.Color.Yellow))
        
    def RemoveFromInventory(self,item):
        """Removes an item from the player's inventory. If the
        same item exists multiple times, only its first
        occurences is removed. ValueError is raised it
        the item does not exist. Note: do not use from
        within EnumInventoryItems() -- ! it provides a different
        scheme to remove entities. """
        assert isinstance(item,InventoryItem)
        self.inventory.remove(item)
        self.game.AddEntity(InventoryChangeAnimStub("-- "+item.GetItemName(),self.pos,color=sf.Color.Red))
            
    def SetPositionAndMoveView(self, pos, ofs=None):
        """Change the players position and adjust the viewport accordingly.
        The optional offset value is the distance from the left viewport
        border."""
        self.SetPosition(pos)
        self.level.SetOriginX(self.pos[0] - (ofs or defaults.respawn_origin_distance))

    def SetColor(self, pos):
        self.color = pos
        for tile in self.tiles:
            tile.SetColor(pos)
            
    def GetDrawOrder(self):
        return self.draworder
        
    def OnLeaveLevel(self):
        for perk in list(self.perks):
            perk.DisablePerk(self)
    
    def Draw(self):
        if self.draw is False:
            return
        if hasattr(self,"flash_halo"): # XXX
            self.game.GetLevel().DrawSingle( self.flash_halo, (self.pos[0]-0.2,self.pos[1]-1.55) )
        
        self.tiles[self._GetTileIndex(self.cur_tile)].DrawRelative(self.pos)
        
    def _GetTileIndex(self,index):
        return self.cur_tile if self.dir == Player.RIGHT else self.cur_tile + Player.MAX_ANIMS
    
    def _Shoot(self):
        # first find a suitable weapon in our inventory
        from weapon import Weapon
        for elem in self.EnumInventoryItems():
            if (isinstance(elem,Weapon)):
                weapon = elem
                break
        else:
            if self.block_shoot is False:
                self.game.AddEntity(InventoryChangeAnimStub("Dude, you have no weapon ...",
                    self.pos,color=sf.Color.Yellow))
                
                self.block_shoot = True
            return
        
        self.cur_tile = Player.ANIM_SHOOT        
        if self.block_shoot is True:
            return
            
        self.moved_once = self.block_shoot = True
        if self.ammo == 0:
            self.game.AddEntity(InventoryChangeAnimStub("Out of ammo, idiot",
                self.pos,color=sf.Color.Yellow))
            return 
        
        self.ammo -= 1
        if self.ammo == 2:
            self.game.AddEntity(InventoryChangeAnimStub("Warn: low ammo",
                self.pos,color=sf.Color.Yellow))

        print("Shoot!")
        def check(other):
            return other.color == self.color
        
        if self.dir == Player.RIGHT:
            weapon.Shoot((self.pos[0]+self.pwidth*1.2,self.pos[1]+self.pheight*0.6),\
                (1.0,0.0),sf.Color(200,200,255),check)
        else:
            weapon.Shoot((self.pos[0]-1.0,self.pos[1]+self.pheight*0.6),\
                (-1.0,0.0),sf.Color(200,200,255),check)
                         
        
    def Update(self, time_elapsed, time):
        if self.game.IsGameRunning() is False:
            return
        
        # Check if one of our perks has expired
        for perk in list(self.perks):
            perk._CheckIfExpired(self) 
        
        inp = Renderer.app.GetInput()
        self.acc = [0, self.level.gravity]
        vec = [0, 0]
        
        pvely = self.vel[1]

        if inp.IsKeyDown(KeyMapping.Get("move-left")):
            self.vel[0] = -defaults.move_speed[0] * self.speed_scale
            self.cur_tile = Player.ANIM_WALK
            self.dir = Player.LEFT

            self.moved_once = True
            
        if inp.IsKeyDown(KeyMapping.Get("move-right")):
            self.vel[0] = defaults.move_speed[0] * self.speed_scale
            self.cur_tile = Player.ANIM_WALK
            self.dir = Player.RIGHT

            self.moved_once = True

        if defaults.debug_updown_move is True or self.move_freely is True:
            if inp.IsKeyDown(KeyMapping.Get("move-up")):
                self.pos[1] -= time * defaults.move_speed[1]
                self.moved_once = True
                self.cur_tile = Player.ANIM_JUMP
            if inp.IsKeyDown(KeyMapping.Get("move-down")):
                self.pos[1] += time * defaults.move_speed[1]
                self.moved_once = True
                self.cur_tile = Player.ANIM_JUMP
        else:
            if inp.IsKeyDown(KeyMapping.Get("move-up")):
                if self.in_jump is False and self.block_jump is False:
                    self.vel[1] -= defaults.jump_vel * self.jump_scale
                    self.in_jump = self.block_jump = True

                    self.cur_tile = Player.ANIM_JUMP
                self.moved_once = True
            else:
                self.block_jump = False
            
        newvel = [self.vel[0] + self.acc[0] * time, self.vel[1] + (self.acc[1] + (defaults.gravity \
            if defaults.debug_updown_move is True else 0)) * time]

        vec[0] += newvel[0] * time
        vec[1] += newvel[1] * time

        newpos = [self.pos[0] + vec[0], self.pos[1] + vec[1]]

        # Check for collisions
        pos, self.vel = self._HandleCollisions(newpos, newvel, time)
        self.SetPosition(pos)
        
        if inp.IsKeyDown(KeyMapping.Get("shoot")):
            self._Shoot()
        else:
            self.block_shoot = False
        
        # (HACK) -- for debugging, prevent the player from falling below the map
        if defaults.debug_prevent_fall_down is True and self.pos[1] > defaults.tiles[1]:
            self.pos[1] = 1
            self.in_jump, self.block_jump = False, False
            self.vel[1] = 0

        self._CheckForTopMapBorder()
        self._CheckForBottomMapBorder()
        self._CheckForLeftMapBorder()
        self._UpdatePostFX()
        
        self.level.Scroll(self.pos)
        if self.moved_once is True:
            if self.setup_autoscroll is False:
                self.level.PopAutoScroll()
                self.setup_autoscroll = True
                
    def _CheckForTopMapBorder(self):
        lv = self.game.GetLevel()
        if lv.GetScroll() & Level.SCROLL_TOP == 0 and self.pos[1] < lv.GetLevelVisibleSize()[1]-lv.GetLevelSize()[1]:
            self._Kill("the map's upper border")
            
    def _CheckForBottomMapBorder(self):
        lv = self.game.GetLevel()
        if  lv.GetScroll() & Level.SCROLL_BOTTOM == 0 and self.pos[1] > defaults.tiles[1]:
            self._Kill("the map's lower border")

    def _CheckForLeftMapBorder(self):
        """Check if we passed the left border of the game, which is
        generally a bad idea because it's the last thing you do """
        origin = self.level.GetOrigin()
        if self.pos[0] < origin[0]:
            if self.pos[0] + self.pwidth > origin[0]:

                if not hasattr(self, "restore_color"):
                    self.restore_color = self.color
                    self.SetColor(sf.Color.Yellow)
                    print("Entering left danger area")
            else:
                self._Kill("the dangerous wall on the left")

        else:
            if hasattr(self, "restore_color"):
                if not self.color is self.restore_color:

                    print("Leaving left danger area, restoring old state")
                    self.SetColor(self.restore_color)
                else:
                    print("Can't restore old color, seemingly the player color " + \
                          "changed while the entity resided in the left danger area")
                delattr(self, "restore_color")

    def _UpdatePostFX(self):
        origin = self.game.GetLevel().GetOrigin()

        # XXX Use Game's coordinate sustem conversion utilities
        self.game.GetLevel().SetPostFXParameter("cur", (self.pos[0] + self.pwidth // 2 - origin[0]) / defaults.tiles[0],
            1.0 - (self.pos[1] + self.pheight // 2 - origin[1]) / defaults.tiles[1])

    def _Kill(self, killer="<add reason>"):
        """Internal stub to kill the player and to fire some nice
        animations to celebrate the event."""
        print("Player has died, official reason: {0}".format(killer))
        if self.game.GetLives() > 0:
            name = "splatter1.txt"
            for i in range(defaults.death_sprites):
                from tile import TileLoader
                
                # add human body parts plus generic splatter
                if i == defaults.death_sprites-2:
                    name = "splatter_player_special.txt"
                elif i == defaults.death_sprites-1:
                    name = "splatter_player_special2.txt"
                    
                t = TileLoader.Load(os.path.join(defaults.data_dir,"tiles_misc",name),self.game)
                
                t.SetSpeed(random.uniform(-1.0, 1.0))
                t.SetDirection((random.random(), random.random()))
                t.SetTTL(random.random()*18.0)
                t.SetPosition((self.pos[0]+self.pwidth/2,self.pos[1]+self.pheight/2))
                
                self.game.AddEntity(t)
            
        self.draw = False
        self.game.Kill(killer,self)

    def _HandleCollisions(self, newpos, newvel, time):
        """Handle any collision events, given the computed new position
        of the player. The funtion returns the actual position after
        collision handling has been performed."""
        self.AddToActiveBBs()

        # That's not a physically correct collision detection -
        # and the algorithm works for rectangles only.
        cnt, hasall = 0, 0
        floor_touch = False
        ab = (newpos[0] + self.pofsx, newpos[1], newpos[0] + self.pofsx + self.pwidth, newpos[1] + self.pheight)
        
        # left, top, right, bottom
        intersect = [[1e5,0.0],[1e5,0.0],[-1e5,0.0],[-1e5,0.0]]
        colliders = []
        fric = 1e10
        for collider in self.game.GetLevel().EnumPossibleColliders(ab):
            if collider is self:
                continue
            
            cd = collider.GetBoundingBox()
            if cd is None:
                continue
            
            cd = (cd[0], cd[1], cd[2] + cd[0], cd[3] + cd[1])     
            
            # is our left border intersecting?
            if cd[2] >= ab[0] >= cd[0]:
                if ab[1] <= cd[1] <= ab[3] or cd[1] <= ab[1] <= cd[3]:
                    
                    res = collider.Interact(self)
                    if res == Entity.KILL:
                        print("hit deadly entity, need to commit suicide")
                        if defaults.debug_godmode is False and self.unkillable == 0:
                            self._Kill(collider.GetVerboseName())
                        return newpos, newvel
            
                    elif res == Entity.BLOCK:
                        intersect[0][0] = min(intersect[0][0],cd[2] - self.pofsx)
                        intersect[0][1] += min( ab[3], cd[3]) - max(ab[1], cd[1])     
                        
                        colliders.append(collider)          
                
            # is our right border intersecting?
            if cd[2] >= ab[2] >= cd[0]:
                if ab[1] <= cd[1] <= ab[3] or cd[1] <= ab[1] <= cd[3]:
                    
                    res = collider.Interact(self)
                    if res == Entity.KILL:
                        print("hit deadly entity, need to commit suicide")
                        if defaults.debug_godmode is False and self.unkillable == 0:
                            self._Kill(collider.GetVerboseName())
                        return newpos, newvel
            
                    elif res == Entity.BLOCK:
                    
                        intersect[2][0] = max(intersect[2][0],cd[0] - self.pwidth - self.pofsx)
                        intersect[2][1] += min( ab[3], cd[3]) - max(ab[1], cd[1])    
                        
                        colliders.append(collider)
                
            # is our lower border intersecting?
            if cd[1] <= ab[3] <= cd[3]:
                if ab[0] <= cd[0] <= ab[2] or cd[0] <= ab[0] <= cd[2]:
                    
                    res = collider.Interact(self)
                    if res == Entity.KILL:
                        print("hit deadly entity, need to commit suicide")
                        if defaults.debug_godmode is False and self.unkillable == 0:
                            self._Kill(collider.GetVerboseName())
                        return newpos, newvel
            
                    elif res == Entity.BLOCK:
               
                        intersect[3][0] = max(intersect[3][0], cd[1] - self.pheight)
                        intersect[3][1] += min( ab[2], cd[2]) - max(ab[0], cd[0])
                        
                        colliders.append(collider)
                        fric = min(fric, collider.GetFriction())
                                           
                    
            # is our top border intersecting?
            if cd[1] <= ab[1] <= cd[3]:
                if ab[0] <= cd[0] <= ab[2] or cd[0] <= ab[0] <= cd[2]:
                    
                    res = collider.Interact(self)
                    if res == Entity.KILL:
                        print("hit deadly entity, need to commit suicide")
                        if defaults.debug_godmode is False and self.unkillable == 0:
                            self._Kill(collider.GetVerboseName())
                        return newpos, newvel
            
                    elif res == Entity.BLOCK:
        
                        # XXX one day, I need to cleanup these messy size calculations in Player
                        intersect[1][0] = min(intersect[1][0], cd[3])
                        intersect[1][1] += min( ab[2], cd[2]) - max(ab[0], cd[0])
                        
                        colliders.append(collider)
                    
        if colliders: #sum(e[1] for e in intersect) != 0:
            #print(intersect)
            cnt += len(colliders)
            for collider in colliders:
                collider.AddToActiveBBs()            
            
            for n,elem in enumerate(intersect): # sorted(enumerate(intersect),key=lambda x:x[1][1],reverse=True):
                if elem[1] < 0.3:
                    continue
            
                if n == 3:
                    newpos[1] = elem[0]
                    newvel[1] = min(0, newvel[1])
                                
                    f = fric*time # XXX too lazy to think of a pure arithmetic solution
                    newvel[0] = newvel[0] - (min(newvel[0],f) if newvel[0]>0 else max(newvel[0],-f))
                    floor_touch = True
                    #print("floor")
        
                    self.cur_tile = Player.ANIM_WALK
                    self.in_jump = False
                    
                elif n == 0:
                    newpos[0] = elem[0]
                    newvel[0] = max(0, newvel[0])
                    #print("left")
                    
                elif n == 2:
                    newpos[0] = elem[0]
                    newvel[0] = min(0, newvel[0])
                    #print("right")
                    
                elif n == 1:
                    newpos[1] = elem[0]
                    newvel[1] = max(0, newvel[1])  
                    #print("top")                 
             
        if floor_touch is False:
            # simulate air friction while we *are* in air. increase the effect
            # the higher the y velocity is. this allows for better control
            # during jumps.
            newvel[0] = max(0.0, newvel[0] - 0.3*time*(math.log(max(2, newvel[1]))/math.log(2)))
            newvel[0] *= (1.0 - time*5)

        #print("Active colliders: {0}".format(cnt))
        return newpos, newvel

    def GetBoundingBox(self):
        # Adjust the size of the bb slightly to increase the likelihood
        # to pass tight tunnels.
        pcb = (defaults.player_caution_border[0] / defaults.tiles_size_px[0], \
            defaults.player_caution_border[1] / defaults.tiles_size_px[1])

        return (self.pos[0] + self.pofsx + pcb[0] / 2, self.pos[1] + pcb[1], \
            self.pwidth - pcb[0], self.pheight - pcb[1])

    def _AddRespawnPoint(self, pos):
        """Add a possible respawn position to the player entity."""
        assert hasattr(self, "respawn_positions")
        self.respawn_positions.append(pos)
        print("Set respawn point {0}|{1}".format(pos[0], pos[1]))
        
    def _AddOrderedRespawnPoint(self, pos):
        """Add a possible respawn position to the player entity,
        that is a respawn point the player jumps to, without regard
        to the position of death. If multiple ordered respawn
        points are registered, the last is taken."""
        if (pos[0] != self.ordered_respawn_positions[-1][0] and pos[1] != self.ordered_respawn_positions[-1][1]):
            self.ordered_respawn_positions.append(pos)
            print("Set ordered respawn point {0}|{1}".format(pos[0], pos[1]))

    def Respawn(self, enable_respawn_points):
        """Used internally by Game.Respawn to respawn the player
        at a given position"""
        assert hasattr(self, "respawn_positions")
        assert len(self.respawn_positions)

        # XXX ordered and normal respawn point can be mixed, although this is a corner-case
        # and not really useful at all.
        min_distance = float(defaults.min_respawn_distance)
        for rpos in sorted(self.respawn_positions if enable_respawn_points is True else (),key=operator.itemgetter(0),reverse=True):
            if rpos[0] > self.pos[0] or mathutil.Length((rpos[0] - self.pos[0], rpos[1] - self.pos[1])) < min_distance:
                continue # this is to protect the player from being
                # respawned in kill zones.
                
            # favour the last ordered respawn point if there is one
            if len(self.ordered_respawn_positions):
                self.SetPositionAndMoveView(self.ordered_respawn_positions[-1])
                self.ordered_respawn_positions.pop()
            
            else:
                self.SetPositionAndMoveView(rpos)
            break
            
        else:
            if len(self.ordered_respawn_positions):
                self.SetPositionAndMoveView(self.ordered_respawn_positions[-1])
                self.ordered_respawn_positions.pop()
            else:
                self.SetPositionAndMoveView(self.respawn_positions[0])

        # Reset our status
        self._Reset()
        self.Protect(defaults.respawn_protection_time)
        raise NewFrame()


class RespawnPoint(Entity):
    """A respawning point represents a possible position where
    the player can respawn if he or she dies"""


    def Update(self, time_elapsed, time):
        if hasattr(self, "didit"):
            return

        for entity in self.game._EnumEntities():
            if hasattr(entity, "_AddRespawnPoint"):
                entity._AddRespawnPoint(self.pos)
                
        self.didit = True

    def GetBoundingBox(self):
        return (self.pos[0], self.pos[1], 0.5, 0.5)

    def Interact(self, other):
        return Entity.ENTER
    
    
class DisabledRespawnPoint(Entity):
    """A disabled respawning point needs to be touched
    once by the player in order to serve as respawn
    point candidate."""


    def Update(self, time_elapsed, time):
        pass

    def GetBoundingBox(self):
        return (self.pos[0], self.pos[1], 0.5, 0.5)

    def Interact(self, other):
        if isinstance(other,Player):

            for entity in self.game._EnumEntities():
                if hasattr(entity, "_AddRespawnPoint"):
                    entity._AddRespawnPoint(self.pos)
                
        return Entity.ENTER


class KillAnimStub(Tile):
    """Implements the text strings that are spawned whenever
    the player is killed."""

    def __init__(self, text, index=None):
        Tile.__init__(self, random.choice(text.split("\n\n")),draworder=11000)

        self.ttl = 0
        
        self.dirvec = [1.0,1.0]
        self.SetColor(sf.Color(150,0,0,255))
        
    def _GetHaloImage(self):
        return Entity._GetHaloImage(self,random.choice(
            ("halo_blood.png","halo_blood2.png","halo_blood3.png","halo_blood4.png","halo_blood5.png")
        ))
        
    def SetDirection(self,dirvec):
        self.dirvec = mathutil.Normalize(dirvec)
        
    def SetSpeed(self,speed):
        self.speed = speed
        
    def SetTTL(self,ttl):
        self.ttl = ttl

    def GetBoundingBox(self):
        return None

    def Update(self, time_elapsed, time_delta):
        self.SetPosition((self.pos[0] + self.dirvec[0] * time_delta * self.speed, self.pos[1] + self.dirvec[1] * time_delta * self.speed))

        if not hasattr(self, "time_start"):
            self.time_start = time_elapsed
            return

        if time_elapsed - self.time_start > self.ttl:
            self.game.RemoveEntity(self) 
        
    def Draw(self):
        Tile.Draw(self)


class InventoryChangeAnimStub(Tile):
    """Implements the text string that is spawned whenever
    the player adds or removes an item from the inventory."""

    def __init__(self,text,pos,speed=1.0,color=sf.Color.Green):
        Tile.__init__(self,text,draworder=11002)
        
        self.SetPosition( pos )
        self.speed = speed
        self.SetColor(color)

    def GetBoundingBox(self):
        return None

    def Update(self,time_elapsed,time_delta):
        self.SetPosition((self.pos[0],self.pos[1]+time_delta*self.speed))

        if self.pos[1] > defaults.tiles[1]:
            self.game.RemoveEntity(self) 
            
    def _GetHaloImage(self):
        return None

        
        
        
        
