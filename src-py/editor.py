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

# Our stuff
import defaults

from fonts import FontCache
from keys import KeyMapping
from game import Game
from log import Log
from renderer import Renderer,Drawable,NewFrame
from highscore import HighscoreManager
from audio import BerlinerPhilharmoniker
from achievements import Achievements

class EditorGame(Game):
    """Special game implementation for the editor"""

    def __init__(self):
        Game.__init__(self,mode=Game.EDITOR,undecorated=True)
        self.cursor_img  = sf.Image()
        self.cursor_img.LoadFromFile(os.path.join(defaults.data_dir,"textures","cursor.png"))
        
        self.cursor = sf.Sprite(self.cursor_img)
        Renderer.app.ShowMouseCursor(False)
        
        self.selection = []
        self.template = dict()
        self.in_select = False
        self.select_start = None
            
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
        assert hasattr(which,"editor_shebang")
        
        tempdict = dict(locals())
        try:
            exec(which.editor_shebang,globals(),tempdict)
        except:
            assert False
            
        t = tempdict['entity']
        t.SetLevel(self.level)
        t.SetColor(which.color)
        return t
    
    def Draw(self):
        Game.Draw(self)
        
        inp = Renderer.app.GetInput()
        mx,my = inp.GetMouseX(),inp.GetMouseY()

        w,h =self.cursor_img.GetWidth(),self.cursor_img.GetHeight()        
        #if not (w/2.0 < mx < defaults.resolution[0]-w/2.0) or not (h/2.0 < my < defaults.resolution[1]-h/2.0):
        #    return

        self.cursor.SetPosition(mx-w/2.0,my-h/2.0)
        Renderer.app.Draw(self.cursor)

        if not self.level:
            return
        
        self.level.SetDistortionParams((100,0,0))   
        # store the mouse position for later use
        self.mx,self.my = mx,my
        
        # get from mouse to tile coordinates
        # (XXX) put this into a nice function or so --- :-)
        offset = self.level.GetOrigin()
        self.tx,self.ty = (mx/defaults.tiles_size_px[0] + offset[0],
            my/defaults.tiles_size_px[1]-self.level.vis_ofs - 0.5)
        
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
            # no entity below the cursor, highlight nearest point 
            self._DrawRectangle((fx,fy,1.0,1.0),sf.Color(150,150,150))
            
        if inp.IsMouseButtonDown(sf.Mouse.Right):
            if inp.IsMouseButtonDown(sf.Mouse.Left):
                # Both mouse buttons pressed, delete template
                for entity,pos in self.template.items():
                    self.level.RemoveEntity(entity)
                    
                self.template = dict()
                raise NewFrame()
            
            # copy current tile
            if "entity" in locals(): 
                if self.in_select is False:
                    if self.select_start is None or not inp.IsKeyDown(sf.Key.LShift):
                        self.template = dict()
                        self.select_start = fx,fy
                        
                    self.in_select = True
                    
                if inp.IsKeyDown(sf.Key.LControl):
                    for y in range(self.select_start[1],fy+1):
                        for x in range(self.select_start[0],fx+1):
                            for e in self.level.EnumEntitiesAt((x+0.5,y+0.5)):
                                self.template[e] = None                                
                    
                else:
                    self.template[entity] = None
                                
        else:
            self.in_select = False
            
        if inp.IsMouseButtonDown(sf.Mouse.Left):
            if not hasattr(self,"pressed_l"):
                # Insert template at this position
                assert self.select_start
                for entity,pos in self.template.items():
                    cloned = self._CloneEntity(entity)
                    cloned.SetPosition((math.floor(self.tx) + entity.pos[0]-self.select_start[0],
                        math.floor(self.ty) + entity.pos[1]-self.select_start[1])
                    )
                    self.level.AddEntity(cloned)
                    
                self.pressed_l = True
        else:
            try:
                delattr(self,"pressed_l")  
            except AttributeError:
                pass
        
        for entity,pos in self.template.items():
            self._DrawRectangle(entity.GetBoundingBox(),sf.Color.Red)
            
        
def main():
    """Main entry point to the editor application"""

    # Read game.txt, which is the master config file
    defaults.merge_config(sys.argv[1] if len(sys.argv)>1 else os.path.join(defaults.config_dir,"game.txt"))
    Log.Enable(defaults.enable_log)

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
    

        
        
        
        
        
        
        