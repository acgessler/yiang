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
import itertools
import collections
import os
import random
import math
import traceback

# My own stuff
import mathutil
import defaults
import validator
from fonts import FontCache
from keys import KeyMapping
from renderer import Drawable,Renderer,DebugTools,NewFrame
from level import Level,LevelLoader
from posteffect import PostFXCache, PostFXOverlay, FadeOutOverlay, FadeInOverlay

class ReturnToMenuDueToFailure(Exception):
    """Sentinel exception to return control to the main
    menu ins response to unexpected disasters (i.e.
    level loading failed). The exception carries a
    description string."""

    def __init__(self,message):
        self.message = message 

    def __str__(self):
        return "(ReturnToMenuDueToFailure): {0}".format(self.message)
    
   
class SimpleDrawable(Drawable):
    
    def __init__(self,sfml_drawable):
        self.draw = sfml_drawable
        
    def Draw(self):
        Renderer.app.Draw(self.draw) 
    

class Game(Drawable):
    """Encapsulates the whole game state, including map tiles,
    enemy and player entities, i.e. ..."""

    def __init__(self, undecorated=False):
        """ Initialize a new Game instance given the primary
        RenderWindow """
        Drawable.__init__(self)
        self.undecorated = undecorated

        if defaults.draw_clamp_to_pixel is True:
            self.ToDeviceCoordinates = self._ToDeviceCoordinates_Floored

        # These are later changed by LoadLevel(...), NextLevel(...)
        self.level_idx = -1
        self.level = None
        
        # Load the first level for testing purposes
        # self.LoadLevel(1)
         
        self.total = 0.0
        self.total_accum = 0.0
        self.score = 0.0
        self.lives = defaults.lives
        self.game_over = False
        self.speed_scale = 1.0
        self.rounds = 1
        self.level_size = (0,0)
        self.suspended = []
        
        self.draw_counter = 0

    def Run(self):
        print("Enter main loop")
        Renderer.AddDrawable(self)
        
    def GetDrawOrder(self):
        return -10

    def Draw(self):
        self.running = True
        self.draw_counter = 0
        
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            self.last_time = 0.0

        for event in Renderer.GetEvents():
            self._HandleIncomingEvent(event)
            
        self.time = self.clock.GetElapsedTime()
        self.total = self.time+self.total_accum

        dtime = (self.time - self.last_time)*self.speed_scale
        self.last_time = self.time

        if not self.level is None:
            try:
                self.level.Draw(self.time,dtime)

            except NewFrame:
                self._UndoFrameTime()
                raise
        
            if defaults.debug_draw_bounding_boxes:
                self.level.DrawBoundingBoxes()

        self._DrawStatusBar()

        if defaults.debug_draw_info:
            self._DrawDebugInfo(dtime)
            
    def IsGameRunning(self):
        return len(self.suspended) == 0
            
    def _UndoFrameTime(self):
        #if not hasattr(self,"clock"):
        #    return
        self.last_time = self.clock.GetElapsedTime() 
        self.total -= self.last_time-self.time

    def _EnumEntities(self):
        """Use this wrapper generator to iterate through all enties
        in the global entity list"""
        
        # XXX move this to Level class. ...
        return self.level.EnumActiveEntities()
    
    def GetUpperStatusBarHeight(self):
        """Get the height of the upper status bar, in tiles"""
        return defaults.status_bar_top_tiles
    
    def GetLowerStatusBarHeight(self):
        """Get the height of the lower status bar, in tiles"""
        return (defaults.tiles[1] - defaults.status_bar_top_tiles - 1.0 - self.level.GetLevelVisibleSize()[1])

    def _DrawStatusBar(self):
        """draw the status bar with the player's score, lives and total game duration"""
        if self.level is None:
            return
        
        statush = self.GetUpperStatusBarHeight()*defaults.tiles_size_px[1]
        if not hasattr(self,"status_bar_font"):
            self.status_bar_font = FontCache.get(defaults.letter_height_status,\
                face=defaults.font_status)

        if not hasattr(self,"life_bar_font"):
            self.life_bar_font = FontCache.get(defaults.letter_height_lives,\
                face=defaults.font_lives)
        
        # and finally the border
        shape = sf.Shape()

        fcol,bcol = sf.Color(120,120,120), sf.Color(50,50,50)
        
        shape.AddPoint(1,0,bcol,fcol)
        shape.AddPoint(defaults.resolution[0]-1,0,bcol,bcol)
        shape.AddPoint(defaults.resolution[0]-1,statush,fcol,bcol)
        shape.AddPoint(1,statush,fcol,bcol)

        shape.SetOutlineWidth(2)
        shape.EnableFill(True)
        shape.EnableOutline(True)

        self.DrawSingle(shape)
        
        status = sf.String("Level {0}.{1}, {2:.2} days\n{3:4.5} $".format(
            self.rounds,
            int(self.level_idx),
            Game.SecondsToDays( self.GetTotalElapsedTime() ),
            self.GetScore()/100),
            Font=self.status_bar_font,Size=defaults.letter_height_status)

        status.SetPosition(8,5)
        status.SetColor(sf.Color.Black)
        self.DrawSingle(status)

        status.SetColor(sf.Color.Yellow)
        status.SetPosition(10,5)
        self.DrawSingle(status)

        # .. and the number of remaining lifes
        string = "\n".join(map(lambda x:x*self.lives,
"  OOO     OOO   \n\
 O****O  O***O  \n\
  O****OO***O   \n\
   O*******O    \n\
    O*****O     \n\
     O***O      \n\
      O*O       \n\
       O        ".split("\n")))
        status = sf.String(string,Font=self.life_bar_font,Size=defaults.letter_height_lives)
        xstart = defaults.resolution[0]-self.lives*defaults.letter_height_lives*10

        status.SetPosition(xstart-2,5)
        status.SetColor(sf.Color.Black)
        self.DrawSingle(status)

        status.SetPosition(xstart+2,5)
        self.DrawSingle(status)

        status.SetPosition(xstart,6)        
        status.SetColor(sf.Color.Yellow)
        self.DrawSingle(status)
        
        # finally, the lower part of the cinematic box
        shape = sf.Shape()

        fcol,bcol = sf.Color(120,120,120), sf.Color(50,50,50)
        statush = self.GetLowerStatusBarHeight() * defaults.tiles_size_px[1]
        
        shape.AddPoint(1,defaults.resolution[1]-statush,bcol,fcol)
        shape.AddPoint(1,defaults.resolution[1],fcol,bcol)
        shape.AddPoint(defaults.resolution[0]-1,defaults.resolution[1],fcol,bcol)
        shape.AddPoint(defaults.resolution[0]-1,defaults.resolution[1]-statush,bcol,bcol)

        shape.SetOutlineWidth(2)
        shape.EnableFill(True)
        shape.EnableOutline(True)

        self.DrawSingle(shape)

    def _HandleIncomingEvent(self,event):
        """Standard window behaviour and debug keys"""
        if not self.IsGameRunning():
            return
        
        try:
            if event.Type == sf.Event.KeyPressed:
                if event.Key.Code == KeyMapping.Get("escape"):
                    self.total_accum += self.time
                    delattr(self,"clock")
                    
                    Renderer.RemoveDrawable(self)
                    raise NewFrame()

                if not defaults.debug_keys:
                    return

                # Debug keys
                if event.Key.Code == KeyMapping.Get("debug-showbb"):
                    defaults.debug_draw_bounding_boxes = not defaults.debug_draw_bounding_boxes
                    
                elif event.Key.Code == KeyMapping.Get("debug-allowup"):
                    defaults.debug_updown_move = not defaults.debug_updown_move

                elif event.Key.Code == KeyMapping.Get("debug-showinfo"):
                    defaults.debug_draw_info = not defaults.debug_draw_info

                elif event.Key.Code == KeyMapping.Get("debug-godmode"):
                    defaults.debug_godmode = not defaults.debug_godmode

                elif event.Key.Code == KeyMapping.Get("debug-kill"):
                    self.Kill("(yourself, you pressed the KILL button!)")
                    
                elif event.Key.Code == KeyMapping.Get("debug-gameover"):
                    self.GameOver()
                    
                elif event.Key.Code == KeyMapping.Get("level-new"):
                    self.LoadLevel(self.level_idx)
                
        except NewFrame:
            print("Received NewFrame notification during event polling")
            raise

    def _DrawDebugInfo(self,dtime):
        """Dump debug information (i.e. entity stats) to the upper right
        corner of the window"""

        if not hasattr(self,"debug_info_font"):
            self.debug_info_font = FontCache.get(defaults.letter_height_debug_info,face=defaults.font_debug_info)
            
        entity_count,entities_active,entities_visible,entities_nowindow = self.level.GetEntityStats()
        drawables_global = len(Renderer.GetDrawables())
        fps = 1.0/dtime

        import gc
        gcc = gc.get_count()

        # this is expensive, but we will survive it.
        locdef = locals().copy()
        locdef.update(defaults.__dict__)
        locdef.update(self.__dict__)
        
        text = """
EntitiesTotal:     {entity_count}
EntitiesActive:    {entities_active}
EntitiesVisible:   {entities_visible}
DrawCalls:         {draw_counter}
EntitiesNoWindow:  {entities_nowindow}
DrawablesGlobal:   {drawables_global}
GCCollections:     {gcc}
GodMode:           {debug_godmode}
UpDownMove:        {debug_updown_move}
PreventFallDown:   {debug_prevent_fall_down}
ShowBoundingBoxes: {debug_draw_bounding_boxes}
ScrollBoth:        {debug_scroll_both}
ScrollSpeed:       {move_map_speed}
SpeedScale/Level:  {speed_scale_per_level}
SpeedScale:        {speed_scale}
LevelSize:         {level_size}

TimeDelta:         {dtime:.4}
1/TimeDelta:       {fps:.4}

""".format(**locdef)
        
        s = sf.String(text,Font=self.debug_info_font,\
            Size=defaults.letter_height_debug_info)

        s.SetPosition(defaults.resolution[0]-302,140)
        s.SetColor(sf.Color.White)
        self.DrawSingle(s)

    def GetClock(self):
        """ Get the timer used to measure time since this
        game was started OR resumed."""
        return self.clock

    def GetTotalElapsedTime(self):
        """Get the total duration of this game, not counting in
        suspend times. The return value is in seconds. """
        return self.total

    @staticmethod
    def SecondsToDays(seconds):
        """Quick helper to convert from seconds to fractions of days"""
        return seconds / (3600*24)

    def GetScore(self):
        """Get the total, accumulated score up to now.
        The score is an integer. """
        return self.score

    def Award(self,points):
        """Award a certain amount of points to the player's
        score as a reward for extreme skillz."""
        pp = points*self.speed_scale
        self.score += pp
        print("Awarding myself {0} points (total: {1})".format(points,self.score))
        return pp

    def GetLives(self):
        """Get the number of lives the player has. They
        die if they are killed and no more lives are available"""
        return self.lives
    
    def IsGameOver(self):
        """Check if the game is over. Once the game is over,
        it cannot be continued or reseted anymore."""
        return self.game_over
    
    def _GetAPlayer(self):
        """Get an arbitrary player instance in the list of 
        entities for the current level. Usually there is just
        a single player in a level, so the return value is 
        predictable."""
        from player import Player
        for entity in self.level.EnumAllEntities():
            if isinstance(entity,Player):
                return entity
        
        # we can safely assume that there MUST be a player.
        assert False
    
    def Kill(self,killer="an unknown enemy ",player=None):
        """Kill the player immediately, respawn if they have
        another life, set game over alternatively"""
        DebugTools.Trace()
        
        if not self.IsGameRunning():
            return 
        
        if player is None:
            player = self._GetAPlayer()
        
        self.score *= 0.9
        if self.lives == 0:
            self.GameOver()
            
        self.lives = self.lives-1

        accepted = (KeyMapping.Get("accept"),KeyMapping.Get("level-new"),KeyMapping.Get("escape"))
        def on_close(key):
            if key == accepted[2]:
                self.GameOver()
            player.Respawn(True if key == accepted[0] else False)
            
        self._FadeOutAndShowStatusNotice(sf.String("""You got killed by {0}

Press {1} to restart at the last respawning point
Press {2} to restart the level
Press {3} to leave the game""".format(
                    killer,
                    KeyMapping.GetString("accept"),
                    KeyMapping.GetString("level-new"),
                    KeyMapping.GetString("escape")
                ),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over,face=defaults.font_game_over
        )),defaults.game_over_fade_time,(500,130),0.0,accepted,sf.Color.Red,on_close)

    def GameOver(self):
        """Fade to black and show stats, then return to the main menu"""
        
        DebugTools.Trace()
        self.game_over = True
        
        from highscore import HighscoreManager
        record = HighscoreManager.SetHighscore(self.score)
        
        print("Game over, score is {0} and time is {1}".format(self.score,
            self.clock.GetElapsedTime()))

        if not hasattr(self,"score_map"):
            self.score_map = collections.defaultdict(lambda : "poor, I am laughing at you",{})
            try:
                with open(os.path.join(defaults.config_dir,"scores.txt"),"rt") as scores:
                    for n,line in enumerate([ll for ll in scores.readlines() if len(ll.strip()) and ll[0] != "#"]):
                        self.score_map[n+1] = line.strip()

            except IOError:
                print("Failure reading scores.txt file")

        accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
        def on_close(key):
            Renderer.RemoveDrawable(self)
            raise NewFrame()
            
        self._FadeOutAndShowStatusNotice(sf.String("""You survived {0:.4} days and collected {1:.4} dollars.
That's {2}.\n\n
Hit {3} or {4} to return to the menu .. """.format(
                    Game.SecondsToDays(self.GetTotalElapsedTime()),
                    self.score/100,
                    "a new high score record" if record is True else self.score_map[math.log(self.score*10+1,2)],
                    KeyMapping.GetString("escape"),
                    KeyMapping.GetString("accept")
                ),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over,face=defaults.font_game_over
        )),defaults.game_over_fade_time,(550,100),0.0,accepted,sf.Color.Green,on_close)
        
        raise NewFrame()
    
    def NextLevel(self):
        """Load the next level, cycle if the last level was reached"""

        DebugTools.Trace()
        print("Scale time by {0}%".format((defaults.speed_scale_per_level-1.0)*100))
        
        self.speed_scale *= defaults.speed_scale_per_level
        import main # XXX (hack)
        print("Level {0} done, advancing to the next level".format(self.level_idx))
        
        accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
        def on_close(key):
            if self.level_idx == main.get_level_count():
                lidx = 1
                self.rounds += 1
            else:
                lidx = self.level_idx+1
                       
            if self.LoadLevel(lidx) is False:
                print("Failure loading level {0}, returning to main menu".format(lidx))
                Renderer.RemoveDrawable(self)

            if key == accepted[0]:
                Renderer.RemoveDrawable(self)
                
            raise NewFrame()

        self._FadeOutAndShowStatusNotice(sf.String(("""Hey, you solved Level {0}!.
Hit {1} to continue .. (don't disappoint me)
Hit {2} to return to the menu""").format(
                    self.level_idx,
                    KeyMapping.GetString("accept"),
                    KeyMapping.GetString("escape")
                ),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over,face=defaults.font_game_over
        )),defaults.game_over_fade_time,(550,120),0.0,accepted,sf.Color.Black,on_close) 
        raise NewFrame()
        
    def LoadLevel(self,idx):
        """Load a particular level and drop the old one"""
        self.DropLevel()
        self.level_idx = idx
        self.level = LevelLoader.LoadLevel(idx,self)
        return False if self.level is None else True
    
    def DropLevel(self):
        """Unload the current level, leaving the game area totally
        empty (which is a valid state, however)"""
        if self.level is None:
            return
        
        print("Unloading level {0}".format(self.level_idx))
        for entity in self.level.EnumAllEntities():
            entity.OnLeaveLevel()
            
        self.level = None
    
    def PushSuspend(self):
        """Increase the 'suspended' counter of the game by one. The
        game halts while the counter is not 0."""
        self.suspended.append(self.clock.GetElapsedTime())
            
    def PopSuspend(self):
        """Decrease the 'suspended' counter of the game by one. The
        game halts while the counter is not 0."""
        assert len(self.suspended) > 0
        
        self.total -= self.clock.GetElapsedTime () - self.suspended[-1]
        self.suspended.pop()

    def _FadeOutAndShowStatusNotice(self,
        text,
        fade_time=1.0,
        size=(550,120),
        auto_time=0.0,
        break_codes=(KeyMapping.Get("accept")),
        text_color=sf.Color.Red,
        on_close=lambda x:None):
        """Tiny utility to wrap the fade out effect used on game over
        and end of level. Alongside, a status message is displayed and
        control is not returned unless the user presses any key
        to continue. The return value is an empty list which is 
        filled with a the key that closed the status notice as
        a soon as this information is available. If the notice
        is closed due to timeout, False is returned as only
        list element. The on_close callback is called with the 
        result value as first parameter, if a suitable function
        is provided."""
        
        # Once this was a powerful god-function, now it is just a
        # pointless wrapper to halt the game while the
        # status notice is visible.
        def on_close_wrapper(result):
            self.PopSuspend()
            on_close(result)
            
            
        from notification import MessageBox
        Renderer.AddDrawable(MessageBox(text,fade_time,size,auto_time,break_codes,text_color,on_close_wrapper))
        self.PushSuspend()

    def DrawSingle(self,drawable,pos=None):
        """Draw a sf.Drawable at a specific position, which is
        specified in tile coordinates."""

        if not pos is None:
            pos = self.ToDeviceCoordinates(pos)
            drawable.SetPosition(*pos)
            
        Renderer.app.Draw(drawable)
        self.draw_counter += 1

    def Clear(self,color):
        """Clear the screen in a specified color"""
        self.draw_counter = 0
        self.app.Clear(color)

    def _ToDeviceCoordinates_Floored(self,coords):
        """Replacement for ToDeviceCoordinate() if defaults.draw_clamp_to_pixels is True """
        return (math.floor(coords[0]*defaults.tiles_size_px[0]),
                math.floor(coords[1]*defaults.tiles_size_px[1]))

    def ToDeviceCoordinates(self,coords):
        """Get from camera coordinates to SFML (device) coordinates"""
        return (coords[0]*defaults.tiles_size_px[0],
                coords[1]*defaults.tiles_size_px[1])
        
    def GetLevelStats(self):
        """Return a 4-tuple: (level,round,num_levels,total_levels)"""
        import main # XXX (hack)
        rcnt = main.get_level_count()
        
        return (self.level_idx,self.rounds,rcnt,rcnt*(self.rounds-1)+self.level_idx)
            
    def GetEntities(self):
        """Get a list of all entities in the game"""
        return Renderer.drawables

    def AddEntity(self,entity):
        """Dynamically add an entity to the list of all active
        entities. The operation is deferred until the next
        frame so it is safe to be called from enumeration
        context"""
        
        # XXX this moved to Level, using Game.AddEntity() is deprecated
        self.level.AddEntity(entity)
        
    def RemoveEntity(self,entity):
        """Dynamically add an entity to the list of all active
        entities. The operation is deferred until the next
        frame so it is safe to be called from enumeration
        context"""
        
        # XXX this moved to Level, using Game.RemoveEntity() is deprecated
        self.level.RemoveEntity(entity)
        
    def GetLevelSize(self):
        """Get the size of the current level, in tiles. The
        return value is a 2-tuple for both axes."""
        # XXX this moved to Level, using Game.GetLevelSize() is deprecated
        return self.level.GetLevelSize()
    
    def GetLevel(self):
        """Obtain the current Level object, or None if no 
        level is currently active."""
        return self.level


class Entity(Drawable):
    """Base class for all kinds of entities, including the player.
    The term `entity` refers to a state machine which is in control
    of a set of tiles. Entities receive Update() callbacks once per
    logical frame."""

    ENTER,KILL = range(2)
    DIR_HOR,DIR_VER=range(2)

    BLOCK_LEFT,BLOCK_RIGHT,BLOCK_UPPER,BLOCK_LOWER,BLOCK = 0x1,0x2,0x4,0x8,0xf
    UPPER_LEFT,UPPER_RIGHT,LOWER_LEFT,LOWER_RIGHT,CONTAINS,ALL = 0x1,0x2,0x4,0x8,0x10,0xf|0x10

    def __init__(self):
        Drawable.__init__(self)
        self.pos = [0,0]
        self.color = sf.Color.White
        self.game = None

    def Update(self,time_elapsed,time_delta):
        """To be implemented"""
        pass

    def SetGame(self,game):
        """Binds the Entity to a Game instance. This is called
        automatically for entities loaded with a level"""
        self.game = game

    def SetPosition(self,pos):
        self.pos = list(pos)
        
        if not self.game is None and not self.game.GetLevel() is None:
            self.game.GetLevel()._MarkEntityAsMoved(self)

    def SetColor(self,color):
        self.color = color
        
    def GetDrawOrder(self):
        return 500
        
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
        about to be unloaded. This means the entity will be
        destroyed as well, but the exact time cannot be
        determined due to the GC."""
        pass

    def GetVerboseName(self):
        """Return a verbose (i.e. non-formal) description of the
        entity. The returned string must be suitable to be
        used in death reports, i.e. 'you got killed by {an unknown entity}',
        'an unknown entity' being the verbose name"""
        return "unknown"

    def _BBCollide(self,rect,mycorner):
        """Collide the first axis-aligned BB (x,y,x2,y2) with the
        second bounding box, return a ORed combination of the
        Entity.UPPER/Entity.LOWER flags."""
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
        
        bb = self.GetBoundingBox()
        if bb is None:
            return 0
        
        dist =  mathutil.PointToBoxSqrEst( self.game.GetOrigin(),bb)
        return dist > defaults.cull_distance_sqr and 1 or dist > defaults.swapout_distance_sqr and 2 or 0
        



        
    

    

    

    

    
