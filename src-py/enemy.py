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
from game import Entity, Game
from tile import Tile, AnimTile

class Enemy(AnimTile):
    """Sentinel base class for all entities"""

    def GetVerboseName(self):
        return "an unknown enemy"
    
    def GetDrawOrder(self):
        return 2000


class SmallTraverser(Enemy):
    """The simplest class of entities, it moves in a certain
    range and kills the player immediately. The class supports
    both horizontal and vertical moves."""

    def __init__(self, text, height, frames, speed=1.0, move_speed=3, randomdir=True, direction=Entity.DIR_HOR, verbose="a Harmful Traverser Unit (HTU)",shrinkbb=0.8):
        AnimTile.__init__(self, text, height, frames, speed, 2)

        self.verbose = verbose
        self.vel = (move_speed * random.choice((-1, 1))) if randomdir is True else 1
        self.direction = direction

        self._ShrinkBB(shrinkbb)

    def Interact(self, other):
        return Entity.KILL

    def GetVerboseName(self):
        return self.verbose
    
    def GetDrawOrder(self):
        return 2100

    def Update(self, time_elapsed, time):
        if not self.game.IsGameRunning():
            return 
            
        rect = self.GetBoundingBox()
        res = 0

        # check for collisions on both sides, turn around if we have one.
        for collider in self.game.GetLevel().EnumPossibleColliders(rect):
            # traverers of the same color collide with each other, others don't.
            if isinstance(collider, SmallTraverser) and not collider.color == self.color:
                continue
            
            mycorner = collider.GetBoundingBox()
            if mycorner is None:
                continue
            
            tj = self._BBCollide_XYWH(rect, mycorner)
            if tj > 0 and collider.Interact(self) != Entity.ENTER:
                collider.AddToActiveBBs()
                res |= tj

        if res > 0:
            self.AddToActiveBBs()
            if self.direction == Entity.DIR_HOR:
                x = self.game.GetLevelSize()[0]
                if self.vel < 0 and (self.pos[0] < 0 or res & (Entity.UPPER_LEFT | Entity.LOWER_LEFT) == (Entity.UPPER_LEFT | Entity.LOWER_LEFT)) or\
                   self.vel > 0 and (self.pos[0] > x or res & (Entity.UPPER_RIGHT | Entity.LOWER_RIGHT) == (Entity.UPPER_RIGHT | Entity.LOWER_RIGHT)):
                   
                    self._Return()
                
                
            elif self.direction == Entity.DIR_VER:
                y = self.game.GetLevelSize()[1]
                if self.vel < 0 and (self.pos[1] < 0 or res & (Entity.UPPER_LEFT | Entity.UPPER_RIGHT) == (Entity.UPPER_LEFT | Entity.UPPER_RIGHT)) or\
                   self.vel > 0 and (self.pos[1] > y or res & (Entity.LOWER_LEFT | Entity.LOWER_RIGHT) == (Entity.LOWER_LEFT | Entity.LOWER_RIGHT)):
                   
                    self._Return()
                
            else:
                assert False

        if self.direction == Entity.DIR_HOR:
            pos = (self.pos[0] + self.vel * time, self.pos[1])
        else:
            pos = (self.pos[0], self.pos[1] + self.vel * time)
        self.SetPosition(pos)
            
        AnimTile.Update(self, time_elapsed, time)
        self.SetState(1 if self.vel > 0 else 0)
        
    def _Return(self):
        self.vel = -self.vel
        # XXX the sound effect seems to shoort for SFMl to handle it.
        #from audio import SoundEffectCache
        #SoundEffectCache.Get("click8a.wav").Play()
        
        
class SmallBob(Enemy):
    """This guy is not actually friendly, but he's much less a danger
    as his older (and bigger) brothers are. He does not shoot, for
    example."""
    def __init__(self, text, height, frames, speed=1.0, move_speed_base = 2.0, shrinkbb=0.8):
        AnimTile.__init__(self, text, height, frames, speed, 2)
        self._ShrinkBB(shrinkbb)

    def Interact(self, other):
        return Entity.KILL

    def GetVerboseName(self):
        return "Small Bob"
    
    def GetDrawOrder(self):
        return 2100

    def Update(self, time_elapsed, time):
        if not self.game.IsGameRunning():
            return 
            
        rect = self.GetBoundingBox()
        res = 0
            
        AnimTile.Update(self, time_elapsed, time)
        self.SetState(0)
        
            
class Robot(SmallTraverser):
    pass








