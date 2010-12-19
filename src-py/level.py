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
import operator
import builtins

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
    
    all_metadata = None
    
    def __init__(self, level, game, lines, 
        color=sf.Color.Black, 
        vis_ofs=0, 
        postfx= [("ingame1.sfx",())], 
        name=None, 
        gravity=None,
        autoscroll_speed=None,
        scroll=None,
        distortion_params =None,
        audio_section=None,
        skip_validation=False,
        lower_offset=0
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
                the default value to switch to level_n, whereas n is the level index.
            skip_validation -- don't bother validating the entire validity.
                Use for performance reasons or if the builtin validation 
                logic reports false positives.
            lower_offset - Offset between the lowest tile in the level and the
                begin of the lower status bar, if enabled. Positive values
                move the status bar down.
        """
        self.scroll = [scroll or Level.SCROLL_RIGHT]
        self.autoscroll_speed = [autoscroll_speed or defaults.move_map_speed]
        
        self.entities, self.entities_add, self.entities_rem, self.entities_mov = set(), set(), set(), set()
        self.origin = [0, 0]
        self.lower_offset = lower_offset
        self.game = game
        self.level = level
        self.color = sf.Color(*color) if color.__class__ in (list,tuple) else color
        self.vis_ofs = vis_ofs
        self.name = name #or "Level " +str(self.level)
        self.gravity = defaults.gravity if gravity is None else gravity
        self.SetDistortionParams((0,0,0) if distortion_params is False else
             ((not defaults.no_distortion and distortion_params) 
             or (30.0,1.5,10.0)
        ))
        
        self.audio_section = audio_section or "level_{0}".format(self.level)
        
        # pre-defined ('well-known') stats entries
        self.stats = {"deaths":[0],"s_kills":[0],"e_kills":[0],"l_kills":[0],"score":[0.0],"achievements":[0]}
        
        self.postfx_rt = []
        self.postfx = postfx or []
        self._LoadPostFX()
        self._LoadMetaData()
        
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
                
                ll = len(line) # precomputed for performance reasons
                if ll == 0:
                    continue

                assert ll % 3 == 0
                for x in range(0, ll, 3):
                    tcode = line[x + 1] + line[x + 2]

                    if tcode[0] in spaces:
                        continue
                    
                    if self._LoadSingleTile(tcode, line[x],x//3,y):
                        ecnt += 1
                    
                xmax = max(x,xmax)
                
        except AssertionError as err:
            print("Level " + str(level) + " is not well-formatted (line {0})".format(line_idx))
            traceback.print_exc()

        self.level_size = (xmax // 3 + 1, y + 1)
        print("Got {0} entities for level {1} [size: {2}x{3}]".format(ecnt, level, *self.level_size))
        assert(ecnt != 0 or game.mode == game.EDITOR)
        
        if not skip_validation:
            validator.validate_level(self.lines, level)
        
        self._ComputeOrigin()
        self._GenerateWindows()
        self._UpdateEntityList()
        self._ComputeOrigin()
        
        #from game import Game
        from loadscreen import LoadScreen
        if self.game.GetGameMode() == game.CAMPAIGN and not LoadScreen.IsRunning():
            from posteffect import FadeInOverlay
            Renderer.AddDrawable( FadeInOverlay(1.5, fade_start=0.0) )
            
        self._GenToDeviceCoordinates()
            
    def AddTileFromCode(self,code,x,y):
        assert len(code)==3
        return self._LoadSingleTile(code[1:], code[0], x, y)
        
    def _LoadSingleTile(self,tcode,ccode,x,y):
        from tile import TileLoader
        # read from the private attachment tiles of the level if the tile
        # code starts with a lower-case character
        if 122 >= ord( tcode[0] ) >= 97: #   in "abcdefghijklmnopqrstuvwxyz":
            tile = TileLoader.Load(self.lvbase + "\\" + tcode + ".txt", self.game)
        else:
            tile = None
            
        if tile is None:
            # (HACK) avoid os.path.join() calls
            tile = TileLoader.Load(self.tlbase + "\\" + tcode + ".txt", self.game)
            if tile is None:
                return None
                
        from tile import TileLoader
        tile.SetColor(TileLoader.GetColor(ccode))
        tile.SetPosition((x, y - self.vis_ofs))
        tile.SetLevel(self)
        
        # (HACK) Editor mode: store color and type code in order to
        # save the level again later this day.
        if self.game.GetGameMode() == 3:
            tile.editor_ccode = ccode
            tile.editor_tcode = tcode
            
        self.AddEntity(tile)
        return tile
    
    def _LoadMetaData(self):
        """Get level-specific meta data from level_metadata.xml"""
        
        if Level.all_metadata is None:
            import xml.sax
            
            Level.all_metadata = {}
            
            class myHandler(xml.sax.ContentHandler):
                
                def __init__(self):
                    xml.sax.ContentHandler.__init__(self)
                    self.out = Level.all_metadata
                
                def startElement(self,name,attrs):
                    if name == "Level":
                        assert "idx" in attrs
                        self.active = self.out.setdefault(int(attrs["idx"]),{})
                    elif name == "Property":
                        assert hasattr(self, "active" )
                        assert "name" in attrs
                        
                        self.active_prop = attrs["name"]
                        
                def endElement(self,name):
                    if name == "Level":
                        delattr(self,"active")
                    elif name == "Property":
                        delattr(self,"active_prop")
                        
                def characters(self,content):
                    if hasattr(self, "active_prop" ) and hasattr(self, "active" ):
                        self.active[ self.active_prop ] = content.strip()
            
            try:
                xml.sax.parse(os.path.join(defaults.data_dir,"level_metadata.xml"),myHandler())
                print("Read level metadata file, got {0} entries with totally {1} properties".format(
                    len(Level.all_metadata),
                    sum(len(v) for v in Level.all_metadata.values())                                                                             
                ))
            except xml.sax.SAXParseException as e:
                print("Failure loading metadata from xml, got SAX parse error: " + e)
            except e:
                print("Failure loading metadata from xml, file is malformed: " + e)
     
        try:
            self.metadata = Level.all_metadata[self.level]
        except KeyError:
            self.metadata = {}
        
    
    def _SetupAudioSection(self):
        if self.audio_section == "current" or self.game.mode == self.game.BACKGROUND:
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
        self.dither_strength = 1.0 # accessed by updaters/DITHER_STRENGTH
        if not distortion_params[2]:
            return
        
        self.distortion_sine_treshold = math.sin(math.pi* (0.5 - self.distortion_params[1]/self.distortion_params[0]) )
    
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
            int((bb[2]) / defaults.level_window_size_abs[0]), 
            int((bb[3]) / defaults.level_window_size_abs[1]))
                    
    def _AddEntityToWindows(self,e):
        """Determine the rectangle covered by an entity and add
        it to the appropriate windows."""
        #if e.pos == Entity.DEFAULT_POS:
            # Wait until the entity has been properly positioned
            #return
        
        bb = e.GetBoundingBoxAbs()
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
                
                for y in range(len(self.windows),yyy+2):
                    self.windows.append([])
                    
                for y in range(yyy+1):
                    this = self.windows[y]
                    for x in range(len(this), xxx+2 ):
                        this.append([])
      
                try:
                    thiswnd = self.windows[yyy][xxx]  
                except IndexError:
                    print("Ignore IndexError trying to select the window the entity belongs to")
                    return
                                
                thiswnd.append(e)
                    
                if not hasattr(e,"windows"):
                    e.windows = []
                        
                e.windows.append(thiswnd)
                    
    def _EnumWindows(self):
        """Enumerate all windows in the scene as a 2-tuple (cull-level, window). 
        cull-level is either 0 (visible),  1 (intersecting), 2 (close) """
        dl,tiles,so = defaults.level_window_size_abs,defaults.tiles,defaults.swapout_distance_rel 
        cull_1 = (-tiles[0]*so[0],tiles[0]*(so[0]+1.0),-tiles[1]*so[1],tiles[1]*(so[1]+1.0))
        
        if self.scroll[-1] & (Level.SCROLL_TOP | Level.SCROLL_BOTTOM) == 0:
            dl = (dl[0],1.5)
        
        hady = False
        for y,ww in enumerate( self.windows ):
            y = y*dl[1] - self.origin[1]
            
            hadx = False
            for x,window in enumerate( ww ):
                x = x*dl[0] - self.origin[0]
                
                if (0 < x and x+dl[0] < tiles[0]) and (0 < y and y+dl[1] < tiles[1]):
                    yield 0,window
                    hadx = hady = True
                
                elif (0 < x < tiles[0] or 0 < x+dl[0] < tiles[0]) and (0 < y < tiles[1] or 0 < y+dl[1] < tiles[1]):
                    yield 1,window
                    hadx = hady = True
                    
                elif (cull_1[0] < x < cull_1[1] or cull_1[0] < x+dl[0] < cull_1[1]) and (cull_1[2] < y < cull_1[3] or cull_1[2] < y+dl[1] < cull_1[3]):
                    yield 2,window
                    hadx = hady = True
                    
                elif hadx:
                    break
            
            #else:
            #    if hady:
            #        break
            
    def _LoadPostFX(self):
        """Load all postfx's in self.postfx and store them
        in self.postfx_rt"""
        self.postfx_rt = []
        for pfx,env in self.postfx:
            self.AddPostFX(pfx, env)
            
        self.default_postfx = list(self.postfx_rt)
        
    def ResetPostFXToDefaults(self):
        """Revert to the default set of postfx specified in the level file"""
        self.postfx_rt = self.default_postfx
                
    def AddPostFX(self,name,env):
        """Temporarily push another postprocessing effect onto
        the effect stack. Use RemovePostFX() to revert."""
        p = PostFXCache.Get(name,env)
        if not p is None:
            self._SetupStandardPostFXParams(p)
        self.postfx_rt.append((name,p,env))
        return p
        
    def _SetupStandardPostFXParams(self,p):
        """Setup some predefined postfx parameters; used internally"""
        if not p:
            return
        p.SetUpdaterParam("game",self.game)
        
    def OnEnable(self):
        self._SetupAudioSection()
        for entity in self.EnumAllEntities():
            entity.OnEnterLevel()
            
        # need to recover postfx state (the 'game' parameter needs to be set properly
        # because postfx instances may be shared across multiple game instances)
        for name,p,env in self.postfx_rt:
            self._SetupStandardPostFXParams(p)
    
    def OnDisable(self):
        for entity in self.EnumAllEntities():
            entity.OnLeaveLevel()

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
                try:
                    self.window_unassigned.remove(entity)
                except KeyError:
                    pass
            
        from game import Game
        from player import Player
        for entity in self.entities_add:
            pos = entity.pos
            
            lx,ly = self.level_size
            #print(pos,lx,ly,self.origin)
            if (pos[0] >= lx or pos[1] >= ly) and self.game.mode == Game.EDITOR and not isinstance(entity,Player):
                self.SetLevelSize((max(pos[0]+1,lx),max(pos[1]+1,ly)))
            
            self.entities.add(entity)
            self._AddEntityToWindows(entity)
            
        mov = self.entities_mov
        self.entities_mov = set()
        for entity in mov:
            if not entity in self.entities or entity in self.entities_add:
                continue
            
            if hasattr(entity,"windows"):
                for window in entity.windows:
                    window.remove(entity)
                    
                entity.windows = []
                
            self._AddEntityToWindows(entity)
            
        self.entities_add, self.entities_rem = set(), set()
        
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
        """Given a bounding box (x,y,x2,y2), enumerate all entities
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
                
    def EnumEntitiesAtGrid(self,pos):
        """Enum all entities touching a specific position, pos, 
        which is specified in tile coordinates"""
        pos = [int(x) for x in pos]
        for entity in self.EnumPossibleColliders((pos[0],pos[1],pos[0],pos[1])):
            
            pob = [int(x) for x in entity.pos]
            if pob == pos:
                yield entity
                
    def FindClosestOf(self,pos,type):
        """Find the closest entity of a particular class type."""
        candidates = []
        
        # XXX this can be easily optimized
        for entity in self.EnumAllEntities():
            if isinstance(entity,type):
                mypos = entity.pos
                candidates.append(((pos[0]-mypos[0])**2 + (pos[1]-mypos[1])**2,entity))
        return None if not candidates else sorted(candidates,key=operator.itemgetter(0))[0][1]
             
    def FindClosestOfSameColor(self,pos,type,color):
        """Find the closest entity of a particular class type,
        an additional requirement is that theh entities' color must 
        match a given color."""
        candidates = []
        
        # XXX this can be easily optimized
        for entity in self.EnumAllEntities():
            if isinstance(entity,type) and entity.color == color:
                mypos = entity.pos
                candidates.append(((pos[0]-mypos[0])**2 + (pos[1]-mypos[1])**2,entity))
        return None if not candidates else sorted(candidates,key=operator.itemgetter(0))[0][1]       
            
    def IsVisible(self,point):
        """Check if a particular point is currently within
        the visible part of the level"""
        return point[0] > self.origin[0] and point[0] < self.origin[0]+defaults.tiles[0] and \
            point[1] > self.origin[1] and point[1] < self.origin[1]+defaults.tiles[1]
            
    def _DoAutoScroll(self, dtime):
        """Move the map view origin to the right according to a time function"""    
        if len(self.game.suspended) > 0:
            return
            
        s = self.autoscroll_speed[-1]
        if isinstance(s,tuple):
            self.SetOrigin((self.origin[0] + dtime * s[0], self.origin[1] +  dtime * s[1]))
                
        else:
            if self.scroll[-1] & Level.SCROLL_LEFT == 0:
                self.SetOrigin((self.origin[0] + dtime * s, self.origin[1]))
        
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
        ox,oy = self.origin
        tx,ty = defaults.tiles
        
        idx = Renderer.GetFrameIndex()
        
        for n,window in self._EnumWindows():
            if n > 2:
                continue
            
            for entity in window:
                self.entities_active.add(entity)
                
                if n == 0:
                    entity.in_visible_set = True
                    entity.is_intersecting = False
                    entity.update_idx = idx
                elif n == 1:
                    bb = entity.GetBoundingBox()
                    if bb:
                        bb = (bb[0]-ox -1.0,bb[1]-oy,bb[2],bb[3])
                        if (0 <= bb[0] <= tx or bb[0]+bb[2] <= tx) and (0 <= bb[1] <= ty or bb[1]+bb[3] <= ty):
                            entity.in_visible_set = True
                            entity.is_intersecting = True
                elif getattr(entity,"update_idx",idx) < idx:
                    entity.in_visible_set = False
                
        self.entities_active.update(self.window_unassigned)
        se = sorted(self.EnumActiveEntities(),key=lambda x:x.GetDrawOrder(),reverse=True)
        
        steps = max(1, int( dtime/(1/defaults.update_tickrate) ))
        stepd = dtime / steps
        timeo = time - dtime
        for n in range(steps):
            for entity in se:
                entity.Update(timeo + n*stepd,stepd)
            
    def _UpdateDistortion(self,time,dtime):
        # distortion_params is (time_between,distortion_time,scale).
        # Use the sine function to get a smooth transition.
        if not self.distortion_params[2]:
            return
        
        sint = math.sin(time * math.pi * 0.5  / self.distortion_params[0])
        if sint > self.distortion_sine_treshold:
            d = (sint - self.distortion_sine_treshold) / (1.0 - self.distortion_sine_treshold)
            #print(d)
            self.dither_strength = 1.0 + d * self.distortion_params[2]
            
            #if defaults.no_ppfx is False: 
            #    if 0.98 > d > 0.5: # and int(d*20) % 4 != 0:
            #        if not "grayscale.sfx" in [ n for n,p,e in self.postfx_rt ]:
            #            self.AddPostFX("grayscale.sfx", ())
            #    else:
            #        self.RemovePostFX("grayscale.sfx")
        else:
            self.dither_strength = 1.0
            #if defaults.no_ppfx is False: 
            #    self.RemovePostFX("grayscale.sfx")
            
    def Draw(self, time, dtime):
        """Called by the Game matchmaker class once per frame,
        may raise Game.NewFrame to advance to the next frame
        and skip any other jobs for this frame"""
        
        self._DoAutoScroll(dtime)
        self._GenToDeviceCoordinates()
            
        self._UpdateEntities(time,dtime)
        self._UpdateDistortion(time,dtime)
        self._DrawEntities()
        self._UpdateEntityList()
        self.game.DrawStatusBar()
        
    def DrawSingle(self, drawable, pos=None):
        """Draw a sf.Drawable at a specific position, which is
        specified in level-relative tile coordinates."""

        if not pos is None:
            drawable.SetPosition(*self.ToCameraDeviceCoordinates(pos))
            
        Renderer.app.Draw(drawable)
        self.game.draw_counter += 1
        
    def ToCameraCoordinates(self, coords):
        """Get from world- to camera coordinates. This transforms
        everything by the local level origin."""
        return (coords[0] - self.origin[0], coords[1] - self.origin[1])
    
    
    def _GenToDeviceCoordinates(self): # optimize - get an optimized closure to avoid some lookups
        floor = math.floor
        origin = self.origin
        tiles_size_px = defaults.tiles_size_px
    
        # on nt, we have a modified PySFML version which does the rounding in C++, which is way faster 
        if defaults.draw_clamp_to_pixel and os.name != "nt": 
            def ToCameraDeviceCoordinates(coords):
                #optimize - merge ToCameraCoordinates and game.ToDeviceCoordinates()
                return (floor((coords[0]- origin[0] )*tiles_size_px[0]),
                        floor((coords[1]- origin[1] )*tiles_size_px[1]))
        else:                          
            def ToCameraDeviceCoordinates(coords):
                #optimize - merge ToCameraCoordinates and game.ToDeviceCoordinates()
                return ((coords[0]- origin[0] )*tiles_size_px[0],
                        (coords[1]- origin[1] )*tiles_size_px[1])
            
        self.ToCameraDeviceCoordinates = ToCameraDeviceCoordinates
    
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
    
    def SetLevelSize(self,*args):
        """Change the size of the level. This is intended for use
        by the editor. It may not be used safely while the game
        is running."""
        ox,oy = self.level_size
        
        lx,ly = [max(1,x) for x in (args if len(args)==2 else args[0])]
        self.level_size = lx,ly
        
        if lx > ox or ly > oy:
            print("Increase level size to {0}/{1}".format(lx,ly))
        
            # Adjust windows accordingly (currently, we will only expand, not
            # shrink our underlying grid of windows)
            nx,ny = [int(x+0.5) for x in (self.level_size[0] / defaults.level_window_size_abs[0],
                self.level_size[1] / defaults.level_window_size_abs[1]
            )]
                
            for y in range(len(self.windows),ny):
                self.windows.append([])
                
            for y in range(0,ny):
                last = self.windows[-1]
                for x in range(len(last),nx):
                    last.append([])
    
    def GetLevelVisibleSize(self):
        """Get size of the visible part of the level. This is
        usually a constant throughout the lifetime of the
        level."""
        return (min( self.level_size[0], defaults.tiles[0] ), min(defaults.tiles[1], 
            self.level_size[1]-self.vis_ofs-1-self.lower_offset 
        ))
    
    def GetOrigin(self):
        """Get the current origin of the game. That is the
        tile coordinate to map to the upper left coordinate
        of the window """
        return self.origin

    def SetOrigin(self, origin):
        """Change the view origin"""
        assert isinstance(origin, tuple)
        self.origin = (min(max(origin[0],0),abs(self.level_size[0]-defaults.tiles[0])), 
            origin[1] if self.scroll[-1] & (Level.SCROLL_TOP|Level.SCROLL_BOTTOM) else -defaults.status_bar_top_tiles
        )
        
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
        return sf.Color.Red if getattr(entity,"is_intersecting",False) else (
             sf.Color.Yellow if len(getattr(entity,"windows",[]))>1 else sf.Color.Green 
        )
        
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
    
# LevelLoader maintains a global cache, so we need to protect 
# it to avoid concurrency problems.
if defaults.no_threading:
    import dummy_threading as threading
else:
    import threading 
    
    
class LevelLoader:
    """Loads levels from their disk representations into memory"""
    
    cache = {}
    name_cache = {}
    
    @staticmethod
    def BuildLevelPath(index):
        """Obtain the (relative) path to the file containing the
        tile setup for a specific level, which is identified by
        its number"""
        return os.path.join(defaults.data_dir, "levels", str(index) + ".txt")
    
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
        file = LevelLoader.BuildLevelPath(index)
        LevelLoader.name_cache[index] = name = "Level {0}".format(index)
        try:
            with open(file,"rt") as file:
                import re
                look = re.search(r"name=(?:_\()?[\"'](.+?)[\"']\)?",file.read(250))
                if not look is None:
                    LevelLoader.name_cache[index] = name = builtins.__dict__["_"] ( look.groups()[0] )
                    print("Guess level name for {0}: {1}".format(index,name))
        except IOError:
            # LevelLoader will take care of this error, we don't bother for now
            pass
        
        return name
    
    @staticmethod
    def EnumLevelIndices():
        """Enumerate all known level numbers in no special order.
        Note that the number 0 is reserved and never assigned.
        There may be gaps within the set of assigned numbers.
        The functin yields 2-tuples: (index,ro) here ro is
        a boolean flag that specifies whether the level can
        be written to, True indicates read-only access."""
        
        import re
        reg = re.compile(r"^(\d+)\.txt$")
        dir = os.path.join(defaults.data_dir,"levels")
        for file in os.listdir(dir):
            m = re.match(reg,file)
            if m:
                yield int( m.groups()[0] ), (getattr(os.path,"is_archived",lambda x: False)(os.path.join(dir, file)))
                                
    @staticmethod
    def ClearCache(clear=None):
        """Clear all cached levels. If one of them is reloaded,
        a guarantee is made that its contents will be fetched
        from disk and not from an in-memory cache. Call this
        function after external changes occured to the level
        file. Note that the tile cache needs to be cleared
        separately by calling TileLoader.ClearCache(). You
        can limit the cache cleanup to a specific set of
        levels by specifying their numbers as first
        parameter."""
        
        if not clear:
            LevelLoader.cache = {}
            LevelLoadeer.name_cache = {}
            return
        
        for n in clear:
            p = LevelLoader.BuildLevelPath(n)
            
            try:
                del LevelLoader.cache[p]
                del LevelLoader.name_cache[n]
            except KeyError:
                pass
        return
    
    @staticmethod
    def LoadLevel(level, game, no_loadscreen=False):
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
        
        if not no_loadscreen and not defaults.no_threading:
            from loadscreen import LoadScreen
            lv = LoadScreen.Load(LevelLoader.LoadLevel,level,game,no_loadscreen=True)
            if lv:
                lv.used_loadscreen = True
            return lv
       
        file = LevelLoader.BuildLevelPath(level)
        lines = LevelLoader.cache.get(file, None)
        if lines is None:
            try:
                print("Loading level from " + file)
                with open(file, "rt", encoding='cp1252') as f:
                    lines = f.read().split("\n", 1)

                    LevelLoader.cache[file] = lines
                      
            except IOError:
                print("Could not open level file " + file + " for reading")

            except AssertionError as err:
                print("Level file " + file + " is not well-formatted:")
                traceback.print_exc()

        if lines is None or len(lines) != 2:
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
            return None
            
        lv = tempdict.get("level", None)
        if lv and isinstance(lv,Level) and game.GetGameMode() == 3: # Game.EDITOR:
            # in editor mode, store the level's full text in the Level instance itself
            lv.editor_raw = lines[1].rstrip()
            lv.editor_shebang = lines[0]
            
        return lv
    
    
    
    
    
    
