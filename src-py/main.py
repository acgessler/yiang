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
from highscore import HighscoreManager
from notification import MessageBox
from audio import SoundEffectCache,BerlinerPhilharmoniker
from achievements import Achievements

# numeric constants for the menu entries
OPTION_RESUME,OPTION_NEWCAMPAGIN,OPTION_NEWGAME,OPTION_TUTORIAL,OPTION_CHOOSELEVEL,\
OPTION_PREFS,OPTION_CREDITS,OPTION_QUIT, = range(8)

# special level numbers, these levels aren't in the regular map rotation
SPECIAL_LEVEL_TUTORIAL = 10000
SPECIAL_LEVEL_INTRO = 20000
SPECIAL_LEVEL_CAMPAIGN = 30000
SPECIAL_LEVEL_MENU = 40000

def get_level_count():
    """Get the number of ordered, regular levels in the data/levels folder."""
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
    tex2.SetPosition(x-5*(size/80.0),y-1*(size/80.0)) # found by guessing
    tex2.SetColor(bgcolor)

    return (tex2,tex)


def sf_draw_string_with_shadow(*args,**kwargs):
    t1,t2 = sf_string_with_shadow(*args,**kwargs)
    Renderer.app.Draw(t1)
    Renderer.app.Draw(t2)

def sf_string(text,font_name,size,x,y,color):
    """Create a sf.String from the given parameters and
    return it. Unlike XXX_with_shadow, this method does not
    supplement a drop shadow."""
    
    font = FontCache.get(size, font_name)
    
    tex = sf.String(text,Font=font,Size=size)
    tex.SetPosition(x,y)
    tex.SetColor(color)

    return tex


SI_CHOOSE_LEVEL,SI_NONE,SI_HIGHSCORE,SI_CREDITS,SI_ACHIEVEMENTS=range(5)

class MainMenu(Drawable):
    """This class is responsible for displaying the main menu
    and to initiate games according to the user's decisions"""

    def __init__(self):
        Drawable.__init__(self)

        # Load the font for the intro
        self.font = FontCache.get(defaults.letter_height_intro)

        # Load the PostFX (I had to try them ...)
        self.effect = PostFXCache.Get("intro.sfx")

        self.cur_option = 4
        self.menu_text = [(None,None)]*len(MainMenu.options)
        self.game = None
        self.swallow_escape = False
        self.ttl = 0
        
        self.block = False
        self.subindex = SI_NONE

        self.clock = sf.Clock()
        self.images = [ ]
        
        from textures import TextureCache
        img = TextureCache.Get(os.path.join(defaults.data_dir,"textures","title_small.png"))
        
        sp = sf.Sprite(img)
        
        x,y =  int(img.GetWidth()*defaults.scale[0]/2),int(img.GetHeight()*defaults.scale[0]/2)
        sp.SetPosition((defaults.resolution[0]-x)/2,10)
        sp.Resize(x,y)
        self.images.append(sp)

        print("Entering main menu")
        self.SetMenuOption(self.cur_option,first=True)

        self.bggame = Game(mode=Game.BACKGROUND,undecorated=True)
        if self.bggame.LoadLevel(SPECIAL_LEVEL_MENU,no_loadscreen=True):
            self.AddSlaveDrawable(self.bggame)

    def _OptionsQuit(self):
        Renderer.Quit()

    def _OptionsCredits(self):
        self.subindex = SI_CREDITS

    def _OptionsNewGame(self):
        def settune():
            if defaults.no_bg_sound is False:
                SoundEffectCache.Get("logo.ogg").Play()
                
        self._TryStartGameFromLevel(1,on_loaded=settune)
        
    def _OptionsNewCampaignGame(self):
        def settune():
            if defaults.no_bg_sound is False:
                SoundEffectCache.Get("logo.ogg").Play()
            
        self._TryStartGameFromLevel(SPECIAL_LEVEL_CAMPAIGN,mode=Game.CAMPAIGN,on_loaded=settune)
        

    def _OptionsTutorial(self):
        self._TryStartGameFromLevel(SPECIAL_LEVEL_TUTORIAL,mode=Game.SINGLE)

    def _OptionsNewGameChoose(self):
        self.subindex = SI_CHOOSE_LEVEL
        
    def _OptionsShowAchievements(self):
        self.subindex = SI_ACHIEVEMENTS
        
    def _OptionsViewHighscore(self):
        import webbrowser
        webbrowser.open(defaults.homepage_url+"/highscore.html",)

    def _OptionsResumeGame(self):
        if self.game is None:
            return

        Renderer.AddDrawable(self.game,self)
        
    def _OptionsNotImplemented(self):
        
        def on_close(result):
            self.block = False
                        
        self.block = True
        accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
        Renderer.AddDrawable( MessageBox(sf.String("""This feature is not currently implemented, sorry.""",
            Size=defaults.letter_height_game_over,
            Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
        )), defaults.game_over_fade_time, (550, 50), 0.0, accepted, sf.Color.Black, on_close))
        
    def _OptionsLoadGame(self):
        pass
    
    def _OptionsSaveGame(self):
        pass
            

    options = [
        ("Resume Game", _OptionsResumeGame, "You will die soon",0.4,False),
        ("Campaign", _OptionsNewCampaignGame, "You will die",1.0,False),
        ("Load", _OptionsLoadGame, "You will die soon",0.7,False),
        ("Save", _OptionsSaveGame, "You will die soon",0.5,False),
        ("Quick Game", _OptionsNewGame, "You will die",1.0,False),
        ("Start Tutorial", _OptionsTutorial, "You will die",0.5,False),
        ("Choose Level", _OptionsNewGameChoose, "Bad idea",0.35,False),
        ("Achievements", _OptionsShowAchievements, "Updates!",0.7,False),
     #   ("Preferences", _OptionsNotImplemented, "Options",1.0),
        ("Credits", _OptionsCredits, "CREDITS",0.4,False),
        ("Online Highscore", _OptionsViewHighscore, "Updates!",0.35,False),
        ("Check for Updates", _OptionsNotImplemented, "Updates!",0.35,False),
        ("Quit!", _OptionsQuit ,"",1.0,False)
    ]
    
    def _TryStartGameFromLevel(self,level,old=None,mode=Game.QUICKGAME,on_loaded=lambda:None):
        if old is None:
            old = self
            
        if not self.game is None:
            
            accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
            def on_close(key):
                if key == accepted[1]:
                    self.game = None
                    self._TryStartGameFromLevel(level,old,mode,on_loaded)
                
            Renderer.AddDrawable( MessageBox(sf.String("""You are currently in a game. 
If you start a new game, all your progress will be lost.

Hit {0} to continue
Hit {1} to cancel""".format(
                    KeyMapping.GetString("accept"),
                    KeyMapping.GetString("escape")
                ),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
            )), defaults.game_over_fade_time, (550, 120), 0.0, accepted, sf.Color.Black, on_close))
            
        else:
        
            self.game = Game(mode=mode)
            Renderer.AddDrawable(self.game,old)
            
            self.game.LoadLevel(level)
            on_loaded()
            

    def GetDrawOrder(self):
        """Drawable's are drawn with ascending draw order"""
        return 1000
    
    def GetCurrentGame(self):
        """Get the currently active Game or None if none is active"""
        return self.game
    
    def Draw(self):
        if not self.game is None and self.game.IsGameOver():
            self.game = None
        
        Renderer.SetClearColor(sf.Color.Black)

        rx,ry = defaults.resolution
        bb = (-10,160,350*defaults.scale[1],ry-60)    

        if not hasattr(self,"m_clock"):
            self.m_clock = sf.Clock()
                  
        self._DrawRectangle(bb,scale=min(1.0, self.m_clock.GetElapsedTime()))
        
        self.base_x,self.base_y = bb[2],bb[1]

        #self.DrawBackground()
        for entry in itertools.chain(self.menu_text):
            Renderer.app.Draw(entry)
            
        a,b = sf_string_with_shadow(
                "Best result so far: $ {0:.4}".format(HighscoreManager.GetHighscoreRecord()/100),
                defaults.font_menu,
                int(20*defaults.scale[1]),
                int(defaults.resolution[0]-225*defaults.scale[1]),
                10,
                sf.Color.Green)
        Renderer.app.Draw(a); 
        Renderer.app.Draw(b)
        
        if self.subindex == SI_CHOOSE_LEVEL:
            self.ChooseLevel()
        elif self.subindex == SI_ACHIEVEMENTS:
            self.ShowAchievements()
        elif self.subindex == SI_CREDITS:
            self.ShowCredits()
            
        if self.block is False:
            for event in Renderer.SwallowEvents():
                # Escape key : exit
                if event.Type == sf.Event.KeyPressed:
                    if event.Key.Code == KeyMapping.Get("escape"):
                        Renderer.Quit()
                        return

                    elif event.Key.Code == KeyMapping.Get("accept"):
                        print("Enter menu entry {0}".format(self.cur_option))
                        MainMenu.options[self.cur_option][1] (self)
                
                    elif event.Key.Code == KeyMapping.Get("menu-down"):
                        self.SetMenuOption(self.cur_option+1)
                     
                    elif event.Key.Code == KeyMapping.Get("menu-up"):
                        self.SetMenuOption(self.cur_option-1)

                if event.Type == sf.Event.Resized:
                    assert False
                    
        for image in self.images:
            Renderer.app.Draw(image)
        
    def _DrawRectangle(self,bb,cola=None,colb=None,scale=1.0):
        shape = sf.Shape()
        cola, colb = cola or sf.Color(40,40,40,int(165*scale)), colb or sf.Color(120,120,120,int(165*scale))
        
        shape.AddPoint(bb[0],bb[1],cola,colb)
        shape.AddPoint(bb[2],bb[1],cola,colb)
        shape.AddPoint(bb[2],bb[3],cola,colb)
        shape.AddPoint(bb[0],bb[3],cola,colb)

        shape.EnableFill(True)
        shape.EnableOutline(True)
        shape.SetOutlineWidth(4)
        
        Renderer.app.Draw(shape) 

    def SetMenuOption(self,i,first=False):
        """Choose the currently selected main menu option, entries
        are enumerated by the global 'options' array. """
        self.cur_option = i % len(MainMenu.options)
        print("Select menu option {0}".format(self.cur_option))

        y = 180
        
        for i in range(len(MainMenu.options)):
            hscaled = int(MainMenu.options[i][3]*defaults.letter_height_menu*defaults.scale[1])
            self.menu_text[i] = sf_string_with_shadow(
                MainMenu.options[i][0],
                defaults.font_menu,
                hscaled,
                40,
                y,
                (sf.Color(100,100,100) if self.cur_option == OPTION_RESUME and self.game is None else sf.Color.Red) 
                    if self.cur_option==i else sf.Color.White )

            y += hscaled*1.5
            
        if MainMenu.options[self.cur_option][-1]:
            MainMenu.options[self.cur_option][1] (self)

    def RecacheDangerSigns(self):
        """Regenerate the dangerous, red flashing matrix-like ghost texts"""
        scale = 8
        color = sf.Color.Red if self.cur_option == OPTION_CREDITS else sf.Color(100,100,100)
        count = 2 if self.cur_option == OPTION_CREDITS else 10
        
        out = []
        for i in range(random.randint(0,count)):
            str = MainMenu.options[self.cur_option][2]
            #str = "soon"
            tex = sf.String(str,Font=self.font,Size=defaults.letter_height_intro*scale)
            tex.SetPosition(random.randint(-defaults.resolution[0],defaults.resolution[0]),
                random.randint(-10,defaults.resolution[1]))
            tex.SetColor(color)

            out.append(tex)
        return out

    def DrawBackground(self):
        """Draw the fuzzy menu background """           
        s = ""
        abc = "AGCT_"
        for y in range(defaults.cells_intro[1]):
            for x in range(defaults.cells_intro[0]):
                s += random.choice(abc)
                
            s += "\n"
               
        text = sf.String(s,Font=self.font,Size=defaults.letter_height_intro)
        text.SetPosition(0,0)
        text.SetColor(sf.Color.Black)
        Renderer.app.Draw(text)

        if defaults.enable_menu_background_danger_stubs is True:
            if self.ttl == 0:
                self.cached_danger_signs = self.RecacheDangerSigns()
                self.ttl = defaults.danger_signs_ttl
            self.ttl = self.ttl-1
            
            for te in self.cached_danger_signs:
                Renderer.app.Draw(te)
        
        if not self.effect is None:
            self.effect.Draw()

    def ChooseLevel(self):
        """Switch to the choose level menu option and return the selected
        level. 0 is returned if the user cancels the operation"""

        base_height = 42
        base_offset = (self.base_x+50,self.base_y)
        rx,ry = defaults.resolution

        height = int(base_height*defaults.scale[1])
        width_spacing, height_spacing = int(height*1.55),int(height*1.2)

        num   = get_level_count()+1
        xnum  = int((rx-base_offset[0]-50)//width_spacing)
        rows  = math.ceil( num/xnum )
        self.level = getattr(self,"level", 1)
        bb = (base_offset[0],base_offset[1],rx-40,ry-60)  
        
        def GetBack():
            self.subindex = SI_NONE
            delattr(self,"cl_clock")
            
        if not hasattr(self,"cl_clock"):
            self.cl_clock = sf.Clock()
                  
        self._DrawRectangle(bb,scale=min(1.0, self.cl_clock.GetElapsedTime()*3.0))

        for event in Renderer.SwallowEvents():
            if event.Type == sf.Event.KeyPressed:
            
                if event.Key.Code == KeyMapping.Get("escape"):
                    GetBack()
                    return

                elif event.Key.Code == KeyMapping.Get("menu-right"):
                    self.level = (self.level+1)%(num)

                elif event.Key.Code == KeyMapping.Get("menu-left"):
                    self.level = (self.level-1)%(num)

                elif event.Key.Code == KeyMapping.Get("menu-down"):
                    self.level = (self.level+xnum)%(num)

                elif event.Key.Code == KeyMapping.Get("menu-up"):
                    self.level = (self.level-xnum)%(num)

                elif event.Key.Code == KeyMapping.Get("accept"):
                    
                    GetBack()
                    self._TryStartGameFromLevel(self.level) 
                   
        for y in range(rows):
            for x in range(min(num-1 - y*xnum,xnum)):
                i = y*xnum +x+1 
                #print(i)

                sf_draw_string_with_shadow(
                    str(i).zfill(2) ,
                    defaults.font_menu,
                    height,
                    base_offset[0]+(x*width_spacing) + 20,
                    base_offset[1]+y*height_spacing + 20,
                    sf.Color.Red if self.level == i else sf.Color.White )
                
        height = int(0.7*height)
        from level import LevelLoader
        sf_draw_string_with_shadow(
            "Press {0} to enter Level {1} - '{2}'".format(KeyMapping.GetString("accept"),self.level,LevelLoader.GuessLevelName(self.level)),
            defaults.font_menu,
            height,
            base_offset[0]+20,
            ry - 130*defaults.scale[1] - height*1.2,
            sf.Color.White )
                
        sf_draw_string_with_shadow(
            "Press {0} to return".format(KeyMapping.GetString("escape")),
            defaults.font_menu,
            height,
            base_offset[0]+20,
            ry - 130*defaults.scale[1],
            sf.Color.White )
        
        
    def ShowAchievements(self):
        """Show a list of all achievements, highlight those earned by the player"""

       
        base_height = 24
        base_offset = (self.base_x+50,self.base_y)
        rx,ry = defaults.resolution

        height = int(base_height*defaults.scale[1])
        num = max(1, len(Achievements.all)) # prevent 1/0
        self.achievement = getattr(self,"achievement", 1)
        width_spacing, height_spacing = 290*defaults.scale[1],int(height*1.2)
        maxdesclenperline = (rx - width_spacing - base_offset[0])/(height*0.7)
        
        bb = (base_offset[0],base_offset[1],rx-40,ry-60)        
        
        def GetBack():
            self.subindex = SI_NONE
            delattr(self,"sa_clock")
            
        if not hasattr(self,"sa_clock"):
            self.sa_clock = sf.Clock()
                  
        self._DrawRectangle(bb,scale=min(1.0, self.sa_clock.GetElapsedTime()*3.0))
        
        for event in Renderer.SwallowEvents():
            if event.Type == sf.Event.KeyPressed:
                
                if event.Key.Code == KeyMapping.Get("escape"):
                    GetBack()
                    return

                elif event.Key.Code == KeyMapping.Get("menu-down"):
                    self.achievement = (self.achievement+1)%(num)

                elif event.Key.Code == KeyMapping.Get("menu-up"):
                    self.achievement = (self.achievement-1)%(num)

                else : # event.Key.Code == KeyMapping.Get("accept"):
                    GetBack()
                    return
                        
        for y, ach in zip( range(num), sorted( Achievements.all, key=lambda x: Achievements.GetInfo(x)["order"]) ):
            info = Achievements.GetInfo(ach)

            sf_draw_string_with_shadow(
               info["name"] or "<missing>",
                defaults.font_menu,
                height,
                base_offset[0]+20,
                base_offset[1]+y*height_spacing+20,
                sf.Color.Red if self.achievement == y else sf.Color.White )
            
            if self.achievement == y:
                sf_draw_string_with_shadow(
                   info["icon"],
                    defaults.font_monospace,
                    height,
                    base_offset[0]+width_spacing+20,
                    base_offset[1]+20,
                    sf.Color.Yellow )
           
                out = ""
                for paragraph in  info["desc"].split("\n"):
                    cnt = 0
                    for word in paragraph.split(" "):
                        if cnt + len(word) > maxdesclenperline:
                            out += "\n"
                            cnt = 0
                        out += word + " "
                        cnt += len(word)
                    out += "\n\n"
                
                sf_draw_string_with_shadow(
                    out,
                    defaults.font_menu,
                    height,
                    base_offset[0]+width_spacing+20,
                    base_offset[1]+200*defaults.scale[1]+20,
                    sf.Color(200,200,200) )
                    

    def ShowCredits(self):
        """Show the game's credits"""

        if not hasattr(self,"cred"):
            try:
                with open(os.path.join("..","CREDITS"),"rt",errors="ignore") as file:
                    self.cred = list(filter(lambda x:not len(x.strip()) or x[0] != "#", file.readlines()))
                    #self.cred.insert(0,"(Press any key to continue)")
            except IOError:
                print("Failure loading credits file")
                return

        height = int(defaults.letter_height_credits*defaults.scale[1]*0.9)
        height_spacing = int(5*defaults.scale[1])


        base_offset = (self.base_x+50,self.base_y)
        rx,ry = defaults.resolution
        
        bb = (base_offset[0],base_offset[1],rx-40,ry-60)        
        def GetBack():
            self.subindex = SI_NONE
            delattr(self,"sc_clock")
            
        if not hasattr(self,"sc_clock"):
            self.sc_clock = sf.Clock()
            
        self._DrawRectangle(bb,scale=min(1.0, self.sc_clock.GetElapsedTime()*3.0))
        for event in Renderer.GetEvents():
            if event.Type == sf.Event.KeyPressed:
                GetBack()
                return

        x,y = base_offset
        for line in self.cred:
            
            if y > ry-100 or line[0] == "=" and y > ry-200:
                x+= (rx-100-base_offset[0])/2.0
                y = base_offset[1]+50
            
            sf_draw_string_with_shadow(
                line+("\n" if line[0] == "=" else ""),
                defaults.font_menu,
                height,
                x+40*defaults.scale[0],
                y+20,
                sf.Color.Red if line[0] == "=" else sf.Color.White)

            y += height+height_spacing
            
                    


def main():
    """Main entry point to the application"""

    # Read game.txt, which is the master config file
    #Log.Enable(defaults.enable_log)
    defaults.merge_config(sys.argv[1] if len(sys.argv)>1 else os.path.join(defaults.config_dir,"game.txt"))
    Log.Enable(defaults.enable_log)
    
    import fshack
    fshack.Enable()
    
    import gettext
    gettext.install('yiang', './locale')
        
    print("Startup ...")
    KeyMapping.LoadFromFile(os.path.join(defaults.config_dir,"key_bindings.txt"))

    Renderer.Initialize()
    HighscoreManager.Initialize()
    Achievements.Initialize()
    BerlinerPhilharmoniker.Initialize()
    
    if defaults.no_bg_sound is False:
        try:
            SoundEffectCache.Get("logo.ogg").Play()
        except AttributeError:
            pass
        
    if defaults.no_halos is True:
        defaults.death_sprites = min( 20, defaults.death_sprites )
    
    """
    accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
    def on_close(key, accepted=accepted):
        if key == accepted[1]:
            if defaults.no_bg_music is False:
                class DummyMusicPlayer(Drawable):
                    def Draw(self):
                        BerlinerPhilharmoniker.Process()
                Renderer.AddDrawable(DummyMusicPlayer())
                BerlinerPhilharmoniker.SetAudioSection("menu")
        
            Renderer.AddDrawable(MainMenu())
            #Renderer.AddDrawable(FadeInOverlay(fade_time=0.8,fade_start=0.0,draworder=50000))
            return 
        sys.exit(0)
               
    Renderer.SetClearColor(sf.Color(100,0,0)) 
    Renderer.AddDrawable( MessageBox(sf.String(
Do not continue if you can't read.
    
Hit {0} to continue
Hit {1} to cancel.format(
                    KeyMapping.GetString("accept"),
                    KeyMapping.GetString("escape")
                ),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
            )), defaults.game_over_fade_time, (550, 150), 0.0, accepted, sf.Color(150,0,0), on_close))
    """
    if defaults.no_bg_music is False:
        class DummyMusicPlayer(Drawable):
            def Draw(self):
                BerlinerPhilharmoniker.Process()
        Renderer.AddDrawable(DummyMusicPlayer())
        BerlinerPhilharmoniker.SetAudioSection("menu")

    Renderer.AddDrawable(MainMenu())
    
    Renderer.DoLoop()
    Renderer.Terminate()
    

