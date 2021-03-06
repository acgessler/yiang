#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [enemy.py]
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

# Python Core
import random
import math
import os
import itertools

# PySFML
import sf

# My own stuff
from stubs import *
from weapon import Shot
from score import ScoreTileAnimStub
from player import KillAnimStub,Player
from sfutil import ColorLerp


class EnemyAnimStub(Tile):
    """Small light spark as leftovers from moving enemies"""

    def __init__(self,sparkhalo=1,statecount=3,ttl=2.5):
        self.sparkhalo = sparkhalo
        self.statecount = statecount
        self.sparkstate = random.randint(0,self.statecount-1)
        Tile.__init__(self, "")
        self.ttl = ttl
    
    def _GetHaloImage(self):
        return Entity._GetHaloImage(self,"enemydrop{0}_{1}.png".format(self.sparkhalo,self.sparkstate+1))  
    
    def GetBoundingBox(self):
        return None
    
    def GetBoundingBoxAbs(self):
        return None  

    def Update(self, time_elapsed, time_delta):
        Tile.Update(self,time_elapsed,time_delta)
        if not hasattr(self, "time_start"):
            self.time_start = time_elapsed
            return

        tdelta = time_elapsed - self.time_start
        if tdelta > self.ttl:
            self.game.RemoveEntity(self)
            return
        
        # fade out, but modulate a high-frequency pulse onto the alpha channel curve
        self.color = sf.Color(self.color.r,self.color.g,self.color.b,(0xff-int(tdelta*0xff/self.ttl)))
        
        
class DirectedEnemyAnimStub(EnemyAnimStub):
    """Directional light sparks from enemies"""

    def __init__(self,dir=[1.0,1.0],speed=10.0,sparkhalo=1,statecount=3,ttl=0.20):
        self.dir = dir
        self.speed = speed
        EnemyAnimStub.__init__(self, sparkhalo, statecount, ttl)
    

    def Update(self, time_elapsed, time_delta):
        EnemyAnimStub.Update(self,time_elapsed,time_delta)
        self.SetPosition((self.pos[0]+ self.dir[0] * self.speed * time_delta,
                         self.pos[1]+ self.dir[1] * self.speed * time_delta))
        
        

class Enemy(AnimTile):
    """Sentinel base class for all entities"""
    
    firstnames,lastnames=None,None
    
    def __init__(self,*args,dropshadow=True, dropshadow_blend_color=sf.Color(40,40,40,150),sparkhalo=1,spark_density=0.5,spark_ttl=2.5,no_flash=False, **kwargs):
        AnimTile.__init__(self,*args,dropshadow=dropshadow,**kwargs)
        self.sparkhalo = sparkhalo
        self.spark_density = spark_density
        self.spark_ttl = spark_ttl
        self.dropshadow_color = self.dropshadow_blend_color = dropshadow_blend_color
        self.no_flash = no_flash

    def GetVerboseName(self):
        return "an unknown enemy"
    
    def GetDrawOrder(self):
        return 2000

    def Kill(self):
        self._Die()
    
    def _Die(self):
        """Invoked when the enemy is slayed"""
        print("Kill entity: {0}".format(self.__class__.__name__))
        self.game.RemoveEntity(self)
        self.game.AddEntity(ScoreTileAnimStub(("{0}" if self.game.GetGameMode()==Game.BACKGROUND else "{0} {1:4.4} ct").
            format(self._GetRandomName(),self.game.Award(self._GetScoreAmount())),
                self.pos,1.0
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
        
    def _SpreadSplatter(self,scale=1.0):
        name = "splatter1.txt"
        remaining = max(0 if self.game.GetFrameRateUnsmoothed() <= defaults.max_framerate_for_sprites else
            defaults.max_useless_sprites - self.game.useless_sprites , 
            defaults.min_death_sprites
        )
        for i in range(min(remaining, int(defaults.death_sprites * scale))):
            from tileloader import TileLoader
                
            t = TileLoader.Load(os.path.join(defaults.data_dir,"tiles_misc",name),self.game)
            t.RandomizeSplatter()
            t.SetPosition(self.pos)
            
            self.game.AddEntity(t)
    
    def Interact(self, other):
        """The default behaviour for enemies is to be killable by a shot with any gun.
        Also, enemies usually don't kill each other """
        if isinstance(other,Shot):
            if other.color == self.color:
                self._Die()
                
        if isinstance(other,Enemy):
            return Entity.BLOCK
            
        return Entity.KILL
    
    def Update(self,time,dtime,real_pos=None):
        # (hack) the extra position argument is needed because some deriving classes hack
        # the position member (i.e. all orbiting entities)
        AnimTile.Update(self,time,dtime)
        
        if not self.no_flash:
            self.dropshadow_color = ColorLerp(self.dropshadow_blend_color,self.color,(math.sin(time*10)+1.0)/2)
        if self.sparkhalo == 0:
            return
        
        pos = real_pos or self.pos
        oldpos = getattr(self,'oldpos',pos)
        if (oldpos[0]-pos[0])**2+(oldpos[1]-pos[1])**2 > self.spark_density:     
            st = EnemyAnimStub(sparkhalo=self.sparkhalo,ttl=self.spark_ttl)
            st.SetColor(self.color)
            st.SetPosition((pos[0]+(oldpos[0]-pos[0])/2+self.dim[0]/2+(random.random()*0.5)-0.25,
                            pos[1]+(oldpos[1]-pos[1])/2+self.dim[1]/2+(random.random()*0.5)-0.25))
            self.game.AddEntity(st)
            
            oldpos = pos
            
        self.oldpos = oldpos
        
        

class SmallTraverser(Enemy):
    """The simplest class of entities, it moves in a certain
    range and kills the player immediately. The class supports
    both horizontal and vertical moves."""

    def __init__(self, text, height, frames, speed=1.0, move_speed=3, randomdir=True, direction=Entity.DIR_HOR, verbose=_("a Harmful Traverser Unit (HTU)"),sparkhalo=None,shrinkbb=0.5,halo_img="default",**kwargs):
        Enemy.__init__(self, text, height, frames, speed, 2, halo_img=halo_img, sparkhalo = (sparkhalo if sparkhalo is not None else (1 if direction==Entity.DIR_HOR else 2)),**kwargs)

        move_speed *= 0.65 # balancing

        self.verbose = verbose
        self.vel = (move_speed * random.uniform(0.8,1.2) * random.choice((-1, 1))) if randomdir is True else 1
        self.direction = direction

        self._ShrinkBB(shrinkbb)

    def GetVerboseName(self):
        return self.verbose
    
    def GetDrawOrder(self):
        return 2100
    
    def _GetScoreAmount(self):
        return -0.05

    def Update(self, time_elapsed, time):
        Enemy.Update(self, time_elapsed, time)
        if not self.game.IsGameRunning():
            return 
            
        ab = self.GetBoundingBoxAbsShrinked()
            
        # left, top, right, bottom
        intersect = [[1e5,0.0],[1e5,0.0],[-1e5,0.0],[-1e5,0.0]]
        colliders = []
        fric = 1e10
        
        if self.direction == Entity.DIR_HOR:
            for collider in self.game.GetLevel().EnumPossibleColliders(ab):
                if isinstance(collider,Enemy) or isinstance(collider,Player) and collider.MeCanDie():
                    continue
                
                cd = collider.GetBoundingBoxAbs()
                if cd is None:
                    continue
                 
                # is our left border intersecting?
                if self._HitsMyLeft(ab,cd):                      
                    res = collider.Interact(self)
                    if res == Entity.BLOCK:
                        self.vel = abs(self.vel)
                        self._Return()
                        break
                    elif res == Entity.KILL:
                        self._Die()
                    
                # is our right border intersecting?
                elif self._HitsMyRight(ab,cd):                      
                    res = collider.Interact(self)
                    if res == Entity.BLOCK:
                        self.vel = -abs(self.vel)
                        self._Return()
                        break
                    elif res == Entity.KILL:
                        self._Die()
        else:
            for collider in self.game.GetLevel().EnumPossibleColliders(ab):
                if isinstance(collider,Enemy) or isinstance(collider,Player) and collider.MeCanDie():
                    continue
                
                cd = collider.GetBoundingBoxAbs()
                if cd is None:
                    continue
                
                
                if self._HitsMyBottom(ab,cd):
                    res = collider.Interact(self)
                    if res == Entity.BLOCK:
                        self.vel = -abs(self.vel)
                        self._Return()
                        break
                    elif res == Entity.KILL:
                        self._Die()
                                               
                # is our top border intersecting?
                elif self._HitsMyTop(ab,cd):
                    res = collider.Interact(self)
                    if res == Entity.BLOCK:
                       self.vel = abs(self.vel)
                       self._Return()
                       break   
                    elif res == Entity.KILL:
                       self._Die()     

        lx,ly = self.level.GetLevelSize()
        if self.direction == Entity.DIR_HOR:
            pos = [self.pos[0] + self.vel * time, self.pos[1]]
            if pos[0] < 0 or pos[0] > lx:
                pos[0] = max(0, min(pos[0],lx))
                self.vel = -self.vel
                self._Return()
        else:
            pos = [self.pos[0], self.pos[1] + self.vel * time]
            if pos[1] < 0 or pos[1] > ly:
                pos[1] = max(0, min(pos[1],ly))
                self.vel = -self.vel
                self._Return()
                
        self.SetPosition(pos)
        self.SetState(1 if self.vel > 0 else 0)
        
    def _Return(self):
        for dir in itertools.product((-2,-1,+1,2.5),(-2.5,-1,+1,+2)):
            if dir[self.direction]/abs(dir[self.direction]) == self.vel/abs(self.vel):
                continue
            l = DirectedEnemyAnimStub(dir, 6.0, ttl=0.3)
            l.SetPosition((self.pos[0]+self.dim[0]*0.4,self.pos[1]+self.dim[1]*0.5))
            l.SetColor(self.color)
            self.game.AddEntity(l)
        
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

    def __init__(self, text, height, frames, speed=1.0, move_speed=3, randomdir=True, verbose=_("a Naughty Pong Pong "),shrinkbb=0.55,killable=True,sparkhalo=0,**kwargs):
        Enemy.__init__(self, text, height, frames, speed, 2, sparkhalo=sparkhalo,**kwargs)

        self.verbose = verbose
        #self.vel = (move_speed * random.choice((-1, 1))) if randomdir is True else 1
        self.vel = -defaults.jump_vel   
        self.killable=killable

        self._ShrinkBB(shrinkbb)

    def GetVerboseName(self):
        return self.verbose
    
    def GetDrawOrder(self):
        return 2100
    
    def _GetScoreAmount(self):
        return -0.01

    def Update(self, time_elapsed, time):
        Enemy.Update(self, time_elapsed, time)
        if not self.game.IsGameRunning():
            return 
        
        if hasattr(self,"relaunch_time"):
            if self.relaunch_time.GetElapsedTime() > 0.5:
                self.vel = -defaults.jump_vel
                delattr(self,"relaunch_time")
            return
        
        self.acc = self.level.gravity*10
        vec = (self.vel + self.acc * time) * time

        pos = self.pos
        self.SetPosition( (pos[0], pos[1] + vec ) )
        
        # Check for possible colliders on the bottom to determine when we
        # are touching the ground
        
        ab = self.GetBoundingBoxAbsShrinked()  
        for collider in self.game.GetLevel().EnumPossibleColliders(ab):
            if collider is self:
                continue
            
            cd = collider.GetBoundingBoxAbs()
            if cd is None:
                continue
            
            # lower border    
            if self._HitsMyBottom(ab, cd):

                if collider.Interact(self) & Entity.BLOCK_TOP:
                    self.vel = min(0,self.vel)
                    collider.AddToActiveBBs()     
                
                    self.relaunch_time = sf.Clock()    
                    break
                    
            # top border
            elif self._HitsMyTop(ab, cd):

                if collider.Interact(self) & Entity.BLOCK_BOTTOM:
                    self.vel = max(0,self.vel)
                    collider.AddToActiveBBs()     
                break
            
                
    def Interact(self, other):
        if isinstance(other,Player) and self.killable:
            ab = self.GetBoundingBoxAbs()
            cd = other.GetBoundingBoxAbs()    
            
            if self._HitsMyTop(ab,cd):
                self._Die()
                return Entity.ENTER
            
        return Entity.KILL
    
        
class RotatingInferno(Enemy):
    """The RotatingInfero class of entities is simply an animated
    tile which rotates around its center in a certain distance."""
    def __init__(self, text, height, frames, speed=1.0, rotate_speed_base = 0.2, radius = 3.5, sparkhalo=0, no_flash=True, **kwargs):
        Enemy.__init__(self, text, height, frames, speed, 1, halo_img="halo_rotating_inferno.png", sparkhalo=sparkhalo, no_flash=no_flash, **kwargs)
        
        self.rotate_speed_base = rotate_speed_base * 0.65 # balancing
        self.ofs_vec = [radius,0]
        
    def Interact(self, other):
        return Entity.KILL
    
    def GetVerboseName(self):
        return _("Rotating Inferno")

    def _Die(self):
        # We CANNOT die.
        return
    
    def SetPosition(self,pos):
        self.real_pos = (pos[0]+self.ofs_vec[0],pos[1]+self.ofs_vec[1])
        Enemy.SetPosition(self,pos)
    
    def Update(self, time_elapsed, time):
        Enemy.Update(self,time_elapsed, time,self.real_pos)
        if not self.game.IsGameRunning():
            return 
        
        angle = (math.pi*2.0*time) * self.rotate_speed_base
        a,b = math.cos(angle), math.sin(angle)
        
        self.ofs_vec = [self.ofs_vec[0]*a-self.ofs_vec[1]*b,self.ofs_vec[0]*b+self.ofs_vec[1]*a]
        self.SetPosition(self.pos)
        
        if not hasattr(self,'spawn_clock'):
            self.spawn_clock = sf.Clock()
        
        elif self.spawn_clock.GetElapsedTime() > 0.2:
            delattr(self,'spawn_clock')
            for dir in itertools.product((-2,-1,+1,2.5),(-2.5,-1,+1,+2)):
                if random.random() > 0.5:
                    continue
                l = DirectedEnemyAnimStub(dir, 6.0, ttl=0.3)
                l.SetPosition((self.real_pos[0]+self.dim[0]*0.4,self.real_pos[1]+self.dim[1]*0.5))
                l.SetColor(self.color)
                self.game.AddEntity(l)
        
    def GetBoundingBox_EditorCatalogue(self): # Special logic for use within the editor
        return (self.pos[0],self.pos[1],self.dim[0],self.dim[1])

    def _UpdateBB(self):
        pass
        
    def GetBoundingBox(self):
        return (self.real_pos[0],self.real_pos[1],self.dim[0],self.dim[1])
    
    def GetBoundingBoxAbs(self):
        return (self.real_pos[0],self.real_pos[1],self.dim[0]+self.real_pos[0],self.dim[1]+self.real_pos[1])
        
    def GetBoundingBoxShrinked(self):
        return self.GetBoundingBox()
        
    def GetBoundingBoxAbsShrinked(self):
        return self.GetBoundingBoxAbs()
    
    def Draw_EditorCatalogue(self): # Special logic for use within the editor
        lv = self.game.GetLevel()
        for offsetit, elem, colored in self.cached: 
            lv.DrawSingle(elem,self.pos)
            
    def Draw(self,*args): 
        lv = self.game.GetLevel()
        for offsetit, elem, colored in self.cached: 
            lv.DrawSingle(elem,self.real_pos)

        
        
class SmallBob(Enemy):
    """This guy is not actually friendly, but he's much less a danger
    as his older (and bigger) brothers are. He does not shoot, for
    example."""
    def __init__(self, text, height, frames, speed=1.0, move_speed_base = 1.2, shrinkbb=0.8,trigger_distance=22, trigger_speed_scale=4.0, accel_time=3.0, no_flash=True):
        Enemy.__init__(self, text, height, frames, speed, 2, halo_img=None,sparkhalo=0,no_flash=no_flash)
        self._ShrinkBB(shrinkbb)
        self.hits = self.hits_needed = 4
        self.vel = self.last = random.choice((-1, 1)) 
        self.move_speed = move_speed_base*random.uniform(0.8,1.2)
        self.trigger_distance = trigger_distance**2
        self.triggered = self.cool_down = False
        self.slow_start = 0.0
        self.trigger_speed_scale = trigger_speed_scale
        self.accel_time = accel_time

    def GetVerboseName(self):
        return _("Small Bob")
    
    def GetDrawOrder(self):
        return 2100
    
    def _GetScoreAmount(self):
        return -0.08
    
    def Interact(self, other):
        """SmallBob needs 4 hits to die"""
        if isinstance(other,Shot):
            self.hits -= 1
            self._SpreadSplatter(0.1* (self.hits_needed - self.hits))
            if self.hits == 0:
                self._Die()
            
        return Entity.KILL

    def Update(self, time_elapsed, time):
        Enemy.Update(self, time_elapsed, time)
        if not self.game.IsGameRunning():
            return 
            
        ab = self.GetBoundingBoxAbsShrinked()
        ab2 = list(ab)
        ab2[1] -= 1
        ab2[3] += 1
        res = 0
        self.SetState(0)
        
        player,pos = self.game._GetAPlayer(),self.pos
        if player:
            ppos = player.pos[0]+player.dim[0]*0.5,player.pos[1]+player.dim[1]*0.5
            if self.triggered and self.trigger_watch.GetElapsedTime()<3.0:
                pass
                
            elif (ppos[0]-pos[0])**2+(ppos[1]-pos[1])**2 < self.trigger_distance and ab[3] > player.pos[1]+player.dim[1] > ab[1]-0.2:
                
                self.cool_down = False
                self.triggered = True
                self.trigger_watch = sf.Clock()
    
                print("Trigger return event due to nearing player")
                if self.last == self.vel:
                    self.vel = -1 if pos[0] > ppos[0] else 1
            else:
                if self.triggered:
                    self.cool_down = True
                    
                self.triggered = False
        
        floor = False
        for collider in self.game.GetLevel().EnumPossibleColliders(ab2):
            if isinstance(collider,Enemy) or isinstance(collider,Player) and collider.MeCanDie():
                continue
            
            cd = collider.GetBoundingBoxAbs()
            if cd is None:
                continue
             
            # is our left border intersecting?
            a = self._HitsMyLeft(ab,cd) 
            b = self._HitsMyRight(ab,cd)
            if a and not b or b and not a:                      
                res = collider.Interact(self)
                if res == Entity.BLOCK:
                    collider.AddToActiveBBs()            
                    self.vel = -1 if b else 1
                    break
                elif res == Entity.KILL:
                    self._Die()
                    
            if self._HitsMyTop(ab2,cd):
                collider.AddToActiveBBs()            
                floor = True
                
        #if not floor and self.last == self.vel:
        #    self.vel = -self.vel
                    
        pos = [self.pos[0] + self.vel * time * self.move_speed * (self.slow_start+1.0 if self.triggered else 1), self.pos[1]]
        self.slow_start = min(self.trigger_speed_scale-1, self.slow_start + self.trigger_speed_scale* (1.0/self.accel_time) * time *
                              (-1 if self.cool_down else 1))
        if self.slow_start < 0:
            self.cool_down = False
            self.slow_start = 0
            
        lx,ly = self.level.GetLevelSize()
        if pos[0] > lx or pos[0] < 0:
            self.vel = -self.vel
            pos[0] = max(0, min(pos[0],lx))
        
        self.SetPosition(pos)
        
            
from weapon import Weapon
class SmallRobot(SmallTraverser):
    
    def __init__(self, *args, speed=0.5, cooldown_time=5, shot_delta=0.25, shots=4, shot_ofs_y=0.55, verbose=_("a Nifty Robot Intruder"), sparkhalo=0, no_flash=True, **kwargs):
        SmallTraverser.__init__(self, *args, verbose=verbose, halo_img=None, sparkhalo=sparkhalo,no_flash=no_flash, **kwargs)
        self.weapon = Weapon()
        self.cooldown_time = cooldown_time
        self.shots = shots
        self.shot_delta = shot_delta
        self.shot_ofs_y = shot_ofs_y
        self.last_shot = -1
        
    def SetGame(self,game):
        self.game = game
        self.weapon.SetGame(game)
        
    def SetLevel(self,level):
        self.level = level
        self.weapon.SetLevel(level)
        
    def _Die(self):
        # We CANNOT die.
        return
    
    def Interact(self,other):
        if isinstance(other,Shot): # avoid swallowing our own shoots
            return Entity.ENTER
        
        return SmallTraverser.Interact(self, other)
    
    def Update(self, time_elapsed, time):
        SmallTraverser.Update(self, time_elapsed, time)
        if not self.game.IsGameRunning():
            return 
        
        if not hasattr(self,"shot_timer") or self.shot_timer.GetElapsedTime() > self.cooldown_time:
            self.shot_timer = sf.Clock()
            
        id = int( self.shot_timer.GetElapsedTime()/self.shot_delta )
        if id == 0 and self.last_shot == self.shots-1:
            self.last_shot = -1
            
        if id < self.shots and id > self.last_shot:
            self.weapon.Shoot((self.pos[0]+self.dim[0]*0.5,self.pos[1]+self.shot_ofs_y),
                (self.vel/abs(self.vel),random.random()/20),
                self.color,[self])
            self.last_shot = id
            
            

class Turret(Enemy):
    def __init__(self, *args, speed=0.5, cooldown_time=4, shot_delta=0.08, shots=7, shot_ofs=((0.3,0.55),(0.6,0.55)), angle_limit=55, distance_limit=5, shot_speed=20, no_flash=True, **kwargs):
        Enemy.__init__(self, *args, speed=speed, states=2, halo_img=None, sparkhalo=0, no_flash=no_flash, **kwargs)
        self.weapon = Weapon(speed=shot_speed)
        self.cooldown_time = cooldown_time
        self.shots = shots
        self.shot_delta = shot_delta
        self.shot_ofs = shot_ofs
        self.last_shot = -1
        self.cos_angle_limit = math.cos( math.radians( angle_limit ) )
        self.distance_limit = distance_limit
        
    def SetGame(self,game):
        self.game = game
        self.weapon.SetGame(game)
        
    def SetLevel(self,level):
        self.level = level
        self.weapon.SetLevel(level)
        
    def GetVerboseName(self):
        return _("Turret")
        
    def _Die(self):
        # We CANNOT die.
        return
    
    def Interact(self,other):
        return Entity.ENTER
    
    def Update(self, time_elapsed, time):
        Enemy.Update(self, time_elapsed, time)
        if not self.game.IsGameRunning():
            return 
        
        player,pos = self.game._GetAPlayer(),self.pos
        if player:
            ppos = player.pos
            if ppos[0] < pos[0]:
                if self.state == 0:
                    self.SetState(1)
            else:
                if self.state == 1:
                    self.SetState(0)
        
        if not hasattr(self,"shot_timer") or self.shot_timer.GetElapsedTime() > self.cooldown_time:
            self.shot_timer = sf.Clock()
            
        id = int( self.shot_timer.GetElapsedTime()/self.shot_delta )
        if id == 0 and self.last_shot == self.shots-1:
            self.last_shot = -1
            
        if id < self.shots and id > self.last_shot:
            dir = (1.0,0)
            if player:
                dir = (ppos[0]-pos[0],(ppos[1]-pos[1])*(1+(random.random()-1)/4))
                dl  = (dir[0]**2 + dir[1]**2) **0.5
                dir = (dir[0]/dl,dir[1]/dl)
                
                # implement angle and distance based limits
                if abs(dir[0]) < self.cos_angle_limit or self.Distance(player) < self.distance_limit:
                    return
            self.weapon.Shoot((self.pos[0]+self.shot_ofs[self.state][0],self.pos[1]+self.shot_ofs[self.state][1]),dir,self.color,[self])
            self.last_shot = id
        
        

# vim: ai ts=4 sts=4 et sw=4
