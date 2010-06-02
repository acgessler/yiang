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
        self.can_jump = True
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

    def SetColor(self,pos):
        for tile in self.tiles:
            tile.SetColor(pos)

    def Update(self,time_elapsed,time,game):
        inp = self.game.GetApp().GetInput()
        vec = [0,0]

        pvely = self.vel[1]

        if inp.IsKeyDown(sf.Key.Left):
            self.vel[0] = -defaults.move_speed[0]
            self.cur_tile[0] = Player.ANIM_LEFT
            
        if inp.IsKeyDown(sf.Key.Right):
            self.vel[0] = defaults.move_speed[0]
            self.cur_tile[0] = Player.ANIM_RIGHT

        if defaults.cheat_allow_updown_move is True:
            if inp.IsKeyDown(sf.Key.Up):
                self.pos[1] += time*defaults.move_speed[1]
            if inp.IsKeyDown(sf.Key.Down):
                self.pos[1] -= time*defaults.move_speed[1]
        else:
            if inp.IsKeyDown(sf.Key.Up):
                if self.can_jump is True:
                    self.vel[1] += defaults.jump_vel
                    self.can_jump = False

                    self.cur_tile.append(Player.ANIM_JUMP_LEFT if \
                        self.cur_tile[-1] == Player.ANIM_LEFT else Player.ANIM_JUMP_RIGHT)
            #else:
            #    self.can_jump = True

        #if inp.IsKeyDown(sf.Key.):
            
        newvel = [self.vel[0] + self.acc[0]*time,self.vel[1] + self.acc[1]*time]
        vec[0] += newvel[0]*time
        vec[1] += newvel[1]*time

        if pvely > 0 and self.vel[1]<0:
            del self.cur_tile[-1] 
            
        newpos = [self.pos[0] + vec[0], self.pos[1] + vec[1]]

        # Check for collisions
        self.pos,self.vel = self._HandleCollisions(newpos,newvel,game)

        # (HACK) -- for debugging, prevent the player from falling below the map
        if False and defaults.debug_prevent_fall_down and self.pos[1]<1:
            self.pos[1] = 1
            self.can_jump = True
            self.vel[1] = 0

        self.vel[0] = 0
        self._UpdatePostFX(game)


    def _UpdatePostFX(self,game):
        game.effect.SetParameter("cur",
            self.pos[0]/defaults.tiles[0],
            self.pos[1]/defaults.tiles[1])

    def _HandleCollisions(self,newpos,newvel,game):
        """Handle any collision events, given the computed new position
        of the player. The funtion returns the actual position after
        collision handling has been performed."""

        rect = (newpos[0]+self.pofsx, newpos[1],self.pwidth,self.pheight)
        # brute force .. :-)
        
        for collider in game.GetEntities():
            mycorner = collider.GetBoundingBox()
            if mycorner is None:
                continue

            mycorner = (mycorner[0],mycorner[1],mycorner[2]+mycorner[0],mycorner[3]+mycorner[1])
            has = 0
             
            # upper left corner
            if mycorner[2]>rect[0]>=mycorner[0] and mycorner[3]>rect[1]>=mycorner[1]:
                has |= 1

            # upper right corner
            if mycorner[2]>rect[0]+rect[2]>=mycorner[0] and mycorner[3]>rect[1]>=mycorner[1]:
                has |= 2

            # lower left corner
            if mycorner[2]>rect[0]>=mycorner[0] and mycorner[3]>rect[1]+rect[3]>=mycorner[1]:
                has |= 4

            # lower right corner
            if mycorner[2]>rect[0]+rect[2]>=mycorner[0] and mycorner[3]>rect[1]+rect[3]>=mycorner[1]:
                has |= 8

            if has == 0:
                continue

            res = collider.Interact(self,game)
            if res == Entity.KILL:
                print("hit deadly entity, need to commit suicide")
                game.Kill()

            elif res != Entity.BLOCK:
                return newpos,newvel

            # collision with ceiling
            if has & (1|2):
                newpos[1] = mycorner[3]-self.pheight
                newvel[1] = min(0,newvel[1])
                #print("ceiling")

            # collision with floor
            if has & (4|8):
                newpos[1] = mycorner[1]
                newvel[1] = max(0,newvel[1])
                #print("floor")

            # collision on the left
            if has & (1|4):
                newpos[0] = mycorner[0]+self.pofsx
                newvel[0] = max(0,newvel[0])
                #print("left")

            # collision on the right
            if has & (2|8):
                newpos[0] = mycorner[2]-self.pwidth
                newvel[0] = min(0,newvel[0])
                #print("right")

            #print("*")
            break

        return newpos,newvel
            
    def Draw(self,game):
        self.tiles[self.cur_tile[-1]].DrawRelative(self.game,self.pos)

    def GetBoundingBox(self):
        return None   



