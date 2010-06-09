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

# My own stuff
import defaults


class Drawable:
    """Master class for all kinds of drawable objects, i.e. tiles,
    overlays, menues, ..."""

    # CULL_ENABLE,CULL_DISABLE = range(2)

    def GetBoundingBox(self):
        """Get the bounding box (x,y,w,h) of the entity or
        None if the entity does not support this concept.
        The bounding box is used for culling, so it is
        highly recommended to return a meaningful value.
        Of course, drawable's which are ALWAYS visible
        should return None."""
        return None

    # def GetCullingPolicy(self):
    #    """ """
    #     return Drawable.CULL_ENABLE


    def Draw(self,game):
        """To be implemented"""
        pass


class _QuitNow(Exception):
    pass

class Renderer:
    """Static class, responsible for maintaining a list of Drawables()
    and rendering them. Also, Renderer owns the window and is
    responsible for initialization and termination"""

    app = sf.RenderWindow()
    drawables = set()
    clear_color = sf.Color.White
    event = None
    loop_running = False

    @staticmethod
    def Initialize():
        """Initialize the rendering infrastructure and
        create a window"""

        Renderer._CheckRequirements()

        print("Creating window ...")
        settings = sf.WindowSettings()
        settings.DepthBits = 0
        settings.StencilBits = 0  
        settings.AntialiasingLevel = defaults.antialiasing_level 
            
        # Create main window
        dm = sf.VideoMode.GetDesktopMode()
        if defaults.fullscreen is True:
        
            defaults.resolution = dm.Width,dm.Height
            Renderer.app = sf.RenderWindow(dm, defaults.caption,sf.Style.Fullscreen, settings)
        else:
            tb = sf.Style.Close if defaults.show_window_caption else sf.Style._None
            Renderer.app = sf.RenderWindow(sf.VideoMode(
                    min(defaults.resolution[0],dm.Width),
                    min(defaults.resolution[1],dm.Height)
                ),
                defaults.caption,tb, settings)


        # Setup a dummy icon, I might add a proper one later
        Renderer.app.SetIcon(16,16,b'\xcd\x22\x22\xff'*256)
        if defaults.framerate_limit > 0:
            Renderer.app.SetFramerateLimit(defaults.framerate_limit)

        print("Updating derived settings ...")
        defaults.update_derived()

        print("-"*60)

    @staticmethod
    def _CheckRequirements():
        """Check if hardware requirements to run the game are met,
        does not return if not"""
    
        if sf.PostFX.CanUsePostFX() is False:
            print("Need to support postprocessing effects, buy better hardware!")
            sys.exit(-100)

    @staticmethod
    def DoLoop():
        """Run the game's main loop until either the window is
        closed or Quit() is called. The return value is True
        if the main loop ended with the user closing the
        window and False if it was stopped by the application
        using the Quit() method."""

        assert not Renderer.loop_running
        Renderer.loop_running = True

        try:
            
            event = sf.Event()
            while Renderer.app.IsOpened():
                Renderer.events = set()
                while Renderer.app.GetEvent(event):
                    #Close window : exit
                    if event.Type == sf.Event.Closed:
                        Renderer.app.Close()

                        Renderer.loop_running = False
                        return True

                    Renderer.events.add(event)
                    event = sf.Event()

                # The background color is not a Drawable because it is *always* first, and active
                Renderer.app.Clear(Renderer.clear_color)

                for drawable in Renderer.drawables:
                    drawable.Draw()

                Renderer.app.Display()

        except _QuitNow:
            pass

        Renderer.loop_running
        return False

    @staticmethod
    def GetEvents():
        return Renderer.events

    @staticmethod
    def AddDrawable(drawable):
        Renderer.drawables.add(drawable)

    @staticmethod
    def ClearDrawables():
        Renderer.drawables = set()

    @staticmethod
    def SetClearColor(color):
        Renderer.clear_color = color

    @staticmethod
    def Quit():
        """Quit the application immediately. If the main loop
        is running, it is stopped and DoLoop() returns False"""
        Renderer.app.Close()
        raise _QuitNow()

    @staticmethod
    def Terminate():
        """Release all resources in our possession"""

        Renderer.app = None

        print("-"*60)
        print("Leaving main menu, shutdown")
        
    

    

    
