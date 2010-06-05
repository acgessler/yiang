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

class Player(Entity):
    """Special entity which responds to user input and moves the
    player tiles accordingly. This entity is unique within a
    single game. """

    ANIM_RIGHT,ANIM_JUMP_RIGHT,ANIM_LEFT,ANIM_JUMP_LEFT = range(4)
    MAX_ANIMS = 4

    def __init__(self,text,game,width,height,ofsx):
        Entity.__init__(self)
        self.game = game
        self.vel = [0,0]
        self.acc = [0,-defaults.gravity]
        self.in_jump, self.block_jump = False,False
        self.cur_tile = [Player.ANIM_RIGHT]

        self.pwidth = width / defaults.tiles_size[0]
        self.pheight = height / defaults.tiles_size[1]
        self.pofsx = ofsx / defaults.tiles_size[0]

        lines = text.split("\n")
        height = len(lines)//Player.MAX_ANIMS

        self.tiles = []
        for i in range(0,(len(lines)//height)*height,height):
            self.tiles.append(Tile("\n".join(lines[i:i+height])))
            self.tiles[-1].SetPosition((0,0))

        assert len(self.tiles) == Player.MAX_ANIMS

    def SetPosition(self,pos):
        self.pos = pos
        #for tile in self.tiles:
        #    tile._Recache()

        # keep the original position, for we need it to implement respawning
        if not hasattr(self,"respawn_positions"):
            self.respawn_positions = []
            self._AddRespawnPoint(pos)

    def SetColor(self,pos):
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

        if inp.IsKeyDown(sf.Key.Left):
            self.vel[0] = -defaults.move_speed[0]
            self.cur_tile[0] = Player.ANIM_LEFT

            self._SetJumpAnimState()
            
        if inp.IsKeyDown(sf.Key.Right):
            self.vel[0] = defaults.move_speed[0]
            self.cur_tile[0] = Player.ANIM_RIGHT

            self._SetJumpAnimState()

        if defaults.debug_updown_move is True:
            if inp.IsKeyDown(sf.Key.Up):
                self.pos[1] -= time*defaults.move_speed[1]
            if inp.IsKeyDown(sf.Key.Down):
                self.pos[1] += time*defaults.move_speed[1]
        else:
            if inp.IsKeyDown(sf.Key.Up):
                if self.in_jump is False and self.block_jump is False:
                    self.vel[1] -= defaults.jump_vel
                    self.in_jump = self.block_jump = True

                    self.cur_tile.append(0)
                    self._SetJumpAnimState()
            else:
                self.block_jump = False
        
            #else:
            #    self.can_jump = True

        #if inp.IsKeyDown(sf.Key.):
            
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

        self.vel[0] = 0
        self._UpdatePostFX(game)

    def _UpdatePostFX(self,game):
        game.effect.SetParameter("cur",
            self.pos[0]/defaults.tiles[0],
            1.0-self.pos[1]/defaults.tiles[1])

    def _Kill(self,game):
        """Internal stub to kill the player and to fire some nice
        animations to celebrate the event"""
        for i in range(30):
            game.AddEntity(KillAnimStub(self.pos,random.uniform(-1.0,1.0),\
                (random.random(),random.random())))
            
        game.Kill()

    def _HandleCollisions(self,newpos,newvel,game):
        """Handle any collision events, given the computed new position
        of the player. The funtion returns the actual position after
        collision handling has been performed."""
        game.AddToActiveBBs(self)

        # brute force collision detection for dummies .. actually I am not proud of it :-)
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


        print("Active colliders: {0}".format(cnt))
        return newpos,newvel
            
    def Draw(self,game):
        self.tiles[self.cur_tile[-1]].DrawRelative(self.game,self.pos)

    def GetBoundingBox(self):
        return (self.pos[0]+self.pofsx, self.pos[1],self.pwidth,self.pheight)

    def _AddRespawnPoint(self,pos):
        """Add a possible respawn position to the player entity."""
        assert hasattr(self,"respawn_positions")
        self.respawn_positions.append(pos)
        print("Set respawn point {0}|{1}".format(pos[0],pos[1]))

    def Respawn(self):
        """Used internally by Game.Respawn to respawn the player
        at a given position"""
        assert hasattr(self,"respawn_positions")
        assert len(self.respawn_positions)

        min_distance = float(defaults.min_respawn_distance)
        for rpos in reversed(self.respawn_positions):
            if math.sqrt((rpos[0]-self.pos[0])*(rpos[0]-self.pos[0])+\
                (rpos[1]-self.pos[1])*(rpos[1]-self.pos[1])) < min_distance:
                continue
            
            self.SetPosition(rpos)
        else:
            self.SetPosition(self.respawn_positions[0])
        print("Respawn at {0}|{1}".format(self.pos[0],self.pos[1]))

class RespawnPoint(Entity):
    """A respawning point represents a possible position where
    the player can respawn if he or she dies"""


    def Update(self,time_elapsed,time,game):
        if hasattr(self,"didit"):
            return

        for entity in game._EnumEntities():
            if hasattr(entity,"_AddRespawnPoint"):
                entity.AddRespawnPoint(self.pos)


class KillAnimStub(Tile):
    """Implements the text string that is spawned whenever
    the player is killed."""

    def __init__(self,pos,speed,dirvec,text="(KILLED)"):
        Tile.__init__(self,text)

        self.opos = pos
        self.SetPosition( pos )
        self.speed = speed
        
        self.dirvec = mathutil.Normalize( dirvec )
        self.SetColor(sf.Color.Red)

    def GetBoundingBox(self):
        return None

    def Update(self,time_elapsed,time_delta,game):
        self.SetPosition((self.pos[0]+self.dirvec[0]*time_delta*self.speed,self.pos[1]+self.dirvec[1]*time_delta*self.speed))

    def Draw(self,game):
        Tile.Draw(self,game)

        # XXX wrong coordinate system
        # color = sf.Color.Red
        # shape = sf.Shape.Line(self.pos[0] - self.dirvec[0]*3,\
        #    self.pos[1] - self.dirvec[1]*3,self.opos[0],self.opos[1],1,color)
        # game.Draw(shape)


        
        
        
        
