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
import mathutil

class Drawable:
    """Master class for all kinds of drawable objects, i.e. tiles,
    overlays, menues, ..."""

    FLAG_DISABLE = 0x1 
    
    def __init__(self,flags=0):
        self.flags = flags


    def SetFlag(self,flag):
        self.flags |= flag

    def RemoveFlag(self,flag):
        self.flags &= ~flag

    def QueryFlag(self,flag):
        return True if self.flags & flag else False


    def GetDrawOrder(self):
        """Drawable's are drawn with ascending draw order"""
        return 0

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


    def Draw(self):
        """To be implemented"""
        pass
    
    
class DebugTools:
    """Implements some state dumpers, tracing tools, etc."""
    
    @staticmethod
    def Trace():
        """Invoke traceback.print_stack in debug builds"""
        if defaults.debug_trace_keypoints is True:
            import traceback

            print("")
            traceback.print_stack()


class _QuitNow(Exception):
    """Throw this to force the main loop to return immediately.
    You can use Renderer.Quit() instead."""
    pass


class NewFrame(Exception):
    """Sentinel exception to abort the current frame and to
    resume with the next, immediately."""
    def __init__(self):
        print("Raising NewFrame sentinel signal")
        DebugTools.Trace()

class Renderer:
    """Static class, responsible for maintaining a list of Drawables()
    and rendering them. Also, Renderer owns the window and is
    responsible for initialization and termination"""

    app = sf.RenderWindow()
    drawables,drawables_add,drawables_rem = set(),set(),set()
    drawables_active = []                                     
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
                Renderer.draw_counter,Renderer.inrange = 0,0
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

                drawable = None
                try:
                    for drawable in sorted(Renderer.drawables,key=lambda x: x.GetDrawOrder()):
                        drawable.Draw()
                except NewFrame:
                    pass
                except Exception as ex:
                    print("[Responsible seems to be a {0} instance]".format(type(drawable)))
                    raise

                # update the drawables list, handle dependencies of changed drawables.
                for entity in Renderer.drawables_add:
                    Renderer.drawables.add(entity)
                    if hasattr(entity,"__drawable_deps__"):
                        for dep in entity.__drawable_deps__:
                            try:
                                Renderer.drawables.remove(dep)
                            except KeyError:
                                pass

                for entity in Renderer.drawables_rem:
                    try:
                        Renderer.drawables.remove(entity)
                        if hasattr(entity, "__drawable_deps__"):
                             for dep in entity.__drawable_deps__:
                                 Renderer.drawables.add(dep)
                                 
                             delattr(entity,"__drawable_deps__")
                    except KeyError:
                        pass

                Renderer.drawables_rem, Renderer.drawables_add = set(),set()

                # toggle front and backbuffer
                Renderer.app.Display()

        except _QuitNow:
            pass

        Renderer.loop_running
        return False

    @staticmethod
    def GetEvents():
        return Renderer.events

    @staticmethod
    def AddDrawable(drawable,substitutes=None):
        """Add a drawable to the list. If a valid active drawable
        is specified for the substitutes parameter, the system will
        disable the corresponding drawable (or list of drawables)
        while the new drawable is active. As soon as this 
        drawable is disabled using RemoveDrawable, all of its
        dependencees are re-activated."""
        assert not drawable is None
        Renderer.drawables_add.add(drawable)
        try:
            Renderer.drawables_rem.remove(drawable)
        except KeyError:
            pass
        
        if not substitutes is None:
            assert not substitutes is drawable
            assert not hasattr(drawable,"__drawable_deps__")
            # hijack the instance a bit
            drawable.__drawable_deps__ = [substitutes] if isinstance(substitutes,Drawable) \
                else substitutes

    @staticmethod
    def RemoveDrawable(drawable,handle_dependencees=True):
        Renderer.drawables_rem.add(drawable)
        
        if handle_dependencees is False:
            drawable.__drawable_deps__ = []

    @staticmethod
    def ClearDrawables():
        Renderer.drawables_rem = Renderer.drawables_add.copy()

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
        
    

    

    
