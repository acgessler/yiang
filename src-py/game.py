
# PySFML
import sf

# Python Core
import itertools

# My own stuff
import defaults
from fonts import FontCache


class Game:
    """Encapsulates the whole game state, including map tiles,
    enemy and player entities, i.e. ..."""


    def __init__(self, app):
        """ """
        self.app = app
        self.origin = [0,0]

        self.entities = []
        self.tiles = []
        for y in range(defaults.cells[1]):
            self.tiles.append([None]*(defaults.cells[0]*2))

        # Generate the portion of the map that is initially needed
        self.SpawnRandomMap(self.origin,defaults.cells[0])
         
        self.clock = sf.Clock()
        self.total = 0.0
        self.total_accum = 0.0
        self.score = 0

        self.status_bar_font = FontCache.get(defaults.letter_height_status,face=defaults.font_status)

    def Run(self):
        """ """
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
            
            for entity in self.entities:
                entity.Update(time)

            for tiles in itertools.chain.from_iterable(self.tiles):
                if not tiles is None:
                    tiles.Draw(self.app)


            # Finally draw the status bar with the player's score and game duration
            status = sf.String("Time:  {0:4.4}\nScore: {1}".format(self.GetTotalElapsedTime(),self.GetScore()),
                Font=self.status_bar_font,Size=defaults.letter_height_status)
            status.SetColor(sf.Color.Green)
            status.SetPosition(10,10)

            self.app.Draw(status)

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

    def SpawnRandomMap(self,start,outxidx):
        pass


class Tile:
    """Base class for tiles, handles common behaviour, i.e, drawing"""
         
    def __init__(self,text,color,pos):

        self.pos = pos
         
        font = FontCache.get(defaults.letter_height)
        self.cached = sf.Text(text,Font=font,Size=defaults.letter_height)
        self.cached.SetColor(color)

    def Draw(self,game):
        origin = game.GetCurOrigin()
         
        self.cached.SetPosition(self.pos[0]-origin[0],self.pos[1]-origin[1])
        game.app.Draw(self.cached)


class Entity:
    """Base class for all kinds of entities, including the player.
    The term `entity` refers to a state machine which is in control
    of a set of tiles. Unlike individual tiles, entities receive
    Update() callbacks once per logical frame."""

    def __init__(self):
        pass

    def Update(self):
        pass
    


    

    

    

    
