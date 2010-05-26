


import sf
import random
import defaults
import sys

def main():
    
    # Create main window
    if defaults.fullscreen is True:
        dm = sf.VideoMode.GetDesktopMode()
        
        defaults.window_dim = dm.Width,dm.Height
        App = sf.RenderWindow(dm, defaults.caption,sf.Style.Fullscreen)
    else:
        App = sf.RenderWindow(sf.VideoMode(*defaults.window_dim), defaults.caption,sf.Style._None)

    defaults.update_derived()

    # Setup a dummy icon, I might add a proper one later
    App.SetIcon(16,16,b'\xcd\x22\x22\xff'*256)

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
                    if (Event.Type == sf.Event.KeyPressed) and (Event.Key.Code == sf.Key.Escape):
                            App.Close()
                            break

                    # Adjust the viewport when the window is resized
                    if Event.Type == sf.Event.Resized:
                            #glViewport(0, 0, Event.Size.Width, Event.Size.Height)
                            pass

                App.Clear(sf.Color.Black)

                font = sf.Font()
                font.LoadFromFile("./../data/fonts/courier_new_bold.ttf",defaults.letter_height_intro)

                for x in range(defaults.cells_intro[0]):
                    for y in range(defaults.cells_intro[1]):

                        # Draw some text on top of our OpenGL object
                        Text = sf.String(random.choice("abcdefghijklmnopqrstuv#@/"),Font=font,Size=defaults.letter_height_intro)
                        Text.SetPosition(x*defaults.letter_height_intro,y*defaults.letter_height_intro)
                        Text.SetColor(sf.Color(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
                        App.Draw(Text)

                # Finally, display the rendered frame on screen
                App.Display()


main()
