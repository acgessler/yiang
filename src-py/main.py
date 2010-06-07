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
import random
import sys
import os
import itertools
import math

# My own stuff
import defaults
from fonts import FontCache
from game import Game
from log import Log

def options_quit():
    sys.exit(0)

def options_credits():
    print("Credits!")
    show_credits()

def options_newgame():
    global game

    game = Game(app)
    game.LoadLevel(1)
    options_resumegame()

def options_newgame_choose():
    global game

    level = choose_level()
    if level == 0:
        return

    game = Game(app)
    game.LoadLevel(level)
    options_resumegame()

def options_resumegame():
    global swallow_escape
    global game

    if game is None:
        return
    
    if game.Run() is True:
        swallow_escape = True

        if game.IsGameOver():
            game = None

options = [
    ("New Game -------------------------------------------", options_newgame, "You will die"),
    ("Resume Game", options_resumegame, "You will die soon"),
    ("Choose Level >>>>>>>>>", options_newgame_choose, "Bad idea"),
    ("Credits", options_credits, "CREDITS"),
    ("Quit!", options_quit,"")
]

# numeric constants for the menu entries
OPTION_NEWGAME,OPTION_RESUME,OPTION_CHOOSELEVEL,OPTION_CREDITS,OPTION_QUIT = range(5)

# mixed global variables to control the main menu
cur_option = 0
menu_text = [(None,None)]*len(options)
game = None
app = None
swallow_escape = False
font = None
effect = sf.PostFX()
event = sf.Event()
ttl = 0

clock = sf.Clock()


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

def choose_level():
    """Switch to the choose level menu option and return the selected
    level. 0 is returned if the user cancels the operaton"""

    height = 80
    width_spacing, height_spacing = 100,100

    num = get_level_count()+1
    xnum = defaults.resolution[0]//width_spacing
    rows = math.ceil( num/xnum )

    level = 1
    while True:

        if app.GetEvent(event):
            if event.Type == sf.Event.KeyPressed:
                if event.Key.Code == sf.Key.Escape:
                    return 0

                elif event.Key.Code == sf.Key.Right:
                    level = (level+1)%(num+1)

                elif event.Key.Code == sf.Key.Left:
                    level = (level-1)%(num+1)

                elif event.Key.Code == sf.Key.Down:
                    level = (level+xnum)%(num+1)

                    # improve the usability of the 'return to menu' field
                    if (level // xnum) == rows-1:
                        level = num

                elif event.Key.Code == sf.Key.Up:
                    level = (level-xnum)%(num+1)

                elif event.Key.Code == sf.Key.Return:
                    break
                
        draw_background()

        for y in range(rows):
            for x in range((num - y*xnum) % xnum):
                i = y*xnum +x +1

                tex2,tex = sf_string_with_shadow(
                    str(i) if i < num else "\n\n\n... back to main menu ",
                    FontCache.get(
                        height,
                        defaults.font_menu),
                    height,
                    20+ (x*width_spacing if i < num else 0),
                    20+y*height_spacing,
                    sf.Color.Red if level == i else sf.Color.Black )
                
                app.Draw(tex2)
                app.Draw(tex)
        
        app.Display()

    return level if level < num else 0


def show_credits():
    """Show the game's credits"""
    try:
        with open(os.path.join("..","CREDITS"),"rt") as file:
            cred = list(filter(lambda x:not len(x.strip()) or x[0] != "#", file.readlines()))
            cred.insert(0,"(Press any key to continue)")
    except IOError:
        print("Failure loading credits file")
        return

    height,height_spacing = 30, 5
    while True:

        if app.GetEvent(event):
            if event.Type == sf.Event.KeyPressed:
                #if event.Key.Code == sf.Key.Escape:
                return
                
        draw_background()

        x,y = 100,50
        for line in cred:
            tex = sf_string(
                line+("\n" if line[0] == "=" else ""),
                FontCache.get(
                    height,
                    defaults.font_menu),
                height,
                x,
                y,
                sf.Color.Red if line[0] == "=" else sf.Color.White)

            y += height+height_spacing
            if y > defaults.resolution[1]-100:
                x+= 500
                y = 130
            
            app.Draw(tex)
        app.Display()


def sf_string_with_shadow(text,font,size,x,y,color,bgcolor=sf.Color(100,100,100)):
    """Spawn a string with a shadow behind, which is actually the same
    string in a different color, moved and scaled slightly. Return a
    2-tuple (a,b) where a is the shadow string"""
    tex = sf.String(text,Font=font,Size=size)
    tex.SetPosition(x,y)
    tex.SetColor(color)

    tex2 = sf.String(text,Font=font,Size=size+1)
    tex2.SetPosition(x-6,y-3)
    tex2.SetColor(bgcolor)

    return (tex2,tex)


def sf_string(text,font,size,x,y,color):
    """Create a sf.String from the given parameters and
    return it. Unlike XXX_with_shadow, this method does not
    supplement a drop shadow."""
    tex = sf.String(text,Font=font,Size=size)
    tex.SetPosition(x,y)
    tex.SetColor(color)

    return tex


def set_menu_option(i):
    """Choose the currently selected main menu option, entries
    are enumerated by the global 'options' array. """
    global cur_option
    cur_option = i % len(options)

    height = 80
    for i in range(len(options)):
        menu_text[i] = sf_string_with_shadow(
            options[i][0],
            FontCache.get(
                height,
                defaults.font_menu),
            height,
            -20,
            100+i*height*1.5,
            (sf.Color(100,100,100) if cur_option == OPTION_RESUME and game is None else sf.Color.Red) 
                if cur_option==i else sf.Color.White )
    

def recache_danger_signs(font):
    """Regenerate the dangerous, red flashing matrix-like ghost texts"""

    scale = 8
    color = sf.Color.Red if cur_option == OPTION_CREDITS else sf.Color(100,100,100)
    count = 2 if cur_option == OPTION_CREDITS else 10
    
    out = []
    for i in range(random.randint(0,count)):
        tex = sf.String(options[cur_option][2],Font=font,Size=defaults.letter_height_intro*scale)
        tex.SetPosition(random.randint(-defaults.resolution[0],defaults.resolution[0]),
            random.randint(-10,defaults.resolution[1]))
        tex.SetColor(color)

        out.append(tex)
    return out


def check_requirements():
    """Check if hardware requirements to run the game are met, does not return if not"""
    
    if sf.PostFX.CanUsePostFX() is False:
        print("Need to support postprocessing effects, buy better hardware.")
        sys.exit(-100)

def draw_background():
    """Draw the fuzzy menu background """
    global ttl
    global cached_danger_signs
    
    app.Clear(sf.Color.White)
               
    s = ""
    abc = "abcdefghijklmnopqrstuvABCDEFGHJIKLMNOPQRSTUVWXYZ#@/^%$"
    for y in range(defaults.cells_intro[1]):
        for x in range(defaults.cells_intro[0]):
            s += random.choice(abc)
            
        s += "\n"
           
    text = sf.String(s,Font=font,Size=defaults.letter_height_intro)
    text.SetPosition(0,0)
    text.SetColor(sf.Color.Black)
    app.Draw(text)

    if ttl == 0:
        cached_danger_signs = recache_danger_signs(font)
        ttl = defaults.danger_signs_ttl
    ttl = ttl-1
        
    for te in cached_danger_signs:
        app.Draw(te)

    effect.SetParameter("strength", (math.sin( clock.GetElapsedTime() ) +1)*0.5);
    app.Draw(effect)


def main():
    """Main entry point to the application"""

    global app
    global swallow_escape
    global ttl
    global effect
    global font
    global event
    check_requirements()

    # Read game.txt, which is the master config file
    #Log.Enable(defaults.enable_log)
    defaults.merge_config(os.path.join(defaults.config_dir,"game.txt"))
    Log.Enable(defaults.enable_log)

    print("Startup ...")
    
    settings = sf.WindowSettings()
    settings.DepthBits = 0
    settings.StencilBits = 0  
    settings.AntialiasingLevel = defaults.antialiasing_level 
        
    # Create main window
    if defaults.fullscreen is True:
        dm = sf.VideoMode.GetDesktopMode()
        
        defaults.resolution = dm.Width,dm.Height
        app = sf.RenderWindow(dm, defaults.caption,sf.Style.Fullscreen, settings)
    else:
        app = sf.RenderWindow(sf.VideoMode(*defaults.resolution), \
            defaults.caption, sf.Style._None, settings)

    print("Created window ...")

    #print(dir(sf.Window))
    defaults.update_derived()

    # Setup a dummy icon, I might add a proper one later
    app.SetIcon(16,16,b'\xcd\x22\x22\xff'*256)

    # Load the font for the intro
    font = FontCache.get(defaults.letter_height_intro)

    # Load the PostFX (I had to try them ...)
    effect.LoadFromFile(os.path.join(defaults.data_dir,"effects","intro.sfx"))
    effect.SetTexture("framebuffer", None);

    if defaults.framerate_limit > 0:
        app.SetFramerateLimit(defaults.framerate_limit)
        
    ttl = 0
    print("Entering main menu")

    set_menu_option(0)
    while app.IsOpened():
        while True:

                if app.GetEvent(event):
                    # Close window : exit
                    # if Event.Type == sf.Event.Closed:
                    #    app.Close()
                    #    break

                    # Escape key : exit
                    if event.Type == sf.Event.KeyPressed:
                        if event.Key.Code == sf.Key.Escape and swallow_escape is False:
                            app.Close()
                            break
                        
                        elif event.Key.Code == sf.Key.Down:
                             set_menu_option(cur_option+1)
                             
                        elif event.Key.Code == sf.Key.Up:
                             set_menu_option(cur_option-1)

                        elif event.Key.Code == sf.Key.Return:
                            options[cur_option][1]()

                    elif event.Type == sf.Event.KeyReleased and event.Key.Code == sf.Key.Escape:
                        swallow_escape = False

                    if event.Type == sf.Event.Resized:
                        assert False

                draw_background()

                for entry in itertools.chain(menu_text):
                    app.Draw(entry)

                app.Display()
    print("Leaving main menu, shutdown")


main()
