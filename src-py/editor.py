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

import sf

# Python core
import sys
import os
import math
import traceback

# Our stuff
import defaults


# Note: some of these imports are only needed because they might be implicitly
# referenced by shebang lines in one of the tiles which we created
from fonts import FontCache
from keys import KeyMapping
from game import Game,Entity
from log import Log
from renderer import Renderer,Drawable,NewFrame
from highscore import HighscoreManager
from audio import BerlinerPhilharmoniker
from achievements import Achievements
from enemy import Enemy
from score import ScoreTile

from minigui import Component, Button, ToggleButton

class EditorCursor(Drawable):
    """Draws the cursor on top of the whole scenery"""
    
    def __init__(self):
        Drawable.__init__(self)
        
        self.cursor_img  = sf.Image()
        self.cursor_img.LoadFromFile(os.path.join(defaults.data_dir,"textures","cursor.png"))
        
        self.cursor = sf.Sprite(self.cursor_img)
        Renderer.app.ShowMouseCursor(False)
        
    def GetDrawOrder(self):
        return 100000
    
    def Draw(self):
        
        inp = Renderer.app.GetInput()
        self.mx,self.my = inp.GetMouseX(),inp.GetMouseY()
        
        # move the cursor according to mouse input
        w,h =self.cursor_img.GetWidth(),self.cursor_img.GetHeight()   
             
        #if not (w/2.0 < mx < defaults.resolution[0]-w/2.0) or not (h/2.0 < my < defaults.resolution[1]-h/2.0):
        #    return

        self.cursor.SetPosition(self.mx-w/2.0,self.my-h/2.0)
        Renderer.app.Draw(self.cursor)

class EditorGame(Game):
    """Special game implementation for the editor"""

    def __init__(self):
        Game.__init__(self,mode=Game.EDITOR,undecorated=True)
        
        self.selection = []
        self.template = dict()
        self.in_select = False
        self.select_start = None
        self.dirty_area = 0.0
        
        Renderer.AddDrawable(EditorCursor())
        
        # Setup basic GUI buttons
        Renderer.AddDrawable((Button(text="Restart",rect=[-200,10,80,25]) + 
             ("release",(lambda src: self.RestartLevel()))
        ))
        Renderer.AddDrawable((Button(text="Kill",rect=[-110,10,80,25]) + 
             ("release",(lambda src: self.Kill("(Kill button)")))
        ))
        
        Renderer.AddDrawable((ToggleButton(text="Suspend\x00Resume",on=True, rect=[-290,10,80,25]) +
             ("off", (lambda src: self.PushSuspend())) +
             ("on",(lambda src: self.PopSuspend())) 
        ))
            
    def _DrawRectangle(self,bb,color):
        shape = sf.Shape()

        bb = [bb[0],bb[1],bb[0]+bb[2],bb[1]+bb[3]]
        bb[0:2] = self.ToDeviceCoordinates(self.level.ToCameraCoordinates( bb[0:2] ))
        bb[2:4] = self.ToDeviceCoordinates(self.level.ToCameraCoordinates( bb[2:4] ))

        shape.AddPoint(bb[0],bb[1],color,color)
        shape.AddPoint(bb[2],bb[1],color,color)
        shape.AddPoint(bb[2],bb[3],color,color)
        shape.AddPoint(bb[0],bb[3],color,color)

        shape.SetOutlineWidth(2)
        shape.EnableFill(False)
        shape.EnableOutline(True)

        self.DrawSingle(shape)
        
    def _CloneEntity(self,which):
        if not hasattr(which,"editor_shebang"):
            print("Failure cloning {0} - no shebang record found".format(which))
            return None
        
        tempdict = dict(locals())
        try:
            exec(which.editor_shebang,globals(),tempdict)
        except:
            print("Failure cloning {0}, exec() fails".format(which))
            traceback.print_exc()
            return None
            
        t = tempdict['entity']
        t.SetLevel(self.level)
        t.SetColor(which.color)
        t.editor_shebang = which.editor_shebang
        return t
    
    def _DrawEditor(self):
        
        inp = Renderer.app.GetInput()
        self.level.SetDistortionParams((100,0,0))   
        
        # get from mouse to tile coordinates
        # (XXX) put this into a nice function or so --- :-)
        offset = self.level.GetOrigin()
        self.tx,self.ty = (self.mx/defaults.tiles_size_px[0] + offset[0],
            self.my/defaults.tiles_size_px[1]-self.level.vis_ofs - 0.5)
        
        fx,fy = math.floor(self.tx),math.floor(self.ty)
        
        # check if there's an entity right here and show its bounding box in white.
        # if there are multiple entities, take the one with the highest 
        # drawing order.
        try:
            entity = sorted(self.level.EnumEntitiesAt((self.tx,self.ty)),key=lambda x:x.GetDrawOrder(),reverse=True)[0]
            bb = entity.GetBoundingBox()
            
            
            self._DrawRectangle(bb,sf.Color.Green)
            self.selection = [entity]
                
        except IndexError:
            # no entity below the cursor, highlight the nearest point and its surroundings
            self._DrawRectangle((fx,fy,1.0,1.0),sf.Color(150,150,150))
            #e = ((x,y) for y in range(-3,4) for x in range(-3,4) if x or y)
            #for x,y in e:
            #    c = int(50 - (x**2 + y**2)**0.5 *0.20 * 50)
            #    self._DrawRectangle((fx+x,fy+y,1.0,1.0),sf.Color(c,c,c))
            
        if inp.IsMouseButtonDown(sf.Mouse.Right):
            if inp.IsMouseButtonDown(sf.Mouse.Left):
                # Both mouse buttons pressed, delete template
                for entity,pos in self.template.items():
                    self.level.RemoveEntity(entity)
                    
                self.template = dict()
                raise NewFrame()
            
            # copy current tile
            if self.in_select is False:
                if self.select_start is None or not inp.IsKeyDown(sf.Key.LShift):
                    self.template = dict()
                    self.select_start = fx,fy
                    
                self.in_select = True
                
            if inp.IsKeyDown(sf.Key.LControl):
                if not hasattr(self,"last_select") or abs(self.last_select[0]-fx)>1 or abs(self.last_select[1]-fy)>1:
                    if not hasattr(self,"last_select"):
                        self.last_select = self.select_start
                    
                    for y in range(self.select_start[1],fy+1,1) if fy >= self.select_start[1] else range(self.select_start[1],fy-1,-1):
                        for x in range(self.last_select[0],fx+1,1) if fx >= self.last_select[0] else range(self.last_select[0],fx-1,-1):
                            for e in self.level.EnumEntitiesAt((x+0.5,y+0.5)):
                                self.template[e] = None  
                                
                    for y in range(self.last_select[1],fy+1,1) if fy >= self.last_select[1] else range(self.last_select[1],fy-1,-1):
                        for x in range(self.select_start[0],fx+1,1) if fx >= self.select_start[0] else range(self.select_start[0],fx-1,-1):
                            for e in self.level.EnumEntitiesAt((x+0.5,y+0.5)):
                                self.template[e] = None                               
                    
                    self.last_select = fx,fy
                
            else:
                if "entity" in locals(): 
                    self.template[entity] = None
                    
                    
            if inp.IsKeyDown(sf.Key.LControl) and self.select_start:
                # draw selection rectangle
                self._DrawRectangle((self.select_start[0],self.select_start[1],
                    self.tx-self.select_start[0],
                    self.ty-self.select_start[1]), sf.Color.Yellow)
                                
        else:
            self.in_select = False
            
        if inp.IsMouseButtonDown(sf.Mouse.Left):
            if not hasattr(self,"pressed_l") or self.last_insert_pos[0]-fx or self.last_insert_pos[1]-fy:
                # Insert template at this position
                if self.select_start:
                    for e,pos in self.template.items():
                        cloned = self._CloneEntity(e)
                        if not cloned:
                            continue
                        cloned.SetPosition((fx + e.pos[0]-self.select_start[0],
                            fy + e.pos[1]-self.select_start[1])
                        )
                        
                        self.AddEntity(cloned)
                    
                self.pressed_l = True
                self.last_insert_pos = fx,fy
        else:
            try:
                delattr(self,"pressed_l")  
            except AttributeError:
                pass
        
        for e,pos in self.template.items():
            bb = e.GetBoundingBox()
            self._DrawRectangle(bb,sf.Color.Red)
            
            if not "entity" in locals() or not entity in self.template:
                self._DrawRectangle((fx + e.pos[0]-self.select_start[0],
                    fy + e.pos[1]-self.select_start[1],bb[2],bb[3]),sf.Color(40,0,0))
                
                
        if inp.IsKeyDown(sf.Key.M):
            self._DrawMiniMap()
            
        #if self.select_start:
        
        
        
    def AddEntity(self,entity):
        """Wrap entity add/remove functions to synchronize with our level table"""
        self.level.AddEntity(entity)
        self._UpdateMiniMap(entity)
        
    def RemoveEntity(self,entity):
        """Wrap entity add/remove functions to synchronize with our level table"""
        self.level.RemoveEntity(entity)
        self._UpdateMiniMap(entity)
        
    def _UpdateMiniMap(self,entity):
        bb = entity.GetBoundingBox()
        self.dirty_area += bb[2]*bb[3] if bb else 1.0
        if self.dirty_area > 8.0: # choosen by trial and error
            self._BuildMiniMap()
            self.dirty_area = 0.0
        
    def _DrawMiniMap(self):
        Renderer.app.Draw(self.minimap_sprite)
        Renderer.app.Draw(self.minimap_shape)
        
    def _GetImg(self,img):
        # Partly copy'n'paste from CampaignLevel's minimap code
        sprite = sf.Sprite(img)
        
        x,y = 35,math.floor(self.GetUpperStatusBarHeight()*defaults.tiles_size_px[0]) + 20
        
        
        w,h = img.GetWidth(),img.GetHeight()
        w = defaults.resolution[0] - x*2
        h = w*img.GetHeight()/img.GetWidth()
        if h > defaults.resolution[1] - y*2:
            h = defaults.resolution[1] - y*2
            w = h*img.GetWidth()/img.GetHeight()
        
        # -0.5 for pixel-exact mapping, seemingly SFML is unable to do this for us
        sprite.SetPosition(x-0.5,y-0.5)
        sprite.Resize(w,h)
        
        sprite.SetColor(sf.Color(0xff,0xff,0xff,0xff))
        sprite.SetBlendMode(sf.Blend.Alpha)
        return sprite,w,h,x,y
        
    def _BuildMiniMap(self):
        # Partly copy'n'paste from CampaignLevel's minimap code
        w,h = self.level.GetLevelSize()
        yofs = self.level.vis_ofs
        
        self.msx,self.msy = (12,9) if w < 100 else ((8,6) if w < 200 else (4,3)) # scale factors in both axes
        w,h = w*self.msx,(h+3)*self.msy
        b = bytearray(b'\x40\x40\x40\xff') * (w*h)
        
        for entity in self.level.EnumAllEntities():
            bb = entity.GetBoundingBox()
            if bb:
                col = entity.color
                xs,ys = int(bb[0])*self.msx, int(bb[1] + yofs)*self.msy
                if not ( 0 <= xs <= w and 0 <= ys <= h ):
                    print("Pos out of range at {0}/{1} -- {2}".format(xs/self.msx,ys/self.msy,entity))
                    continue
                
                # highlight enemies and score tiles
                if isinstance(entity, Enemy):
                    for y in range(int(bb[3]+0.5) * self.msy):
                        for x in range(int(bb[2]+0.5) * self.msx):
                            if x%2 and y%2:
                                n = (w*(y+ys) + x+xs)*4
                                b[n:n+4] = col.r,col.g,col.b,col.a
                elif isinstance(entity, ScoreTile):
                    for y in range(int(bb[3]+0.5) * self.msy):
                        for x in range(int(bb[2]+0.5) * self.msx):
                            if x%2:
                                n = (w*(y+ys) + x+xs)*4
                                b[n:n+4] = col.r,col.g,col.b,col.a
                else:
                    for y in range(int(bb[3]+0.5) * self.msy):
                        for x in range(int(bb[2]+0.5) * self.msx):
                            n = (w*(y+ys) + x+xs)*4
                            b[n:n+4] = col.r,col.g,col.b,col.a
        
        self.minimap = sf.Image()
        self.minimap.LoadFromPixels(w,h, bytes(b))
        self.minimap_sprite,self.sw,self.sh,self.sx,self.sy = self._GetImg(self.minimap)
        
        # finally, construct the rectangle around the minimap
        self.minimap_shape = sf.Shape()
        bcol = sf.Color(0xcd,0x90,0x0,0xff)
        
        # interestingly, the 0.5px offset is not needed for
        # lines and other geometric shapes. Awesome.
        self.minimap_shape.AddPoint(self.sx,self.sy,bcol,bcol)
        self.minimap_shape.AddPoint(self.sx+self.sw,self.sy,bcol,bcol)
        self.minimap_shape.AddPoint(self.sx+self.sw,self.sy+self.sh,bcol,bcol)
        self.minimap_shape.AddPoint(self.sx,self.sy+self.sh,bcol,bcol)

        self.minimap_shape.SetOutlineWidth(3)
        self.minimap_shape.EnableFill(False)
        self.minimap_shape.EnableOutline(True)
    
    def Draw(self):
        Game.Draw(self)
        
        inp = Renderer.app.GetInput()
        self.mx,self.my = inp.GetMouseX(),inp.GetMouseY()

        # Nothing to do is no level is loaded
        if self.level:
            if self.level != getattr(self,"prev_level",None):
                
                self._BuildMiniMap()
                self.prev_level = self.level
                
            self._DrawEditor()
        
        
def main():
    """Main entry point to the editor application"""

    # Read game.txt, which is the master config file
    defaults.merge_config(sys.argv[1] if len(sys.argv)>1 else os.path.join(defaults.config_dir,"game.txt"))
    Log.Enable(defaults.enable_log)
    
    defaults.caption = "YIANG-ED 0.1"
    defaults.resolution[0] = 1450;
    defaults.resizable = True

    print("Startup ...")
    KeyMapping.LoadFromFile(os.path.join(defaults.config_dir,"key_bindings.txt"))

    Renderer.Initialize()
    
    # Perform dummy initializations of some subsystems which are
    # needed for running a Game, but are not necessarily
    # useful for the editor
    HighscoreManager.InitializeDummy()
    Achievements.InitializeDummy()
    BerlinerPhilharmoniker.InitializeDummy()
    
    # Run the game as usual but push the EditorOverlay on top of it
    game = EditorGame()
    game.LoadLevel(1)
    Renderer.AddDrawable(game)
    
    Renderer.DoLoop()
    Renderer.Terminate()
    

        
        
        
        
        
        
        