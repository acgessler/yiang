

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


def options_quit():
    sys.exit(0)

def options_credits():
    print("Credits!")

def options_newgame():
    global game
    global app

    game = Game(app)
    options_resumegame()

def options_resumegame():
    global swallow_escape
    assert not game is None
    
    if game.Run() is True:
        swallow_escape = True

options = [
    ("New Game -------------------------------------------", options_newgame, "You will die"),
    ("Resume Game", options_resumegame, "You will die soon"),
    ("Credits", options_credits, defaults.credits_string),
    ("Quit!", options_quit,"")
]

# numeric constants for the menu entries
OPTION_NEWGAME,OPTION_RESUME,OPTION_CREDITS,OPTION_QUIT = range(4)

# mixed global variables to control the main menu
cur_option = 0
menu_text = [(None,None)]*len(options)
game = None
app = None
swallow_escape = False

clock = sf.Clock()

def set_menu_option(i):
    global cur_option
    cur_option = i % len(options)

    height = 100

    for i in range(len(options)):
        tex = sf.String(options[i][0],Font=FontCache.get(height),Size=height)
        tex.SetPosition(-20,100+i*height*1.5)
        
        tex.SetColor((sf.Color(100,100,100) if cur_option == OPTION_RESUME and game is None else sf.Color.Red)
            if cur_option==i else sf.Color.Black)

        tex2 = sf.String(options[i][0],Font=FontCache.get(height+2),Size=height+2)
        tex2.SetPosition(-24,98+i*height*1.5)
        tex2.SetColor(sf.Color(100,100,100))
                     
        menu_text[i] = (tex2,tex)
    

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
        

def main():
    """Main entry point to the application"""

    global app
    global swallow_escape
    check_requirements()

    # Read game.txt, which is the master config file
    defaults.merge_config(os.path.join(defaults.config_dir,"game.txt"))
    
    # Create main window
    if defaults.fullscreen is True:
        dm = sf.VideoMode.GetDesktopMode()
        
        defaults.resolution = dm.Width,dm.Height
        app = sf.RenderWindow(dm, defaults.caption,sf.Style.Fullscreen)
    else:
        app = sf.RenderWindow(sf.VideoMode(*defaults.resolution), defaults.caption, sf.Style._None)

    #print(dir(sf.Window))
    defaults.update_derived()

    # Setup a dummy icon, I might add a proper one later
    app.SetIcon(16,16,b'\xcd\x22\x22\xff'*256)

    # Load the font for the intro
    font = FontCache.get(defaults.letter_height_intro)

    # Load the PostFX (I had to try them ...)
    effect = sf.PostFX()
    effect.LoadFromFile(os.path.join(defaults.data_dir,"effects","intro.sfx"))
    effect.SetTexture("framebuffer", None);

    app.SetFramerateLimit(30)
    ttl = 0

    set_menu_option(0)
    clock = sf.Clock()
    
    while app.IsOpened():
        # Process events
        event = sf.Event()
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

                    # Adjust the viewport when the window is resized
                    if event.Type == sf.Event.Resized:
                        assert False

                app.Clear(sf.Color.White)
               
                s = ""
                abc = "abcdefghijklmnopqrstuvABCDEFGHJIKLMNOPQRSTUVWXYZ#@/^%$"
                for y in range(defaults.cells_intro[1]):
                    for x in range(defaults.cells_intro[0]):
                        s += random.choice(abc)
                        
                    s += "\n"
                       
                Text = sf.String(s,Font=font,Size=defaults.letter_height_intro)
                Text.SetPosition(0,0)
                Text.SetColor(sf.Color.Black)
                app.Draw(Text)

                if ttl == 0:
                    cached_danger_signs = recache_danger_signs(font)
                    ttl = defaults.danger_signs_ttl
                ttl = ttl-1
                    
                for te in cached_danger_signs:
                    app.Draw(te)

                effect.SetParameter("strength", (math.sin( clock.GetElapsedTime() ) +1)*0.5);
                app.Draw(effect)
                for entry in itertools.chain(menu_text):
                    app.Draw(entry)

                # Finally, display the rendered frame on screen
                app.Display()


main()
