
# PySFML
import sf

# My own stuff
import defaults
from game import Entity,TileLoader,Game,Tile

class Player(Entity):
    """Special entity which responds to user input and moves the
    player tiles accordingly. This entity is unique within a
    single game. """

    def __init__(self,text):
        Entity.__init__(self)
        #self.game = Game.Get()
        self.pos = [0,3] # in tile coordinates
        self.vel = [0,0]
        self.acc = [0,defaults.gravity]
        self.can_jump = True
        self.last_time = 0

        self.tiles = [Tile.CreateSimple("#",sf.Color.White,(0,1)),
            Tile.CreateSimple("#",sf.Color.White,(0,2)),
            Tile.CreateSimple("*",sf.Color.White,(0,3))]

    def Update(self,time_elapsed):
        inp = self.game.GetApp().GetInput()
        
        time = time_elapsed - self.last_time
        self.last_time = time_elapsed
        vec = [0,0]

        if defaults.cheat_allow_updown_move is True:
            if inp.IsKeyDown(sf.Key.Up):
                self.pos[1] += time*defaults.move_speed[1]
            if inp.IsKeyDown(sf.Key.Down):
                self.pos[1] -= time*defaults.move_speed[1]
        else:
            if inp.IsKeyDown(sf.Key.Up):
                if self.can_jump is True:
                    self.vel[1] += defaults.jump_vel
                    self.can_jump = False
            #else:
            #    self.can_jump = True

        #if inp.IsKeyDown(sf.Key.):
            
            
        if inp.IsKeyDown(sf.Key.Left):
            self.vel[0] = -defaults.move_speed[0]
        if inp.IsKeyDown(sf.Key.Right):
            self.vel[0] = defaults.move_speed[0]

        # 

        self.vel[0] += self.acc[0]*time
        self.vel[1] += self.acc[1]*time

        vec[0] += self.vel[0]*time
        vec[1] += self.vel[1]*time
            
        self.pos[0] += vec[0]
        self.pos[1] += vec[1]

        # (HACK) -- for debugging, prevent the player from falling below the map
        if defaults.debug_prevent_fall_down and self.pos[1]<0:
            self.pos[1] = 0
            self.can_jump = True
            self.vel[1] = 0

        self.vel[0] = 0


    def Draw(self):
        for tile in self.tiles:
            tile.DrawRelative(self.game,self.pos)
