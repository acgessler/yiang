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

# Python Core
import traceback
import random
import itertools
import collections
import os
import itertools
import math

# My own stuff
import defaults
import validator
from renderer import Renderer
from fonts import FontCache
from posteffect import PostFXCache

class Level:
    """The Level class represents the currently loaded level and is responsible
    for both drawing and updating - also it maintains the list of all entities
    in the level"""
    
    SCROLL_LEFT,SCROLL_RIGHT,SCROLL_TOP,SCROLL_BOTTOM = 1,2,4,8
    SCROLL_ALL = 0xf
    
    def __init__(self, level, game, lines, 
        color=sf.Color.Black, 
        vis_ofs=0, 
        postfx= [("ingame1.sfx",())], 
        name=None, 
        gravity=None,
        autoscroll_speed=None,
        scroll=None,
        distortion_params =None,
        audio_section=None
        ):
        """Construct a level given its textual description 
        
        Parameters:
            game -- Game instance to host the level
            level -- 1-based level index
            lines -- Textual level description, split into lines
            color -- The 'halo' color behind the player
            vis_ofs -- Offset on the y axis where the visible part 
               of the level starts. The number of rows is constant.
            scroll -- Any combination of the SCROLL_XXX constants, defaults to SCROLL_RIGHT
            autoscroll_speed -- Automatic side-scrolling speed, in units per second.
                Defaults to 0.0. May be a 2-tuple, in which case the second value is
                the scrolling speed on the y axis.
            distortion_params -- Audio&video distortion density. Must be a
                 3-tuple (time_between,distortion_time,distortion_strength).
            audio_section -- Name of the audio section to switch to. Pass 'current' to
                leave the audio background untouched upon entering this level. Leave
                the default value to switch to level_n, wheras n is the level index.
        """
        self.scroll = [scroll or Level.SCROLL_RIGHT]
        self.autoscroll_speed = [autoscroll_speed or defaults.move_map_speed]
        
        self.entities, self.entities_add, self.entities_rem, self.entities_mov = set(), set(), set(), set()
        self.origin = [0, 0]
        self.game = game
        self.level = level
        self.color = sf.Color(*color) if isinstance(color, tuple) else color
        self.vis_ofs = vis_ofs
        self.name = name
        self.gravity = defaults.gravity if gravity is None else gravity
        self.SetDistortionParams((not defaults.no_distortion and distortion_params) or (30.0,5.0,10.0))
        
        self.audio_section = audio_section or "level_{0}".format(self.level)
        self._SetupAudioSection()
        
        # pre-defined ('well-known') stats entries
        self.stats = {"deaths":[0],"s_kills":[0],"e_kills":[0],"l_kills":[0],"score":[0.0],"achievements":[0]}
        
        self.postfx_rt = []
        self.postfx = postfx or []
        self._LoadPostFX()
        
        self.entities_active = set()
        self.window_unassigned = set()
        
        assert self.game
        assert self.level >= 0
        
        spaces = [" ", "\t", "."]
        line_idx, ecnt = 0, 0
        
        self.lines = lines = lines.split("\n")
        assert len(lines) > 0
        
        self.lvbase = os.path.join(defaults.data_dir, "levels", str(level))
        self.tlbase = os.path.join(defaults.data_dir, "tiles")
        
        xmax = 0
        try:
            for y, line in enumerate(lines):
                line_idx += 1
                line = line.rstrip(" \n\t.")
                if len(line) == 0:
                    continue

                assert len(line) % 3 == 0
                for x in range(0, len(line), 3):
                    tcode = line[x + 1] + line[x + 2]

                    if tcode[0] in spaces:
                        continue
                    
                    self._LoadSingleTile(tcode, line[x],x//3,y)
                    ecnt += 1
                    
                xmax = max(x,xmax)
                
        except AssertionError as err:
            print("Level " + str(level) + " is not well-formatted (line {0})".format(line_idx))
            traceback.print_exc()

        self.level_size = (xmax // 3 + 1, y)
        print("Got {0} entities for level {1} [size: {2}x{3}]".format(ecnt, level, *self.level_size))
        
        validator.validate_level(self.lines, level)
        
        self._ComputeOrigin()
        self._GenerateWindows()
        self._UpdateEntityList()
        self._ComputeOrigin()
        
        from audio import BerlinerPhilharmoniker
        BerlinerPhilharmoniker.SetAudioSection("level_default")
        
        from game import Game
        if self.game.GetGameMode() == Game.CAMPAIGN:
            from posteffect import FadeInOverlay
            Renderer.AddDrawable( FadeInOverlay(1.5, fade_start=0.0) )
        
    def _LoadSingleTile(self,tcode,ccode,x,y):
        from tile import TileLoader
        # read from the private attachment tiles of the level if the tile
        # code starts with a lower-case character
        if 122 >= ord( tcode[0] ) >= 97: #   in "abcdefghijklmnopqrstuvwxyz":
            tile = TileLoader.Load(self.lvbase + "/" + tcode + ".txt", self.game)
        else:
            tile = None
            
        if tile is None:
            # (HACK) avoid os.path.join() calls
            tile = TileLoader.Load(self.tlbase + "/" + tcode + ".txt", self.game)
                
        tile.SetColor(LevelLoader.cached_color_dict[ccode])
        tile.SetPosition((x, y - self.vis_ofs))
        tile.SetLevel(self)
            
        self.AddEntity(tile)
        return tile
    
    def _SetupAudioSection(self):
        if self.audio_section == "current":
            return
        
        from audio import BerlinerPhilharmoniker
        
        try:
            BerlinerPhilharmoniker.SetAudioSection(self.audio_section)
        except KeyError:
            BerlinerPhilharmoniker.SetAudioSection("level_default")
    
    def SetDistortionParams(self,distortion_params):
        """Control the frequency, length and strength of 'high-distortion' periods.
        distortio_params is a 3-tuple of exactly these parameters."""
        self.distortion_params = distortion_params
        self.distortion_sine_treshold = math.sin(math.pi* (0.5 - self.distortion_params[1]/self.distortion_params[0]) )
        self.dither_strength = 1.0 # accessed by updaters/DITHER_STRENGTH
    
    def CountStats(self,name,add):
        """Change a specific entry in the stats dictionary.
        'name' is the name of the counter to modify, 
        and 'add' is the signed amount."""
        self.stats.setdefault(name,[0])[0] += add
    
    def GetStatsString(self):
        """Take the current gameplay statistics and format them nicely.
        The resulting string takes 8 lines.
        """
        return """Statistics (last level played):
        
        {deaths:4} - Suicidal Deaths Committed
        {score:4.4} ct. - Score Received
        {s_kills:4} - Minor Enemy Kills:   
        {l_kills:4} - Major Enemy Kills:  
        {e_kills:4} - Epic Enemy Kills
        {achievements:4} - Achievements earned
""".format(**dict( [(k,v[0]) for k,v in self.stats.items()]  ))
        
    def GetLevelIndex(self):
        """Get the one-based index of the current level"""
        return self.level
        
    def _GenerateWindows(self):
        """Subdivide the whole scene into windows"""
        self.windows = []
        
        # note: add 1.0 because self.level_size could be off a bit.
        num =  (int(self.level_size[0] / defaults.level_window_size_abs[0] + 1.5), 
            int(self.level_size[1] / defaults.level_window_size_abs[1] + 1.5))
        
        #print(num)
        for y in range(num[1]):
            self.windows.append([])
            l = self.windows[-1]
            
            for x in range(num[0]):
                l.append([])
                
        for e in self.entities:
            self._AddEntityToWindows(e)
            
    def _BBToWindowRange(self,bb):
        """Get the range of windows a BB is spanned over"""
        return (int(bb[0] / defaults.level_window_size_abs[0]), 
            int(bb[1] / defaults.level_window_size_abs[1]),
            int((bb[0]+bb[2]) / defaults.level_window_size_abs[0]), 
            int((bb[1]+bb[3]) / defaults.level_window_size_abs[1]))
                    
    def _AddEntityToWindows(self,e):
        """Determine the rectangle covered by an entity and add
        it to the appropriate windows."""
        bb = e.GetBoundingBox()
        if bb is None:
            self.window_unassigned.add(e)
            
            # elements with no explicit bounding box are
            # a) collected in a special 'window' and
            # b) always assumed to be visible, they are responsible
            #    for removing themselves from all relevant lists when
            #    they are no longer visible.
            e.window_unassigned = True
            e.in_visible_set = True
            e.windows = []
            return
            
        xx,yy,xe,ye = self._BBToWindowRange(bb)
        
        #print(xx,yy,xe,ye)
        for xxx in range(xx,xe+1):
            for yyy in range(yy,ye+1):
                
                for y in range(len(self.windows),yyy+1):
                    self.windows.append([])
                    
                for y in range(yyy+1):
                    this = self.windows[y]
                    for x in range(len(this), xxx+1 ):
                        this.append([])
      
                thiswnd = self.windows[yyy][xxx]              
                thiswnd.append(e)
                    
                if not hasattr(e,"windows"):
                    e.windows = []
                        
                e.windows.append(thiswnd)
                    
    def _EnumWindows(self):
        """Enumerate all windows in the scene as a 2-tuple (cull-level, window). 
        cull-level is either 0 (visible), 1 (close) or 2 (away)"""
        dl,tiles = defaults.level_window_size_abs,defaults.tiles
        cull_1 = (-tiles[0]*0.25,tiles[0]*1.25,-tiles[1]*0.25,tiles[1]*1.25)
        
        for y,ww in enumerate( self.windows ):
            y = y*dl[1] - self.origin[1]
            
            for x,window in enumerate( ww ):
                x = x*dl[0] - self.origin[0]
                
                if (0 < x < tiles[0] or 0 < x+dl[0] < tiles[0]) and (0 < y < tiles[1] or 0 < y+dl[1] < tiles[1]):
                    yield 0,window
                    
                elif (cull_1[0] < x < cull_1[1] or cull_1[0] < x+dl[0] < cull_1[1]) and (cull_1[2] < y < cull_1[3] or cull_1[2] < y+dl[1] < cull_1[3]):
                    yield 1,window
            
    def _LoadPostFX(self):
        """Load all postfx's in self.postfx and store them
        in self.postfx_rt"""
        self.postfx_rt = []
        for pfx,env in self.postfx:
            self.AddPostFX(pfx, env)
                
    def AddPostFX(self,name,env):
        """Temporarily push another postprocessing effect onto
        the effect stack. Use RemovePostFX() to revert."""
        p = PostFXCache.Get(name,env)
        if not p is None:
            p.SetUpdaterParam("game",self.game)
        self.postfx_rt.append((name,p,env))

    def RemovePostFX(self,name):
        """Remove a specific postfx from the stack. If there is
        more than one effect with this name on the stack,
        the most recently added is taken"""
        self.postfx_rt.reverse()
        try:
            self.postfx_rt.remove([e for e in self.postfx_rt if e[0] == name][0])
        except IndexError:
            pass
        self.postfx_rt.reverse()

    def _UpdateEntityList(self):
        """Used internally to apply deferred changes to the entity
        list. Changes are deferred till the end of the frame to
        avoid changing list sizes while iterating through them."""
        for entity in self.entities_rem:
            if hasattr(entity,"windows"):
                
                for window in entity.windows:
                    try:    
                        window.remove(entity)
                    except ValueError:
                        # (Hack) Happens in editor mode from time to time.
                        # I guess it happens whenever an entity is removed
                        # in the very same frame it is added.
                        print("Caught ValueError during _UpdateEntityList()")
                        
                delattr(entity,"windows")
            
            try:    
                self.entities.remove(entity)
            except KeyError:
                pass
                
            if hasattr(entity,"window_unassigned"):
                self.window_unassigned.remove(entity)
            
        for entity in self.entities_add:
            self.entities.add(entity)
            self._AddEntityToWindows(entity)
            
        for entity in self.entities_mov:
            if not entity in self.entities or entity in self.entities_add:
                continue
            
            if hasattr(entity,"windows"):
                for window in entity.windows:
                    window.remove(entity)
                    
                entity.windows = []
                
            self._AddEntityToWindows(entity)
            
        self.entities_add, self.entities_rem, self.entities_mov = set(), set(), set()
        
    def GetEntityStats(self):
        """Return a 4-tuple (entities_total,entities_active,entities_visible,entities_nowindow).
        These numbers are for statistical and informative purposes, they need not be exact."""
        return (len(self.entities),
                len(self.entities_active), 
                len([e for e in self.entities_active if e.in_visible_set is True]),
                len(self.window_unassigned)
         )
        
    def EnumAllEntities(self):
        """Return an sequence (actually a set) of all entities
        in the level, be they active or not."""
        return self.entities
        
    def EnumActiveEntities(self):
        """Enum all entities which are currently 'active', that is
        they are subject to regular updates and some of them
        are visible."""
        return self.entities_active
            
    def EnumVisibleEntities(self):
        """Enum all entities which are currently 'visible'.
        Visible entities are always active."""
        return [e for e in self.entities_active if e.in_visible_set is True]
    
    def EnumPossibleColliders(self,bb):
        """Given a bounding box (x,y,w,h), enumerate all entities
        within the same window that could possibly collide."""
        had = set()
        xx,yy,xe,ye = self._BBToWindowRange(bb)
        yy = min(yy,len(self.windows))
        ye = min(ye,len(self.windows)-1)
        for yyy in range(yy,ye+1):
            xx = min(xx,len(self.windows[yyy]))
            xe = min(xe,len(self.windows[yyy])-1)
        
            for xxx in range(xx,xe+1):
                thiswnd = self.windows[yyy][xxx]
                
                for entity in thiswnd:
                    if entity in had:
                        continue
                    
                    yield entity
                    had.add(entity)
                    
    def EnumEntitiesAt(self,pos):
        """Enum all entities touching a specific position, pos, 
        which is specified in tile coordinates"""
        for entity in self.EnumPossibleColliders((pos[0],pos[1],pos[0],pos[1])):
            bb = entity.GetBoundingBox()
            
            if bb[0] <= pos[0] <= bb[2]+bb[0] and bb[1] <= pos[1] <= bb[3]+bb[1]:
                yield entity
            
    def IsVisible(self,point):
        """Check if a particular point is currently within
        the visible part of the level"""
        return point[0] > self.origin[0] and point[0] < self.origin[0]+defaults.tiles[0] and \
            point[1] > self.origin[1] and point[1] < self.origin[1]+defaults.tiles[1]
            
    def _DoAutoScroll(self, dtime):
        """Move the map view origin to the right according to a time function"""    
        if len(self.game.suspended) > 0:
            return
            
        if self.scroll[-1] & Level.SCROLL_LEFT == 0:
            if isinstance(self.autoscroll_speed[-1],tuple):
                self.SetOrigin((self.origin[0] + dtime * self.autoscroll_speed[-1][0], self.origin[1] +  dtime * self.autoscroll_speed[-1][1]))
            else:
                self.SetOrigin((self.origin[0] + dtime * self.autoscroll_speed[-1], self.origin[1]))
        
    def Scroll(self,pos):
        """ Update the view according to the player's position 'pos' 
        and the levels scrolling settings"""
        scroll = self.scroll[-1] 
        if defaults.debug_godmode is True:
            scroll |= Level.SCROLL_RIGHT|Level.SCROLL_LEFT if (scroll & (Level.SCROLL_LEFT|Level.SCROLL_RIGHT)) else 0
            scroll |= Level.SCROLL_TOP|Level.SCROLL_BOTTOM if (scroll & (Level.SCROLL_TOP|Level.SCROLL_BOTTOM)) else 0
        
        if scroll & Level.SCROLL_LEFT:
            rmax = float(defaults.left_scroll_distance)
            if pos[0] < self.origin[0] + rmax:
                self.SetOrigin((pos[0] - rmax, self.origin[1]))
            
        if scroll & Level.SCROLL_RIGHT:
            rmax = float(defaults.right_scroll_distance)
            if pos[0] > self.origin[0] + defaults.tiles[0] - rmax:
                self.SetOrigin((pos[0] - defaults.tiles[0] + rmax, self.origin[1]))
                
        if scroll & Level.SCROLL_TOP:
            rmax = float(defaults.top_scroll_distance)
            if pos[1] < self.origin[1] + rmax:
                self.SetOrigin((self.origin[0], pos[1] - rmax))
                
        if scroll & Level.SCROLL_BOTTOM:
            rmax = float(defaults.bottom_scroll_distance)
            if pos[1] > self.origin[1] + defaults.tiles[1] - rmax:
                self.SetOrigin((self.origin[0], pos[1] - defaults.tiles[1] + rmax))
                
    def PushAutoScroll(self,status):
        self.autoscroll_speed += [status]
        
    def PopAutoScroll(self):
        if not self.autoscroll_speed:
            print("Warn: PopAutoScroll() called, but the stack is empty")
            return
        del self.autoscroll_speed[-1]
        
    def PushScroll(self,scroll):
        self.scroll += [scroll]
        
    def PopScroll(self):
        del self.scroll[-1]
        
    def GetScroll(self):
        return self.scroll[-1]
    
    def GetAutoScroll(self):
        return self.autoscroll_speed[-1]
    
    def _DrawEntities(self):
        Renderer.SetClearColor(self.color)
        havepfx = False
        for entity in sorted(self.EnumVisibleEntities(),key=lambda x:x.GetDrawOrder()):
            if entity.GetDrawOrder() > 10000 and havepfx is False and not defaults.no_ppfx:
                for name,fx,env in self.postfx_rt:
                    if not fx is None:
                        fx.Draw()
                havepfx = True
                
            entity.Draw()
        
        if havepfx is False and not defaults.no_ppfx:
            for name,fx,env in self.postfx_rt:
                if not fx is None:
                    fx.Draw()
                
    def _UpdateEntities(self,time,dtime):
        self.entities_active = set()
        for n,window in self._EnumWindows():
            if n == 2:
                continue
            
            for entity in window:
                self.entities_active.add(entity)
                entity.in_visible_set = n == 0
                
        self.entities_active.update(self.window_unassigned)
        for entity in self.EnumActiveEntities():
            entity.Update(time,dtime)
            
    def _UpdateDistortion(self,time,dtime):
        # distortion_params is (time_between,distortion_time,scale).
        # Use the sine function to get a smooth transition.
        sint = math.sin(time * math.pi * 0.5  / self.distortion_params[0])
        if sint > self.distortion_sine_treshold:
            d = (sint - self.distortion_sine_treshold) / (1.0 - self.distortion_sine_treshold)
            #print(d)
            self.dither_strength = 1.0 + d * self.distortion_params[2]
            
            if defaults.no_ppfx is False: 
                if 0.98 > d > 0.5: # and int(d*20) % 4 != 0:
                    if not "grayscale.sfx" in [ n for n,p,e in self.postfx_rt ]:
                        self.AddPostFX("grayscale.sfx", ())
                else:
                    self.RemovePostFX("grayscale.sfx")
        else:
            self.dither_strength = 1.0
            if defaults.no_ppfx is False: 
                self.RemovePostFX("grayscale.sfx")
                
    def OnEnable(self):
        self._SetupAudioSection()
        for entity in self.EnumAllEntities():
            entity.OnEnterLevel()
    
    def OnDisable(self):
        for entity in self.EnumAllEntities():
            entity.OnLeaveLevel()
            
    def Draw(self, time, dtime):
        """Called by the Game matchmaker class once per frame,
        may raise Game.NewFrame to advance to the next frame
        and skip any other jobs for this frame"""
            
        self._UpdateEntities(time,dtime)
        self._DoAutoScroll(dtime)
        self._UpdateDistortion(time,dtime)
        self._DrawEntities()
        self._UpdateEntityList()
        self.game.DrawStatusBar()
        
    def DrawSingle(self, drawable, pos=None):
        """Draw a sf.Drawable at a specific position, which is
        specified in level-relative tile coordinates."""

        if not pos is None:
            pos = self.game.ToDeviceCoordinates(self.ToCameraCoordinates(pos))
            drawable.SetPosition(*pos)
            
        Renderer.app.Draw(drawable)
        self.game.draw_counter += 1
        
    def ToCameraCoordinates(self, coords):
        """Get from world- to camera coordinates. This transforms
        everything by the local level origin."""
        return (coords[0] - self.origin[0], coords[1] - self.origin[1])
    
    def GetPostFX(self):
        """Get the list of all active postprocessing effects
        on top of this level. Post effects are applied in-order"""
        return self.postfx_rt
    
    def GetName(self):
        """Get the name of the level or None if the level is unnamed"""
        return self.name
    
    def SetPostFXParameter(self,*arg):
        """Set a shared parameter in all active postprocessing
        effects on top of this level."""
        for r in self.postfx_rt:
            r.SetParameter(*arg)
        
    def _ComputeOrigin(self):
        """Used internally to setup the initial origin of the
        of the level view."""
        
        # (HACK) Locate the first Player entity
        from player import Player
        for entity in self.EnumAllEntities():
            if isinstance(entity, Player):
                self.SetOrigin((entity.pos[0]-defaults.tiles[0]/2,entity.pos[1]-defaults.tiles[1]/2))
                break
                
        else:
            self.SetOrigin((0, -defaults.status_bar_top_tiles))
        
    
    def GetLevelSize(self):
        """Get the size of the current level, in tiles. The return
        value is a 2-tuple."""
        return self.level_size
    
    def GetLevelVisibleSize(self):
        """Get size of the visible part of the level. This is
        usually a constant throughout the lifetime of the
        level."""
        return (min( self.level_size[0], defaults.tiles[0] ), min(defaults.tiles[1], self.level_size[1] ))
    
    def GetOrigin(self):
        """Get the current origin of the game. That is the
        tile coordinate to map to the upper left coordinate
        of the window """
        return self.origin

    def SetOrigin(self, origin):
        """Change the view origin"""
        assert isinstance(origin, tuple)
        self.origin = (min(max(origin[0],0),self.level_size[0]-defaults.tiles[0]), 
            origin[1] if self.scroll[-1] & Level.SCROLL_TOP  else -defaults.status_bar_top_tiles )
        
    def SetOriginX(self, origin):
        """Change the view origin but leave the y axis intact"""
        self.origin = (min(max(origin,0),self.level_size[0]-defaults.tiles[0]),self.origin[1])
    
    def AddEntity(self, entity):
        """Dynamically add an entity to the list of all active
        entities. The operation is deferred until the next
        frame so it is safe to be called from enumeration
        context"""
        entity.SetGame(self.game)
        self.entities_add.add(entity)
        
        try:
            self.entities_rem.remove(entity)
        except KeyError:
            pass
        
    def RemoveEntity(self, entity):
        """Dynamically add an entity to the list of all active
        entities. The operation is deferred until the next
        frame so it is safe to be called from enumeration
        context"""
        self.entities_rem.add(entity)
        
    def _MarkEntityAsMoved(self, entity):
        """Indicate that a particular entity has changed its
        position in this frame. This is used internally by
        Entity.SetPosition()"""
        if not hasattr(entity,"window_unassigned"):
            self.entities_mov.add(entity)
        
    def _GetEntityDefBBColor(self,entity):
        """Set the bounding box color for an entity that doesn't override
        this setting explicitly."""    
        return sf.Color.Yellow if len(entity.windows)>1 else sf.Color.Green 
        
    def DrawBoundingBoxes(self):
        """Draw visible bounding boxes around all entities in the level"""
        for entity in self.EnumVisibleEntities():
            bb = entity.GetBoundingBox()
            if bb is None:
                continue

            shape = sf.Shape()

            bb = [bb[0],bb[1],bb[0]+bb[2],bb[1]+bb[3]]
            bb[0:2] = self.game.ToDeviceCoordinates(self.ToCameraCoordinates( bb[0:2] ))
            bb[2:4] = self.game.ToDeviceCoordinates(self.ToCameraCoordinates( bb[2:4] ))

            color = self._GetEntityDefBBColor(entity) if getattr(entity,"highlight_bb",None) is None else entity.highlight_bb
            shape.AddPoint(bb[0],bb[1],color,color)
            shape.AddPoint(bb[2],bb[1],color,color)
            shape.AddPoint(bb[2],bb[3],color,color)
            shape.AddPoint(bb[0],bb[3],color,color)

            shape.SetOutlineWidth(1)
            shape.EnableFill(False)
            shape.EnableOutline(True)

            self.game.DrawSingle(shape)
            
            # entities are forced to update their color once per frame
            try:
                delattr(entity,"highlight_bb")
            except AttributeError:
                pass
    
    
class LevelLoader:
    """Loads levels from their disk representations into memory"""
    
    cache = {}
    name_cache = {}
    
    @staticmethod
    def GuessLevelName(index):
        """Try to guess the name of the level with index 'index'.
        The function tries to extract the name from the level's
        shebang line, it does not actually interpret or load it."""
        
        if index in LevelLoader.name_cache:
            return LevelLoader.name_cache[index]
            
        # try to obtain the written name of the level by
        # skimming through its shebang line looking
        # for name="..."
        file = os.path.join(defaults.data_dir, "levels", str(index)+".txt")
        LevelLoader.name_cache[index] = name = "Level {0}".format(index)
        try:
            with open(file,"rt") as file:
                import re
                look = re.search(r"name=\"(.+?)\"",file.read(250))
                if not look is None:
                    LevelLoader.name_cache[index] = name = look.groups()[0]
                    print("Guess level name for {0}: {1}".format(index,name))
        except IOError:
            # LevelLoader will take care of this error, we don't bother for now
            pass
        
        return name
    
    @staticmethod
    def EnumLevelIndices():
        """Enumerate all known level numbers in no special order.
        Note that the number 0 is reserved and never assigned.
        There may be gaps within the set of assigned numbers."""
        
        import re
        reg = re.compile(r"(\d+)\.txt")
        for file in os.listdir(os.path.join(defaults.data_dir,"levels")):
            m = re.match(reg,file)
            if m:
                yield int( m.groups()[0] )
    
    @staticmethod
    def LoadLevel(level, game):
        """Load a particular level, return a valid Level instance on success,
        otherwise None.
        
        File format for level files:
          <exec-statement>
          <raw>
        The <exec-statement> must be a valid python expression of the
        following form:
        ..... <out> = SomeClassInheritingLevel(CTorArgs)
        
        For use with the c'tor, several placeholder arguments are
        supported:
        
        <game> Current Game instance
        <raw> Raw text contents of the file, excluding the 'shebang'
        <level> One-based index of the level
        <out> The returned Level object
        
        To get default behaviour, use:
        <out> = Level(<level>,<game>,<raw>)
        """
        
        print("Loading level from disc: " + str(level))

        # this remains as the default color table if we can't read config/color.txt
        color_dict_default = collections.defaultdict(lambda: sf.Color.White, {
            "r" : sf.Color.Red,
            "g" : sf.Color.Green,
            "b" : sf.Color.Blue,
            "y" : sf.Color.Yellow,
            "_" : sf.Color.White,
        })

        # the actual mapping table has been outsourced to config/colors.txt
        if not hasattr(LevelLoader, "cached_color_dict"):

            def complain_on_fail():
                print("Encountered unknown color key")
                return sf.Color.White
            
            LevelLoader.cached_color_dict = collections.defaultdict(complain_on_fail, color_dict_default)
            try:
                with open(os.path.join(defaults.config_dir, "colors.txt"), "rt") as scores:
                    for n, line in enumerate([ll for ll in scores.readlines() if len(ll.strip()) and ll[0] != "#"]):
                        code, col = [l.strip() for l in line.split("=")]

                        assert len(col) in (6,8)
                        LevelLoader.cached_color_dict[code] = sf.Color(
                            int(col[0:2], 16), 
                            int(col[2:4], 16), 
                            int(col[4:6], 16), 
                            int(col[6:8], 16) if len(col)==8 else 255 
                        )

                print("Caching colors.txt file, got {0} dict entries".format(len(LevelLoader.cached_color_dict)))

            except IOError:
                print("Failure reading colors.txt file")
            except AssertionError:
                print("color.txt is not well-formed: ")
                traceback.print_exc()
       
        file = os.path.join(defaults.data_dir, "levels", str(level) + ".txt")
        lines = LevelLoader.cache.get(file, None)
        if lines is None:
            try:
                print("Loading level from " + file)
                with open(file, "rt") as f:
                    lines = f.read().split("\n", 1)
                    assert len(lines) == 2

                    LevelLoader.cache[file] = lines
                      
            except IOError:
                print("Could not open level file " + file + " for reading")

            except AssertionError as err:
                print("Level file " + file + " is not well-formatted:")
                traceback.print_exc()

        if lines is None:
            return None

        replace = {
            "<out>"  : "level",
            "<raw>"  : 'r"""' + lines[1].rstrip() + ' """',
            "<game>" : "game",
            "<level>"  : "level"
        }

        l = lines[0]
        for k, v in replace.items():
            l = l.replace(k, v)

        #print(l)
        tempdict = dict(locals())

        try:
            exec(l, globals(), tempdict)
        except:
            print("exec() fails loading level {0}, executing line: {1} ".format(file, l))
            traceback.print_exc()
            
        lv = tempdict.get("level", None)
        if lv and game.GetGameMode() == 3: # Game.EDITOR:
            # in editor mode, store the level's full text in the Level instance itself
            lv.editor_raw = lines[1].rstrip()
            
        return lv
    
    
    
    
    
    
