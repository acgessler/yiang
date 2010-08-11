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
import math
import os

# PySFML
import sf

# My own stuff
import defaults
from game import Entity, Game, EntityWithEditorImage
from tile import Tile, AnimTile
from weapon import Shot
from score import ScoreTileAnimStub
from player import KillAnimStub,Player

class Enemy(AnimTile):
    """Sentinel base class for all entities"""
    
    firstnames,lastnames=None,None

    def GetVerboseName(self):
        return "an unknown enemy"
    
    def GetDrawOrder(self):
        return 2000
    
    def _Die(self):
        """Invoked when the enemy is slayed"""
        print("Kill entity: {0}".format(self.__class__.__name__))
        self.game.RemoveEntity(self)
        self.game.AddEntity(ScoreTileAnimStub("{1} {0:4.4} ct".
            format(self.game.Award(self._GetScoreAmount()),
                self._GetRandomName()),self.pos,1.0
            )
        )
        self._SpreadSplatter()
        
        self.level.CountStats("s_kills",1)
        
    def _GetRandomName(self):
        Enemy.firstnames = Enemy.firstnames or [ e.strip() for e in open(
            os.path.join(defaults.data_dir,"messages","firstnames.txt"),
            "rt").readlines() ]
            
        Enemy.lastnames = Enemy.lastnames or [ e.strip() for e in open(
            os.path.join(defaults.data_dir,"messages","lastnames.txt"),
            "rt").readlines() ]
            
        return "{0} {1}".format( random.choice(Enemy.firstnames),
            random.choice(Enemy.lastnames)
        )
        
    def _GetScoreAmount(self):
        """Get the score the player receives for slaying this enemy"""
        return -0.05
        
    def _SpreadSplatter(self):
        name = "splatter1.txt"
        remaining = max(0 if self.game.GetFrameRateUnsmoothed() <= defaults.max_framerate_for_sprites else
            defaults.max_useless_sprites - self.game.useless_sprites , 
            defaults.min_death_sprites
        )
        for i in range(min(remaining, defaults.death_sprites)):
            from tile import TileLoader
                
            t = TileLoader.Load(os.path.join(defaults.data_dir,"tiles_misc",name),self.game)
            t.RandomizeSplatter()
            t.SetPosition(self.pos)
            
            self.game.AddEntity(t)
    
    def Interact(self, other):
        """The default behaviour for enemies is to be killable by a shot with any gun.
        Also, enemies usually don't kill each other """
        if isinstance(other,Enemy):
            return Entity.BLOCK
        
        if isinstance(other,Shot):
            self._Die()
            
        return Entity.KILL
    

class SmallTraverser(Enemy):
    """The simplest class of entities, it moves in a certain
    range and kills the player immediately. The class supports
    both horizontal and vertical moves."""

    def __init__(self, text, height, frames, speed=1.0, move_speed=3, randomdir=True, direction=Entity.DIR_HOR, verbose="a Harmful Traverser Unit (HTU)",shrinkbb=0.65):
        AnimTile.__init__(self, text, height, frames, speed, 2)

        self.verbose = verbose
        self.vel = (move_speed * random.choice((-1, 1))) if randomdir is True else 1
        self.direction = direction

        self._ShrinkBB(shrinkbb)

    def GetVerboseName(self):
        return self.verbose
    
    def GetDrawOrder(self):
        return 2100
    
    def _GetScoreAmount(self):
        return -0.05

    def Update(self, time_elapsed, time):
        AnimTile.Update(self, time_elapsed, time)
        if not self.game.IsGameRunning():
            return 
            
        ab = self.GetBoundingBoxAbs()
            
        # left, top, right, bottom
        intersect = [[1e5,0.0],[1e5,0.0],[-1e5,0.0],[-1e5,0.0]]
        colliders = []
        fric = 1e10
        for collider in self.game.GetLevel().EnumPossibleColliders(ab):
            if collider is self:
                continue
            
            if isinstance(collider,Enemy):
                continue
            
            cd = collider.GetBoundingBoxAbs()
            if cd is None:
                continue
             
            if self.direction == Entity.DIR_HOR:
                # is our left border intersecting?
                if self._HitsMyLeft(ab,cd):                      
                    res = collider.Interact(self)
                    if res == Entity.BLOCK:
                        self.vel = abs(self.vel)
                        break
                    elif res == Entity.KILL:
                        self._Die()
                    
                # is our right border intersecting?
                elif self._HitsMyRight(ab,cd):                      
                    res = collider.Interact(self)
                    if res == Entity.BLOCK:
                        self.vel = -abs(self.vel)
                        break
                    elif res == Entity.KILL:
                        self._Die()
            else:
                 if self._HitsMyBottom(ab,cd):
                    res = collider.Interact(self)
                    if res == Entity.BLOCK:
                        self.vel = -abs(self.vel)
                        break
                    elif res == Entity.KILL:
                        self._Die()
                                               
                 # is our top border intersecting?
                 elif self._HitsMyTop(ab,cd):
                    res = collider.Interact(self)
                    if res == Entity.BLOCK:
                       self.vel = abs(self.vel)
                       break   
                    elif res == Entity.KILL:
                       self._Die()     

        lx,ly = self.level.GetLevelSize()
        if self.direction == Entity.DIR_HOR:
            pos = (self.pos[0] + self.vel * time, self.pos[1])
            if pos[0] < 0 or pos[0] > lx:
                self._Return()
        else:
            pos = (self.pos[0], self.pos[1] + self.vel * time)
            if pos[1] < 0 or pos[1] > ly:
                self._Return()
                
        self.SetPosition(pos)
        self.SetState(1 if self.vel > 0 else 0)
        
    def _Return(self):
        self.vel = -self.vel
        # XXX the sound effect seems to shoort for SFMl to handle it.
        #from audio import SoundEffectCache
        #SoundEffectCache.Get("click8a.wav").Play()
        
        
class SmallTraverserBlocker(EntityWithEditorImage):
    """An invisible tile with a single purpose: block
    only SmallTraverser's, but not the player or 
    somebody else. """
    
    def __init__(self,file="stblock_stub.png"):
        EntityWithEditorImage.__init__(self,file)
        self.dim = (1,1)
        
    def Interact(self,other):
        return Entity.BLOCK if isinstance(other, SmallTraverser) else Entity.ENTER
    
    def GetBoundingBox(self):
        return (self.pos[0],self.pos[1],self.dim[0],self.dim[1])
        
        
class NaughtyPongPong(Enemy):
    """Jumps to a certain height, then falls down, and halts
    a few moments. Can be killed only by Mario-style (
    jump on its top ..)"""

    def __init__(self, text, height, frames, speed=1.0, move_speed=3, randomdir=True, verbose="a Naughty Pong Pong (NPP)",shrinkbb=0.65):
        AnimTile.__init__(self, text, height, frames, speed, 2)

        self.verbose = verbose
        #self.vel = (move_speed * random.choice((-1, 1))) if randomdir is True else 1
        self.vel = -defaults.jump_vel

        self._ShrinkBB(shrinkbb)

    def GetVerboseName(self):
        return self.verbose
    
    def GetDrawOrder(self):
        return 2100
    
    def _GetScoreAmount(self):
        return -0.01

    def Update(self, time_elapsed, time):
        AnimTile.Update(self, time_elapsed, time)
        if not self.game.IsGameRunning():
            return 
        
        if hasattr(self,"relaunch_time"):
            if self.relaunch_time.GetElapsedTime() > 0.5:
                self.vel = -defaults.jump_vel
                delattr(self,"relaunch_time")
            return
        
        self.acc = self.level.gravity*10
        vec = (self.vel + self.acc * time) * time

        self.pos[1] += vec
        
        # check for possible colliders on the bottom to determine when we
        # are touching the ground
        
        ab = self.GetBoundingBoxAbs()  
        for collider in self.game.GetLevel().EnumPossibleColliders(ab):
            if collider is self:
                continue
            
            cd = collider.GetBoundingBoxAbs()
            if cd is None:
                continue
            
            # lower border    
            if self._HitsMyBottom(ab, cd):
                self.vel = min(0,self.vel)
                collider.AddToActiveBBs()     
                
                self.relaunch_time = sf.Clock()    
                break
                    
            # top border
            if self._HitsMyTop(ab, cd):
                self.vel = max(0,self.vel)
                break
                
    def Interact(self, other):
        if isinstance(other,Player):
            ab = self.GetBoundingBoxAbs()
            cd = other.GetBoundingBoxAbs()    
            
            if self._HitsMyTop(ab,cd) or self._HitsMyBottom(cd,ab):
                self._Die()
                return Entity.ENTER
            
        return Entity.KILL
    
        
class RotatingInferno(Enemy):
    """The RotatingInfero class of entities is simply an animated
    tile which rotates around its center in a certain distance."""
    def __init__(self, text, height, frames, speed=1.0, rotate_speed_base = 0.2, radius = 3.5):
        AnimTile.__init__(self, text, height, frames, speed, 1, halo_img="halo_rotating_inferno.png")
        
        self.rotate_speed_base = rotate_speed_base
        self.ofs_vec = [radius,0]
        
    def Interact(self, other):
        return Entity.KILL
    
    def GetVerboseName(self):
        return "Rotating Inferno"
    
    def SetPosition(self,pos):
        self.real_pos = (pos[0]+self.ofs_vec[0],pos[1]+self.ofs_vec[1])
        Enemy.SetPosition(self,pos)
    
    def Update(self, time_elapsed, time):
        Enemy.Update(self,time_elapsed, time)
        if not self.game.IsGameRunning():
            return 
        
        angle = (math.pi*2.0*time) * self.rotate_speed_base
        a,b = math.cos(angle), math.sin(angle)
        
        self.ofs_vec = [self.ofs_vec[0]*a-self.ofs_vec[1]*b,self.ofs_vec[0]*b+self.ofs_vec[1]*a]
        self.SetPosition(self.pos)
        
    def GetBoundingBox_EditorCatalogue(self): # Special logic for use within the editor
        return (self.pos[0],self.pos[1],self.dim[0],self.dim[1])
        
    def GetBoundingBox(self):
        return (self.real_pos[0],self.real_pos[1],self.dim[0],self.dim[1])
    
    def Draw_EditorCatalogue(self): # Special logic for use within the editor
        lv = self.game.GetLevel()
        for offsetit, elem in self.cached: 
            lv.DrawSingle(elem,self.pos)
            
    def Draw(self): 
        lv = self.game.GetLevel()
        for offsetit, elem in self.cached: 
            lv.DrawSingle(elem,self.real_pos)

        
        
class SmallBob(Enemy):
    """This guy is not actually friendly, but he's much less a danger
    as his older (and bigger) brothers are. He does not shoot, for
    example."""
    def __init__(self, text, height, frames, speed=1.0, move_speed_base = 2.0, shrinkbb=0.8):
        AnimTile.__init__(self, text, height, frames, speed, 2)
        self._ShrinkBB(shrinkbb)
        self.hits = 4

    def GetVerboseName(self):
        return "Small Bob"
    
    def GetDrawOrder(self):
        return 2100
    
    def _GetScoreAmount(self):
        return -0.08
    
    def Interact(self, other):
        """SmallBob needs 4 hits to die"""
        if isinstance(other,Shot):
            self.hits -= 1
            if self.hits == 0:
                self._Die()
            
        return Entity.KILL

    def Update(self, time_elapsed, time):
        if not self.game.IsGameRunning():
            return 
            
        rect = self.GetBoundingBox()
        res = 0
            
        AnimTile.Update(self, time_elapsed, time)
        self.SetState(0)
        
            
class Robot(SmallTraverser):
    pass








