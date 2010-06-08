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
import defaults
import validator
from fonts import FontCache
from keys import KeyMapping

class NewFrame(Exception):
    """Sentinel exception to abort the current frame and to
    resume with the next, immediately."""
    pass


class ReturnToMenuDueToFailure(Exception):
    """Sentinel exception to return control to the main
    menu ins response to unexpected disasters (i.e.
    level loading failed). The exception carries a
    description string."""

    def __init__(self,message):
        self.message = message 

    def __str__(self):
        return "(ReturnToMenuDueToFailure): {0}".format(self.message)
    

class Game:
    """Encapsulates the whole game state, including map tiles,
    enemy and player entities, i.e. ..."""

    def __init__(self, app):
        """ Initialize a new Game instance given the primary
        RenderWindow """
        self.app = app

        # These are later changed by LoadLevel(...)
        self.entities = set()
        self.level = -1
        self.origin = [0,0]

        # Load the first level for testing purposes
        # self.LoadLevel(1)
         
        self.clock = sf.Clock()
        self.total = 0.0
        self.total_accum = 0.0
        self.score = 0.0
        self.lives = defaults.lives
        self.last_time = 0
        self.game_over = False
        self.speed_scale = 1.0
        self.rounds = 1
        self.level_size = (0,0)

        self.entities_add,self.entities_rem = set(),set()

        self._LoadPostFX()

    def Run(self):
        """ Run the main loop. If the game was previsouly suspended,
        the old status is recovered. The function returns True if
        the mainloop is quit due to a call to Suspend() and False
        if the application was closed by the user"""
        self.running = True
        self.clock.Reset()

        print("Enter mainloop")

        try: # Do or do not. There is no try
            event = sf.Event()
            while self.running is True:
                if not self.app.IsOpened():
                    return False

                if self.app.GetEvent(event):
                    self._HandleIncomingEvent(event)

                self.Clear(sf.Color.Black)
                    
                time = self.clock.GetElapsedTime()
                self.total = time+self.total_accum

                dtime = (time - self.last_time)*self.speed_scale
                self.last_time = time

                try:
                    for entity in self._EnumEntities():
                        entity.Update(time,dtime,self)

                    for entity in self._EnumEntities():
                        entity.Draw(self)
                except NewFrame:
                    pass

                self.app.Draw(self.effect)
                
                if defaults.debug_draw_bounding_boxes:
                    self._DrawBoundingBoxes()

                self._DrawStatusBar()

                if defaults.debug_draw_info:
                    self._DrawDebugInfo(dtime)

                # update the entity list
                for entity in self.entities_add:
                    self.entities.add(entity)

                for entity in self.entities_rem:
                    try:
                        self.entities.remove(entity)
                    except KeyError:
                        pass

                self.entities_rem,self.entities_add = set(),set()
                # Toggle buffers 
                self.app.Display()

            self.total_accum += self.clock.GetElapsedTime()

        except ReturnToMenuDueToFailure as e:
            return str(e)
        
        print("Leave mainloop")
        return True

    def _LoadPostFX(self):
        """Load all postprocessing effects which we might need"""
        self.effect = sf.PostFX()
        self.effect.LoadFromFile(os.path.join(defaults.data_dir,"effects","ingame1.sfx"))
        self.effect.SetTexture("framebuffer", None);
        self.effect.SetParameter("cur",0.0,0.0)
        self.effect.SetParameter("fade",1.0)

    def _EnumEntities(self):
        """Use this wrapper generator to iterate through all enties
        in the global entity list"""
        #copy = self.entities.copy()

        self.endit = False
        for entity in self.entities:
            yield entity
            if self.endit is True:
                raise NewFrame()

    def _DrawStatusBar(self):
        """draw the status bar with the player's score, lives and total game duration"""

        if not hasattr(self,"status_bar_font"):
            self.status_bar_font = FontCache.get(defaults.letter_height_status,\
                face=defaults.font_status)

        if not hasattr(self,"life_bar_font"):
            self.life_bar_font = FontCache.get(defaults.letter_height_lives,\
                face=defaults.font_lives)
        
        # and finally the border
        shape = sf.Shape()

        fcol,bcol = sf.Color(120,120,120), sf.Color(50,50,50)
        statush = 90
        
        shape.AddPoint(1,0,bcol,fcol)
        shape.AddPoint(defaults.resolution[0]-1,0,bcol,bcol)
        shape.AddPoint(defaults.resolution[0]-1,statush,fcol,bcol)
        shape.AddPoint(1,statush,fcol,bcol)

        shape.SetOutlineWidth(2)
        shape.EnableFill(True)
        shape.EnableOutline(True)

        self.app.Draw(shape)
        
        status = sf.String("Level {0}.{1}, {2:.2} days\n{3:4.5} $".format(
            self.rounds,
            self.level,
            Game.SecondsToDays( self.GetTotalElapsedTime() ),
            self.GetScore()/100),
            Font=self.status_bar_font,Size=defaults.letter_height_status)

        status.SetPosition(8,5)
        status.SetColor(sf.Color.Black)
        self.Draw(status)

        status.SetColor(sf.Color.Yellow)
        status.SetPosition(10,5)
        self.Draw(status)


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
        xstart = defaults.resolution[0]-self.lives*defaults.letter_height_lives*12

        status.SetPosition(xstart-2,5)
        status.SetColor(sf.Color.Black)
        self.Draw(status)

        status.SetPosition(xstart+2,5)
        self.Draw(status)

        status.SetPosition(xstart,6)        
        status.SetColor(sf.Color.Yellow)
        self.Draw(status)

    def _HandleIncomingEvent(self,event):
        """Standard window behaviour and debug keys"""
        # Close window : exit
        # if event.Type == sf.Event.Closed:
        #    self.app.Close()
        #    break

        # Escape key : return to main menu, suspend the game
        try:
            if event.Type == sf.Event.KeyPressed:
                if event.Key.Code == KeyMapping.Get("escape"):
                    self.Suspend()
                    return

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
                    self.Kill()
                    
                elif event.Key.Code == KeyMapping.Get("debug-gameover"):
                    self.GameOver()
                    
                elif event.Key.Code == KeyMapping.Get("level-new"):
                    self.LoadLevel(self.level)
                
        except NewFrame:
            print("Received NewFrame notification during event polling")
            pass
                
    def _DrawBoundingBoxes(self):
        """Draw visible bounding boxes around all entities in the scene"""
        for entity in self._EnumEntities():
            bb = entity.GetBoundingBox()
            if bb is None:
                continue

            shape = sf.Shape()

            bb = [bb[0],bb[1],bb[0]+bb[2],bb[1]+bb[3]]
            bb[0:2] = self.ToDeviceCoordinates(self.ToCameraCoordinates( bb[0:2] ))
            bb[2:4] = self.ToDeviceCoordinates(self.ToCameraCoordinates( bb[2:4] ))

            color = sf.Color.Red if getattr(entity,"highlight_bb",False) is True else sf.Color.Green
            shape.AddPoint(bb[0],bb[1],color,color)
            shape.AddPoint(bb[2],bb[1],color,color)
            shape.AddPoint(bb[2],bb[3],color,color)
            shape.AddPoint(bb[0],bb[3],color,color)

            shape.SetOutlineWidth(1)
            shape.EnableFill(False)
            shape.EnableOutline(True)

            self.Draw(shape)
            entity.highlight_bb = False

    def _DrawDebugInfo(self,dtime):
        """Dump debug information (i.e. entity stats) to the upper right
        corner of the window"""

        if not hasattr(self,"debug_info_font"):
            self.debug_info_font = FontCache.get(defaults.letter_height_debug_info,face=defaults.font_debug_info)
            
        entity_count, entities_range = len(self.entities),0
        fps = 1.0/dtime

        import gc
        gcc = gc.get_count()

        # this is expensive, but we will survive it.
        locdef = locals().copy()
        locdef.update(defaults.__dict__)
        locdef.update(self.__dict__)
        
        text = """
EntitiesTotal:     {entity_count}
EntitiesInRange:   {entities_range}
DrawCalls:         {draw_counter}
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

        s.SetPosition(defaults.resolution[0]-302,119)
        s.SetColor(sf.Color.White)
        self.Draw(s)

    def AddToActiveBBs(self,entity):
        """Debug feature, mark a specific entity for highlighting
        in the next frame. Its bounding box will then be drawn
        in red"""
        entity.highlight_bb = True # (HACK, inject a hidden attribute)

    def Suspend(self):
        """ Suspend the game """
        self.running = False

    def GetApp(self):
        """ Get the sf.RenderWindow which we're rendering to """
        return self.app

    def GetCurOrigin(self):
        """ Get the world space position the upper left corner
        of the window is currently mapped to. """
        return self.origin

    def GetClock(self):
        """ Get the timer used to measure time since this
        game was started OR resumed."""
        return self.clock

    def GetTotalElapsedTime(self):
        """Get the total duration of this game, not counting in
        suspend times. The return valuue is in seconds. """
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

    def Kill(self):
        """Kill the player immediately, respawn if they have
        another life, set game over alternatively"""
        if self.lives == 0:
            self.GameOver()
            
        self.lives = self.lives-1
        self._Respawn()

    def _Respawn(self):
        """Respawn the player at the beginning of the level"""
        for entity in self._EnumEntities():
            if hasattr(entity,"Respawn"):
                entity.Respawn(self)
                raise NewFrame()

    def GetLives(self):
        """Get the number of lives the player has. They
        die if they are killed and no more lives are available"""
        return self.lives


    def GetOrigin(self):
        """Get the current origin of the game. That is the
        tile coordinate to map to the upper left coordinate
        of the window """
        return self.origin

    def SetOrigin(self,origin):
        """Change the view origin"""
        assert isinstance(origin,tuple)
        self.origin = origin
    

    def IsGameOver(self):
        """Check if the game is over. Once the game is over,
        it cannot be continued or reseted anymore."""
        return self.game_over

    def GameOver(self):
        """Fade to black and show stats, then return to the main menu"""

        self.game_over = True
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

        if self._FadeOutAndShowStatusNotice(defaults.game_over_fade_time,
            sf.String(("You survived {0:.4} days and collected {1:.4} dollars.\nThat's {2}.\n\nHit ENTER to continue .. (Should you not want to "+
                    "continue,\nrest assured that this status notice will stay here forever)").format(
                Game.SecondsToDays(self.GetTotalElapsedTime()),
                self.score/100,
                self.score_map[math.log(self.score*10+1,2)]),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over,face=defaults.font_game_over
        ))) is True:
            self.Suspend()

    def _FadeOutAndShowStatusNotice(self,fade_time,text,size=(550,120)):
        """Tiny utility to wrap the fade out effect used on game over
        and end of level. Alongside, a status message is displayed and
        control is not returned unless the user presses any key
        to continue."""

        inp = self.app.GetInput()
        #while inp.IsKeyDown(KeyMapping.Get("accept")):
        #    pass

        ret = True
        clock = sf.Clock()
        event = sf.Event()
        while self.running is True:
            if not self.app.IsOpened():
                ret = False
                break

            if self.app.GetEvent(event):
                if event.Type == sf.Event.KeyPressed and event.Key.Code == KeyMapping.Get("accept"):
                    break

            self.Clear(sf.Color.Black)
            time = clock.GetElapsedTime()

            # draw all entities, but don't update them
            for entity in self._EnumEntities():
                entity.Draw(self)

            self.effect.SetParameter("fade",1.0 - time/fade_time)
            self.Draw(self.effect)
            self._DrawStatusBar()

            # now the message box showing the match result
            self._DrawStatusNotice(text,size)
            self.app.Display()

        self.effect.SetParameter("fade",1.0)
        return ret

    def _DrawStatusNotice(self,text,size=(550,120)):
        """Utility to draw a messagebox-like status notice in the
        center of the screen."""
        fg,bg = sf.Color(160,160,160),sf.Color(50,50,50)
        
        shape = sf.Shape()
        shape.AddPoint((defaults.resolution[0]-size[0])/2,(defaults.resolution[1]-size[1])/2,fg,bg )
        shape.AddPoint((defaults.resolution[0]+size[0])/2,(defaults.resolution[1]-size[1])/2,fg,bg )
        shape.AddPoint((defaults.resolution[0]+size[0])/2,(defaults.resolution[1]+size[1])/2,fg,bg )
        shape.AddPoint((defaults.resolution[0]-size[0])/2,(defaults.resolution[1]+size[1])/2,fg,bg )
        
        shape.SetOutlineWidth(4)
        shape.EnableFill(True)
        shape.EnableOutline(True)
        self.Draw(shape)
        pos = ((defaults.resolution[0]-size[0]+30)/2,(defaults.resolution[1]-size[1]+18)/2)
        
        text.SetColor(sf.Color.Black)
        text.SetPosition(pos[0]+1,pos[1]+1)
        self.Draw(text)

        text.SetColor(sf.Color.Red)
        text.SetPosition(pos[0],pos[1])
        self.Draw(text)

    def Draw(self,drawable,pos=None):
        """Draw a sf.Drawable at a specific position, which is
        specified in tile coordinates."""

        if not pos is None:
            pos = self.ToDeviceCoordinates(self.ToCameraCoordinates( pos ))
            drawable.SetPosition(*pos)
            
        self.app.Draw(drawable)
        self.draw_counter += 1

    def Clear(self,color):
        """Clear the screen in a specified color"""
        self.draw_counter = 0
        self.app.Clear(color)

    def ToDeviceCoordinates(self,coords):
        """Get from camera coordinates to SFML (device) coordinates"""
        return (math.floor(coords[0]*defaults.tiles_size_px[0]),
                math.floor(coords[1]*defaults.tiles_size_px[1]))

    def ToCameraCoordinates(self,coords):
        """Get from world- to camera coordinates"""
        return (coords[0]-self.origin[0],coords[1]-self.origin[1])

    def GetLevelSize(self):
        """Get the size of the current level, in tiles. The return
        value is a 2-tuple."""
        return self.level_size

    def LoadLevel(self,level):
        """Load a particular level, return True on success"""

        print("Loading level from disc: "+str(level))
        self.level = level
        self.origin = [0,0]
        self.entities = set()

        color_dict = collections.defaultdict(lambda: sf.Color.White, {
            "r" : sf.Color.Red,
            "g" : sf.Color.Green,
            "b" : sf.Color.Blue,
            "y" : sf.Color.Yellow,
            "_" : sf.Color.White,
        })

        spaces = [" ","\t","."]
        line_idx = 0
        
        try:
            with open(os.path.join(defaults.data_dir,"levels",str(level)+".txt"), "rt") as f:
                self.lines = lines = f.readlines()
                assert len(lines)>0

                for y,line in enumerate(lines):

                    line_idx += 1
                    line = line.rstrip(" \n\t.")
                    if len(line) == 0:
                        continue

                    diff = len(lines) - defaults.tiles[1]

                    assert len(line)%3 == 0
                    for x in range(0,len(line),3):
                        ccode = line[x]
                        tcode = line[x+1]+line[x+2]

                        if tcode[0] in spaces:
                            continue

                        from tile import TileLoader
                        tile = TileLoader.Load(os.path.join(defaults.data_dir,"tiles",tcode+".txt"),self)
                        tile.SetColor(color_dict[ccode])
                        tile.SetPosition((x//3, y - diff))

                        self.entities.add(tile)

                self.level_size = (x//3,y)

            print("Got {0} entities for level {1}".format(len(self.entities),level))
                
        except IOError:
            print("Failure loading level "+str(level))
            return False

        except AssertionError as err:
            print("Level "+str(level)+" is not well-formatted (line {0})".format(line_idx))
            traceback.print_exc()

        return validator.validate_level(self.lines,level)

    def NextLevel(self):
        """Load the next level, cycle if the last level was reached"""
        
        self.speed_scale *= defaults.speed_scale_per_level
        import main # XXX (hack)
        print("Level {0} done, advancing to the next level".format(self.level))

        if self._FadeOutAndShowStatusNotice(defaults.game_over_fade_time,
            sf.String(("Hey, you solved Level {0}!.\n\nHit ENTER to continue .. (this is compulsory)").format(self.level),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over,face=defaults.font_game_over
        ))) is False:
            self.Suspend()

        if self.level == main.get_level_count():
            lidx = 1
            self.rounds += 1
        else:
            lidx = self.level+1
            
        if self.LoadLevel(lidx) is False:
            raise ReturnToMenuDueToFailure("Failure loading level {0}".format(lidx))

    def GetLevelStats(self):
        """Return a 4-tuple: (level,round,num_levels,total_levels)"""
        import main # XXX (hack)
        rcnt = main.get_level_count()
        
        return (self.level,self.rounds,rcnt,rcnt*(self.rounds-1)+self.level)
            
    def GetEntities(self):
        """Get a list of all entities in the game"""
        return self.entities

    def AddEntity(self,entity):
        """Dynamically add an entity to the list of all active
        entities. The operation is deferred until the next
        frame so it is safe to be called from enumeration
        context"""
        self.entities_add.add(entity)

    def RemoveEntity(self,entity):
        """Dynamically add an entity to the list of all active
        entities. The operation is deferred until the next
        frame so it is safe to be called from enumeration
        context"""
        self.entities_rem.add(entity)

class Entity:
    """Base class for all kinds of entities, including the player.
    The term `entity` refers to a state machine which is in control
    of a set of tiles. Entities receive Update() callbacks once per
    logical frame."""

    ENTER,KILL = range(2)
    DIR_HOR,DIR_VER=range(2)

    BLOCK_LEFT,BLOCK_RIGHT,BLOCK_UPPER,BLOCK_LOWER,BLOCK = 0x1,0x2,0x4,0x8,0xf
    UPPER_LEFT,UPPER_RIGHT,LOWER_LEFT,LOWER_RIGHT,CONTAINS,ALL = 0x1,0x2,0x4,0x8,0x10,0xf|0x10

    def __init__(self):
        self.pos = [0,0]
        self.color = sf.Color.White

    def Update(self,time_elapsed,time_delta,game):
        pass

    def Draw(self,game):
        pass

    def SetPosition(self,pos):
        self.pos = list(pos)

    def SetColor(self,color):
        self.color = color

    def GetBoundingBox(self):
        """Get the bounding box (x,y,w,h) of the entity or
        None if the entity does not support this concept"""
        return None

    def Interact(self,other,game):
        return Entity.BLOCK

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



        
    

    

    

    

    
