
# PySFML
import sf

# My own stuff
import defaults
from game import Entity,TileLoader,Game,Tile

class Player(Entity):
    """Special entity which responds to user input and moves the
    player tiles accordingly. This entity is unique within a
    single game. """

    ANIM_RIGHT,ANIM_JUMP_RIGHT,ANIM_LEFT,ANIM_JUMP_LEFT = range(4)
    MAX_ANIMS = 4

    def __init__(self,text,game):
        Entity.__init__(self)
        self.game = game
        self.vel = [0,0]
        self.acc = [0,defaults.gravity]
        self.can_jump = True
        self.cur_tile = [Player.ANIM_RIGHT]

        lines = text.split("\n")
        height = len(lines)//Player.MAX_ANIMS

        self.tiles = []
        for i in range(0,(len(lines)//height)*height,height):
            self.tiles.append(Tile("\n".join(lines[i:i+height])))
            self.tiles[-1].SetPosition((0,1))

        assert len(self.tiles) == Player.MAX_ANIMS

    def SetPosition(self,pos):
        #for tile in self.tiles:
        #    tile.SetPosition(pos)
        pass

    def SetColor(self,pos):
        for tile in self.tiles:
            tile.SetColor(pos)

    def Update(self,time_elapsed,time,game):
        inp = self.game.GetApp().GetInput()
        vec = [0,0]

        pvely = self.vel[1]

        if inp.IsKeyDown(sf.Key.Left):
            self.vel[0] = -defaults.move_speed[0]
            self.cur_tile[0] = Player.ANIM_LEFT
            
        if inp.IsKeyDown(sf.Key.Right):
            self.vel[0] = defaults.move_speed[0]
            self.cur_tile[0] = Player.ANIM_RIGHT

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

                    self.cur_tile.append(Player.ANIM_JUMP_LEFT if \
                        self.cur_tile[-1] == Player.ANIM_LEFT else Player.ANIM_JUMP_RIGHT)
            #else:
            #    self.can_jump = True

        #if inp.IsKeyDown(sf.Key.):
            
            
        self.vel[0] += self.acc[0]*time
        self.vel[1] += self.acc[1]*time

        vec[0] += self.vel[0]*time
        vec[1] += self.vel[1]*time

        if pvely > 0 and self.vel[1]<0:
            del self.cur_tile[-1] 
            
        self.pos[0] += vec[0]
        self.pos[1] += vec[1]

        # (HACK) -- for debugging, prevent the player from falling below the map
        if defaults.debug_prevent_fall_down and self.pos[1]<1:
            self.pos[1] = 1
            self.can_jump = True
            self.vel[1] = 0

        self.vel[0] = 0

        self._UpdatePostFX(game)


    def _UpdatePostFX(self,game):
        game.effect.SetParameter("cur",
            self.pos[0]/defaults.tiles[0],
            self.pos[1]/defaults.tiles[1])   


    def Draw(self,game):
        self.tiles[self.cur_tile[-1]].DrawRelative(self.game,self.pos)
