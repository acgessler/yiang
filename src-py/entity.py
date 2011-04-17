#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [game.py]
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


# PySFML
import sf

# Python Core
import itertools
import collections
import os
import random
import math
import traceback
import threading

# My own stuff
import mathutil
import defaults
from renderer import Drawable,Renderer
from game import Game

def gen_halo_default():
    """Programmatically generate the default 'halo', which 
    is a simple background rectangle behind the tile"""
    text = bytes([0x60,0x60,0x60,0x90])
    
    img = sf.Image()
    img.LoadFromPixels(64,64,bytes([min(max(x+random.randint(-5,5),0),0xff) for x in text*(64*64)]))
    return img

class Entity(Drawable):
    """Base class for all kinds of entities, including the player.
    The term `entity` refers to a state machine which is in control
    of a set of tiles. Entities receive Update() callbacks once per
    logical frame."""

    ENTER,KILL = 0x100,0x200
    DIR_HOR,DIR_VER=range(2) # don't change!

    BLOCK_LEFT,BLOCK_RIGHT,BLOCK_TOP,BLOCK_BOTTOM,BLOCK = 0x1,0x2,0x4,0x8,0xf
    
    # deprecated, pertains to _CollideBB
    UPPER_LEFT,UPPER_RIGHT,LOWER_LEFT,LOWER_RIGHT,CONTAINS,ALL = 0x1,0x2,0x4,0x8,0x10,0xf|0x10
    
    
    DEFAULT_POS = [-10000,10000]
    DEFAULT_DIM = [1,1]
    
    lock = threading.Lock()
    halo_cache = {None:None}
    default_halo_providers = {
            "default":gen_halo_default
    }
    
    def __init__(self):
        Drawable.__init__(self)
        self.pos = Entity.DEFAULT_POS
        self.dim = Entity.DEFAULT_DIM
        self.color = sf.Color.White
        self.game = None
        self.in_visible_set = False

    def Update(self,time_elapsed,time_delta):
        """To be implemented"""
        pass

    def SetGame(self,game):
        """Binds the Entity to a Game instance. This is called
        automatically for all entities loaded as part of a level"""
        self.game = game
        if game.level:
            self.level = game.level
            #self._Optimize()
        
    def SetLevel(self,level):
        """Binds the Entity to a Level instance. This is called
        automatically for all entities loaded as part of a level"""
        self.level = level
        #if level.game:
        #    self._Optimize()
            
    #def _Optimize(self):
    #    level = self.level
    #    
    #    old = self.SetPosition
    #    def SetPosition_Quick(pos): # optimize
    #        old(pos)
    #        level._MarkEntityAsMoved(self)
    #        self._UpdateBB()
    #    
    #    self.SetPosition = SetPosition_Quick

    def SetPosition(self,pos):
        self.pos = list(pos)
        
        if self.game:
            level= self.game.level
            if level:
                level._MarkEntityAsMoved(self)
            
        self._UpdateBB()
        
    def _UpdateBB(self):
        """Called whenever the bounding box of the entity 
        might have changed. Entity does not further utilize
        this information, but deriving classes might do this.
        """
        pass

    def SetColor(self,color):
        self.color = color
        
    def GetDrawOrder(self):
        return 500
    
    def GetFriction(self):
        return 1000
        
    def AddToActiveBBs(self,color=sf.Color.Red):
        """Debug feature, mark a specific entity for highlighting
        in the next frame. Its bounding box will then be drawn
        in the color specified"""
        self.highlight_bb = color

    def Interact(self,other):
        return Entity.BLOCK

    def Respawn(self,enable_respawn_points):
        """Invoked when the player is killed and needs to respawn"""
        pass
    
    def OnLeaveLevel(self):
        """Invoked when the level the entity belongs to is 
        left by the player. The level remains in memory
        and may be re-entered later."""
        pass
    
    def OnEnterLevel(self):
        """Invoked whenever the player enters the level
        the entity belongs to. OnEnterLevel() and OnLeaveLevel()
        pairs are always matched. """
        pass

    def GetVerboseName(self):
        """Return a verbose (i.e. non-formal) description of the
        entity. The returned string must be suitable to be
        used in death reports, i.e. 'you got killed by {an unknown entity}',
        'an unknown entity' being the verbose name"""
        return "unknown"
    
    def _HitsMyTop(self,ab,cd):
        return cd[1] <= ab[1] <= cd[3] and (ab[0] <= cd[0] <= ab[2] 
            or cd[0] <= ab[0] <= cd[2] and  min( ab[2], cd[2]) - max(ab[0], cd[0]) >= 0.1)
        
    def _HitsMyBottom(self,ab,cd):
        return cd[1] <= ab[3] <= cd[3] and (ab[0] <= cd[0] <= ab[2] 
            or cd[0] <= ab[0] <= cd[2] and min( ab[2], cd[2]) - max(ab[0], cd[0]) >= 0.1)
        
    def _HitsMyRight(self,ab,cd):
        return cd[2] >= ab[2] >= cd[0] and (ab[1] <= cd[1] <= ab[3] 
            or cd[1] <= ab[1] <= cd[3] and min( ab[3], cd[3]) - max(ab[1], cd[1]) >= 0.1)
        
    def _HitsMyLeft(self,ab,cd):
        return cd[2] >= ab[0] >= cd[0] and (ab[1] <= cd[1] <= ab[3] 
            or cd[1] <= ab[1] <= cd[3] and min( ab[3], cd[3]) - max(ab[1], cd[1]) >= 0.1)
        
        
    def _IsContained(self,ab,cd):
        return ab[0] <= cd[0] and cd[2] <= ab[2] and ab[1] <= cd[1] and cd[3] <= ab[3]
        
        
    def _HitsMyTop2(self,ab,cd):
        return cd[1] <= ab[1] <= cd[3] and (ab[0] <= cd[0] <= ab[2] 
            or cd[0] <= ab[0] <= cd[2] )
        
    def _HitsMyBottom2(self,ab,cd):
        return cd[1] <= ab[3] <= cd[3] and (ab[0] <= cd[0] <= ab[2] 
            or cd[0] <= ab[0] <= cd[2] )
        
    def _HitsMyRight2(self,ab,cd):
        return cd[2] >= ab[2] >= cd[0] and (ab[1] <= cd[1] <= ab[3] 
            or cd[1] <= ab[1] <= cd[3] )
        
    def _HitsMyLeft2(self,ab,cd):
        return cd[2] >= ab[0] >= cd[0] and (ab[1] <= cd[1] <= ab[3] 
            or cd[1] <= ab[1] <= cd[3] )

    def _BBCollide(self,rect,mycorner):
        """Collide the first axis-aligned BB (x,y,x2,y2) with the
        second bounding box, return a ORed combination of the
        Entity.UPPER/Entity.LOWER flags.
        
        
        This is DEPRECATED, use CollideLineSegmentWithRectangle().
        """
        has = 0
        
        # upper left corner
        if mycorner[2]>rect[0]>=mycorner[0] and mycorner[3]>rect[1]>=mycorner[1]:
            has |= Entity.UPPER_LEFT

        # upper right corner
        if mycorner[2]>rect[2]>=mycorner[0] and mycorner[3]>rect[1]>=mycorner[1]:
            has |= Entity.UPPER_RIGHT

        # lower left corner
        if mycorner[2]>rect[0]>=mycorner[0] and mycorner[3]>rect[3]>=mycorner[1]:
            has |= Entity.LOWER_LEFT

        # lower right corner
        if mycorner[2]>rect[2]>=mycorner[0] and mycorner[3]>rect[3]>=mycorner[1]:
            has |= Entity.LOWER_RIGHT

        # check an arbitrary corner the other way round, this checks for
        # containment (which shouldn't happen regularly for
        # collision detection will prevent it)
        if rect[2]>mycorner[2]>=rect[0] and rect[3]>mycorner[3]>=rect[1]:
            has |= Entity.CONTAINS

        return has

    def _BBCollide_XYWH(self,a,b):
        """Collide the first axis-aligned BB (x,y,width,height) with the
        second bounding box, return a ORed combination of the
        Entity.UPPER/Entity.LOWER flags."""
        return self._BBCollide((a[0],a[1],a[0]+a[2],a[1]+a[3]),
            (b[0],b[1],b[0]+b[2],b[1]+b[3]))
        
    def GetCullRegion(self):
        """Deprecated"""
        bb = self.GetBoundingBox()
        if bb is None:
            return 0
        
        dist =  mathutil.PointToBoxSqrEst( self.game.GetOrigin(),bb)
        return dist > defaults.cull_distance_sqr and 1 or dist > defaults.swapout_distance_sqr and 2 or 0
    
    def _GetHaloImage(self,halo_img):
        """Obtain the halo image to be shown in the background of
        the entity (not too strong, alpha should be pretty low).
        None is a valid return value, it disables the whole effect."""
        if defaults.no_halos is True:
            return None
            
        with Entity.lock:
            if not halo_img in Entity.halo_cache:
                if halo_img in Entity.default_halo_providers:
                    img = Entity.default_halo_providers[halo_img]()
                else:
                    from textures import TextureCache
                    
                    file = os.path.join(defaults.data_dir,("textures" if not '/' in halo_img else ""),halo_img)
                    print(file)
                    img = TextureCache.Get(file)
                    if not img:
                        img = TextureCache.Get(halo_img)
                        if not img:
                            print("Failure loading halo from both {0} and {1}, giving up".format(file,halo_img))
                    
                Entity.halo_cache[halo_img] = img
                return img
            
        return Entity.halo_cache[halo_img]
    
    
    def Distance(self,other):
        """Find a quick estimate for the distance between @self and @other"""
        midpoint1 = (self.pos[0]+self.dim[0]*0.5,self.pos[1]+self.dim[1]*0.5)
        midpoint2 = (other.pos[0]+other.dim[0]*0.5,other.pos[1]+other.dim[1]*0.5)
        return (midpoint1[0]-midpoint2[0])**2+(midpoint1[1]-midpoint2[1])**2
        

class EntityWithEditorImage(Entity):
    """A normal entity except it displays a splash bitmap instead
    of the actual entity when it is being used in editor mode"""
    def __init__(self,editor_stub_img="noise.png"):
        Entity.__init__(self)
        self.editor_stub_img = editor_stub_img
        
    def Update(self, time_elapsed, time):
        
        if self.game.GetGameMode() == Game.EDITOR:
            if not hasattr(self,"respawn_img") and self.editor_stub_img:
                from textures import TextureCache
                self.respawn_img = TextureCache.Get(os.path.join(defaults.data_dir,"textures",self.editor_stub_img))
                
                tx,ty = defaults.tiles_size_px
                bb = self.GetBoundingBox() or (None,None,1,1)
                
                self.respawn_sprite = sf.Sprite(self.respawn_img)
                self.respawn_sprite.Resize(tx*bb[2],ty*bb[3])
                
    def Draw(self):
        if self.game.GetGameMode() == Game.EDITOR  and self.editor_stub_img:
            self.game.GetLevel().DrawSingle( self.respawn_sprite, self.pos )
            
# vim: ai ts=4 sts=4 et sw=4
