#! /usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [materials.py]
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

# PySFML
import sf

# My own stuff
import defaults
from game import Entity,Game, EntityWithEditorImage
from tile import AnimTile,Tile,TileLoader
from player import Player
from renderer import Renderer,Drawable

class Iceblock(Tile):
    """Iceblock is a normal tile with low friction"""
    
    def __init__(self,*args,friction=0.0,**kwargs):
        Tile.__init__(self,*args,**kwargs)
        self.friction = friction
        
    def GetFriction(self):
        return self.friction
    
    
class InvisibleTile(EntityWithEditorImage,Tile):
    """Invisible tile with editor support"""
    
    def __init__(self,*args,editor_image="invisible_stub.png",**kwargs):
        Tile.__init__(self,*args,**kwargs)
        EntityWithEditorImage.__init__(self,editor_image)
        
    def Update(self,t,dt):
        Tile.Update(self,t,dt)
        EntityWithEditorImage.Update(self,t,dt)
        
    def Draw(self):
        Tile.Draw(self)
        EntityWithEditorImage.Draw(self)
        
        
class OneSidedWall(Tile):
    """OneSidedWall allows the player to pass in only one direction"""
    
    def __init__(self,*args,block=Entity.BLOCK_LEFT,**kwargs):
        Tile.__init__(self,*args,**kwargs)
        self.block = block
        
    def Interact(self,other):
        return self.block
            
        
class BackgroundLight(Tile):
    """Show only a halo background, no real tile contents.
    This is no real illumination, but it serves well as cheap fake light."""
    
    def __init__(self,*args,darken=0.8, **kwargs):
        self.darken =  max(0.15, darken*0.6)
        Tile.__init__(self,"", *args,draworder=-10000, collision=Entity.ENTER,**kwargs)
        
    # def _GetHaloImage(self):
    #    img = Entity._GetHaloImage(self,self.halo_img)
    #    if not img:
    #        return None
    #    
    #    s = sf.Sprite(img)
    #    s.SetColor(sf.Color(0,0,0, 0xff))
    #    s.Resize(self.dim[0] * defaults.tiles_size_px[0],
    #        self.dim[1] * defaults.tiles_size_px[1]
    #    )
    #    return s
    
    def Draw(self):
        if len(self.cached) < 2:
            return
        
        lv = self.game.GetLevel()
        offset,elem = self.cached[1]
            
        d = self.darken
        c = self.color
        elem.SetColor(sf.Color( int(c.r*d), int(c.g*d), int(c.b*d) ,0xff ))
        lv.DrawSingle(elem,self.pos)
    
    
    
    
    
    
    
    
    

# vim: ai ts=4 sts=4 et sw=4