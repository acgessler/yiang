#!echo "This file is not executable"
# -*- coding: UTF_8 -*-

#/////////////////////////////////////////////////////////////////////////////////
# Yet Another Jump'n'Run Game, unfair this time.
# (c) 2010 Alexander Christoph Gessler
#
# HIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO self.event SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
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
import random
import sys
import os
import itertools
import math

# My own stuff
import defaults
from fonts import FontCache
from keys import KeyMapping
from game import Game
from log import Log
from renderer import Renderer,Drawable
from posteffect import PostFXCache,FadeInOverlay,FadeOutOverlay

# numeric constants for the menu entries
OPTION_NEWGAME,OPTION_RESUME,OPTION_TUTORIAL,OPTION_CHOOSELEVEL,OPTION_PREFS,OPTION_CREDITS,OPTION_QUIT, = range(7)

# special level numbers, these levels aren't in the regular map rotation
SPECIAL_LEVEL_TUTORIAL = 10000

def get_level_count():
    """Get the number of levels in the data/levels folder."""
    global level_count
    if "level_count" in globals():
        return level_count
    
    for level_count in itertools.count(1):
        f = os.path.join(defaults.data_dir,"levels","{0}.txt".format(level_count))
        if not os.path.exists(f):
            break

    level_count -= 1

    print("cache level count: {0}".format(level_count))
    return level_count


def sf_string_with_shadow(text,font_name,size,x,y,color,bgcolor=sf.Color(100,100,100),shadow_diff=0):
    """Spawn a string with a shadow behind, which is actually the same
    string in a different color, moved and scaled slightly. Return a
    2-tuple (a,b) where a is the shadow string"""

    font = FontCache.get(size, font_name)
    
    tex = sf.String(text,Font=font,Size=size)
    tex.SetPosition(x,y)
    tex.SetColor(color)


    font = FontCache.get(size+shadow_diff, font_name)

    tex2 = sf.String(text,Font=font,Size=size+shadow_diff)
    tex2.SetPosition(x-5*(size/80.0),y-1*(size/80.0)) # found by guess
    tex2.SetColor(bgcolor)

    return (tex2,tex)


def sf_string(text,font_name,size,x,y,color):
    """Create a sf.String from the given parameters and
    return it. Unlike XXX_with_shadow, this method does not
    supplement a drop shadow."""
    
    font = FontCache.get(size, font_name)
    
    tex = sf.String(text,Font=font,Size=size)
    tex.SetPosition(x,y)
    tex.SetColor(color)

    return tex


class MainMenu(Drawable):
    """This class is responsible for displaying the main menu
    and to initiate games according to the user's decisions"""

    def __init__(self):
        Drawable.__init__(self)

        # Load the font for the intro
        self.font = FontCache.get(defaults.letter_height_intro)

        # Load the PostFX (I had to try them ...)
        self.effect = PostFXCache.Get("intro.sfx")
            
        self.cur_option = 0
        self.menu_text = [(None,None)]*len(MainMenu.options)
        self.game = None
        self.swallow_escape = False
        self.ttl = 0

        self.clock = sf.Clock()
        self.images = []
        self._LoadImages()

        print("Entering main menu")
        self.SetMenuOption(0)

        Renderer.SetClearColor(sf.Color.White)

    def _OptionsQuit(self):
        Renderer.Quit()

    def _OptionsCredits(self):
        print("Credits!")
        self.ShowCredits()

    def _OptionsNewGame(self):
        if not self.game is None:
            
            accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
            def on_close(key, accepted=accepted, outer=self):
                if key == accepted[1]:
                    
                    outer.game = Game(Renderer.app)
                    outer.game.LoadLevel(1)
                    outer._OptionsResumeGame()
                    return
                
                    
            self.game._FadeOutAndShowStatusNotice(defaults.game_over_fade_time,
            sf.String(("""You are currently in a game. 
If you start a new game, all your progress will be lost.

Hit {0} to continue
Hit {1} to cancel""").format(
                    KeyMapping.GetString("accept"),
                    KeyMapping.GetString("escape")
                ),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
        )), (550, 120), 0.0, accepted, sf.Color.Black, on_close) 
            
        else:
            self.game = Game(Renderer.app)
            self.game.LoadLevel(1)
            self._OptionsResumeGame()

    def _OptionsTutorial(self):
        self.game = Game(Renderer.app)
        self.game.LoadLevel(SPECIAL_LEVEL_TUTORIAL)
        self._OptionsResumeGame()

    def _OptionsNewGameChoose(self):
        self.ChooseLevel()

    def _OptionsResumeGame(self):
        if self.game is None:
            return

        Renderer.AddDrawable(self.game,self)
        
        #if self.game.Run() is True:
        #    self.swallow_escape = True

        #    if self.game.IsGameOver():
        #        self.game = None
            

    options = [
        ("New Game", _OptionsNewGame, "You will die",1.0),
        ("Resume Game", _OptionsResumeGame, "You will die soon",0.4),
        ("Start Tutorial", _OptionsTutorial, "You will die",0.4),
        ("Choose Level", _OptionsNewGameChoose, "Bad idea",0.4),
        ("Preferences", _OptionsCredits, "Options",1.0),
        ("Credits", _OptionsCredits, "CREDITS",1.0),
        ("Quit!", _OptionsQuit ,"",1.0)
    ]


    def _LoadImages(self):
        # actually this is not used atm
        if defaults.enable_menu_image_bg is True:
            img = sf.Image()
            if not img.LoadFromFile(os.path.join(defaults.data_dir, "splash", "menu1.png")):
                print("failure loading menu bg")

            self.images.append(img)

    def GetDrawOrder(self):
        """Drawable's are drawn with ascending draw order"""
        return 1000
    
    def Draw(self):
        
        if not self.game is None and self.game.IsGameOver():
            self.game = None
        
        Renderer.SetClearColor(sf.Color.White)
        for event in Renderer.GetEvents():
            # Escape key : exit
            if event.Type == sf.Event.KeyPressed:
                if event.Key.Code == KeyMapping.Get("escape") and self.swallow_escape is False:
                    Renderer.Quit()
                    return

                elif event.Key.Code == KeyMapping.Get("accept"):
                    print("Enter menu entry {0}".format(self.cur_option))
                    MainMenu.options[self.cur_option][1] (self)
                
                elif event.Key.Code == KeyMapping.Get("menu-down"):
                    self.SetMenuOption(self.cur_option+1)
                     
                elif event.Key.Code == KeyMapping.Get("menu-up"):
                    self.SetMenuOption(self.cur_option-1)

            elif event.Type == sf.Event.KeyReleased and event.Key.Code == KeyMapping.Get("escape"):
                self.swallow_escape = False

            if event.Type == sf.Event.Resized:
                assert False

        self.DrawBackground()
        for entry in itertools.chain(self.menu_text):
            Renderer.app.Draw(entry)

    def SetMenuOption(self,i):
        """Choose the currently selected main menu option, entries
        are enumerated by the global 'options' array. """
        self.cur_option = i % len(MainMenu.options)
        print("Select menu option {0}".format(self.cur_option))

        height = 80
        y = 120
        for i in range(self.cur_option):
            y -= height*MainMenu.options[i][3]
        
        
        for i in range(len(MainMenu.options)):
            hscaled = int(MainMenu.options[i][3]*height*(defaults.scale[1]))
            self.menu_text[i] = sf_string_with_shadow(
                MainMenu.options[i][0],
                defaults.font_menu,
                hscaled,
                100,
                y,
                (sf.Color(100,100,100) if self.cur_option == OPTION_RESUME and self.game is None else sf.Color.Red) 
                    if self.cur_option==i else sf.Color.White )

            y += hscaled*1.5
        

    def RecacheDangerSigns(self):
        """Regenerate the dangerous, red flashing matrix-like ghost texts"""
        scale = 8
        color = sf.Color.Red if self.cur_option == OPTION_CREDITS else sf.Color(100,100,100)
        count = 2 if self.cur_option == OPTION_CREDITS else 10
        
        out = []
        for i in range(random.randint(0,count)):
            tex = sf.String(MainMenu.options[self.cur_option][2],Font=self.font,Size=defaults.letter_height_intro*scale)
            tex.SetPosition(random.randint(-defaults.resolution[0],defaults.resolution[0]),
                random.randint(-10,defaults.resolution[1]))
            tex.SetColor(color)

            out.append(tex)
        return out

    def DrawBackground(self):
        """Draw the fuzzy menu background """           
        s = ""
        abc = "abcdefghijklmnopqrstuvABCDEFGHJIKLMNOPQRSTUVWXYZ#@/^%$"
        for y in range(defaults.cells_intro[1]):
            for x in range(defaults.cells_intro[0]):
                s += random.choice(abc)
                
            s += "\n"
               
        text = sf.String(s,Font=self.font,Size=defaults.letter_height_intro)
        text.SetPosition(0,0)
        text.SetColor(sf.Color.Black)
        Renderer.app.Draw(text)

        # if self.ttl == 0:
        #    self.cached_danger_signs = self.RecacheDangerSigns()
        #    self.ttl = defaults.danger_signs_ttl
        # self.ttl = self.ttl-1
            
        #for te in self.cached_danger_signs:
        #    Renderer.app.Draw(te)

        #self.effect.SetParameter("strength", (math.sin( self.clock.GetElapsedTime()/20.0 ) +1)*0.5);
        
        if not self.effect is None:
            self.effect.Draw()

        for image in self.images:
            sprite = sf.Sprite(image)
            sprite.SetPosition(0,0)
            sprite.Resize(defaults.resolution[0],defaults.resolution[1])
            sprite.SetBlendMode(sf.Blend.Alpha)
            
            Renderer.app.Draw(sprite)

    def ChooseLevel(self):
        """Switch to the choose level menu option and return the selected
        level. 0 is returned if the user cancels the operation"""

        
        class LevelChooser(Drawable):

            def __init__(self,outer):
                
                self.base_height = 90
                self.base_offset = (35,35)

                self.height = int(self.base_height*defaults.scale[1])
                self.width_spacing, self.height_spacing = int(self.height*1.55),int(self.height*1.2)

                self.outer = outer
                self.num   = get_level_count()+1
                self.xnum  = (defaults.resolution[0]-self.base_offset[0]*2)//self.width_spacing
                self.rows  = math.ceil( self.num/self.xnum )
                self.level = 1

            def _BackToMenu(self):
                Renderer.RemoveDrawable(self)
                
            def Draw(self):
                for event in Renderer.GetEvents():
                    if event.Type == sf.Event.KeyPressed:
                    
                        if event.Key.Code == KeyMapping.Get("escape"):
                            return self._BackToMenu()

                        elif event.Key.Code == KeyMapping.Get("menu-right"):
                            self.level = (self.level+1)%(self.num)

                        elif event.Key.Code == KeyMapping.Get("menu-left"):
                            self.level = (self.level-1)%(self.num)

                        elif event.Key.Code == KeyMapping.Get("menu-down"):
                            self.level = (self.level+self.xnum)%(self.num)

                            # improve the usability of the 'return to menu' field
                            if (self.level // self.xnum) == self.rows-1:
                                self.level = self.num

                        elif event.Key.Code == KeyMapping.Get("menu-up"):
                            self.level = (self.level-self.xnum)%(self.num)

                        elif event.Key.Code == KeyMapping.Get("accept"):
                            if self.level == self.num:
                                return self._BackToMenu()
                            
                            self.outer.game = Game(Renderer.app)
                            self.outer.game.LoadLevel(self.level)
                            
                            Renderer.RemoveDrawable(self,False)
                            Renderer.AddDrawable(self.outer.game,self.outer)

            
                self.outer.DrawBackground()

                #print(rows,xnum)
                for y in range(self.rows):
                    for x in range(min(self.num - y*self.xnum,self.xnum)):
                        i = y*self.xnum +x +1
                        #print(i)

                        tex2,tex = sf_string_with_shadow(
                            str(i).zfill(2) if i < self.num else "\n... back",
                            defaults.font_menu,
                            self.height,
                            self.base_offset[0]+ (x*self.width_spacing if i < self.num else 0),
                            self.base_offset[1]+y*self.height_spacing,
                            sf.Color.Red if self.level == i else sf.Color.Black )
                        
                        Renderer.app.Draw(tex2)
                        Renderer.app.Draw(tex)

        Renderer.AddDrawable(LevelChooser(self),self)


    def ShowCredits(self):
        """Show the game's credits"""

        class Credits(Drawable):

            def __init__(self,outer):
                self.outer = outer
                try:
                    with open(os.path.join("..","CREDITS"),"rt") as file:
                        self.cred = list(filter(lambda x:not len(x.strip()) or x[0] != "#", file.readlines()))
                        self.cred.insert(0,"(Press any key to continue)")
                except IOError:
                    print("Failure loading credits file")
                    return

                self.height,self.height_spacing = 30,5

            def _BackToMenu(self):
                Renderer.RemoveDrawable(self)
                Renderer.AddDrawable(self.outer)
                
            def Draw(self):
                for event in Renderer.GetEvents():
                    if event.Type == sf.Event.KeyPressed:
                        return self._BackToMenu()
                        
                self.outer.DrawBackground()

                x,y = 100,50
                for line in self.cred:
                    tex = sf_string(
                        line+("\n" if line[0] == "=" else ""),
                        defaults.font_menu,
                        self.height,
                        x,
                        y,
                        sf.Color.Red if line[0] == "=" else sf.Color.White)

                    y += self.height+self.height_spacing
                    if y > defaults.resolution[1]-100:
                        x+= 500
                        y = 130
                    
                    Renderer.app.Draw(tex)
                
        Renderer.AddDrawable(Credits(self),self)

def main():
    """Main entry point to the application"""

    # Read game.txt, which is the master config file
    #Log.Enable(defaults.enable_log)
    defaults.merge_config(sys.argv[1] if len(sys.argv)>1 else os.path.join(defaults.config_dir,"game.txt"))
    Log.Enable(defaults.enable_log)

    print("Startup ...")
    KeyMapping.LoadFromFile(os.path.join(defaults.config_dir,"key_bindings.txt"))

    Renderer.Initialize()
    
    Renderer.AddDrawable(MainMenu())
    Renderer.AddDrawable(FadeInOverlay(fade_time=0.8,fade_start=0.0,draworder=50000))
    
    Renderer.DoLoop()
    
    Renderer.Terminate()
    
main()
