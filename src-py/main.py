#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [main.py]
# (c) 2008-2011 Yiang Development Team
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
from renderer import Renderer,Drawable,NewFrame
from posteffect import PostFXCache,FadeInOverlay,FadeOutOverlay
from highscore import HighscoreManager
from notification import MessageBox
from audio import SoundEffectCache,BerlinerPhilharmoniker
from achievements import Achievements

import preboot # preboot.py *must* be loaded first ----- but if we do so,
# we end up with strange tile scalings.

# numeric constants for the menu entries
OPTION_RESUME,OPTION_NEWCAMPAGIN,OPTION_NEWGAME,OPTION_TUTORIAL,OPTION_CHOOSELEVEL,\
OPTION_PREFS,OPTION_CREDITS,OPTION_QUIT, = range(8)

# special level numbers, these levels aren't in the regular map rotation
SPECIAL_LEVEL_TUTORIAL = 10000
SPECIAL_LEVEL_INTRO = 20000
SPECIAL_LEVEL_CAMPAIGN = 30000

SPECIAL_LEVEL_MENUBG_START = 40000
SPECIAL_LEVEL_MENUBG_END = -1


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


def sf_string_with_shadow(text,font_name,size,x,y,color,bgcolor=sf.Color(0,0,0),shadow_diff=0):
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
        self.menu_text = [None]*len(MainMenu.options)
        self.game = None
        self.swallow_escape = False
        self.ttl = 0
        
        self.block = False
        self.subindex = SI_NONE

        self.clock = sf.Clock()
        self.images = [ ]
        
        # uncomment to enable a logo image at the top of the menu screen
        """
        from textures import TextureCache
        img = TextureCache.Get(os.path.join(defaults.data_dir,"textures","title_small.png"))
        
        sp = sf.Sprite(img)
        
        x,y =  int(img.GetWidth()*defaults.scale[0]/2),int(img.GetHeight()*defaults.scale[0]/2)
        sp.SetPosition((defaults.resolution[0]-x)/2,10)
        sp.Resize(x,y)
        self.images.append(sp)
        """

        print("Entering main menu")
        self.SetMenuOption(self.cur_option,first=True)
        
        # copy'n'paste from loadsceen.py
        global SPECIAL_LEVEL_MENUBG_END
        if SPECIAL_LEVEL_MENUBG_END < SPECIAL_LEVEL_MENUBG_START:
            from level import LevelLoader
            
            m = SPECIAL_LEVEL_MENUBG_START-1
            for n,readonly in sorted(LevelLoader.EnumLevelIndices()):
                if n < SPECIAL_LEVEL_MENUBG_START:
                    continue
                if n-m != 1:
                    break
                m = n
                
            SPECIAL_LEVEL_MENUBG_END = m+1
            
        import random
        self.bggame = Game(mode=Game.BACKGROUND,undecorated=True)
        if self.bggame.LoadLevel(random.randint(SPECIAL_LEVEL_MENUBG_START,SPECIAL_LEVEL_MENUBG_END-1),no_loadscreen=True):
            self.AddSlaveDrawable(self.bggame)

    def _OptionsQuit(self):
        self.AskQuit()

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
        #import webbrowser
        #webbrowser.open(defaults.homepage_url+"/highscore.html",)
        
        self.subindex = SI_HIGHSCORE

    def _OptionsResumeGame(self):
        if self.game is None:
            return

        Renderer.AddDrawable(self.game,self)
        
    def _OptionsNotImplemented(self):
        
        def on_close(result):
            self.block = False
                        
        self.block = True
        accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
        Renderer.AddDrawable( MessageBox(sf.String(_("""This feature is not currently implemented, sorry."""),
            Size=defaults.letter_height_game_over,
            Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
        )), defaults.game_over_fade_time, (550, 50), 0.0, accepted, sf.Color.Black, on_close))
        
    def _OptionsLoadGame(self):
        pass
    
    def _OptionsSaveGame(self):
        pass
            

    options = [ # don't need [2] anymore
        [_("Resume Game"), _OptionsResumeGame, None,0.4,False, False],
        [_("New Campaign"), _OptionsNewCampaignGame, None,1.0,False, True],
        [_("Load"), _OptionsLoadGame, None,0.7,False, True],
        [_("Save"), _OptionsSaveGame, None,0.5,False, False],
        [_("Quick Game"), _OptionsNewGame, None,0.85,False, True],
        [_("Start Tutorial"), _OptionsTutorial, None,0.5,False, True],
        [_("Choose Level"), _OptionsNewGameChoose, None,0.35,False, True],
        [_("Achievements"), _OptionsShowAchievements, None,0.7,False,True],
     #   ("Preferences", _OptionsNotImplemented, "Options",1.0),
        [_("Credits"), _OptionsCredits, None,0.4,False,True],
        [_("Online Highscore"), _OptionsViewHighscore, None,0.35,False,True],
        [_("Check for Updates"), _OptionsNotImplemented, None,0.35,False,True],
        [_("Quit!"), _OptionsQuit ,None,1.0,False,True]
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
                
            Renderer.AddDrawable( MessageBox(sf.String(_("""You are currently in a game. 
If you start a new game, all your progress will be lost.

Hit {0} to continue
Hit {1} to cancel""").format(
                    KeyMapping.GetString("accept"),
                    KeyMapping.GetString("escape")
                ),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
            )), defaults.game_over_fade_time, (550, 120), 0.0, accepted, sf.Color.Black, on_close))
            
        else:
        
            self._SetGame(Game(mode=mode))
            Renderer.AddDrawable(self.game,old)
            self.game.LoadLevel(level,False)
            
            on_loaded()
            
    def _SetGame(self, game):
        self.game = game
        self.EnableMenu(0, not not game)
        self.EnableMenu(3, not not game)

    def GetDrawOrder(self):
        """Drawable's are drawn with ascending draw order"""
        return 1000
    
    def GetCurrentGame(self):
        """Get the currently active Game or None if none is active"""
        return self.game
    
    def AskQuit(self):
        if not self.GetCurrentGame():
            Renderer.Quit()
            
        accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
        def on_close(key):
            if key == accepted[1]:
                Renderer.Quit()
            
        Renderer.AddDrawable( MessageBox(sf.String(_("""You are currently in a game. 
If you quit without saving, all your progress will be lost.

Hit {0} to continue without fear
Hit {1} to reconsider your decision""").format(
                KeyMapping.GetString("accept"),
                KeyMapping.GetString("escape")
            ),
            Size=defaults.letter_height_game_over,
            Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
        )), defaults.game_over_fade_time, (550, 120), 0.0, accepted, sf.Color.Black, on_close))
    
    def Draw(self):
        # game over? drop our reference to it.
        if self.game and self.game.IsGameOver():
            self._SetGame(None)
        
        Renderer.SetClearColor(sf.Color.Black)

        rx,ry = defaults.resolution
        bb = (-10,160,375*defaults.scale[1],ry-60)    

        if not hasattr(self,"m_clock"):
            self.m_clock = sf.Clock()
                  
        #self._DrawRectangle(bb,scale=min(1.0, self.m_clock.GetElapsedTime()))
        
        self.base_x,self.base_y = bb[2],bb[1]

        #self.DrawBackground()
        for entry in itertools.chain(self.menu_text):
            if entry:
                Renderer.app.Draw(entry)
            
        a,b = sf_string_with_shadow(
                _("Profile: {1} / best result so far: $ {0:.4}").format(HighscoreManager.GetHighscoreRecord()/100,defaults.cur_user_profile),
                defaults.font_menu,
                int(20*defaults.scale[1]),
                int(defaults.resolution[0]-425*defaults.scale[1]),
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
        elif self.subindex == SI_HIGHSCORE:
            self.ShowHighscore()
            
        if self.block is False:
            for event in Renderer.SwallowEvents():
                # Escape key : exit
                if event.Type == sf.Event.KeyPressed:
                    if event.Key.Code == KeyMapping.Get("escape"):
                        self.AskQuit()
                        return

                    elif event.Key.Code == KeyMapping.Get("accept"):
                        print("Enter menu entry {0}".format(self.cur_option))
                        MainMenu.options[self.cur_option][1] (self)
                
                    elif event.Key.Code == KeyMapping.Get("menu-down"):
                        self.SetMenuOption(self.cur_option+1)
                     
                    elif event.Key.Code == KeyMapping.Get("menu-up"):
                        self.SetMenuOption(self.cur_option-1)

                if event.Type == sf.Event.Resized:
                    continue
                
                if event.Type == sf.Event.Closed: # XXX currently processed in Renderer
                    self.AskQuit()
                    
        for image in self.images:
            Renderer.app.Draw(image)
            
        if self.m_clock.GetElapsedTime() > 2:
            Achievements.CheckAcknowledgeStatus()
        
    def _DrawRectangle(self,bb,cola=None,colb=None,scale=1.0):
        shape = sf.Shape()
        basea = 255 if defaults.no_ppfx else 175 
        cola, colb = cola or sf.Color(40,40,40,int(basea*scale)), colb or sf.Color(120,120,120,int(basea*scale))
        
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

        y = 180 * defaults.scale[1]
        
        for i in range(len(MainMenu.options)):
            opt = MainMenu.options[i]
            if not opt[5]:
                self.menu_text[i] = None
                continue
            
            hscaled = int(opt[3]*defaults.letter_height_menu*defaults.scale[1])
            self.menu_text[i] = sf_string_with_shadow(
                 opt[0],
                 defaults.font_menu,
                 hscaled,
                 40,
                 y,
                 sf.Color.Red if self.cur_option==i else sf.Color.White )           
            

            y += hscaled*1.5
            
        if MainMenu.options[self.cur_option][4]:
            MainMenu.options[self.cur_option][4] (self)
            
    def UpdateMenu(self):
        return self.SetMenuOption(self.cur_option)
    
    def ToggleMenu(self, which):
        MainMenu.options[which][5] = not MainMenu.options[which][5]
        self.UpdateMenu() 
        
    def EnableMenu(self, which, what):
        MainMenu.options[which][5] = what
        self.UpdateMenu() 

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

        num   = get_level_count()
        xnum  = int((rx-base_offset[0]-50)//width_spacing)
        rows  = math.ceil( num/xnum )
        self.level = getattr(self,"level", 0)
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
                    self.level = (self.level+( (xnum+num - xnum*rows) if (self.level//xnum == rows-1) else xnum  ) )%(num) 

                elif event.Key.Code == KeyMapping.Get("menu-up"):
                    self.level = (self.level-( (xnum+num - xnum*rows) if (self.level//xnum == 0) else xnum  ) )%(num) 

                elif event.Key.Code == KeyMapping.Get("accept"):
                    
                    GetBack()
                    self._TryStartGameFromLevel(self.level+1) 
                   
        for y in range(rows):
            for x in range(min(num - y*xnum,xnum)):
                i = y*xnum +x 
                #print(i)

                sf_draw_string_with_shadow(
                    str(i+1).zfill(2) ,
                    defaults.font_menu,
                    height,
                    base_offset[0]+(x*width_spacing) + 20,
                    base_offset[1]+y*height_spacing + 20,
                    sf.Color.Red if self.level == i else sf.Color.White )
                
        height = int(0.5*height)
        from level import LevelLoader
        sf_draw_string_with_shadow(
            _("Press {0} to enter Level {1} - '{2}'").format(KeyMapping.GetString("accept"),self.level+1,LevelLoader.GuessLevelName(self.level+1)),
            defaults.font_menu,
            height,
            base_offset[0]+20,
            ry - 130*defaults.scale[1] - height*1.2,
            sf.Color.White )
                
        sf_draw_string_with_shadow(
            _("Press {0} to return").format(KeyMapping.GetString("escape")),
            defaults.font_menu,
            height,
            base_offset[0]+20,
            ry - 130*defaults.scale[1],
            sf.Color.White )
        
        
    def AskForNetworkUse(self,on_done=None):
        """Ask the user if they want to allow us to connect to yiang-thegame.com."""
        
        accepted = (KeyMapping.Get("yes"),KeyMapping.Get("no"),KeyMapping.Get("accept"))
        def on_close(a):
            if a == accepted[0]:
                defaults.allow_network_use = True
                
                if on_done:
                    on_done()
                
                return
            elif a == accepted[1]:
                defaults.allow_network_use = False
                
            # automatically return to the main menu
            self.subindex = SI_NONE
            
            if on_done:
                on_done()
        
        Renderer.AddDrawable( MessageBox(sf.String(_("""Some features of this game require an internet connection.
        
Do you want to allow YIANG to connect to the master server ({0})
to automatically obtain updates and updated highscore tables? Note that this is
a permanent setting. This annoying dialog won't bother you again if you opt-in.

Hit either {1} (yes) or {2} (no) to proceed.
""".format(defaults.server_name,KeyMapping.GetString("yes"),KeyMapping.GetString("no"))),
            Size=defaults.letter_height_game_over,
            Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
        )), defaults.game_over_fade_time, (750, 150), 0.0, accepted, sf.Color.Black, on_close))
        
        
    def ShowHighscore(self):
        """Show online highscore"""
        
        import urllib.request
        import json
       
        base_height = 24
        base_offset = [self.base_x+50,self.base_y]
        rx,ry = defaults.resolution

        height = int(base_height*defaults.scale[0])-2
        #height_large = (height*3)/2
        height_small = height # (height*5)/6
        width_spacing, height_spacing = 290*defaults.scale[1],int(height*1.2)
        bb = (base_offset[0],base_offset[1],rx-40,ry-60)        
        
        def GetBack():
            self.subindex = SI_NONE
            try:
                delattr(self,"hs_clock")
                delattr(self,"hs_json")
            except AttributeError:
                pass
            
        if not defaults.allow_network_use:
            self.subindex = SI_NONE
            
            def on_try_again():
                if defaults.allow_network_use:
                    self.subindex = SI_HIGHSCORE
            
            self.AskForNetworkUse(on_try_again)
            return
            
        if not hasattr(self,"hs_clock"):
            self.hs_clock = sf.Clock()
            
                  
        self._DrawRectangle(bb,scale=min(1.0, self.hs_clock.GetElapsedTime()*3.0))
        extra = ""
        
        if not hasattr(self,"cur_hs_page"):
            self.cur_hs_page = 0
            
        if not hasattr(self,"cur_hs_itemcnt"):
            self.cur_hs_itemcnt = int(12 * defaults.scale[1]/defaults.scale[0])
        
        if not hasattr(self,'hs_json'):
            page = self.cur_hs_page
            itemcnt = self.cur_hs_itemcnt 
            url = defaults.highscore_json_url+"?page={page}&itemcnt={itemcnt}{extra}".format(**locals())
            print("Send json request: {0}".format(url))
            
            try:
                self.hs_json = json.loads( urllib.request.urlopen(url).read().decode() )
            except Exception as a:
                
                print("Failure: {0}".format(a))
                
                def on_close(a):
                    pass
                
                accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
                Renderer.AddDrawable( MessageBox(sf.String(_("""Failure retrieving highscore list from the server"""),
                    Size=defaults.letter_height_game_over,
                    Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
                )), defaults.game_over_fade_time, (550, 50), 0.0, accepted, sf.Color.Black, on_close))
                
                GetBack()
                return
        
        base_offset[0] += int(20*defaults.scale[0])
        base_offset[1] += int(85*defaults.scale[0])
        sf_draw_string_with_shadow(_("""This is the list of the people who have devoted their time to master YIANG. 
Consider them heroes."""),defaults.font_menu,
            height_small,
            base_offset[0],
            base_offset[1]-int(65*defaults.scale[0]),
            sf.Color.White)
        
        sf_draw_string_with_shadow(
            "   #    {0}    {1}    {2}".format(_("Region"),_("Score"),_("Name")),
            defaults.font_monospace,
            height,
            base_offset[0],
            base_offset[1],
            sf.Color.Red,sf.Color.Black)
        
        base = self.cur_hs_itemcnt * self.cur_hs_page
        for y,elem in enumerate(self.hs_json["items"]):
            rank = base+y+1
            color = sf.Color(155,155,155)
            
            # special coloring for the first three ranks
            if rank <= 3:
                color = sf.Color(220,220,220)
                
            bgcolor = sf.Color.Black
                
            sf_draw_string_with_shadow(
                    "{0:>4}.    {1:>2}    {2:>9}    {3:<32}".format(rank,elem["country"], elem["score"]/100000, elem["player"]),
                    defaults.font_monospace,
                    height,
                    base_offset[0],
                    base_offset[1]+(y+2)*height_spacing,
                    color,
                    bgcolor)
            
        sf_draw_string_with_shadow(_("Page {0} out of {1}\nUse {2} and {3} to change").format(
                self.cur_hs_page,
                self.hs_json["pages"],
                KeyMapping.GetString("menu-left"),
                KeyMapping.GetString("menu-right") 
            ),defaults.font_menu,
            height_small,
            base_offset[0],
            base_offset[1]+(y+2)*height_spacing+int(40*defaults.scale[0]),
            sf.Color.White)

            
        for event in Renderer.SwallowEvents():
            if event.Type == sf.Event.KeyPressed:
            
                if event.Key.Code == KeyMapping.Get("menu-right"):
                    self.cur_hs_page += 1
                    try:
                        self.cur_hs_page = min(self.cur_hs_page, self.hs_json["pages"]-1)
                        delattr(self,"hs_json")
                    except AttributeError:
                        pass

                elif event.Key.Code == KeyMapping.Get("menu-left"):
                    self.cur_hs_page -= 1
                    self.cur_hs_page = max(self.cur_hs_page,0)
                    try:
                        delattr(self,"hs_json")
                    except AttributeError:
                        pass
                    
                else: 
                    GetBack()
                    return
        
        
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
                
                if event.Key.Code == KeyMapping.Get("menu-down"):
                    self.achievement = (self.achievement+1)%(num)

                elif event.Key.Code == KeyMapping.Get("menu-up"):
                    self.achievement = (self.achievement-1)%(num)

                else:
                    GetBack()
                    return
                    
        have = Achievements.have    
        for y, ach in zip( range(num), sorted( Achievements.all, key=lambda x: Achievements.GetInfo(x)["order"]) ):
            info = Achievements.GetInfo(ach)

            sf_draw_string_with_shadow(
               info["name"] or "<missing>",
                defaults.font_menu,
                height,
                base_offset[0]+20,
                base_offset[1]+y*height_spacing+20,
                (sf.Color.Red if ach in have else sf.Color(175,0,0)) if self.achievement == y else (sf.Color.White if ach in have else sf.Color(160,160,160)))
            
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
            
                    


        
import userprofile


def LaunchMenu():
    if defaults.no_bg_music is False:
        class DummyMusicPlayer(Drawable):
            def Draw(self):
                BerlinerPhilharmoniker.Process()
        Renderer.AddDrawable(DummyMusicPlayer())
        BerlinerPhilharmoniker.SetAudioSection("menu")

    from posteffect import BlurInOverlay, FadeInOverlay
    Renderer.AddDrawable(BlurInOverlay(2.0,0.0))
    Renderer.AddDrawable(FadeInOverlay(2.5,0.0))
    Renderer.AddDrawable(MainMenu())



def main():
    """Main entry point to the application"""
        
    print("Startup ...")
    KeyMapping.LoadFromFile(os.path.join(defaults.config_dir,"key_bindings.txt"))
    
    userprofile.LoadPreviousProfile()

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
    
    
    """accepted = (KeyMapping.Get("escape"),KeyMapping.Get("accept"))
    def on_close(key, accepted=accepted):
        if key == accepted[1]:
            LaunchMenu():
            return 
        sys.exit(0)
               
    Renderer.SetClearColor(sf.Color(100,0,0)) 
    Renderer.AddDrawable( MessageBox(sf.String(

    
Hit {0} to continue
Hit {1} to cancel.format(
                    KeyMapping.GetString("accept"),
                    KeyMapping.GetString("escape")
                ),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
            )), defaults.game_over_fade_time, (550, 150), 0.0, accepted, sf.Color(150,0,0), on_close))
    """
    
    def next():
        next = lambda:userprofile.SetupSelectionGUI(LaunchMenu)
        
        if defaults.no_intro:
            next()
        else:
            from title import Title
            Renderer.AddDrawable(Title(next))
    
    if defaults.no_logo:
        next()
    else:
        from studiosplash import Splash
        Renderer.AddDrawable(Splash(next))
        
    Renderer.DoLoop()
    Renderer.Terminate()
    

# vim: ai ts=4 sts=4 et sw=4