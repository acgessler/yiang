


import sf

def main():

    # Create main window
    App = sf.RenderWindow(sf.VideoMode(1024, 700), "Yet another Jump'n'Run (an unfair one)")
    #App.PreserveOpenGLStates(True)

    while App.IsOpened():
        # Process events
        Event = sf.Event()
        while App.GetEvent(Event):
                # Close window : exit
                if Event.Type == sf.Event.Closed:
                        App.Close()

                # Escape key : exit
                if (Event.Type == sf.Event.KeyPressed) and (Event.Key.Code == sf.Key.Escape):
                        App.Close()

                # Adjust the viewport when the window is resized
                if Event.Type == sf.Event.Resized:
                        #glViewport(0, 0, Event.Size.Width, Event.Size.Height)
                        pass

                App.Clear(sf.Color.Black)


                # Draw some text on top of our OpenGL object
                Text = sf.String("This is a rotating cube")
                Text.SetPosition(230., 300.)
                Text.SetColor(sf.Color(128, 0, 128))
                App.Draw(Text)

                # Finally, display the rendered frame on screen
                App.Display()


main()
