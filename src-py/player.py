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

# PySFML
import sf

# My own stuff
import defaults
import mathutil
from game import Entity,TileLoader,Game,Tile
from keys import KeyMapping

class Player(Entity):
    """Special entity which responds to user input and moves the
    player tiles accordingly. This entity is unique within a
    single game. """

    ANIM_RIGHT,ANIM_JUMP_RIGHT,ANIM_LEFT,ANIM_JUMP_LEFT = range(4)
    MAX_ANIMS = 4

    def __init__(self,text,game,width,height,ofsx):
        Entity.__init__(self)
        self.game = game

        self.pwidth = width / defaults.tiles_size[0]
        self.pheight = height / defaults.tiles_size[1]
        self.pofsx = ofsx / defaults.tiles_size[0]

        lines = text.split("\n")
        height = len(lines)//Player.MAX_ANIMS

        self._Reset()

        self.tiles = []
        for i in range(0,(len(lines)//height)*height,height):
            self.tiles.append(Tile("\n".join(lines[i:i+height])))
            self.tiles[-1].SetPosition((0,0))

        assert len(self.tiles) == Player.MAX_ANIMS

    def _Reset(self):
        """Reset the state of the player instance, this is needed
        for proper respawning"""
        self.vel = [0,0]
        self.acc = [0,-defaults.gravity]
        self.in_jump, self.block_jump, self.moved_once = True,False,False
        self.cur_tile = [Player.ANIM_RIGHT]

    def SetPosition(self,pos):
        self.pos = list(pos)
        #for tile in self.tiles:
        #    tile._Recache()

        # keep the original position, for we need it to implement respawning
        if not hasattr(self,"respawn_positions"):
            self.respawn_positions = []
            self._AddRespawnPoint(pos)

    def SetColor(self,pos):
        self.color = pos
        for tile in self.tiles:
            tile.SetColor(pos)

    def _SetJumpAnimState(self):
        if len(self.cur_tile)<=1:
            return
        
        self.cur_tile[-1] = (Player.ANIM_JUMP_LEFT if \
            self.cur_tile[-2] == Player.ANIM_LEFT else Player.ANIM_JUMP_RIGHT)

    def Update(self,time_elapsed,time,game):
        inp = self.game.GetApp().GetInput()
        vec = [0,0]

        pvely = self.vel[1]

        if inp.IsKeyDown(KeyMapping.Get("move-left")):
            self.vel[0] = -defaults.move_speed[0]
            self.cur_tile[0] = Player.ANIM_LEFT

            self._SetJumpAnimState()
            self.moved_once = True
            
        if inp.IsKeyDown(KeyMapping.Get("move-right")):
            self.vel[0] = defaults.move_speed[0]
            self.cur_tile[0] = Player.ANIM_RIGHT

            self._SetJumpAnimState()
            self.moved_once = True

        if defaults.debug_updown_move is True:
            if inp.IsKeyDown(KeyMapping.Get("move-up")):
                self.pos[1] -= time*defaults.move_speed[1]
                self.moved_once = True
            if inp.IsKeyDown(KeyMapping.Get("move-down")):
                self.pos[1] += time*defaults.move_speed[1]
                self.moved_once = True
        else:
            if inp.IsKeyDown(sf.Key.Up):
                if self.in_jump is False and self.block_jump is False:
                    self.vel[1] -= defaults.jump_vel
                    self.in_jump = self.block_jump = True

                    self.cur_tile.append(0)
                    self._SetJumpAnimState()

                self.moved_once = True
            else:
                self.block_jump = False
        
            
        newvel = [self.vel[0] + self.acc[0]*time,self.vel[1] + (self.acc[1]
            +(defaults.gravity if defaults.debug_updown_move is True else 0))*time]

        vec[0] += newvel[0]*time
        vec[1] += newvel[1]*time

        newpos = [self.pos[0] + vec[0], self.pos[1] + vec[1]]

        # Check for collisions
        self.pos,self.vel = self._HandleCollisions(newpos,newvel,game)

        # (HACK) -- for debugging, prevent the player from falling below the map
        if defaults.debug_prevent_fall_down is True and self.pos[1]<1:
            self.pos[1] = 1
            self.in_jump, self.block_jump = False,False
            self.vel[1] = 0
            
        elif self.pos[1] < 1.0 or self.pos[1] > defaults.tiles[1]:
            self._Kill(game)

        self._CheckForLeftMapBorder(game)
        self._MoveMap(game,time)
        self._CheckForRightMapBorder(game)

        self.vel[0] = 0
        self._UpdatePostFX(game)

    def _CheckForLeftMapBorder(self,game):
        """Check if we passed the left border of the game, which is
        generally a bad idea. """

        origin = game.GetOrigin()
        if defaults.debug_godmode is True or defaults.debug_scroll_both is True:
            # GODMODE: scroll to the left as usual
            rmax = float(defaults.right_scroll_distance)
            if self.pos[0] < origin[0]+defaults.tiles[0]+rmax:
                game.SetOrigin((self.pos[0]-rmax,origin[1]))
                return
        
        if self.pos[0] < origin[0]:
            if self.pos[0]+self.pwidth > origin[0]:

                self.restore_color = self.color
                self.SetColor(sf.Color.Yellow)
                print("Entering left danger area")
            else:
                self._Kill(game)

        else:
            if hasattr(self,"restore_color"):
                if not self.color is self.restore_color:

                    print("Leaving left danger area, restoring old state")
                    self.SetColor(self.restore_color)
                else:
                    print("Can't restore old color, seemingly the player color "+\
                          "changed while the entity resided in the left danger area")
                delattr(self,"restore_color")

    def _CheckForRightMapBorder(self,game):
        """Check if we approached the right border of the game, which
        forces the map to scroll immediately"""
        origin = game.GetOrigin()
        rmax = float(defaults.right_scroll_distance)
        if self.pos[0] > origin[0]+defaults.tiles[0]-rmax:
            game.SetOrigin((self.pos[0]-defaults.tiles[0]+rmax,origin[1]))

    def _MoveMap(self,game,dtime):
        """Move the map view origin according to a time function"""
        if self.moved_once is False:
            return
            
        origin = game.GetOrigin()
        game.SetOrigin((origin[0]+dtime*defaults.move_map_speed,origin[1]))

    def _UpdatePostFX(self,game):
        origin = game.GetOrigin()

        # XXX Use Game's coordinate sustem conversion utilities
        game.effect.SetParameter("cur",
            (self.pos[0]+self.pwidth//2-origin[0])/defaults.tiles[0],
            1.0-(self.pos[1]+self.pheight//2-origin[1])/defaults.tiles[1])

    def _Kill(self,game):
        """Internal stub to kill the player and to fire some nice
        animations to celebrate the event"""
        if game.GetLives() > 0:
            for i in range(30):
                game.AddEntity(KillAnimStub(self.pos,random.uniform(-1.0,1.0),\
                    (random.random(),random.random()),random.random()*12.0))
            
        game.Kill()

    def _HandleCollisions(self,newpos,newvel,game):
        """Handle any collision events, given the computed new position
        of the player. The funtion returns the actual position after
        collision handling has been performed."""
        game.AddToActiveBBs(self)

        # brute force collision detection for dummies .. actually I am not proud of it :-)
        # XXX rewrite this, do proper intersection between the movement vector and the
        # bb borders.
        cnt,hasall = 0,0
        for collider in game._EnumEntities():
            if collider is self:
                continue
            
            mycorner = collider.GetBoundingBox()
            if mycorner is None:
                continue

            mycorner = (mycorner[0],mycorner[1],mycorner[2]+mycorner[0],mycorner[3]+mycorner[1])
            rect = (newpos[0]+self.pofsx, newpos[1],newpos[0]+self.pofsx+self.pwidth,newpos[1]+self.pheight)
                            
            hasall = self._BBCollide(mycorner,rect)
            if hasall == 0:
                continue

            cnt += 1
            game.AddToActiveBBs(collider)

            res = collider.Interact(self,game)
            if res == Entity.KILL:
                print("hit deadly entity, need to commit suicide")
                if defaults.debug_godmode is False:
                    self._Kill(game)

            elif res != Entity.BLOCK:
                continue

            # collision with ceiling
            if hasall & (Entity.LOWER_LEFT|Entity.LOWER_RIGHT) and hasall & (Entity.UPPER_LEFT|Entity.UPPER_RIGHT) == 0:
                newpos[1] = mycorner[3]
                newvel[1] = max(0,newvel[1])
                #print("ceiling")

                cnt += 1
                game.AddToActiveBBs(collider)

            # collision with floor
            elif hasall & (Entity.UPPER_LEFT|Entity.UPPER_RIGHT) and hasall & (Entity.LOWER_LEFT|Entity.LOWER_RIGHT) == 0:
                newpos[1] = mycorner[1]-self.pheight
                newvel[1] = min(0,newvel[1])

                #print("floor")

                if len(self.cur_tile)>1:
                    del self.cur_tile[-1]

                self.in_jump = False

                cnt += 1
                game.AddToActiveBBs(collider)

            
        for collider in game._EnumEntities():
            if collider is self:
                continue
            
            mycorner = collider.GetBoundingBox()
            if mycorner is None:
                continue

            mycorner = (mycorner[0],mycorner[1],mycorner[2]+mycorner[0],mycorner[3]+mycorner[1])
            rect = (newpos[0]+self.pofsx, newpos[1],newpos[0]+self.pofsx+self.pwidth,newpos[1]+self.pheight)
                            
            hasall = self._BBCollide(mycorner,rect)
            if hasall == 0:
                continue

            res = collider.Interact(self,game)
            if res != Entity.BLOCK:
                continue

            # collision on the left
            if hasall & (Entity.LOWER_RIGHT|Entity.UPPER_RIGHT) and hasall & (Entity.LOWER_LEFT|Entity.LOWER_RIGHT) == 0:
                newpos[0] = mycorner[2]
                newvel[0] = max(0,newvel[0])
                #print("left")

                cnt += 1
                game.AddToActiveBBs(collider)

            # collision on the right
            elif hasall & (Entity.LOWER_LEFT|Entity.UPPER_LEFT) and hasall & (Entity.LOWER_RIGHT|Entity.UPPER_RIGHT) == 0:
                newpos[0] = mycorner[0]-self.pwidth-self.pofsx
                newvel[0] = min(0,newvel[0])
                #print("right")

                cnt += 1
                game.AddToActiveBBs(collider)


        #print("Active colliders: {0}".format(cnt))
        return newpos,newvel
            
    def Draw(self,game):
        self.tiles[self.cur_tile[-1]].DrawRelative(self.game,self.pos)

    def GetBoundingBox(self):
        # Adjust the size of the bb slightly to increase the likelihood
        # to pass tight tunnels.
        pcb = (defaults.player_caution_border[0]/defaults.tiles_size_px[0],\
            defaults.player_caution_border[1]/defaults.tiles_size_px[1])

        return (self.pos[0]+self.pofsx+pcb[0]/2, self.pos[1]+pcb[1],\
            self.pwidth-pcb[0],self.pheight-pcb[1])

    def _AddRespawnPoint(self,pos):
        """Add a possible respawn position to the player entity."""
        assert hasattr(self,"respawn_positions")
        self.respawn_positions.append(pos)
        print("Set respawn point {0}|{1}".format(pos[0],pos[1]))

    def Respawn(self,game):
        """Used internally by Game.Respawn to respawn the player
        at a given position"""
        assert hasattr(self,"respawn_positions")
        assert len(self.respawn_positions)

        min_distance = float(defaults.min_respawn_distance)
        for rpos in reversed(self.respawn_positions):
            if rpos[0]>self.pos[0] or mathutil.Length((rpos[0]-self.pos[0],rpos[1]-self.pos[1])) < min_distance:
                continue # this is to protect the player from being
                # respawned in kill zones.
            
            self.SetPosition(rpos)
            break
            
        else:
            self.SetPosition(self.respawn_positions[0])
        print("Respawn at {0}|{1}".format(self.pos[0],self.pos[1]))
        # Adjust the game origin accordingly
        game.SetOrigin((self.pos[0]-defaults.respawn_origin_distance,0))

        # Reset our status
        self._Reset()

class RespawnPoint(Entity):
    """A respawning point represents a possible position where
    the player can respawn if he or she dies"""


    def Update(self,time_elapsed,time,game):
        if hasattr(self,"didit"):
            return

        for entity in game._EnumEntities():
            if hasattr(entity,"_AddRespawnPoint"):
                entity._AddRespawnPoint(self.pos)
                
        self.didit = True        

class KillAnimStub(Tile):
    """Implements the text string that is spawned whenever
    the player is killed."""

    def __init__(self,pos,speed,dirvec,ttl,text="YOU DIED HERE"):
        Tile.__init__(self,text)

        self.opos = pos
        self.SetPosition( pos )
        self.speed = speed
        self.ttl = ttl
        
        self.dirvec = mathutil.Normalize( dirvec )
        self.SetColor(sf.Color.Red)

    def GetBoundingBox(self):
        return None

    def Update(self,time_elapsed,time_delta,game):
        self.SetPosition((self.pos[0]+self.dirvec[0]*time_delta*self.speed,self.pos[1]+self.dirvec[1]*time_delta*self.speed))

        if not hasattr(self,"time_start"):
            self.time_start = time_elapsed
            return

        if time_elapsed - self.time_start > self.ttl:
            game.RemoveEntity(self) 
        
    def Draw(self,game):
        Tile.Draw(self,game)

        # could use Rotate(), Scale() as well
        start = game.ToDeviceCoordinates(game.ToCameraCoordinates((
            self.pos[0]-(self.pos[0]-self.opos[0])*0.25+0.8,self.pos[1]-(self.pos[1]-self.opos[1])*0.25)))
        end = game.ToDeviceCoordinates(game.ToCameraCoordinates(
            (self.opos[0],self.opos[1])))
        
        shape = sf.Shape.Line(start[0],start[1],end[0],end[1],1,sf.Color.Red)
        game.Draw(shape)


        
        
        
        
