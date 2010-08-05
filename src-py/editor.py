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
import itertools
import collections

# Our stuff
import defaults


# Note: some of these imports are only needed because they might be implicitly
# referenced by shebang lines in one of the tiles 
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
from keys import KeyMapping
from tile import Tile,AnimTile,TileLoader

from minigui import Component, Button, ToggleButton, GUIManager

def override(x):
    return x

class EditorCursor(Drawable):
    """Draws the cursor on top of the whole scenery"""
    
    def __init__(self):
        Drawable.__init__(self)
        
        self.cursor_img  = sf.Image()
        self.cursor_img.LoadFromFile(os.path.join(defaults.data_dir,"textures","cursor.png"))
        
        self.cursor = sf.Sprite(self.cursor_img)
        Renderer.app.ShowMouseCursor(False)
        
    @override 
    def GetDrawOrder(self):
        return 100000
    
    @override 
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
        self.actions = [] # undo/redo stack
        self.cur_action = 0 # Location in the stack
        self.overlays = [] # each overlay is a simple callable called during rendering
        self.save_counter = 0
        
        self.inp = Renderer.app.GetInput()
        
        Renderer.AddDrawable(EditorCursor())
        
        def GrabPlayer():
            for elem in self.level.EnumAllEntities():
                if isinstance(elem, Player):
                    
                    self.ReplaceSelection([elem])
                    
                    # (Hack): the fact that this entity is no
                    # longer in the scene ensures that this
                    # instance will be reused, thus the current
                    # inventory is kept.
                    self.ControlledRemoveEntity(elem)
                    print("Remove existing player but add it to the selection template")
                    break
            else:
                print("Didn't find a player, add one first!")
                
        def AskRestartLevel():
            if not self.UnsavedChanges():
                self.RestartLevel()
                return
                
            accepted = (KeyMapping.Get("accept"),KeyMapping.Get("level-new"),KeyMapping.Get("escape"))
            def on_close(key):
                if key == accepted[2]:
                    self.swallow_escape = False
                    return
                if key == accepted[0]:
                    self.Save()
                self.RestartLevel()
                
            self.swallow_escape = True # Hack to prevent Escape from being triggered again
            self._FadeOutAndShowStatusNotice(_("""Don't you want to save first?
    
    Press {0} to save first and reload then
    Press {1} to reload immediately, without saving 
    Press {2} to abort""").format(
                        KeyMapping.GetString("accept"),
                        KeyMapping.GetString("level-new"),
                        KeyMapping.GetString("escape")),
                defaults.game_over_fade_time,(560,130),0.0,accepted,sf.Color.Green,on_close)
        
        # Setup basic GUI buttons
        self.AddSlaveDrawable((Button(text="Reload",rect=[-200,10,80,25]) + 
             ("release",(lambda src: AskRestartLevel()))
        ))
        self.AddSlaveDrawable((Button(text="Kill",rect=[-110,10,80,25]) + 
             ("release",(lambda src: self.Kill("(Kill button)")))
        ))
        
        """
        self.AddSlaveDrawable((Button(text="+Life",rect=[-80,120,50,25]) + 
             ("release",(lambda src: self.AddLife()))
        ))
        
        # Right side bar
        self.AddSlaveDrawable((Button(text="+1ct",rect=[-80,150,50,25]) + 
             ("release",(lambda src: self.Award(1.0)))
        ))
        self.AddSlaveDrawable((Button(text="Move PL",rect=[-80,180,50,25]) + 
             ("release",(lambda src: GrabPlayer()))
        ))
        """
        
        def UpdateUndoState(gui):
            gui.disabled = self.cur_action==0
            
        def UpdateRedoState(gui):
            gui.disabled = self.cur_action>=len(self.actions)
        
        # Upper left / general editor functionality
        self.AddSlaveDrawable((Button(text="Leave", rect=[30, 10, 60, 25]) + 
              ("release", (lambda src: self._OnEscape()))
        ))
        self.AddSlaveDrawable((Button(text="Save", rect=[100, 10, 60, 25]) + 
		      ("release", (lambda src: self.Save()))
        ))
        self.AddSlaveDrawable((Button(text="Undo", rect=[200, 10, 50, 25]) + 
              ("update",  (lambda src: UpdateUndoState(src))) +
		      ("release", (lambda src: self.Undo()))
        ))
        self.AddSlaveDrawable((Button(text="Redo", rect=[260, 10, 50, 25]) + 
              ("update",  (lambda src: UpdateRedoState(src))) +
		      ("release", (lambda src: self.Redo()))
        ))
        
        #self.AddSlaveDrawable((Button(text="+",rect=[-80,210,50,25]) + 
        #     ("release",(lambda src: self.AddColumn( -1, 1 )))
        #))
        
        
        def EditSettings():
            pass
        
        self.AddSlaveDrawable((Button(text="Edit Level Settings", rect=[350, 10, 150, 25]) + 
              ("release", (lambda src: EditSettings()))
        ))
        
        def Resume():
            # Move the view origin that the player is visible
            if self.IsEditorRunning():
                for elem in self.level.EnumAllEntities():
                    if isinstance(elem, Player):
                        from level import Level
                        
                        x,y = elem.pos
                        lx,ly = self.level.GetLevelVisibleSize()
                        ox,oy = self.level.GetOrigin()
                        
                        # sanity border ...
                        sanity = 8
                        ox += sanity if self.level.scroll[-1] & Level.SCROLL_LEFT else 0
                        oy += sanity if self.level.scroll[-1] & Level.SCROLL_TOP  else 0
                        
                        lx -= sanity*2 if self.level.scroll[-1] & Level.SCROLL_RIGHT  else 0
                        ly -= sanity*2 if self.level.scroll[-1] & Level.SCROLL_BOTTOM else 0
                        
                        if x < ox or x > ox+lx or y < oy or y > oy+ly:
                            lx,ly = self.level.GetLevelVisibleSize()
                            self.level.SetOrigin((x-lx/2,y-ly/2))
                            print(".. change origin to set the player free")
                            break
                    
            self.EditorPopSuspend()
        
        self.PushSuspend()
        self.AddSlaveDrawable((ToggleButton(text="Suspend\x00Resume",on=False, rect=[-290,10,80,25]) +
             ("update", (lambda src: src.__setattr__("on",not self.IsEditorRunning()))) +
             ("off", (lambda src: self.EditorPushSuspend())) +
             ("on",(lambda src: Resume())) 
        ))
            
        self.AddSlaveDrawable((ToggleButton(text="Abandon God\x00Become God",on=defaults.debug_godmode, rect=[-400,10,100,25]) +
             ("update", (lambda src: src.__setattr__("on",defaults.debug_godmode))) +
             ("off", (lambda src: defaults.__setattr__("debug_godmode",False))) +
             ("on",(lambda src: defaults.__setattr__("debug_godmode",True))) 
        ))
        
        self.AddSlaveDrawable((ToggleButton(text="Hide stats\x00Show stats",on=defaults.debug_godmode, rect=[-510,10,100,25]) +
             ("update", (lambda src: src.__setattr__("on",defaults.debug_draw_info))) +
             ("off", (lambda src: defaults.__setattr__("debug_draw_info",False))) +
             ("on",(lambda src: defaults.__setattr__("debug_draw_info",True))) 
        ))
        
        self.AddSlaveDrawable((ToggleButton(text="Hide BBs\x00Show BBs",on=defaults.debug_draw_bounding_boxes, rect=[-620,10,100,25]) +
             ("update", (lambda src: src.__setattr__("on",defaults.debug_draw_bounding_boxes))) +
             ("off", (lambda src: defaults.__setattr__("debug_draw_bounding_boxes",False))) +
             ("on",(lambda src: defaults.__setattr__("debug_draw_bounding_boxes",True))) 
        ))
        
        self.AddSlaveDrawable((ToggleButton(text="Disable PostFX\x00Enable PostFx",on=not defaults.no_ppfx, rect=[-730,10,100,25]) +
             ("update", (lambda src: src.__setattr__("on",not defaults.no_ppfx))) +
             ("off", (lambda src: defaults.__setattr__("no_ppfx",True))) +
             ("on",(lambda src: defaults.__setattr__("no_ppfx",False))) 
        ))
        
        
        class Overlay_ShowCatalogue:
            def __str__(self):
                return "<ShowCatalogue - show the tile catalogue on top of the editor>"
            
            def __call__(self2):
                pass
            
            
        class Overlay_ShowColorMenu:
            
            def __str__(self):
                return "<ShowColorMenu - show the current color palette>"
            
            def __init__(self2):
    
                self2.x,self2.y = self.fx,self.fy
                
                if hasattr(self,"template") and self.template:
                    self2.entities = list(self.template.keys())
                    
                elif hasattr(self,"cur_entity") and self.cur_entity:
                    self2.entities = [self.cur_entity]
        
                else:
                    self2.entities = []
                    
                ox,oy = self.level.GetOrigin()
                
                w,h = 64,64
                space = 5
                
                #
                xb = -w*0.5
                xb = xb+(self.tx-ox)*defaults.tiles_size_px[0] 
                
                yb = -h*0.5
                yb = yb+(self.ty-oy)*defaults.tiles_size_px[1] 
                
                from tile import TileLoader
                colors = TileLoader.cached_color_dict
                
                self2.elements = []
                old_color = dict((e,e.color) for e in self2.entities)
                
                def SetColor(color,sticky=False):
                    if not sticky:
                        for entity in self2.entities:
                            entity.SetColor(color)
                        return
                    
                    with self.BeginTransaction() as transaction:
                        for entity in self2.entities:
                                
                            # In order for undo/redo to work, we must ensure that
                            # the entity is temporarily reset to its old color
                            # before we commit the operation.
                            
                            entity.color = old_color[entity]
                            self.ControlledSetEntityColor(entity,color)
                            
                            # Needed or the 'mouse_leave' callback will overwrite our changes
                            old_color[entity] = color
                            
                def SetOldColor():
                    for entity in self2.entities:
                        entity.SetColor(old_color[entity])
        
                def AddNewColor():
                    pass
                    # TODO
                    
                def ChangeElementDrawOrder(order):
                    for e in self2.elements:
                        e.GetDrawOrder = lambda :order
                
                extra_items = 2
                gap = 2
                for rad in itertools.count():
                    if (rad*2-2)**2 - (gap)**2 >= len(colors)+extra_items:
                        break
                
                gaps = [n for n in range(-gap+1,gap-1)]
                src  = (((x+0.5)*(w+space),(y+0.5)*(h+space)) for x in range(-rad+1,rad-1) for y in range(-rad+1,rad-1) 
                        if not x in gaps or not y in gaps)
                
                try:
                    for code,color in colors.items():
                        x,y = next(src)
                        self2.elements.append(Button(text="{0:X}\n{1:X}\n{2:X}\n{3:X}".format(color.r,color.g,color.b,color.a), 
                            bgcolor=color, 
                            fgcolor=sf.Color.White if color.r+color.g+color.b < 500 else sf.Color.Black,
                            rect=[xb+x,yb+y,w,h]) + 
                            ("release",     (lambda src,color=color: SetColor(color,True))) +
                            ("mouse_enter", (lambda src,color=color: SetColor(color))) +
                            ("mouse_leave", (lambda src: SetOldColor()))
                        )
                    x,y = next(src)
                    self2.elements.append(Button(text="New", rect=[xb+x,yb+y,w,h]) + 
                        ("release",     (lambda src: AddNewColor()))
                    )
                    x,y = next(src)
                    self2.elements.append(ToggleButton(text="Undim\x00Dim", rect=[xb+x,yb+y,w,h]) + 
                        ("on",     (lambda src: ChangeElementDrawOrder(self.GetDrawOrder()-1))) +
                        ("off",    (lambda src: ChangeElementDrawOrder(Component.GetDrawOrder(self2.elements))))
                    )
                except StopIteration:
                    # corner case, no more space left in the rondell
                    pass
                    
                for e in self2.elements:
                    self.AddSlaveDrawable(e)
                
            def _RemoveMe(self2):
                self.RemoveOverlay(self2)
                for e in self2.elements:
                    self.RemoveSlaveDrawable(e)
            
            def __call__(self2):
                inp = self.inp
                if not inp.IsKeyDown(sf.Key.C):
                    self2._RemoveMe()
                    
                # Draw the origin tile in blue 
                for e in self2.entities:
                    bb = e.GetBoundingBox()
                    if bb:
                        self._DrawRectangle(bb,sf.Color(0,0,255))
        
        
        class Overlay_ShowContextMenu(Drawable):
            
            def __str__(self):
                return "<ShowContectMenu - show the context menu accessible on the I key>"
            
            def __init__(self2):
                Drawable.__init__(self2)
                self.AddSlaveDrawable(self2)
                
                # Store the currently selected tile, it will be
                # our future origin for all operations, even
                # if the user moves the mouse further (which
                # is unavoidable, because we're going to present
                # him/her a few neat new buttons)
                self2.x,self2.y = self.fx,self.fy
                
                if hasattr(self,"template") and self.template:
                    self2.entities = list(self.template.keys())
                    
                elif hasattr(self,"cur_entity") and self.cur_entity:
                    self2.entities = [self.cur_entity]
        
                else:
                    self2.entities = []
                
                ox,oy = self.level.GetOrigin()
                
                xb = 40, -242, -100, -100
                xb = [x+(self.tx-ox)*defaults.tiles_size_px[0] for x in xb]
                
                yb = 0, 0, -120, +70
                yb = [y+(self.ty-oy)*defaults.tiles_size_px[1] for y in yb]
                
                
                def PlacePlayerHere():
                    for elem in self.level.EnumAllEntities():
                        if isinstance(elem, Player):
                            self.ControlledSetEntityPosition(elem,(self2.x,self2.y))
                            break
                    else:
                        print("Could not find a valid player, creating one!")
                        PlaceEntity("_PL")
                    
                def DeleteThisTile():
                    with self.BeginTransaction() as transaction:
                        for e in self2.entities:
                            self.ControlledRemoveEntity(e)
                                              
                    # break the overlay chain, we need a new frame for
                    # the pending deletion to be dispatched to all
                    # who need to know about it. This is a bit of a
                    # design issue, but it's rooted too deep to solve
                    # it this nevel.
                    raise NewFrame()
                    
                    
                yguiofs,yguisize,xguisize = 27,20,190
                
                self2.elements = [
                    (Button(text="Insert rows(s) here", 
                        rect=[xb[2],yb[2],xguisize,yguisize],fgcolor=sf.Color.Green) + 
                        ("release", (lambda src: self.ControlledExpandLevel(1,self2.x,1)))
                    ),
                    
                    (Button(text="Delete rows(s) here", 
                        rect=[xb[2],yb[2]+yguiofs,xguisize,yguisize],fgcolor=sf.Color.Red) +                         
                        ("release", (lambda src: self.ControlledShrinkLevel(1,self2.x,1)))
                    ),
                    
                    (Button(text="Insert rows(s) here", 
                        rect=[xb[3],yb[3],xguisize,yguisize],fgcolor=sf.Color.Green) +                        
                        ("release", (lambda src: self.ControlledExpandLevel(1,self2.x-1,1)))
                    ),
                    
                    (Button(text="Delete rows(s) here", 
                        rect=[xb[3],yb[3]+yguiofs,xguisize,yguisize],fgcolor=sf.Color.Red) +                       
                        ("release", (lambda src: self.ControlledShrinkLevel(1,self2.x-1,1)))
                    ),
                    
                    
                    
                    (Button(text="Insert column(s) here", 
                        rect=[xb[0],yb[0],xguisize,yguisize],fgcolor=sf.Color.Green) +                         
                        ("release", (lambda src: self.ControlledExpandLevel(0,self2.x,1)))
                    ),
                    
                    (Button(text="Delete column(s) here", 
                        rect=[xb[0],yb[0]+yguiofs,xguisize,yguisize],fgcolor=sf.Color.Red) +                         
                        ("release", (lambda src: self.ControlledShrinkLevel(0,self2.x,1)))
                    ),         
                    
                    (Button(text="Insert column(s) here", 
                        rect=[xb[1],yb[1],xguisize,yguisize],fgcolor=sf.Color.Green) +                         
                        ("release", (lambda src: self.ControlledExpandLevel(0,self2.x,1)))
                    ),       
                    
                    (Button(text="Delete column(s) here", 
                        rect=[xb[1],yb[1]+yguiofs,xguisize,yguisize],fgcolor=sf.Color.Red) +                        
                        ("release", (lambda src: self.ControlledShrinkLevel(0,self2.x,1)))
                    ),
                ]
                
                # Add special context-specific items
                yn = 80
                if len(self2.entities):
                    self2.elements.append(Button(text="Delete this tile(s)", rect=[xb[3],yb[3]+yn,xguisize,yguisize],fgcolor=sf.Color.Red) + 
                        ("release", (lambda src: DeleteThisTile()))
                    )
                    yn += yguiofs
                        
                else:
                    self2.elements.append(Button(text="Place player here", 
                        rect=[xb[3],yb[3]+yn,xguisize,yguisize]) + 
                        
                        ("release", (lambda src: PlacePlayerHere()))
                    )
                    yn += yguiofs   
                                    
                    self2.elements.append(Button(text="Place respawn line here", 
                        rect=[xb[3],yb[3]+yn,xguisize,yguisize]) + 
                        
                        ("release", (lambda src: self._PlaceEntity("_RE",(self2.x,self2.y))))
                    )
                    yn += yguiofs 
                                      
                    self2.elements.append(Button(text="Place respawn point here", 
                        rect=[xb[3],yb[3]+yn,xguisize,yguisize]) + 
                        
                        ("release", (lambda src: self._PlaceEntity("_RD",(self2.x,self2.y))))
                    )
                    yn += yguiofs
                    
                # Load more context-specific actions from the editoractions registry
                import editoractions
                handlers = editoractions.GetHandlers()
                
                for h in handlers:
                    
                    match = [e for c in h.GetClasses() for e in self2.entities if isinstance(e, c)]
                    if match:
                        hh = h(self)
                        hh(match)
                        
                        for elem in hh.elements:
                            elem.rect=[xb[3],yb[3]+yn,xguisize,yguisize]
                            
                            self2.elements.append(elem)
                            yn += yguiofs
                
                rx,ry = defaults.resolution
                for e in self2.elements:
                    
                    # Always place the GUI elements at a place where no clipping is needed
                    if e.x+e.w > rx:
                        e.x = 5+e.x-self2.x
                        
                    if e.y+e.h > ry:
                        e.y = 5+e.y-self2.y
                        
                    #if e.y < defaults.status_bar_top_tiles*defaults.tiles_size_px[1]:
                    #    e.y += defaults.status_bar_top_tiles*defaults.tiles_size_px[1]
                    
                    e.draworder = 52000
                    self.AddSlaveDrawable(e)
            
            def _RemoveMe(self2):
                self.RemoveOverlay(self2)
                for e in self2.elements:
                    self.RemoveSlaveDrawable(e)
                    
                self.RemoveSlaveDrawable(self2)
            
            def __call__(self2):
                inp = self.inp
                if not inp.IsKeyDown(sf.Key.I):
                    self2._RemoveMe()
                    
                # Draw the origin tile in blue 
                for e in self2.entities:
                    bb = e.GetBoundingBox()
                    if bb:
                        self._DrawRectangle(bb,sf.Color(0,0,255))
                    
            def GetDrawOrder(self):
                return -100
                    
            def Draw(self2):
                # Draw the grid before postprocessing and regular drawing occurs   
                r = 9
                e = ((x,y) for y in range(-r+1,r) for x in range(-r+1,r) if x or y)
                for x,y in e:
                    c = int(50 - (x**2 + y**2)**0.5 * (0.5/r) * 50)
                    if c <= 10:
                        continue
                    self._DrawRectangle((self2.x+x,self2.y+y,1.0,1.0),sf.Color(c,c,c),thickness=1)
                    
            
        
        class Overlay_ShowMinimap(Drawable):
            
            def __init__(self2):
                Drawable.__init__(self2)
                self.AddSlaveDrawable(self2)
            
            def __str__(self):
                return "<ShowMinimap - renders the minimap on top of the editor>"
            
            def __call__(self2):
                inp = self.inp
                if not inp.IsKeyDown(sf.Key.M):
                    self.RemoveOverlay(self2)
                    self.RemoveSlaveDrawable(self2)
                
            def GetDrawOrder(self):
                return 52000
                
            def Draw(self2):
                self._DrawMiniMap()
                    
                    
        class Overlay_EditorInsert:
            def __str__(self):
                return "<EditorInsert overlay - implements the insertion functionality>"
            
            def __call__(self2):
                inp = self.inp
                if inp.IsMouseButtonDown(sf.Mouse.Left):
                    if not self.mousepos_covered_by_gui:
                        if not hasattr(self,"pressed_l") or self.last_insert_pos[0]-self.fx or self.last_insert_pos[1]-self.fy:
                            # Insert template at this position
                            if self.select_start:
                                with self.BeginTransaction() as transaction:
                                    for e,pos in self.template.items():
                                        cloned = self._CloneEntity(e)
                                        if not cloned:
                                            continue
                                        cloned.SetPosition((self.fx + e.pos[0]-self.select_start[0],
                                            self.fy + e.pos[1]-self.select_start[1])
                                        )
                                        
                                        self.ControlledAddEntity(cloned)
                                
                            self.pressed_l = True
                            self.last_insert_pos = self.fx,self.fy
                else:
                    try:
                        delattr(self,"pressed_l")  
                    except AttributeError:
                        pass
                
            
        class Overlay_EditorDelete:
            def __str__(self):
                return "<EditorDelete overlay - implements the entity deletion logic>"
            
            def __call__(self2):
                inp = self.inp
                if inp.IsMouseButtonDown(sf.Mouse.Right):
                    if inp.IsMouseButtonDown(sf.Mouse.Left):
                        if not self.mousepos_covered_by_gui:
                            # Both mouse buttons pressed, delete template
                            for entity,pos in self.template.items():
                                self.ControlledRemoveEntity(entity)
                                
                            self.template = dict()
                            
                            # break the overlay chain, we need a new frame for
                            # the pending deletion to be dispatched to all
                            # who need to know about it.
                            raise NewFrame()
                    
                    
        class Overlay_EditorSelect:
            def __str__(self):
                return "<EditorSelect overlay - implements the entity selection logic>"
            
            def __call__(self2):
                inp = self.inp
                if inp.IsMouseButtonDown(sf.Mouse.Right):
                    if not self.mousepos_covered_by_gui:
                        # copy current tile
                        if self.in_select is False:
                            if self.select_start is None or not inp.IsKeyDown(sf.Key.LShift):
                                self.template = dict()
                                self.select_start = self.fx,self.fy
                                
                            self.in_select = True
                            
                        if inp.IsKeyDown(sf.Key.LControl):
                            if not hasattr(self,"last_select") or abs(self.last_select[0]-self.fx)>1 or abs(self.last_select[1]-self.fy)>1:
                                if not hasattr(self,"last_select"):
                                    self.last_select = self.select_start
                                
                                for y in range(self.select_start[1],self.fy+1,1) if self.fy >= self.select_start[1] else range(self.select_start[1],self.fy-1,-1):
                                    for x in range(self.last_select[0],self.fx+1,1) if self.fx >= self.last_select[0] else range(self.last_select[0],self.fx-1,-1):
                                        for e in self.level.EnumEntitiesAt((x+0.5,y+0.5)):
                                            self.template[e] = None  
                                            
                                for y in range(self.last_select[1],self.fy+1,1) if self.fy >= self.last_select[1] else range(self.last_select[1],self.fy-1,-1):
                                    for x in range(self.select_start[0],self.fx+1,1) if self.fx >= self.select_start[0] else range(self.select_start[0],self.fx-1,-1):
                                        for e in self.level.EnumEntitiesAt((x+0.5,y+0.5)):
                                            self.template[e] = None                               
                                
                                self.last_select = self.fx,self.fy
                            
                        else:
                            if hasattr(self,"cur_entity"): 
                                self.template[self.cur_entity] = None
                else:
                    self.in_select = False
                    
        
        class Overlay_EditorBasics:
            def __str__(self):
                return "<EditorBasics overlay - implements item highlighting and acts as overlay manager>"
            
            def __call__(self2):
                inp = self.inp
                # check if there's an entity right here and show its bounding box in white.
                # if there are multiple entities, take the one with the highest 
                # drawing order.
                try:
                    self.cur_entity = self.last_entity = sorted(self.level.EnumEntitiesAt((self.tx,self.ty)),
                        key=lambda x:x.GetDrawOrder(),reverse=True
                    )[0]
                    bb = self.cur_entity.GetBoundingBox()
                                    
                    self._DrawRectangle(bb,sf.Color.Green)
                    self.selection = [self.cur_entity]
                        
                except IndexError:
                    # no entity below the cursor, highlight the nearest point and its surroundings
                    self._DrawRectangle((self.fx,self.fy,1.0,1.0),sf.Color(150,150,150))
                    try:
                        delattr(self,"cur_entity")
                    except AttributeError:
                        pass
                    # disabled, turns out to be too expensive
                    #e = ((x,y) for y in range(-3,4) for x in range(-3,4) if x or y)
                    #for x,y in e:
                    #    c = int(50 - (x**2 + y**2)**0.5 *0.20 * 50)
                    #    self._DrawRectangle((fx+x,fy+y,1.0,1.0),sf.Color(c,c,c))
                    
                if inp.IsMouseButtonDown(sf.Mouse.Right) and not self.mousepos_covered_by_gui:               
                     if inp.IsKeyDown(sf.Key.LControl) and self.select_start:
                        # draw selection rectangle
                        self._DrawRectangle((self.select_start[0],self.select_start[1],
                            self.tx-self.select_start[0],
                            self.ty-self.select_start[1]), sf.Color.Yellow)
                                        
                for e,pos in self.template.items():
                    bb = e.GetBoundingBox()
                    self._DrawRectangle(bb,sf.Color.Red)
                    
                    if not "entity" in locals() or not entity in self.template:
                        self._DrawRectangle((self.fx + e.pos[0]-self.select_start[0],
                            self.fy + e.pos[1]-self.select_start[1],bb[2],bb[3]),sf.Color(40,0,0))
                        
                # Activate the 'DrawMinimap' overlay on M
                if inp.IsKeyDown(sf.Key.M) and not [e for e in self.overlays 
                    if not hasattr(e,"__class__") or e.__class__== Overlay_ShowMinimap]:
                        
                    self.PushOverlay(Overlay_ShowMinimap())
                    
                # Activate the 'DrawContextMenu' overlay on I
                if inp.IsKeyDown(sf.Key.I) and not [e for e in self.overlays 
                    if not hasattr(e,"__class__") or e.__class__== Overlay_ShowContextMenu]:
                        
                    self.PushOverlay(Overlay_ShowContextMenu())
                    
                # Activate the 'DrawColorMenu' overlay on I
                if inp.IsKeyDown(sf.Key.C) and not [e for e in self.overlays 
                    if not hasattr(e,"__class__") or e.__class__== Overlay_ShowColorMenu]\
                    and hasattr(self,"last_entity"):
                        
                    self.PushOverlay(Overlay_ShowColorMenu())
                    
                
        # note: order matters, don't change
        self.PushOverlay(Overlay_EditorBasics())
        self.PushOverlay(Overlay_EditorInsert())
        self.PushOverlay(Overlay_EditorDelete())
        self.PushOverlay(Overlay_EditorSelect())
        
    def _PlaceEntity(self,codename,pos):
        elem = self._LoadTileFromTag(codename)
        
        elem.SetPosition(pos)
        self.ControlledAddEntity(elem)
        return elem
        
    def _SelectEntity(self,codename,pos):
        elem = self._LoadTileFromTag(codename) if isinstance(codename,str) else codename
        elem.SetPosition(pos)
            
        assert isinstance(elem,Entity)
        self._ReplaceSelection([elem])
        return elem
         
    def EditorPushSuspend(self):
        
        # Walk through all entities present in the captured scene
        # and check if they changed their position or color.
        # Restore the previous values and re-add those entities
        # which have been entirely removed.
        if len(self.suspended)==0 and self.level:
            assert hasattr(self,"capture")
            
            entities = set(self.level.EnumAllEntities())
            for elem,oldstate in self.capture.items():
                if not elem in entities:
                    self.level.AddEntity(elem)
                    
                # SetPosition() triggers lengthy updates, so avoid calling it for nothing
                if elem.pos != oldstate[0]:
                    elem.SetPosition(oldstate[0])
                    
                elem.color = oldstate[1]
            delattr(self,"capture")
                
        Game.PushSuspend(self)
        
    def EditorPopSuspend(self):
        Game.PopSuspend(self)
        
        # Capture all entities that are currently active
        # in the scene (excluding those not
        # assigned to a window)
        if len(self.suspended)==0 and self.level:
            self.capture = {}
            for elem in self.level.EnumAllEntities():
                if not hasattr(elem,"window_unassigned"):
                    self.capture[elem] = elem.pos,elem.color
    
    def IsEditorRunning(self):
        return not hasattr(self,"capture")
        
    def _LoadTileFromTag(self,codename):
        """Load a tile with a given 3-character code (color + type)
        and assign it to the current level"""
        elem = TileLoader.LoadFromTag(codename,self)
        elem.SetLevel(self.level)
        elem.SetPosition((0,0))
        
        return elem
        
    def _ReplaceSelection(self,sel):
        """Replace the current selection with the entities
        contained in the given sequence."""
        if not sel:
            return
        
        self.template = dict()
        for elem in sel:
            self.template[elem] = None
                        
        # Needed to emulate proper selection
        self.select_start = sel[0].pos if sel[0].pos!=Entity.DEFAULT_POS else (self.tx,self.ty)
        
    def _SaveLevelBackup(self):
        """Save a backup of the current level. Previous backups are kept""" 
        self._SaveBackup(self.level_file)
        
    def _SaveBackup(self,file):
        """Save a backup of an arbitrary file, provided a sub-folder
        'backup' exists""" 
        head, tail = os.path.split(file)
        tail, ext  = os.path.splitext(tail)
        
        import time
        path = os.path.join(head, "backup", "{0}_{1}.{2}.backup".format( tail, time.ctime(), ext ))
        path = path.replace(":"," ") # make the string returned by ctime() a valid filename
        path = path.replace(" ","_")
        
        import shutil
        try:
            shutil.copy2(file, path)
        except (IOError, os.error) as why:
            print("WARN: Failure creating backup file {0}, this is bad. ".format(path))
            return
        
        print("Saved backup for {0} to {1}".format(file,path))
        
    def PushOverlay(self,ov):
        self.overlays.append(ov)
        
    def PopOverlay(self):
        self.overlays.pop()
        
    def RemoveOverlay(self,ov):
        # XXX no reentrant or threadsafe
        self.overlays.reverse()
        self.overlays.remove(ov)
        self.overlays.reverse()
        
    def _UpdateLevelSize(self):
        """Recompute self.level.level_size basing on the current state"""
        pass
    
    @staticmethod
    def _FindUnallocatedColorIndex():
        """Get a fresh color index which is not yet use, raise
        KeyError if such an index does not exist"""
        import curses.ascii
        
        # Our level files are ASCII so far, but this is no
        # fixed requirement which could not be changed, now
        # that we have an editor to hide the storage 
        # details.
        
        from tile import TileLoader
        colors = TileLoader.cached_color_dict
        
        forbidden_forest = [" ", "\t", ".", "\n", "\r"]
        for i in range(0,255):
            s = chr(i)
            if curses.ascii.isprint(s) and not s in forbidden_forest and not s in colors.keys():
                return s
        
        raise KeyError()

    @staticmethod
    def _FindClosestColorIndex(color):
        """Find the color index whose color's absolute value
        is as close as possible to the given color """
        
        # Note: copy'n'paste from Level
        colors = TileLoader.cached_color_dict
        assert len(colors)
        
        def diff(a,b):
            return abs(a.r-b.r) + abs(a.g-b.g) + abs(a.b-b.b) + abs(a.a-b.a) 
        return sorted(diff(e,color) for e in colors)[0]
    
    @staticmethod
    def AddGlobalColorEntity(color,desc="(created by editor)"):
        """Register a new color globally. This cannot be undone easily,
        so use it with care. Colors are stored globally in the
        config/colors.txt file. The function allocates and returns
        a fresh one-character index to the color, which can be used
        from within level files to reference the color.
        The index of the closest color (determined by the summed
        absolute difference of all color channels) is returned
        if the function is out of indices."""
        
        colors = TileLoader.cached_color_dict
        
        if color in colors:
            return # Sanity check
        
        # Find an empty index to use
        try:
            index = self._FindUnallocatedColorIndex()
            print("Adding new color entry with index {0}: RGBA={1:X}{2:x}{3:x}{4:x}".format(
                index,color.r,color.g,color.b,color.a))
            
            # Slurp the color config file and append our new contents,
            # make a backup as usual.
            file = os.path.join(defaults.config_dir,"colors.txt")
            self.SaveBackup(file)
            new = """
            
            # {0}
{1}={2:x}{3:x}{4:x}{5:x} 
""".format(desc,index,color.r,color.g,color.b,color.a)

            with open(file,"at") as out:
                out.write(new)
                
            print("{0} has been updated to reflect the changes".format(file))
            
            # Finally, propagate the change to the global color table
            colors[index] = color
        except KeyError:
            
            index = self._FindClosestColorIndex(color) 
            print("Out of color indices! Reusing existing index {0}".format(index))
            
        return index
        
    def Save(self):
        self._UpdateLevelSize()
        
        yofs = self.level.vis_ofs
        grid = [ [None for x in range(self.level.level_size[0])] for y in range(self.level.level_size[1]+yofs)]
        x,y = -1000,-1000
        entity = None
        try:
            for entity in self.level.EnumAllEntities():
                if hasattr(entity,"editor_tcode"):
                    assert hasattr(entity,"editor_ccode")
                    
                    x,y = entity.pos
                    x,y = math.floor(x),math.floor(y)+yofs
                    
                    if not grid[y][x] is None:
                        print("Warn: ignoring duplicate tile {0} at {1}/{2}, existing tile is {3}".format(entity,x,y,grid[y][x]))
                        continue
                    
                    grid[y][x] = entity    
        except BaseException as b:
            print("Fatal exception during saving: {0}, x: {1}, y: {2}, e: {3} [level size: {4}, yofs: {5}]".
                  format(b,x,y,entity,self.level.level_size,yofs))
            return
        
        # Be sure to have a full backup saved before we do anything
        self._SaveLevelBackup()
        
        # Clear LevelLoader's cache for this level, this ensures
        # that the file contents are refetched from fisk the next
        # time they're requested.
        from level import LevelLoader
        LevelLoader.ClearCache([self.level_idx])
        
        from tile import TileLoader
        rcolors = dict((v,k) for k,v in TileLoader.cached_color_dict.items())
        
        def ccol(col):
            try:
                return rcolors[col]
            except KeyError:
                # A new color! Save it immediately before it runs away ...
                return self.AddGlobalColorEntry(col)
            
        try:
            # build the output text prior to clearing the file
            cells = "\n".join("".join([((ccol(n.color)+n.editor_tcode) 
                  if not n is None and hasattr(n,"editor_ccode") else ".  ") for n in row
                ])  for row in grid)
            
            with open(self.level_file,"wt") as out:
                out.write(self.level.editor_shebang+"\n")
                out.write(cells)
                
        except IOError:
            print("Failure saving level file")
            return
            
        print("Wrote level successfully to {0}, overwriting existing contents".
             format(self.level_file))
        
        self.save_counter = self.cur_action
        
    def UnsavedChanges(self):
        return self.save_counter != self.cur_action
            
    def _DrawRectangle(self,bb,color,thickness=2):
        shape = sf.Shape()

        bb = [bb[0],bb[1],bb[0]+bb[2],bb[1]+bb[3]]
        bb[0:2] = self.ToDeviceCoordinates(self.level.ToCameraCoordinates( bb[0:2] ))
        bb[2:4] = self.ToDeviceCoordinates(self.level.ToCameraCoordinates( bb[2:4] ))

        shape.AddPoint(bb[0],bb[1],color,color)
        shape.AddPoint(bb[2],bb[1],color,color)
        shape.AddPoint(bb[2],bb[3],color,color)
        shape.AddPoint(bb[0],bb[3],color,color)

        shape.SetOutlineWidth(thickness)
        shape.EnableFill(False)
        shape.EnableOutline(True)

        self.DrawSingle(shape)
        
    def _CloneEntity(self,which,force=False):
        
        # Don't clone if the given template object is nowhere in 
        # the scene, unless explicitly forbidden.
        if not force and not which in self.level.EnumAllEntities():
            print("Reusing existing entity {0}, no need to clone".format(which))
            return which
        
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
        
        # Duplicate editor-related information which is
        # needed that our new tile can be properly
        # saved and restored and even further duplicated.
        t.editor_shebang = which.editor_shebang
        t.editor_tcode = which.editor_tcode
        t.editor_ccode = which.editor_ccode 
        return t
    
    def _DrawEditor(self):
        
        inp = Renderer.app.GetInput()
        self.level.SetDistortionParams((100,0,0))   
        
        # get from mouse to tile coordinates
        # (XXX) put this into a nice function or so --- :-)
        offset = self.level.GetOrigin()
        self.tx,self.ty = (self.mx/defaults.tiles_size_px[0] + offset[0],
            self.my/defaults.tiles_size_px[1]- defaults.status_bar_top_tiles)
        
        self.fx,self.fy = math.floor(self.tx),math.floor(self.ty)
        
        # call all overlays in order of addition, operate
        # on a copy to allow PushOverlay/RemoveOverlay() calls
        # during processing the overlays.
        if self.IsEditorRunning():
            [e() for e in list(self.overlays)]
        
    def Undo(self,recursive=False):
        """Undo the last step, if possible"""
        if self.cur_action < 1:
            print("No more steps to undo!")
            return
        
        if self.actions[self.cur_action-1] is None:
            # transaction sentinel
            self.cur_action -= 1
            if recursive:
                print("Reach end of transaction")
                return
                
            print("Reach begin of transaction")
            self.Undo(True)
            return
        
        if not "undo" in self.actions[self.cur_action-1]:
            print("This operation cannot be undone!")
            return
        
        self.cur_action -= 1
        print("Undoing action {0}, which describes itself so: {1}".
              format(self.cur_action,self.actions[self.cur_action]["desc"]))
        self.actions[self.cur_action]["undo"]()
        
        if recursive:
            self.Undo(True)
    
    def Redo(self,recursive=False):
        """Redo the previously undone step, if possible"""
        if self.cur_action == len(self.actions):
            print("No more steps to redo!")
            return
        
        if self.actions[self.cur_action] is None:
            # transaction sentinel
            self.cur_action += 1
            if recursive:
                print("Reach end of transaction")
                return
                
            print("Reach begin of transaction")
            self.Redo(True)
            return
        
        if not "redo" in self.actions[self.cur_action]:
            print("This operation cannot be redone!")
            return
        
        print("Redoing action {0}, which describes itself so: {1}".
              format(self.cur_action,self.actions[self.cur_action]["desc"]))
        self.actions[self.cur_action]["redo"]()
        
        self.cur_action += 1
        if recursive:
            self.Redo(True)
        
    def PushAction(self,action):
        """Push a controlled (i.e. undoable) action onto the action stack.
        The provided dict should define the undo and redo entries,
        which must both be callable, but may be ommitted if they are
        not supported."""
        
        assert isinstance(action,dict)
        
        action.setdefault("desc","(no description given)")
        if len(self.actions) > self.cur_action:
            del self.actions[self.cur_action:]
            
        assert len(self.actions) == self.cur_action
        self.actions.append(action)
        
        if self.save_counter > self.cur_action:
            self.save_counter = -1
        
        self.cur_action += 1
        print("Push undoable action onto action stack: {0}, stack height is now: {1}".
              format(action["desc"],len(self.actions)))
        
    def BeginTransaction(self):
        """Begin a transaction on the action stack. Transactions are
        atomic, they are always reverted in whole, or not. Call
        EndTransaction() to end the transaction.
        
        BeginTransaction() is a context manager."""
        
        self.actions.append(None)
        self.cur_action += 1
        print("Push transaction sentinel onto action stack (BEGIN)")
        
        outer = self
        class Context:
            
            def __enter__(self):
                return self
            
            def __exit__(self,exc_type, exc_val, exc_tb):
                outer.EndTransaction()
                return False
        return Context()
        
    def EndTransaction(self):
        """Counterpart to BeginTransaction()"""
        
        self.actions.append(None)
        self.cur_action += 1
        print("Push transaction sentinel onto action stack (END)")
        
    def ExpandLevel(self,axis,pos,add):
        """Insert 'add' rows or columns starting at position
        'pos'. 'axis' is 0 to add columns on the x-axis,
        and 1 to add rows on the y-axis."""
        
        lx,ly = self.level.level_size
        sanity = self.level.vis_ofs*2
        
        # Build a bounding box covering the region to be moved to the right
        bb = (pos,-sanity,lx-pos,ly+sanity*2) if axis==0 else (-sanity,pos,lx+sanity*2,ly-pos)
        for elem in self.level.EnumPossibleColliders(bb):
            px,py = elem.pos
            if bb[0]<px<bb[0]+bb[2] and bb[1]<py<bb[1]+bb[3]:
                        
                px += add if axis == 0 else 0
                py += add if axis == 1 else 0
                elem.SetPosition((px,py))
                
        lx += add if axis==0 else 0
        ly += add if axis==1 else 0
        
        self.level.level_size = lx,ly
        self.dirty_area += 100 # ensure that the minimap is updated soon
        self._PrepareMiniMapVisibleRect()
        
    def ShrinkLevel(self,axis,pos,add):
        """Delete 'del' rows or columns starting at position
        'pos'. 'axis' is 0 to erase columns on the x-axis,
        and 1 to add rows on the y-axis. Returns a list of all
        deleted entities."""
        
        lx,ly = self.level.level_size
        sanity = self.level.vis_ofs*2
        
        ret = []
        
        # Build a bounding box covering the region to be erased
        bb = (pos,-sanity,add,ly+sanity*2) if axis==0 else (-sanity,pos,lx+sanity*2,add)
        for elem in self.level.EnumPossibleColliders(bb):
            px,py = elem.pos
            if bb[0]<px<bb[0]+bb[2] and bb[1]<py<bb[1]+bb[3]:
                self.level.RemoveEntity(elem)
                ret.append(elem)
        
        # Build a bounding box covering the region to be moved to the left
        bb = (pos+add,-sanity,lx-pos-add,ly+sanity*2) if axis==0 else (-sanity,pos+add,lx+sanity*2,ly-pos-add)
        for elem in self.level.EnumPossibleColliders(bb):
            px,py = elem.pos
            if bb[0]<px<bb[0]+bb[2] and bb[1]<py<bb[1]+bb[3]:
                adjust = px>=lx-1 and axis==0 or py>=ly-1 and axis==1
                
                px -= add if axis == 0 else 0
                py -= add if axis == 1 else 0
                elem.SetPosition((px,py))
                
        lx -= add if axis==0 else 0
        ly -= add if axis==1 else 0
                
        self.level.level_size = lx,ly
        self.dirty_area += 100 # ensure that the minimap is updated soon
        self._PrepareMiniMapVisibleRect()
        
        return ret
        
    def ControlledExpandLevel(self,axis,pos,add):
        """Same as ExpandLevel(), except it records the
        operation on the action stack."""
        
        def ExpandLevel():
            self.ExpandLevel(axis,pos,add)
            
        def ShrinkLevel():
            self.ShrinkLevel(axis,pos,add)
        
        self.PushAction({"desc":"Expand level by {0} {1} on axis {2}, starting at offset {3}".format(
                add, "rows" if axis==1 else "columns", axis, pos                                             
            ),
            "redo" : (lambda: ExpandLevel()),
            "undo" : (lambda: ShrinkLevel())
        })
        ExpandLevel()
        
    def ControlledShrinkLevel(self,axis,pos,add):
        """Same as ShrinkLevel(), except it records the
        operation on the action stack."""
        
        def ShrinkLevel():
            return self.ShrinkLevel(axis,pos,add)
            
        recover = ShrinkLevel()
        
        def ExpandLevel():   
            self.ExpandLevel(axis,pos,add)
            for elem in recover:
                self.level.AddEntity(elem)
        
        self.PushAction({"desc":"Shrink level by {0} {1} on axis {2}, starting at offset {3}".format(
                add, "rows" if axis==1 else "columns", axis, pos                                             
            ),
            "redo" : (lambda: ShrinkLevel()),
            "undo" : (lambda: ExpandLevel())
        })
        
        
    def ControlledAddEntity(self,entity):
        """Wrap entity add/remove functions to synchronize with our level table"""
        
        # Find out if there's another entity at this position, if yes, remove it.
        e = [e for e in self.level.EnumVisibleEntities() 
             if   int(e.pos[0])==int(entity.pos[0]) 
             and  int(e.pos[1])==int(entity.pos[1])
             and  hasattr(e,"editor_ccode")
        ]
        
        if e:
            assert len(e)==1
            e = e[0]
            if e is entity:
                return # should not happen, but still put a safeguard here to catch the case

            
        def RemoveEntity():
            self.level.RemoveEntity(entity)
            self._UpdateMiniMap(entity)
            
            if e: # Restore the previous entity at this position
                self.level.AddEntity(e)
                self._UpdateMiniMap(e)
            
        def AddEntity():
            if e: # Remove the previous entity at this position
                self.level.RemoveEntity(e)
                self._UpdateMiniMap(e)
                
            self.level.AddEntity(entity)
            self._UpdateMiniMap(entity)
            
        self.PushAction({"desc":"Add entity {0} [leads to removal of {1}]".format(
                entity, e or "(None, location was previously empty)"                                                
            ),
            "redo" : (lambda: AddEntity()),
            "undo" : (lambda: RemoveEntity())
        })
        
        AddEntity()
        
    def ControlledRemoveEntity(self,entity):
        """Wrap entity add/remove functions to synchronize with our level table"""
        
        def RemoveEntity():
            self.level.RemoveEntity(entity)
            self._UpdateMiniMap(entity)
            
        def AddEntity():
            self.level.AddEntity(entity)
            self._UpdateMiniMap(entity)
        
        self.PushAction({"desc":"Remove entity {0}".format(
                entity                                                
            ),
            "redo" : (lambda: RemoveEntity()),
            "undo" : (lambda: AddEntity())
        })
        
        RemoveEntity()
        
    def ControlledSetEntityColor(self,entity,color):
        """Use instead of a simple assignment to entity.color to create
        an empty on the action stack"""
        
        def SetColor(color):
            entity.color = color
        
        old_color = entity.color
        self.PushAction({"desc":"Change color of {0} to {1}/{2}/{3}/{4}".format(
                entity,color.r,color.g,color.b,color.a                                                        
            ),
            "redo" : (lambda: SetColor(color)),
            "undo" : (lambda: SetColor(old_color))
        })
        
        SetColor(color)
        
    def ControlledSetEntityPosition(self,entity,pos):
        """Use instead of a simple call to Entity.SetPosition() to create
        an empty on the action stack"""
        
        def SetPosition(pos):
            entity.SetPosition(pos)
        
        old_color = entity.pos
        self.PushAction({"desc":"Change position of {0} to {1}".format(
                entity,pos                                                     
            ),
            "redo" : (lambda: SetPosition(pos)),
            "undo" : (lambda: SetPosition(old_color))
        })
        
        SetPosition(pos)
        
    def _UpdateMiniMap(self,entity):
        bb = entity.GetBoundingBox()
        self.dirty_area += math.ceil( bb[2] )* math.ceil(bb[3]) if bb else 1.0
        
    def _DrawMiniMap(self):
        if self.dirty_area > 10.0: # choosen by trial and error as a good treshold value
            self._GenMiniMapImage()
            self.dirty_area = 0.0
            
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
        self.msx,self.msy = (12,9) if w < 100 else ((8,6) if w < 200 else ((4,3) if w < 250 or h < 250 else (1,1))) 
        w,h = w*self.msx,(h)*self.msy
        b = bytearray(b'\x30\x30\x30\xa0') * (w*h)
        
        # msxp is the scaling factor to get from tiles to destination (backbuffer) pixels 
        if hasattr(self,"sw"):
            self.msxp,self.msyp = (self.sw/self.minimap.GetWidth())*self.msx,(self.sh/self.minimap.GetHeight())*self.msy
        
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
        
        if not hasattr(self,"minimap"):
            self.minimap = sf.Image()
        self.minimap.LoadFromPixels(w,h, bytes(b))
        
    def _BuildMiniMap(self):
        # First, create the image and generate its contents
        self._GenMiniMapImage()
        
        self.minimap_sprite,self.sw,self.sh,self.sx,self.sy = self._GetImg(self.minimap)
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
    
    def _GetLevelInfo(self):
        # the level *must* be in LevelLoader's cache
        # self.cached_level_lines = LevelLoader.cache.get(file, None)
    
        # Moved to TileLoader and LevelLoader, which store the
        # needed meta-info directly in their corresponding
        # child objects.
        
        self.level_file = os.path.join(defaults.data_dir, "levels", str(self.level_idx) + ".txt")
        pass
    
    @override 
    def _OnEscape(self):   
        if not self.UnsavedChanges():
            Game._OnEscape(self)
            return
            
        accepted = (KeyMapping.Get("accept"),KeyMapping.Get("level-new"),KeyMapping.Get("escape"))
        def on_close(key):
            if key == accepted[2]:
                self.swallow_escape = False 
                return
            if key == accepted[0]:
                self.Save()
            
            Game._OnEscape(self)
            
        self.swallow_escape = True # Hack to prevent Escape from being triggered again
        self._FadeOutAndShowStatusNotice(_("""You are about to leave. Save first?

Press {0} to save first and leave then
Press {1} to leave immediately, without saving 
Press {2} to abort""").format(
                    KeyMapping.GetString("accept"),
                    KeyMapping.GetString("level-new"),
                    KeyMapping.GetString("escape")),
            defaults.game_over_fade_time,(560,130),0.0,accepted,sf.Color.Green,on_close)
    
    @override 
    def Draw(self):
            
        Game.Draw(self)
        self.mx,self.my = self.inp.GetMouseX(),self.inp.GetMouseY()
        
        for elem in GUIManager.EnumAllComponents():
            rect = elem.rect # warn, this is a lengthy property access
            if rect[0] <= self.mx <= rect[0]+rect[2] and rect[1] <= self.my <= rect[1]+rect[3]:
                self.mousepos_covered_by_gui = True
                break
        else:
            self.mousepos_covered_by_gui = False

        # Nothing to do is no level is loaded
        if self.level:
            if self.level != getattr(self,"prev_level",None):
                
                self._GetLevelInfo()
                self._BuildMiniMap()
                self.prev_level = self.level
                
            self._DrawEditor()
            
    @override 
    def OnChangeResolution(self,newres):
        # needed because the visible part of the map has changed
        if self.level:
            self._BuildMiniMap()
        
        
class EditorMenu(Drawable):
    """Editor's level selection menu"""
    
    def __init__(self):
        Drawable.__init__(self)
        
        
        def AddLevelButtons():
            x,y = 50,100
            for i in sorted( LevelLoader.EnumLevelIndices() ):
                nam = LevelLoader.GuessLevelName(i)
                
                self.AddSlaveDrawable((Button(text="{0} (#{1})".format(nam,i),rect=[x,y,300,25]) + 
                    ("release",(lambda src,i=i: EditLevel(i)))
                ))
                
                y += 30
                if y >= defaults.resolution[1]-100:
                    y = 100
                    x += 310
        
        def NewLevel():
            import genemptylevel
            genemptylevel.Main()
            
            # first remove all buttons, then re-add them - this time
            # including the button for the newly created level
            for e in [elem for elem in self.slaves if isinstance(elem,Button) and elem.text.count("#")]:
                self.RemoveSlaveDrawable(e)
            
            AddLevelButtons()
         
        self.AddSlaveDrawable((Button(text="Create new level (follow instructions in console)",rect=[50,50,450,25]) + 
             ("release",(lambda src: NewLevel()))
        ))
        
        from level import LevelLoader
        def EditLevel(i):
            game = EditorGame()
            if game.LoadLevel(i):
                Renderer.AddDrawable(game,self)
        
        AddLevelButtons()
        
    @override 
    def Draw(self):
        Renderer.SetClearColor(sf.Color(100,100,100))
    
        for event in Renderer.GetEvents():
            # Escape key : exit
            if event.Type == sf.Event.KeyPressed:
                if event.Key.Code == KeyMapping.Get("escape"):
                    Renderer.Quit()
                    return
    
def main():
    """Main entry point to the editor application"""

    # Read game.txt, which is the master config file
    defaults.merge_config(sys.argv[1] if len(sys.argv)>1 else os.path.join(defaults.config_dir,"game.txt"))
    Log.Enable(defaults.enable_log)
    
    import gettext
    gettext.install('yiang', './locale')
    
    defaults.caption = "YIANG-ED 0.1"
    defaults.resolution[0] = 1450;
    defaults.resizable = True

    print("Startup ...")
    KeyMapping.LoadFromFile(os.path.join(defaults.config_dir,"key_bindings.txt"))

    Renderer.Initialize()
    GUIManager.Enable()
    
    # Perform dummy initializations of some subsystems which are
    # needed for running a Game, but are not necessarily
    # useful for the editor
    HighscoreManager.InitializeDummy()
    Achievements.InitializeDummy()
    BerlinerPhilharmoniker.InitializeDummy()
    
    # Run the game as usual but push the EditorOverlay on top of it
    Renderer.AddDrawable(EditorMenu())
    
    Renderer.DoLoop()
    Renderer.Terminate()
    

        
        
        
        
        
        
        
