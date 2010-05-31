
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
        self.entities = []
        self.level = -1

        # Load the first level for testing purposes
        # self.LoadLevel(1)
         
        self.clock = sf.Clock()
        self.total = 0.0
        self.total_accum = 0.0
        self.score = 0
        self.lives = defaults.lives
        self.last_time = 0

        self.effect = sf.PostFX()
        self.effect.LoadFromFile(os.path.join(defaults.data_dir,"effects","ingame1.sfx"))
        self.effect.SetTexture("framebuffer", None);
        self.effect.SetParameter("cur",0.0,0.0)

        self.status_bar_font = FontCache.get(defaults.letter_height_status,face=defaults.font_status)

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
                # Close window : exit
                # if event.Type == sf.Event.Closed:
                #    self.app.Close()
                #    break

                # Escape key : return to main menu, suspend the game
                if event.Type == sf.Event.KeyPressed:
                    if event.Key.Code == sf.Key.Escape:
                        self.Suspend()
                        continue

            self.app.Clear(sf.Color.Black)
                
            time = self.clock.GetElapsedTime()
            self.total = time+self.total_accum

            dtime = time - self.last_time
            self.last_time = time

            self.origin[0] += dtime*defaults.move_map_speed
            
            for entity in self.entities:
                entity.Update(time,dtime,self)

            for entity in self.entities:
                entity.Draw(self)

            self.app.Draw(self.effect)

            # Now draw the status bar with the player's score and game duration
            status = sf.String("Time:  {0:4.4}\nScore: {1}".format(self.GetTotalElapsedTime(),self.GetScore()),
                Font=self.status_bar_font,Size=defaults.letter_height_status)
            status.SetColor(sf.Color.White)
            status.SetPosition(10,10)

            self.app.Draw(status)

            # Toggle buffers 
            self.app.Display()

        self.total_accum += self.clock.GetElapsedTime()
        print("Leave mainloop")
        return True

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
        """ Get the total duration of this game, not counting in
        suspend times. The return valuue is in seconds. """
        return self.total

    def GetScore(self):
        """ Get the total, accumulated score up to now.
        The score is an integer. """
        return self.score

    def Award(self,points):
        """ Award a certain amount of points to the player's
        score as a reward for extreme skillz."""
        self.score += points

    def Kill(self):
        """Kill the player immediately, set game over state"""
        pass

    def Draw(self,drawable,pos):
        """ Draw a sf.Drawable at a specific position, which is
        specified in tile coordinates."""

        # (invert y, so the lower left corner is the cooordinate system origin)
        drawable.SetPosition((pos[0]-self.origin[0]) * defaults.tiles_size[0] * defaults.letter_size[0],
            defaults.resolution[1] - (pos[1]-self.origin[1]+1) * defaults.tiles_size[1] * defaults.letter_size[1])
        
        self.app.Draw(drawable)

    def LoadLevel(self,level):
        """Load a particular level"""

        print("Loading level from disc: "+str(level))
        self.level = level
        self.entities = []

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
                        tile.SetPosition((x//3, defaults.tiles[1] - y + diff-1))

                        self.entities.append(tile)

            print("Got {0} entities for level {1}".format(len(self.entities),level))
                
        except IOError:
            print("Failure loading level "+str(level))

        except AssertionError as err:
            print("Level "+str(level)+" is not well-formatted:")
            print(err)
    

class Entity:
    """Base class for all kinds of entities, including the player.
    The term `entity` refers to a state machine which is in control
    of a set of tiles. Entities receive Update() callbacks once per
    logical frame."""

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

    def CheckCollision(self,rect,game):
        return None

    def Interact(self,game):
        pass


class Tile(Entity):
    """Base class for tiles, handles common behaviour, i.e, drawing"""
         
    def __init__(self,text="<no text specified>"):
        Entity.__init__(self)

        self.text = text
        self._Recache()

    def SetColor(self,color):
        Entity.SetColor(self,color)
        self.cached.SetColor(self.color)

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

        
    

    

    

    

    
