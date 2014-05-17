#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [player.py]
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

# Python core
import math
import random
import os
import operator

# My own stuff
from stubs import *
from complexanim import Anim,AnimSet


class InventoryItem:
    """Base class for inventory items.
    Such items are collected by the player and are subsequently
    reused to perform specific actions, i.e. open doors.
    
    Permanent inventory items remain in the player's inventory
    upon level switching. That is used i.e. to control the
    story-related items the player has to collect.
    """
    
    def __init__(self):
        pass
    
    def GetItemName(self):
        """Return a descriptive item name to be displayed to the user"""
        return "an unnamed inventory item"
    
    def SameKind(self,other):
        return not not (type(self) == type(other) and self.color == other.color)
    
    def TakeMe(self,player):
        """Let the player take the item and remove it from the scene"""
        if not hasattr(self,"item_taken"):
            # we need to deal with te situation that the player may interact 
            # with us multiple times in a single frame, so we may not yet 
            # have been removed from the entity list.
            player.AddToInventory(self)
            self.game.RemoveEntity(self)
            self.item_taken = True
    
                

class Player(Entity):
    """Special entity which responds to user input and moves the
    player tiles accordingly. Multiple player's can coexist in
    a single level."""

    ANIM_WALK, ANIM_JUMP, ANIM_SHOOT = range(3)
    MAX_ANIMS = 3
    
    LEFT,RIGHT=range(2)

    def __init__(self, text, width, height, ofsx, move_freely=False, draworder=1000, animset='player'):
        Entity.__init__(self)

        pcb = (defaults.player_caution_border[0] / defaults.tiles_size_px[0], 
            defaults.player_caution_border[1] / defaults.tiles_size_px[1])
        
        self.pofsx = ofsx / defaults.tiles_size[0] + pcb[0]*0.5
        self.pofsy = pcb[1]*0.5

        self.pwidth = width / defaults.tiles_size[0] + pcb[0]*0.5
        self.pheight = height / defaults.tiles_size[1] - pcb[1]*0.5
        
        self.dirchange_clock = None
        self.move_steady = None
        self.steady_stand = None
        self.shoot_anim_timer = None
        self.turnto = None
        self.count_shoot_unsuccessful = 0
        self.weapon_shoot_unsuccessful = 0
        
        self.was_spinning = False
        
        # XXX get rid of pwith and pheight
        self.dim = self.pwidth,self.pheight
        self.draworder = draworder

        lines = text.split("\n")
        height = len(lines) // (Player.MAX_ANIMS*2)

        from weapon import Weapon
        self.inventory = []
        self.ordered_respawn_positions = []
        self.ammo = [0]
        self.move_freely = move_freely
        self.block_input = False

        def config_tile(t):
            t.SetDim(self.dim)
            t.SetPosition((0,0))

        self.animset = AnimSet(animset)
        self.animset.ConfigureTilesGlobally(config_tile)
        self.animset.Select('idle_left')

        self.dead = False
        self.scale = 1.0
        
    def __str__(self):
        return "<ThePlayer>"
        
    def SetLevel(self,level):
        Entity.SetLevel(self,level)
        
        self.inventory = level.inventory_shared
        self._Reset()
        
    def SetGame(self,game):
        Entity.SetGame(game)
        self.ammo = game.GetCookie("ammo",self.ammo)
        
    def GetRemainingAmmo(self):
        return self.ammo[0]
    
    def Scale(self,factor):
        """Scale the player's body dimensions on all axes uniformly"""
        assert factor > 0.0
        
        #self.rsize *= factor
        self.dim = self.dim[0]*factor,self.dim[1]*factor
        self.pwidth *= factor
        self.pheight *= factor
        self.pofsx *= factor
        self.pofsy *= factor
        
        def config_tile(t):
            t.Scale(factor)

        self.animset.ConfigureTilesGlobally(config_tile)
        
        self.scale *= factor
        
    def Unscale(self):
        """Undo any scaling applied to the object"""
        self.Scale(1.0/self.scale)

    def _Reset(self):
        """Reset the state of the player instance, this is needed
        for proper respawning"""
        self.vel = [0, 0]
        self.in_jump = self.block_jump = not not self.level.gravity
        self.in_djump = self.block_djump = not not self.level.gravity 
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
        self.dead = False
        self.Unscale()
        
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
                outer.unkillable += 1
                
            def _RemoveMe(self):
                outer.unkillable = max(0, outer.unkillable- 1)
                try:
                    delattr( outer, "flash_halo" )
                    outer.protectors.remove(self)
                except (AttributeError,ValueError):
                    pass
                
                print("End respawn protection on {0}".format(outer))                  
                Renderer.RemoveDrawable(self)
            
            def Draw(self):
                if self.timer.GetElapsedTime()>self.time:
                    self._RemoveMe()
                    
        
        print("Set respawn protection on {0}".format(self))
        
        img = self._GetHaloImage("halo_protect.png")
        if not img is None:
            self.flash_halo = sf.Sprite(img)
            self.flash_halo.Resize(self.pwidth * defaults.tiles_size_px[0],self.pheight * defaults.tiles_size_px[1])
            self.flash_halo.SetColor(sf.Color(255,255,0,160))
           
        p = Proxy() 
        self.__dict__.setdefault("protectors",[]).append(p)
        Renderer.AddDrawable(p)
        
    def DropProtection(self):
        for e in list(getattr(self,"protectors",[])):
            e._RemoveMe()
        
    def SetGame(self, game):
        self.game = game
        
        def config_tile(t):
            t.SetGame(self.game)
        self.animset.ConfigureTilesGlobally(config_tile)
        
        
    def SetPosition(self, pos):
        Entity.SetPosition(self,pos)

        # (HACK) keep the original position, for we need it to implement respawning
        if not hasattr(self, "respawn_positions"):
            self.respawn_positions = []
            self._AddRespawnPoint(pos)
            
    def EnumInventoryItems(self):
        """Yields all inventory items in unspecified order.
        use send(item) to mark a specific item for deletion.
        
        DO not break loops through this generator!!"""
        erase = []
        for item in self.inventory:
            assert isinstance(item,InventoryItem)
            
            item = ( yield item )
            if not item is None:
                print("Remove inventory item during EnumInventoryItems!")
                erase.append(item)
                
        for item in erase:
            self.RemoveFromInventory(item)
            
            
    def AddToInventory(self,item):
        """Adds an item to the player's inventory. The same
        item can be added multiple times."""
        assert isinstance(item,InventoryItem)
        
        cnt = len([i for i in self.inventory if i.SameKind(item)])
        
        self.inventory.append(item)
        self.game.AddEntity(InventoryChangeAnimStub("++ Added "+item.GetItemName() + 
            (_(" [#{0} of this item]").format(cnt+1) if cnt else "") + _(" to inventory"),self.pos))
        
        print("Add item to inventory: {0}".format(item))
        
    def AddAmmo(self,ammo):
        """Add a specific amount of ammo to the player's inventory.
        One shoot consumes one unit of ammo.""" 
        assert ammo > 0
        self.ammo[0] += ammo
        self.game.AddEntity(InventoryChangeAnimStub(_("++ {0}x ammo").format(ammo),
            self.pos,color=sf.Color.Yellow,border=False))
        
        print("Add ammo: {0}".format(ammo))
        
    def RemoveFromInventory(self,item):
        """Removes an item from the player's inventory. If the
        same item exists multiple times, only its first
        occurences is removed. ValueError is raised it
        the item does not exist. Note: do not use from
        within EnumInventoryItems() -- ! it provides a different
        scheme to remove entities. """
        assert isinstance(item,InventoryItem)
        self.inventory.remove(item)
        cnt = len([i for i in self.inventory if i.SameKind(item)])
        self.game.AddEntity(InventoryChangeAnimStub("-- "+item.GetItemName()+
            (_(" [I have {0} more of this kind]").format(cnt) if cnt else ""),
            self.pos,color=sf.Color.Red))
            
    def SetPositionAndMoveView(self, pos, ofs=None):
        """Change the players position and adjust the viewport accordingly.
        The optional offset value is the distance from the left viewport
        border."""
        
        
        # some tiles (i.e. Heat) may be relying on the fact that they
        # receive continous Update() calls while the player is in
        # a certain range. If the player suddently changes his position,
        # those tiles may not react correctly because they miss
        # the ultimate Update() call that would cause them to revert
        # their effect (postfx in case of the Heat effect) on the
        # player or the screen. So we need to grab the previous
        # visible set, move the player and call Update() once on all
        # tiles that were previously visible. 
        
        
        entities = self.level.EnumActiveEntities(); 
        self.SetPosition(pos)
        
        t = self.game.time
        tdelta = self.game.time_delta
        for e in entities:
            if e != self: # exclude the player since this would trigger unwanted Interact() calls
                e.Update(t,tdelta) 
        
        self.level.SetOriginX(self.pos[0] - (ofs or defaults.respawn_origin_distance))

    def SetColor(self, pos):
        self.color = pos
            
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
        
        t = self.animset.GetCurrentTile()
        
        # draw a quick shadow to improve the visibility of the player
        old, t.color = self.color, sf.Color(30,30,30,150)
        
        ofs_x = 1.0/defaults.tiles_size_px[0]
        ofs_y = 1.0/defaults.tiles_size_px[1]
        t.DrawRelative((self.pos[0]-ofs_x,self.pos[1]-ofs_y))
        t.DrawRelative((self.pos[0]-ofs_x,self.pos[1]+ofs_y))
        t.DrawRelative((self.pos[0]+ofs_x,self.pos[1]+ofs_y))
        t.DrawRelative((self.pos[0]+ofs_x,self.pos[1]-ofs_y))
        
        t.color = old
        t.DrawRelative(self.pos)
        
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
                messages = [
                    _("Dude, you have no weapon ..."),
                    _("You don't have a weapon"),
                    _("You DON'T have a weapon"),
                    _(".. and unless you have a wand (which you don't have), it's unlikely that this situation will change by means other than picking up a weapon"),
                    _("I don't know why I'm saying this again: you have no weapon"),
                    _("If you don't stop, I'll recite a poem"),
                    _("I'll just ignore you"),
                    _("--")
                ]
                
                self.game.AddEntity(InventoryChangeAnimStub(messages[min(self.weapon_shoot_unsuccessful,len(messages)-1)],
                    self.pos,color=sf.Color.Yellow))
                
                self.weapon_shoot_unsuccessful += 1
                self.block_shoot = True
            return
        
        self.cur_tile = Player.ANIM_SHOOT        
        if self.block_shoot is True:
            return
            
        self.moved_once = self.block_shoot = True
        if self.ammo[0] == 0:
            messages = [
                _("Out of ammo"),
                _("Still out of ammo"),
                _("Still out of ammo - bored?"),
                _("Still out of ammo. Please don't hit 'shoot' unless you have ammo"),
                _("Stop it!"),
                _("If you don't stop, I'll recite a poem"),
                _("I'll just ignore you"),
                _("--")
            ]
            
            self.game.AddEntity(InventoryChangeAnimStub(messages[min(self.count_shoot_unsuccessful,len(messages)-1)],self.pos,color=sf.Color.Yellow))
            self.count_shoot_unsuccessful += 1
            return 
        
        self.count_shoot_unsuccessful = 0
        self.weapon_shoot_unsuccessful = 0
        
        self.ammo[0] -= 1
        if self.ammo[0] == 2:
            self.game.AddEntity(InventoryChangeAnimStub(_("Warn: low ammo"),
                self.pos,color=sf.Color.Yellow))
        
        if self.dir == Player.RIGHT:
            weapon.Shoot((self.pos[0]+self.pwidth*1.2,self.pos[1]+self.pheight*0.6),\
                (1.0,0.0),self.color,[self],None,True)
        else:
            weapon.Shoot((self.pos[0]-1.0,self.pos[1]+self.pheight*0.6),\
                (-1.0,0.0),self.color,[self],None,True)
            
    def Interact(self,other):
        from weapon import Shot
        if isinstance(other, Shot):
            if self.MeCanDie():
                self._Kill("a ray-blaster shot")
            return Entity.BLOCK
            
        return Entity.Interact(self,other)
                         
    def Update(self, time_elapsed, time):
        # XXX refactor this function, probably use an external controller distinct from the view logic.
        if not self.game.IsGameRunning() or self.dead:
            return
            
        # if self.game.mode == Game.BACKGROUND:
        #    return
        
        # Check if one of our perks has expired
        for perk in list(self.perks):
            perk._CheckIfExpired(self) 
        
        
        self.acc = [0, self.level.gravity]
        vec = [0, 0]
        
        pvely = self.vel[1]
        anim = None
        move = False
        
        cur_anim = self.animset.GetCurrent()
        
        def lr_suffix():
            return '_'+('left' if self.dir == Player.LEFT else 'right')

        inp = Renderer.app.GetInput()
        if not self.block_input:

            if defaults.debug_updown_move is True or self.move_freely is True:
                if inp.IsKeyDown(KeyMapping.Get("move-up")):
                    self.pos[1] -= time * defaults.move_speed[1]
                    self.moved_once = True
                    anim = 'jump'+lr_suffix()
                if inp.IsKeyDown(KeyMapping.Get("move-down")):
                    self.pos[1] += time * defaults.move_speed[1]
                    self.moved_once = True
                    anim = 'jump'+lr_suffix()
            else:
                if inp.IsKeyDown(KeyMapping.Get("move-up")):
                    if self.in_jump is False and self.block_jump is False:
                        self.vel[1] -= defaults.jump_vel * self.jump_scale
                        self.in_jump = self.level.gravity != 0 
                        self.block_jump = True
    
                        anim = 'jump'+lr_suffix()
                    self.moved_once = True
                    
                else:
                    self.block_jump = False
                    
                if inp.IsKeyDown(KeyMapping.Get("move-down")):
                    if self.in_djump is False and self.block_djump is False:
                        self.vel[1] += defaults.jump_vel * self.jump_scale
                        self.in_djump = self.level.gravity != 0 
                        self.block_djump = True
    
                        anim = 'jump'+lr_suffix()
                        self.moved_once = True
                else:
                    self.block_djump = False

                    
            if inp.IsKeyDown(KeyMapping.Get("move-left")):
                if self.dir == Player.RIGHT or (self.dirchange_clock and self.dirchange_clock.GetElapsedTime() < defaults.turnaround_delay):
                    # player changes direction from right to left
                    if self.vel[0] > 0 or self.in_jump:
                        # player was moving to the right, so first get to idle-right
                        anim = 'right_to_midr'
                    
                    self.vel[0] = 0
                    self.turnto = 'l'
                    
                    if self.dir == Player.RIGHT:
                        self.dirchange_clock = sf.Clock()               
                else:
                    self.dirchange_clock = None
                    self.vel[0] = -defaults.move_speed[0] * self.speed_scale
                    if not self.turnto and not self.in_jump:
                        anim = 'walk_left'
                
                self.dir = Player.LEFT
                self.moved_once = True
                move = True
                
            if inp.IsKeyDown(KeyMapping.Get("move-right")):
                if self.dir == Player.LEFT or (self.dirchange_clock and self.dirchange_clock.GetElapsedTime() < defaults.turnaround_delay):
                    # player changes direction from right to left
                    if self.vel[0] < 0 or self.in_jump:
                        # player was moving to the right, so first get to idle-right
                        anim = 'left_to_midl'
                        
                    self.vel[0] = 0
                    self.turnto = 'r'
                    
                    if self.dir == Player.LEFT:
                        self.dirchange_clock = sf.Clock()
                else:
                    self.dirchange_clock = None
                    self.vel[0] = defaults.move_speed[0] * self.speed_scale
                    if not self.turnto and not self.in_jump:
                        anim = 'walk_right'
                
                
                #if not self.in_jump: # do not trigger walking animation while jumping
                #    anim = 'walk'+lr_suffix()
                    
                self.dir = Player.RIGHT
                self.moved_once = True
                move = True

            # HACK: fake acceleration effect when walking, kept separate from self.acc to avoid interfering with other effects
            if self.vel[0] == 0:
                self.move_steady = None
                if not self.steady_stand:
                    self.steady_stand = sf.Clock()
            else:
                self.steady_stand = None
                if not self.move_steady:
                    self.move_steady = sf.Clock()
                    s = 0.02
                elif self.in_jump:
                    s = 1.0
                else:
                    s = math.exp(self.move_steady.GetElapsedTime())-1
                self.vel[0] *= min(s,0.33)*3

            if self.turnto == 'l' and anim != 'right_to_midr':
                if cur_anim == 'idle_right':
                    # player in idle_right, so get to idle_left
                    anim = 'midr_to_midl'
                elif cur_anim == 'idle_left':
                    anim = 'midl_to_left'
                elif not cur_anim in ('midl_to_left','midr_to_midl','right_to_midr'):
                    if self.vel[0] < 0:
                        anim = 'walk_left'
                    if self.was_spinning:
                        anim = 'spin_left'
                    self.turnto = None
                    
            elif self.turnto == 'r' and anim != 'left_to_midl':
                if cur_anim == 'idle_left':
                    anim = 'midl_to_midr'
                elif cur_anim == 'idle_right':
                    anim = 'midr_to_right'
                elif not cur_anim in ('midr_to_right','midl_to_midr','left_to_midl'):
                    if self.vel[0] > 0:
                        anim = 'walk_right'
                    if self.was_spinning:
                        anim = 'spin_right'
                    self.turnto = None   
        
        newvel = [self.vel[0] + self.acc[0] * time, self.vel[1] + (self.acc[1] + (defaults.gravity \
            if defaults.debug_updown_move is True else 0)) * time]

        vec[0] += max(-defaults.max_velocity_x, min(defaults.max_velocity_x, newvel[0])) * time
        vec[1] += max(-defaults.max_velocity_y, min(defaults.max_velocity_y, newvel[1])) * time

        newpos = [self.pos[0] + vec[0], self.pos[1] + vec[1]]

        # Check for collisions
        pos, self.vel, touch_lower = self._HandleCollisions(newpos, newvel, time)
        self.SetPosition(pos)
        
        if touch_lower:
            self.was_spinning = False
        
        if hasattr(self,"extra_vel"):
            # Apply extra velocity, such as coming from air flows
            self.vel = [self.extra_vel[0]+self.vel[0],self.extra_vel[1]+self.vel[1]]
            delattr(self,"extra_vel")

            anim = 'spin'+lr_suffix()
            self.was_spinning = True
        
        # (HACK) -- for debugging, prevent the player from falling below the map
        if defaults.debug_prevent_fall_down is True and self.pos[1] > defaults.tiles[1]:
            self.pos[1] = 1
            self.in_jump, self.block_jump = False, False
            self.vel[1] = 0
            
        self._CheckForTopMapBorder()
        self._CheckForBottomMapBorder()
        self._CheckForLeftMapBorder()
        self._UpdatePostFX()
        
        # Very quick fix to make it work if there are multiple players around in the level
        players = sorted(((pl,pl.pos[0]) for pl in self.level.players),key=operator.itemgetter(1))
        if players[-1][0] is self:
            self.level.Scroll(self.pos)
        
        if self.moved_once is True:
            if self.setup_autoscroll is False:
                self.level.PopAutoScroll()
                self.setup_autoscroll = True

        # handle shots
        if inp.IsKeyDown(KeyMapping.Get("shoot")):
            self._Shoot()
            shoot_anim = True

            self.pre_shoot = anim or cur_anim
            self.shoot_anim_timer = sf.Clock()
        else:
            self.block_shoot = False
            shoot_anim = self.shoot_anim_timer and self.shoot_anim_timer.GetElapsedTime() < defaults.shoot_anim_delay

        if shoot_anim:
            anim = 'shoot'+lr_suffix()
        else:
            self.shoot_anim_timer = None
            #if cur_anim[:5] == 'shoot':
            #    anim = self.pre_shoot

        # handle walk-to-idle transition after some idleing time has passed
        if anim is None and not self.in_jump and not self.turnto:
            if self.steady_stand and self.steady_stand.GetElapsedTime() > defaults.idle_delay:
                if self.dir == Player.LEFT:
                    if cur_anim != 'idle_left':
                        anim = 'left_to_midl'
                elif cur_anim != 'idle_right':
                    anim = 'right_to_midr'
            else:
                anim = 'walk'+lr_suffix()+'_preparetoidle'          
        
        if anim:
            print(anim)
            self.animset.Select(anim)
        self.animset.UpdateCurrentTile(time_elapsed,time)
                
    def _CheckForTopMapBorder(self):
        lv = self.game.GetLevel()
        if lv.GetScroll() & Level.SCROLL_TOP == 0 and self.pos[1] < -self.level.vis_ofs and defaults.debug_godmode is False:
            self._Kill("the map's upper border")
            
    def _CheckForBottomMapBorder(self):
        lv = self.game.GetLevel()
        if  lv.GetScroll() & Level.SCROLL_BOTTOM == 0 and self.pos[1] > defaults.tiles[1]:
            self._Kill("the map's lower border")

    def _CheckForLeftMapBorder(self):
        """Check if we passed the left border of the game, which is
        generally a bad idea because it's the last thing you do """
        if len(self.level.players) > 1:
            return
            
        origin = self.level.GetOrigin()
        if self.pos[0] < origin[0]:
            if self.pos[0] + self.pwidth > origin[0]:

                if not hasattr(self, "restore_color"):
                    self.restore_color = self.color
                    self.SetColor(sf.Color.Yellow)
                    print("Entering left danger area")
            else:
                self._Kill(_("the dangerous wall on the left"))

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
        #origin = self.game.GetLevel().GetOrigin()

        # XXX Use Game's coordinate sustem conversion utilities
        #self.game.GetLevel().SetPostFXParameter("cur", (self.pos[0] + self.pwidth // 2 - origin[0]) / defaults.tiles[0],
        #    1.0 - (self.pos[1] + self.pheight // 2 - origin[1]) / defaults.tiles[1])
        pass
    
    def _SpreadSplatter(self):
        name = "splatter1.txt"
        remaining = min( max(self.game.MaxUselessSprites(), 
            defaults.min_death_sprites_player
        ),defaults.death_sprites_player)
        
        from tileloader import TileLoader
        for i in range(remaining):
            # add human body parts plus pieces of generic splatter
            if i == remaining-2:
                name = "splatter_player_special.txt"
            elif i == remaining-1:
                name = "splatter_player_special2.txt"
                
            t = TileLoader.Load(os.path.join(defaults.data_dir,"tiles_misc",name),self.game)
            
            t.RandomizeSplatter()
            t.SetPosition((self.pos[0]+self.pwidth/2,self.pos[1]+self.pheight/2))
            self.game.AddEntity(t)

    def _Kill(self, killer=None):
        """Internal stub to kill the player and to fire some nice
        animations to celebrate the event."""
        if self.dead:
            return # we are already bad. dumbass.
        
        killer = killer or _("<add reason>")
        print("Player has died, official reason: {0}".format(killer))
        if self.game.GetLives() > 0:
            self._SpreadSplatter()
                
        if self.game.GetGameMode() == Game.BACKGROUND:
            
            if not hasattr(self,'showed_bgdead_report'):
                self.showed_bgdead_report = True
            
                from score import ScoreTileAnimStub
                self.game.AddEntity(ScoreTileAnimStub(_(
    """This is just the menu so you can't die here, \nbut still: this was not healthy. 
Spreading all your blood across the entire\nscreen rarely is."""),self.pos,0.7))
        else:
            from posteffect import FlashOverlay
            Renderer.AddDrawable(FlashOverlay(sf.Color(80,0,0),0.1,5.5,2))
            
        self.draw = False
        self.dead = True
        self.game.Kill(killer,self)
        
        
    def MeCanDie(self):
        return defaults.debug_godmode is False and self.unkillable==0
    
        
    def _HandleCollisions(self, newpos, newvel, time):
        """Handle any collision events, given the computed new position
        of the player. The funtion returns the actual position after
        collision handling has been performed."""
        self.AddToActiveBBs()

        # That's not a physically correct collision detection -
        # and the algorithm works for rectangles only.
        cnt, hasall = 0, 0
        floor_touch = False
        
        old_ab = self.GetBoundingBoxAbs()
        ab = self.GetBoundingBoxAbsForPos(newpos) 
        
        dx,dy = ab[0]-old_ab[0], ab[1]-old_ab[1]
        taps = max(1, int((dx**2 + dy**2)**0.5 / defaults.collision_tap_size))
        
        ignore = [False,False,False,False]
            
        dx,dy = dx/taps,dy/taps
        #all = set()
        for n in range(taps):
            
            # left, top, right, bottom
            intersect = [[1e5,0.0],[1e5,0.0],[-1e5,0.0],[-1e5,0.0]]
            colliders = set()
            fric = 1e10
        
            n = n+1
            ab = old_ab[0]+dx*n,old_ab[1]+dy*n,old_ab[2]+dx*n,old_ab[3]+dy*n
            
            # (hack) temporarily set this bb as our own so colliders can rely on GetBoundingBox[Abs]() and GetPosition().
            # store a tuple to trigger problems if self.pos is accessed or modified by other means
            # than the aforementioned methods. This would indicate that this hack might have unwanted
            # side-effects.
            self.pos = (old_ab[0]+dx*n,old_ab[1]+dy*n)
        
            for collider in self.game.GetLevel().EnumPossibleColliders(ab):
                if collider is self: # or collider in all:
                    continue
                
                cd = collider.GetBoundingBoxAbsShrinked()
                if cd is None:
                    continue
            
                res = None   
                
                # is our left border intersecting?
                if cd[2] >= ab[0] >= cd[0]:
                    if ab[1] <= cd[1] <= ab[3] or cd[1] <= ab[1] <= cd[3]:
                        
                        res = collider.Interact(self)
                        if res == Entity.KILL:
                            print("hit deadly entity, need to commit suicide")
                            if self.MeCanDie():
                                self._Kill(collider.GetVerboseName())
                                return newpos, newvel, False
                
                        elif res & Entity.BLOCK_RIGHT and newvel[0] < 0:
                            intersect[0][0] = min(intersect[0][0],cd[2] - self.pofsx)
                            intersect[0][1] += min( ab[3], cd[3]) - max(ab[1], cd[1])     
                            
                            colliders.add(collider)          
                    
                # is our right border intersecting?
                if cd[2] >= ab[2] >= cd[0]:
                    if ab[1] <= cd[1] <= ab[3] or cd[1] <= ab[1] <= cd[3]:
                        
                        res = res or collider.Interact(self)
                        if res == Entity.KILL:
                            print("hit deadly entity, need to commit suicide")
                            if self.MeCanDie():
                                self._Kill(collider.GetVerboseName())
                                return newpos, newvel, False
                
                        elif res & Entity.BLOCK_LEFT and newvel[0] > 0:
                        
                            intersect[2][0] = max(intersect[2][0],cd[0] - self.pwidth - self.pofsx)
                            intersect[2][1] += min( ab[3], cd[3]) - max(ab[1], cd[1])    
                            
                            colliders.add(collider)
                    
                # is our lower border intersecting?
                if cd[1] <= ab[3] <= cd[3]:
                    if ab[0] <= cd[0] <= ab[2] or cd[0] <= ab[0] <= cd[2]:
                        
                        res = res or collider.Interact(self)
                        if res == Entity.KILL:
                            print("hit deadly entity, need to commit suicide")
                            if self.MeCanDie():
                                self._Kill(collider.GetVerboseName())
                                return newpos, newvel, False
                
                        elif res & Entity.BLOCK_TOP and (newvel[1] > 0 or self.level.gravity == 0):
                   
                            intersect[3][0] = max(intersect[3][0], cd[1] - self.pheight - self.pofsy)
                            intersect[3][1] += min( ab[2], cd[2]) - max(ab[0], cd[0])
                            
                            colliders.add(collider)
                            fric = min(fric, collider.GetFriction())
                                               
                        
                # is our top border intersecting?
                if cd[1] <= ab[1] <= cd[3]:
                    if ab[0] <= cd[0] <= ab[2] or cd[0] <= ab[0] <= cd[2]:
                        
                        res = res or collider.Interact(self)
                        if res == Entity.KILL:
                            print("hit deadly entity, need to commit suicide")
                            if self.MeCanDie():
                                self._Kill(collider.GetVerboseName())
                                return newpos, newvel, False
                
                        elif res & Entity.BLOCK_BOTTOM and (newvel[1] < 0 or self.level.gravity == 0):
            
                            # XXX one day, I need to cleanup these messy size calculations in Player
                            intersect[1][0] = min(intersect[1][0], cd[3] - self.pofsy)
                            intersect[1][1] += min( ab[2], cd[2]) - max(ab[0], cd[0])
                            
                            colliders.add(collider)
                    
            pain = 0
            if colliders: #sum(e[1] for e in intersect) != 0:
                cnt += len(colliders)
                for collider in colliders:
                    collider.AddToActiveBBs()            
                
                for n,elem in enumerate(intersect): # sorted(enumerate(intersect),key=lambda x:x[1][1],reverse=True):
                    if elem[1] < 0.3 or ignore[n]:
                        continue
                
                    #if elem[1] > 0.6:
                    ignore[n] = True
                    
                    if n == 3:
                        newpos[1] = elem[0]
                        pain +=  newvel[1]
                        painpos = ((ab[0]+ab[2])*0.5,ab[3])
                        
                        newvel[1] = min(0, newvel[1])
                                    
                        f = fric*time # XXX too lazy to think of a pure arithmetic solution
                        newvel[0] = newvel[0] - (min(newvel[0],f) if newvel[0]>0 else max(newvel[0],-f))
                        floor_touch = True
                        #print("floor")
            
                        self.cur_tile = Player.ANIM_WALK
                        self.in_jump = self.in_djump = False
                        
                    elif n == 0:
                        newpos[0] = elem[0]
                        pain += -newvel[0]
                        painpos = (ab[0],(ab[3]+ab[1])*0.5)
                        
                        newvel[0] = max(0, newvel[0])
                        #print("left")
                        
                    elif n == 2:
                        newpos[0] = elem[0]
                        pain += newvel[0]
                        painpos = (ab[2],(ab[3]+ab[1])*0.5)
                        
                        newvel[0] = min(0, newvel[0])
                        #print("right")
                        
                    elif n == 1:
                        newpos[1] = elem[0]
                        pain += -newvel[1]
                        painpos = ((ab[0]+ab[2])*0.5,ab[1])
                        
                        newvel[1] = max(0, newvel[1])  
                        #print("top")   
                            
            if pain > defaults.pain_treshold:
                print("Very hard landing, spawning cries")  
                self._ExperiencePain(self.vel,pain/defaults.pain_treshold,painpos) 
                     
             
        if floor_touch is False:
            # simulate air friction while we *are* in air. increase the effect
            # the higher the y velocity is. this allows for better control
            # during jumps.
            newvel[0] = max(0.0, newvel[0] - 0.3*time*(math.log(max(2, newvel[1]))/math.log(2)))
            newvel[0] *= (1.0 - time*5)

        #print("Active colliders: {0}".format(cnt))
        return newpos, newvel, floor_touch
    
    def _ExperiencePain(self,vel,pain,pos):
        name = "splatter2.txt"
        remaining = min( max(self.game.MaxUselessSprites(), 
            defaults.min_pain_sprites_player
        ),int(defaults.pain_sprites_player*pain))
        
        from posteffect import BlurInOverlay
        Renderer.AddDrawable(BlurInOverlay(min(4, 0.25*pain),0.4**pain))
        
        from tileloader import TileLoader
        for i in range(remaining):
            t = TileLoader.Load(os.path.join(defaults.data_dir,"tiles_misc",name),self.game)
            
            t.RandomizeSplatter()
            t.SetDirection((-vel[0]*random.uniform(0.5,1.5) + (random.uniform(-0.5,0.5)*vel[1]),
                            -vel[1]*random.uniform(0.5,1.5) + (random.uniform(-0.5,0.5)*vel[0])))
            
            t.SetPosition(pos)
            self.game.AddEntity(t)
    
    def SetExtraVelocity(self,vel):
        """Set extra velocity which is added to the physics simulation
        as is. Can be called at any time, but processing occurs
        during the next frame."""
        x,y = getattr(self,"extra_vel",(0,0))
        self.extra_vel = (x+vel[0],y+vel[1])

    def GetBoundingBox(self):
        return self.GetBoundingBoxForPos(self.pos)
    
    # XXX these are called a lot, so they need to be fast    
    def GetBoundingBoxForPos(self,pos):
        return (pos[0] + self.pofsx, pos[1] + self.pofsy, self.pwidth, self.pheight)
        
    def GetBoundingBoxAbsForPos(self,pos):
        bb = self.GetBoundingBoxForPos(pos)
        return (bb[0],bb[1],bb[0]+bb[2],bb[3]+bb[1])
    
    def GetBoundingBoxAbs(self):
        bb = self.GetBoundingBoxForPos(self.pos)
        return (bb[0],bb[1],bb[0]+bb[2],bb[3]+bb[1])
    

    def _AddRespawnPoint(self, pos, color=None):
        """Add a possible respawn position to the player entity."""
        assert hasattr(self, "respawn_positions")
        self.respawn_positions.append((pos,color or self.color))
        print("Set respawn point {0}|{1}".format(pos[0], pos[1]))
        
    def _AddOrderedRespawnPoint(self, pos, color=None):
        """Add a possible respawn position to the player entity,
        that is a respawn point the player jumps to, without regard
        to the position of his death. If multiple ordered respawn
        points are registered, the most recent is taken."""
        if not self.ordered_respawn_positions or (pos[0] != self.ordered_respawn_positions[-1][0][0] and pos[1] != self.ordered_respawn_positions[-1][0][1]):
            self.ordered_respawn_positions.append((pos,color or self.color))
            print("Set ordered respawn point {0}|{1}".format(pos[0], pos[1]))

    def Respawn(self, enable_respawn_points):
        """Used internally by Game.Respawn to respawn the player
        at a given position"""
        assert hasattr(self, "respawn_positions")
        assert len(self.respawn_positions)

        # favour the last ordered respawn point if there is one.
        # The two kinds of respawn points are handled totally independently.
        min_distance = float(defaults.min_respawn_distance)
        
        if len(self.ordered_respawn_positions) and enable_respawn_points is True:
            for rpos,color in reversed(self.ordered_respawn_positions):
                if mathutil.Length((rpos[0] - self.pos[0], rpos[1] - self.pos[1])) < min_distance:
                    npos,ncol = rpos,color
                    self.ordered_respawn_positions.pop()
                    break
            else:
                npos,ncol = self.ordered_respawn_positions[-1]
                self.ordered_respawn_positions.pop()
            
        else:    
            for rpos,color in sorted( (self.respawn_positions if enable_respawn_points is True else ()) ,key=lambda x:x[0][0],reverse=True):
                if rpos[0] > self.pos[0] or mathutil.Length((rpos[0] - self.pos[0], rpos[1] - self.pos[1])) < min_distance:
                    continue # this is to protect the player from being
                    # respawned in kill zones.
                
                npos,ncol = rpos,color
                break
                
            else:
                npos,ncol = self.respawn_positions[0]
            
        if self.game.mode == self.game.BACKGROUND:
            self.SetPosition(npos)
        else:
            self.SetPositionAndMoveView(npos)
        self.SetColor(ncol)
        
        print("Respawn at {0}".format(npos))

        # Reset our status
        self._Reset()
        self.Protect(defaults.respawn_protection_time)
        
        self.level.ResetPostFXToDefaults()

        if self.game.GetGameMode() != Game.BACKGROUND:
            from posteffect import QuickFocus
            Renderer.AddDrawable(QuickFocus(self))
        

class RespawnPoint(EntityWithEditorImage):
    """A respawning point represents a possible position where
    the player can respawn if he or she dies"""
    
    def __init__(self,editor_stub="respawn_stub2.png"):
        EntityWithEditorImage.__init__(self,editor_stub)
        self.editor_stub_img = editor_stub

    def Update(self, time_elapsed, time):
        EntityWithEditorImage.Update(self,time_elapsed, time)
        
        if hasattr(self, "didit"):
            return

        for entity in self.game._EnumEntities():
            if hasattr(entity, "_AddRespawnPoint"):
                entity._AddRespawnPoint(self.pos)
                
        self.didit = True

    def GetBoundingBox(self):
        return (self.pos[0], self.pos[1], 1.0, 2.0)

    def Interact(self, other):
        return Entity.ENTER

    
class DisabledRespawnPoint(RespawnPoint):
    """A disabled respawning point needs to be touched
    once by the player in order to serve as respawn
    point candidate."""

    def __init__(self):
        RespawnPoint.__init__(self,"respawn_stub.png")
        self.didit = True 

    def Interact(self, other):
        if isinstance(other,Player):
            other._AddOrderedRespawnPoint(self.pos)
                
        return Entity.ENTER



class KillAnimStub(Tile):
    """Implements the text strings that are spawned whenever
    the player is killed."""

    def __init__(self, text, index=None):
        Tile.__init__(self, random.choice(text.split("\n\n")) if random.random() > 0.95 else "",
            draworder=11000,
            rsize=random.randint(9,16),
            dropshadow=True,
            permute=False)

        self.ttl = 0
        
        self.dirvec = [1.0,1.0]
        self.SetColor(sf.Color(random.randint(100,150),0,0,255))
        
    def SetGame(self,game):
        if self.game is game:
            return
            
        Tile.SetGame(self,game)
        self.game.useless_sprites += 1
        
    def _GetHaloImage(self):
        return Entity._GetHaloImage(self,random.choice(
            ("halo_blood.png","halo_blood2.png","halo_blood3.png","halo_blood4.png","halo_blood5.png")
        ))
        
    def SetDirection(self,dirvec):
        if dirvec[0]==0 and dirvec[1]==0:
            return   
        self.dirvec = list( mathutil.Normalize(dirvec) )
        
    def SetSpeed(self,speed):
        self.speed = speed*3
        
    def SetTTL(self,ttl):
        self.ttl = ttl/2

    def GetBoundingBox(self):
        return None
    
    def GetBoundingBoxAbs(self):
        return None
    
    def RandomizeSplatter(self):
        """Setup random direction, speed and ttl"""
        self.SetSpeed(random.uniform(-1.0, 1.0))
        self.SetDirection((random.uniform(-1.0, 1.0),random.uniform(-1.0, 1.0)))
        
        self.SetTTL(random.random()*10.0)

    def Update(self, time_elapsed, time_delta):
        self.SetPosition((self.pos[0] + self.dirvec[0] * time_delta * self.speed, 
            self.pos[1] + self.dirvec[1] * time_delta * self.speed))
        
        self.dirvec[0] = self.dirvec[0] * pow(0.65,time_delta)
        self.dirvec[1] = self.dirvec[1] * pow(0.65,time_delta)

        if not hasattr(self, "time_start"):
            self.time_start = time_elapsed
            return

        ox,oy = self.level.GetOrigin()
        if time_elapsed - self.time_start > self.ttl or not (ox <= self.pos[0] <= ox+defaults.tiles[0]):
            self.game.RemoveEntity(self)
            self.game.useless_sprites -= 1
        
    def Draw(self):
        Tile.Draw(self)


class InventoryChangeAnimStub(Tile):
    """Implements the text string that is spawned whenever
    the player adds or removes an item from the inventory."""
    
    # XXX code just duplicated from ScoreAnimStub ...

    def __init__(self,text,pos,speed=1.0,color=sf.Color.Green,rsize=None,border=True):
        
        self.border = border
        if border:
            text = text.split('\n')
            maxlen = max(len(n) for n in text) + 4
            text = '\n'.join(['-' * maxlen] + ['[ ' + n.ljust(maxlen-4) + ' ]' for n in text] + ['-' * maxlen])
        
        Tile.__init__(self,text,draworder=11002,rsize=rsize,permute=False)
        
        self.SetPosition( pos )
        self.speed = speed
        self.SetColor(color)

    def GetBoundingBox(self):
        return None
    
    def GetBoundingBoxAbs(self):
        return None

    def Update(self,time_elapsed,time_delta):
        self.SetPosition((self.pos[0],self.pos[1]+time_delta*self.speed))

        if self.pos[1] > defaults.tiles[1]:
            self.game.RemoveEntity(self) 
        

    def _GetHaloImage(self):
        return Tile._GetHaloImage(self) if self.border else None
        
class DropProtection(EntityWithEditorImage):
    """Special, invisible entity to reset the player's
    respawn protection to zero, if any."""
    
    def __init__(self,editor_stub="noprotect_stub.png"):
        EntityWithEditorImage.__init__(self,editor_stub)

    def GetBoundingBox(self):
        return (self.pos[0], self.pos[1], 1.0, 1.0)

    def Interact(self, other):
        if isinstance(other,Player):
            other.DropProtection()
        return Entity.ENTER
        

        
import level    
level.Player = Player        
        

# vim: ai ts=4 sts=4 et sw=4
