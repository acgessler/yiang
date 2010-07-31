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
from player import Player

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
        Renderer.AddDrawable((Button(text="+Life",rect=[-80,120,50,25]) + 
             ("release",(lambda src: self.AddLife()))
        ))
        Renderer.AddDrawable((Button(text="+1ct",rect=[-80,150,50,25]) + 
             ("release",(lambda src: self.Award(1.0)))
        ))
        
        def Resume():
                
            # Move the view origin that the player is visible
            if not self.IsGameRunning():
                for elem in self.level.EnumAllEntities():
                    if isinstance(elem, Player):
                        x,y = elem.pos
                        lx,ly = self.level.GetLevelVisibleSize()
                        ox,oy = self.level.GetOrigin()
                        if x < ox or x > ox+lx or y < oy or y > oy+ly:
                            self.level.SetOrigin((x-lx/2,y-ly/2))
                            break
                    
            self.PopSuspend()
        
        self.PushSuspend()
        Renderer.AddDrawable((ToggleButton(text="Suspend\x00Resume",on=False, rect=[-290,10,80,25]) +
             ("update", (lambda src: src.__setattr__("on",self.IsGameRunning()))) +
             ("off", (lambda src: self.PushSuspend())) +
             ("on",(lambda src: Resume())) 
        ))
            
        Renderer.AddDrawable((ToggleButton(text="Abandon God\x00Become God",on=defaults.debug_godmode, rect=[-400,10,100,25]) +
             ("update", (lambda src: src.__setattr__("on",defaults.debug_godmode))) +
             ("off", (lambda src: defaults.__setattr__("debug_godmode",False))) +
             ("on",(lambda src: defaults.__setattr__("debug_godmode",True))) 
        ))
        
        Renderer.AddDrawable((ToggleButton(text="Hide stats\x00Show stats",on=defaults.debug_godmode, rect=[-510,10,100,25]) +
             ("update", (lambda src: src.__setattr__("on",defaults.debug_draw_info))) +
             ("off", (lambda src: defaults.__setattr__("debug_draw_info",False))) +
             ("on",(lambda src: defaults.__setattr__("debug_draw_info",True))) 
        ))
        
        Renderer.AddDrawable((ToggleButton(text="Hide BBs\x00Show BBs",on=defaults.debug_draw_bounding_boxes, rect=[-620,10,100,25]) +
             ("update", (lambda src: src.__setattr__("on",defaults.debug_draw_bounding_boxes))) +
             ("off", (lambda src: defaults.__setattr__("debug_draw_bounding_boxes",False))) +
             ("on",(lambda src: defaults.__setattr__("debug_draw_bounding_boxes",True))) 
        ))
        
        Renderer.AddDrawable((ToggleButton(text="Disable PostFX\x00Enable PostFx",on=not defaults.no_ppfx, rect=[-730,10,100,25]) +
             ("update", (lambda src: src.__setattr__("on",not defaults.no_ppfx))) +
             ("off", (lambda src: defaults.__setattr__("no_ppfx",True))) +
             ("on",(lambda src: defaults.__setattr__("no_ppfx",False))) 
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
                        
                        self.ControlledAddEntity(cloned)
                    
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
        
    def ControlledAddEntity(self,entity):
        """Wrap entity add/remove functions to synchronize with our level table"""
        self.level.AddEntity(entity)
        print(entity)
        self._UpdateMiniMap(entity)
        
    def ControlledRemoveEntity(self,entity):
        """Wrap entity add/remove functions to synchronize with our level table"""
        self.level.RemoveEntity(entity)
        self._UpdateMiniMap(entity)
        
        
    def _UpdateMiniMap(self,entity):
        bb = entity.GetBoundingBox()
        self.dirty_area += bb[2]*bb[3] if bb else 1.0
        if self.dirty_area > 8.0: # choosen by trial and error
            self._GenMiniMapImage()
            self.dirty_area = 0.0
        
    def _DrawMiniMap(self):
        self.DrawSingle(self.minimap_sprite)
        self.DrawSingle(self.minimap_shape)
        
        # Adjust the origin according to the mouse position
        if self.sx+self.sw > self.mx > self.sx and self.sy+self.sh > self.my > self.sy:
            w,h = self.level.GetLevelVisibleSize()
            self.level.SetOrigin(((self.mx-self.sx)/self.msxp - w*0.5,(self.my-self.sy)/self.msyp -h*0.5))
            ox,oy = self.level.GetOrigin()
            
            # Suspend the game if we moved the player outside the visible scene
            for elem in self.level.EnumActiveEntities():
                if isinstance(elem, Player):
                    x,y = elem.pos
                    lx,ly = self.level.GetLevelVisibleSize()
                    if x < ox or x > ox+lx or y < oy or y > oy+ly:
                        if self.IsGameRunning():
                            self.PushSuspend()
                        break

        else:
            ox,oy = self.level.GetOrigin()
        
        # Draw the currently visible part of the map
        #print(ox,oy)
        oy += self.level.vis_ofs
        
        # slight adjustments for proper alignment with the outer border of the minimap
        self.minimap_visr.SetPosition(ox*self.msxp + self.sx - 2,oy*self.msyp + self.sy + 4)
        self.DrawSingle(self.minimap_visr)
        
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
    
    def _GenMiniMapImage(self):
        print("Update MiniMap image")
        w,h = self.level.GetLevelSize()
        yofs = self.level.vis_ofs
        
        # scale factors in both axes
        self.msx,self.msy = (12,9) if w < 100 else ((8,6) if w < 200 else ((4,3) if w < 250 and h < 250 else (1,1))) 
        w,h = w*self.msx,(h)*self.msy
        b = bytearray(b'\x30\x30\x30\xa0') * (w*h)
        
        for entity in sorted( self.level.EnumAllEntities(), key=lambda x:x.GetDrawOrder() ):
            
            if isinstance(entity, Player):
                continue
            
            bb = entity.GetBoundingBox()
            if bb:
                col = entity.color
                
                xs,ys = int(bb[0])*self.msx, int(bb[1] + yofs)*self.msy
                if not ( 0 <= xs <= w and 0 <= ys <= h ):
                    print("Pos out of range at {0}/{1} -- {2}".format(xs/self.msx,ys/self.msy,entity))
                    continue
                
                # highlight enemies ...
                if isinstance(entity, Enemy):
                    for y in range(int(bb[3]+0.5) * self.msy):
                        for x in range(int(bb[2]+0.5) * self.msx):
                            if x%2 and y%2:
                                n = (w*(y+ys) + x+xs)*4
                                b[n:n+4] = col.r*col.a//0xff,col.g*col.a//0xff,col.b*col.a//0xff,0xff
                                
                # .. and score tiles
                elif isinstance(entity, ScoreTile):
                    for y in range(int(bb[3]+0.5) * self.msy):
                        for x in range(int(bb[2]+0.5) * self.msx):
                            if x%2:
                                n = (w*(y+ys) + x+xs)*4
                                b[n:n+4] = col.r*col.a//0xff,col.g*col.a//0xff,col.b*col.a//0xff,0xff
                
                # for invisible tiles, draw only the edges and make them opaque
                elif col.a < 10:
                    for y in range(int(bb[3]+0.5) * self.msy):
                        for x in (0,int(bb[2]+0.5) * self.msx):
                            n = (w*(y+ys) + x+xs)*4
                            b[n:n+4] = col.r,col.g,col.b,0xff
                    for y in (0,int(bb[3]+0.5) * self.msy):
                        for x in range(int(bb[2]+0.5) * self.msx):
                            n = (w*(y+ys) + x+xs)*4
                            b[n:n+4] = col.r,col.g,col.b,0xff
                            
                # draw all others according to their color and bounding boxes
                # entities with low draw order are assumed to be background 
                # tiles which are drawn with low intensity (most background
                # tiles are huge, and we want to avoid huge solid rectangles
                # on the minimap which would confuse the user)
                else:      
                    ascale = 1.0 if entity.GetDrawOrder() > 0 else 0.1
                    for y in range(int(bb[3]+0.5) * self.msy):
                        for x in range(int(bb[2]+0.5) * self.msx):
                            n = (w*(y+ys) + x+xs)*4
                            b[n:n+4] = int(col.r*ascale)*col.a//0xff,int(col.g*ascale)*col.a//0xff,int(col.b*ascale)*col.a//0xff,0xff
        
        self.minimap = sf.Image()
        self.minimap.LoadFromPixels(w,h, bytes(b))
        
    def _BuildMiniMap(self):
        # First, create the image and generate its contents
        self._GenMiniMapImage()
        
        self.minimap_sprite,self.sw,self.sh,self.sx,self.sy = self._GetImg(self.minimap)
        
        # msxp is the scaling factor to get from tiles to destination (backbuffer) pixels 
        self.msxp,self.msyp = (self.sw/self.minimap.GetWidth())*self.msx,(self.sh/self.minimap.GetHeight())*self.msy
        
        # Then construct the rectangle around the minimap
        self.minimap_shape = self._GenRectangularShape(self.sx-3,self.sy-3,self.sw,self.sh,sf.Color(0xcd,0x90,0x0,0xff))
        self.minimap_shape.SetOutlineWidth(3)
        self.minimap_shape.EnableFill(False)
        self.minimap_shape.EnableOutline(True)
        
        # ... and prepare the visible rectangle
        self._PrepareMiniMapVisibleRect()
        
    def _PrepareMiniMapVisibleRect(self):
        w,h = self.level.GetLevelVisibleSize()

        self.minimap_visr = self._GenRectangularShape(0,0, w*self.msxp, h*self.msyp,sf.Color(0xff,0xff,0xff,0x50))
        self.minimap_visr.EnableFill(True)
        self.minimap_visr.EnableOutline(False)
        
    def _GenRectangularShape(self,sx,sy,sw,sh,bcol):
        sx,sy,sw,sh = math.floor(sx+0.5),math.floor(sy+0.5),math.floor(sw+0.5),math.floor(sh+0.5)
        shape = sf.Shape()
        bcol = bcol or sf.Color(0xcd,0x90,0x0,0xff)
        
        # interestingly, the 0.5px offset is not needed for
        # lines and other geometric shapes. Awesome.
        shape.AddPoint(sx,sy,bcol,bcol)
        shape.AddPoint(sx+sw,sy,bcol,bcol)
        shape.AddPoint(sx+sw,sy+sh,bcol,bcol)
        shape.AddPoint(sx,sy+sh,bcol,bcol)
        return shape
    
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
            
    def OnChangeResolution(self,newres):
        # needed because the visible part of the map has changed
        if self.level:
            self._BuildMiniMap()
        
        
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
    

        
        
        
        
        
        
        