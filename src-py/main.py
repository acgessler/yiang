

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


def options_quit():
    sys.exit(0)

def options_credits():
    print("Credits!")

def options_newgame():
    pass

def options_resumegame():
    pass

options = [
    ("New Game -------------------------------------------", options_newgame, "You will die"),
    ("Resume Game", options_resumegame, "You will die soon"),
    ("Credits", options_credits, defaults.credits_string),
    ("Quit!", options_quit,"")
]
cur_option = 0
menu_text = [(None,None)]*len(options)

clock = sf.Clock()

def set_menu_option(i):
    global cur_option
    cur_option = i % len(options)

    height = 100

    for i in range(len(options)):
        tex = sf.String(options[i][0],Font=FontCache.get(height),Size=height)
        tex.SetPosition(-20,100+i*height*1.5)
        
        tex.SetColor(sf.Color.Red if cur_option==i else sf.Color.Black)

        tex2 = sf.String(options[i][0],Font=FontCache.get(height+2),Size=height+2)
        tex2.SetPosition(-24,98+i*height*1.5)
        tex2.SetColor(sf.Color(100,100,100))
                     
        menu_text[i] = (tex2,tex)
    

def recache_danger_signs(font):
    """Regenerate the dangerous, red flashing matrix-like ghost texts"""
    
    out = []
    for i in range(random.randint(0,10)):
        tex = sf.String(options[cur_option][2],Font=font,Size=defaults.letter_height_intro*8)
        tex.SetPosition(random.randint(-defaults.resolution[0]*2,defaults.resolution[0]),
            random.randint(-10,defaults.resolution[1]))
        tex.SetColor(sf.Color(100,100,100))

        out.append(tex)
    return out


def check_requirements():
    """Check if hardware requirements to run the game are met, does not return if not"""
    
    if sf.PostFX.CanUsePostFX() is False:
        print("Need to support postprocessing effects, buy better hardware.")
        sys.exit(-100)

def main():
    check_requirements()

    # Read game.txt, which is the master config file
    defaults.merge_config(os.path.join(defaults.config_dir,"game.txt"))
    
    # Create main window
    if defaults.fullscreen is True:
        dm = sf.VideoMode.GetDesktopMode()
        
        defaults.resolution = dm.Width,dm.Height
        App = sf.RenderWindow(dm, defaults.caption,sf.Style.Fullscreen)
    else:
        App = sf.RenderWindow(sf.VideoMode(*defaults.resolution), defaults.caption, sf.Style._None)

    defaults.update_derived()

    # Setup a dummy icon, I might add a proper one later
    App.SetIcon(16,16,b'\xcd\x22\x22\xff'*256)

    # Load the font for the intro
    font = FontCache.get(defaults.letter_height_intro)

    # Load the PostFX (I had to try them ...)
    effect = sf.PostFX()
    effect.LoadFromFile(os.path.join(defaults.data_dir,"effects","intro.sfx"))
    effect.SetTexture("framebuffer", None);

    App.SetFramerateLimit(30)
    ttl = 0

    set_menu_option(0)
    clock = sf.Clock()
    
    while App.IsOpened():
        # Process events
        Event = sf.Event()
        while True:

                if App.GetEvent(Event):
                    # Close window : exit
                    if Event.Type == sf.Event.Closed:
                        App.Close()
                        break

                    # Escape key : exit
                    if Event.Type == sf.Event.KeyPressed:
                        if Event.Key.Code == sf.Key.Escape:
                            App.Close()
                            break
                        elif Event.Key.Code == sf.Key.Down:
                             set_menu_option(cur_option+1)
                             
                        elif Event.Key.Code == sf.Key.Up:
                             set_menu_option(cur_option-1)

                        elif Event.Key.Code == sf.Key.Return:
                            options[cur_option][1]()

                    # Adjust the viewport when the window is resized
                    if Event.Type == sf.Event.Resized:
                        assert False

                App.Clear(sf.Color.White)
               
                s = ""
                abc = "abcdefghijklmnopqrstuvABCDEFGHJIKLMNOPQRSTUVWXYZ#@/^%$"
                for y in range(defaults.cells_intro[1]):
                    for x in range(defaults.cells_intro[0]):
                        s += random.choice(abc)
                        
                    s += "\n"
                       
                Text = sf.String(s,Font=font,Size=defaults.letter_height_intro)
                Text.SetPosition(0,0)
                Text.SetColor(sf.Color.Black)
                App.Draw(Text)

                if ttl == 0:
                    cached_danger_signs = recache_danger_signs(font)
                    ttl = defaults.danger_signs_ttl
                ttl = ttl-1
                    
                for te in cached_danger_signs:
                    App.Draw(te)

                effect.SetParameter("strength", (math.sin( clock.GetElapsedTime() ) +1)*0.5);
                App.Draw(effect)
                for entry in itertools.chain(menu_text):
                    App.Draw(entry)

                

                # Finally, display the rendered frame on screen
                App.Display()


main()
