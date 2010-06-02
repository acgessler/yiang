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

# My own stuff
import defaults
from fonts import FontCache


class Game:
    """Encapsulates the whole game state, including map tiles,
    enemy and player entities, i.e. ..."""

    def __init__(self, app):
        """ Initialize a new Game instance given the primary
        RenderWindow """
        self.app = app
        self.origin = [0,0]

        # These are later changed by LoadLevel(...)
        self.entities = set()
        self.level = -1

        # Load the first level for testing purposes
        # self.LoadLevel(1)
         
        self.clock = sf.Clock()
        self.total = 0.0
        self.total_accum = 0.0
        self.score = 0.0
        self.lives = defaults.lives
        self.last_time = 0
        self.game_over = False

        self._LoadPostFX()

        self.status_bar_font = FontCache.get(defaults.letter_height_status,face=defaults.font_status)
        self.life_bar_font = FontCache.get(defaults.letter_height_lives,face=defaults.font_lives)

    def Run(self):
        """ Run the main loop. If the game was previsouly suspended,
        the old status is recovered. The function returns True if
        the mainloop is quit due to a call to Suspend() and False
        if the application was closed by the user"""
        self.running = True
        self.clock.Reset()

        print("Enter mainloop")

        event = sf.Event()
        while self.running is True:
            if not self.app.IsOpened():
                return False

            if self.app.GetEvent(event):
                self._HandleIncomingEvent(event)

            self.app.Clear(sf.Color.Black)
                
            time = self.clock.GetElapsedTime()
            self.total = time+self.total_accum

            dtime = time - self.last_time
            self.last_time = time

            self.origin[0] += dtime*defaults.move_map_speed
            
            for entity in self._EnumEntities():
                entity.Update(time,dtime,self)

            for entity in self._EnumEntities():
                entity.Draw(self)

            self.app.Draw(self.effect)

            if defaults.debug_draw_bounding_boxes:
                self._DrawBoundingBoxes()

            self._DrawStatusBar()

            # Toggle buffers 
            self.app.Display()

        self.total_accum += self.clock.GetElapsedTime()
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
        """Special generator, maintains a copy of the entity list so
        the real list can freely be modified during the iteration"""
        copy = self.entities.copy()
        for entity in copy:
            yield entity

    def _DrawStatusBar(self):
        """draw the status bar with the player's score, lives and total game duration"""
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
        
        status = sf.String("{0:.2} days\n{1} $".format(
            Game.SecondsToDays( self.GetTotalElapsedTime() ),
            self.GetScore()/100),
            Font=self.status_bar_font,Size=defaults.letter_height_status)

        status.SetPosition(8,5)
        status.SetColor(sf.Color.Black)
        self.app.Draw(status)

        status.SetColor(sf.Color.Yellow)
        status.SetPosition(10,5)
        self.app.Draw(status)


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
        self.app.Draw(status)

        status.SetPosition(xstart+2,5)
        self.app.Draw(status)

        status.SetPosition(xstart,6)        
        status.SetColor(sf.Color.Yellow)
        self.app.Draw(status)

    def _HandleIncomingEvent(self,event):
        """Standard window behaviour and debug keys"""
        # Close window : exit
        # if event.Type == sf.Event.Closed:
        #    self.app.Close()
        #    break

        # Escape key : return to main menu, suspend the game
        if event.Type == sf.Event.KeyPressed:
            if event.Key.Code == sf.Key.Escape:
                self.Suspend()
                return

            if not defaults.debug_keys:
                return

            # Debug keys
            if event.Key.Code == sf.Key.B:
                defaults.debug_draw_bounding_boxes = not defaults.debug_draw_bounding_boxes
                
            elif event.Key.Code == sf.Key.G:
                 defaults.debug_updown_move = not  defaults.debug_updown_move

            elif event.Key.Code == sf.Key.K:
                 self.Kill()

            elif event.Key.Code == sf.Key.Q:
                 self.GameOver()
                
    def _DrawBoundingBoxes(self):
        """Draw visible bounding boxes around all entities in the scene"""
        for entity in self._EnumEntities():
            bb = entity.GetBoundingBox()
            if bb is None:
                continue

            shape = sf.Shape()

            bb = [bb[0],bb[1],bb[0]+bb[2],bb[1]+bb[3]]
            bb[0:2] = self._ToDeviceCoordinates(self._ToCameraCoordinates( bb[0:2] ))
            bb[2:4] = self._ToDeviceCoordinates(self._ToCameraCoordinates( bb[2:4] ))
            
            shape.AddPoint(bb[0],bb[1],sf.Color.Green,sf.Color.Green)
            shape.AddPoint(bb[2],bb[1],sf.Color.Green,sf.Color.Green)
            shape.AddPoint(bb[2],bb[3],sf.Color.Green,sf.Color.Green)
            shape.AddPoint(bb[0],bb[3],sf.Color.Green,sf.Color.Green)
            #shape.AddPoint(bb[0],bb[1],sf.Color.Green,sf.Color.Green)

            shape.SetOutlineWidth(1)
            shape.EnableFill(False)
            shape.EnableOutline(True)

            self.app.Draw(shape)

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
        self.score += points
        print("Awarding myself {0} points (total: {1})".format(points,self.score))

    def Kill(self):
        """Kill the player immediately, respawn if they have
        another life, set game over alternatively"""
        if self.lives == 0:
            self.GameOver()
            
        self.lives = self.lives-1
        self._Respawn()

    def IsGameOver(self):
        """Check if the game is over. Once the game is over,
        it cannot be continued or reseted anymore."""
        return self.game_over

    def GameOver(self):
        """Fade to black and show stats, then return to the main menu"""

        self.game_over = True
        print("Game over, score is {0} and time is {1}".format(self.score,
            self.clock.GetElapsedTime()))
        self.clock.Reset()

        event = sf.Event()
        while self.running is True:
            if not self.app.IsOpened():
                return False

            if self.app.GetEvent(event):
                if event.Type == sf.Event.KeyPressed:
                    self.Suspend()
                    return

            self.app.Clear(sf.Color.Black)
            time = self.clock.GetElapsedTime()

            # draw all entities, but don't update them
            for entity in self._EnumEntities():
                entity.Draw(self)

            self.effect.SetParameter("fade",1.0 - time/defaults.game_over_fade_time)
            self.app.Draw(self.effect)
            self._DrawStatusBar()

            # now the message box showing the match result
            fg,bg = sf.Color(160,160,160),sf.Color(50,50,50)
            size = (550,120)
            
            shape = sf.Shape()
            shape.AddPoint((defaults.resolution[0]-size[0])/2,(defaults.resolution[1]-size[1])/2,fg,bg )
            shape.AddPoint((defaults.resolution[0]+size[0])/2,(defaults.resolution[1]-size[1])/2,fg,bg )
            shape.AddPoint((defaults.resolution[0]+size[0])/2,(defaults.resolution[1]+size[1])/2,fg,bg )
            shape.AddPoint((defaults.resolution[0]-size[0])/2,(defaults.resolution[1]+size[1])/2,fg,bg )
            
            shape.SetOutlineWidth(4)
            shape.EnableFill(True)
            shape.EnableOutline(True)
            self.app.Draw(shape)

            text = sf.String("You survived {0:.4} days and collected {1:.4} dollars.\nThat's {2}".format(
                Game.SecondsToDays(self.GetTotalElapsedTime()),
                self.score/100,
                "pretty awesome, but you can do better.\n\nPress any key to continue .. (Should you not want to "+
                    "continue,\nrest assured that this status notice will stay here forever)"),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over,face=defaults.font_game_over
            ))
            pos = ((defaults.resolution[0]-size[0]+30)/2,(defaults.resolution[1]-size[1]+18)/2)
            
            text.SetColor(sf.Color.Black)
            text.SetPosition(pos[0]+1,pos[1]+1)
            self.app.Draw(text)

            text.SetColor(sf.Color.Red)
            text.SetPosition(pos[0],pos[1])
            self.app.Draw(text)

            self.app.Display()

    def _Respawn(self):
        pass

    def Draw(self,drawable,pos):
        """Draw a sf.Drawable at a specific position, which is
        specified in tile coordinates."""

        pos = self._ToDeviceCoordinates(self._ToCameraCoordinates( pos ))
        
        drawable.SetPosition(*pos)
        self.app.Draw(drawable)

    def _ToDeviceCoordinates(self,coords):
        """Get from camera coordinates to SFML (device) coordinates"""
        return (coords[0]*defaults.tiles_size_px[0],
                coords[1]*defaults.tiles_size_px[1])

    def _ToCameraCoordinates(self,coords):
        """Get from world- to camera coordinates"""
        return (coords[0]-self.origin[0],coords[1]-self.origin[1])

    def LoadLevel(self,level):
        """Load a particular level"""

        print("Loading level from disc: "+str(level))
        self.level = level
        self.entities = set()

        color_dict = collections.defaultdict(lambda: sf.Color.White, {
            "r" : sf.Color.Red,
            "g" : sf.Color.Green,
            "b" : sf.Color.Blue,
            "y" : sf.Color.Yellow,
            "_" : sf.Color.White,
        })

        spaces = [" ","\t"]
        
        try:
            with open(os.path.join(defaults.data_dir,"levels",str(level)+".txt"), "rt") as f:
                lines = f.readlines()
                assert len(lines)>0
                
                for y,line in enumerate(lines): 
                    line = line.rstrip()
                    if len(line) == 0:
                        continue

                    diff = len(lines) - defaults.tiles[1]

                    assert len(line)%3 == 0
                    for x in range(0,len(line),3):
                        ccode = line[x]
                        tcode = line[x+1]+line[x+2]

                        if tcode[0] in spaces:
                            continue

                        tile = TileLoader.Load(os.path.join(defaults.data_dir,"tiles",tcode+".txt"),self)
                        tile.SetColor(color_dict[ccode])
                        tile.SetPosition((x//3, y - diff))

                        self.entities.add(tile)

            print("Got {0} entities for level {1}".format(len(self.entities),level))
                
        except IOError:
            print("Failure loading level "+str(level))

        except AssertionError as err:
            print("Level "+str(level)+" is not well-formatted:")
            print(err)

    def GetEntities(self):
        """Get a list of all entities in the game"""
        return self.entities

class Entity:
    """Base class for all kinds of entities, including the player.
    The term `entity` refers to a state machine which is in control
    of a set of tiles. Entities receive Update() callbacks once per
    logical frame."""

    ENTER,BLOCK,KILL = range(3)

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

    def GetBoundingBox(self,rect,game):
        """Get the bounding box (x,y,w,h) of the entity or
        None of the entity does not support this concept"""
        return None

    def Interact(self,other,game):
        return Entity.BLOCK


class Tile(Entity):
    """Base class for tiles, handles common behaviour, i.e, drawing"""
         
    def __init__(self,text="<no text specified>",width=defaults.tiles_size[0],height=defaults.tiles_size[1]):
        Entity.__init__(self)

        self.text = text
        self.dim = (width//defaults.tiles_size[0],height//defaults.tiles_size[1])
        self._Recache()

        self.color = sf.Color.White
        self.pos = [0,0]

    def __str__(self):
        return "Tile, pos: {0}|{1}, text:\n{2}".format(\
            self.pos[0],self.pos[1],self.text)

    def SetColor(self,color):
        Entity.SetColor(self,color)
        self.cached.SetColor(self.color)

    def GetBoundingBox(self):
        return (self.pos[0],self.pos[1],self.dim[0],self.dim[1])

    def _Recache(self):
        """Cache the tile string from self.text"""
        font = FontCache.get(defaults.letter_size[1])
        self.cached = sf.String(self.text,Font=font,Size=defaults.letter_size[1])
        
        self.cached.SetColor(self.color)

    @staticmethod
    def CreateSimple(char,color,pos):
        """Create a tile which consists solely of a particular color,
        in a single color at a specific location."""
        t = Tile((char*defaults.tiles_size[0]+'\n')*defaults.tiles_size[1])
        t.SetColor(color)
        t.SetPosition(pos)

        return t

    def Draw(self,game):
        """Draw the tile given a Game instance, which defines the
        render target and the coordinate system origin for the tile"""
        game.Draw(self.cached,self.pos)

    def DrawRelative(self,game,offset):
        """Same as Draw(), except it adds an offset to the tile
        position. The offset is specified in tile coordinates"""
        game.Draw(self.cached,(self.pos[0]+offset[0],self.pos[1]+offset[1]))


class AnimTile(Tile):
    """ Adds simple animation to a Tile, which rotates the
    actual image that is displayed. The animation is either
    played automatically or manually."""

    
    def __init__(self,text,height,frames,speed):
        """ Read an animated tile from a text block. Such a textual
        description contains the ASCII images for all frames,
        separated by an empty line for clarity.

            Parameters:
               text Text block
               height Character height of the tile
               frames Number of frames in the file
               speed Playback speed, -1 for manual playback. This is
                the total time to play the whole animation, not to
                shift from one frame to the next

            Throws:
                AssertionError
        """

        Tile.__init__(self)
        
        lines = text.split("\n")
        n = 0

        self.texts = []
        for frame in range(frames):
            assert n+height<=len(lines)
            self.texts.append("\n".join(lines[n:n+height]))
            n += height+1

        self.speed = -1 if speed == -1 else speed / len(self.texts)
        self.animidx = -1
        self.animofs = 0

    def __str__(self):
        return "AnimTile, pos: {0}|{1}, frames: {2}, speed: {3}, text:\n{2}".format(\
            self.pos[0],self.pos[1],
            self.GetNumFrames(),
            self.speed,self.text)

    def Next(self):
        """Manually advance to the next frame"""
        self.Set(self.Get()+1)

    def Get(self):
        """Get the current frame index"""
        return self.animidx

    def Set(self,idx):
        """Set the current animation frame """
        self.animofs = idx-self.animidx
        self.animidx = idx

        if self.speed==-1:
            self._UpdateAnim()

    def GetNumFrames(self):
        """Get the number of valid animation frames"""
        return len(self.texts)

    def GotoRandom(self):
        """Advance to a random frame"""
        self.Set(random.randint(0,self.GetNumFrames()-1))

    def Update(self,time_elapsed,time_delta,game):
        """Overridden from Entity"""
        if self.speed == -1:
            return
            
        animidx = time_elapsed // self.speed + self.animofs
        if self.animidx == animidx:
            return

        self.animidx = animidx
        self._UpdateAnim()

    def _UpdateAnim(self):
        self.text = self.texts[int(self.animidx) % self.GetNumFrames()]
        self._Recache()
        

class TileLoader:
    """Utility class to load static or animated sets of tiles from
    unformatted ASCII text files"""

    cache = {}
    
    @staticmethod
    def Load(file,game):
        """Load from a file in the following file format:
          <exec-statement>
          <raw>
        Any occurence of <raw> in the <exec-statement> is replaced by
        <raw>. <out> in the Python line denotes the output object,
        one may use 'entity' as well. Other substitutions:
        <game> the current Game instance.
        """

        
        lines = TileLoader.cache.get(file,None)

        if lines is None:
            try:
                print("Loading tile from "+file)
                with open(file,"rt") as f:
                    lines = f.read().split("\n",1)
                    assert len(lines)==2

                    TileLoader.cache[file] = lines
                      
            except IOError:
                print("Could not open "+file+" for reading")

            except AssertionError as err:
                print("File "+file+" is not well-formatted:")
                print(err)

        if lines is None:
            return Tile()

        replace = {
            "<out>"  : "entity",
            "<raw>"  : 'r"""'+lines[1].rstrip()+' """',
            "<game>" : "game"
        }

        l = lines[0]
        for k,v in replace.items():
            l = l.replace(k,v)

        #print(l)

        tempdict = dict(locals())
        exec(l,globals(),tempdict)
        return tempdict.get("entity",Tile())

        
    

    

    

    

    
