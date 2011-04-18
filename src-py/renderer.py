#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [renderer.py]
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

# Python core
import os
import platform
import math

# PySFML
import sf

# My own stuff
import defaults
import mathutil

if defaults.no_threading:
    import dummy_threading as threading
else:
    import threading 
    

class Drawable:
    """Master class for all kinds of drawable objects, i.e. tiles,
    overlays, menues, .... Drawable defines some basic traits
    of these objects. High-level drawable objects are maintained
    by the Renderer class, which wraps the main loop of the game.
    
    Level tiles and game entities are Drawable's as well, but 
    they are maintained by the Game class (which is itself a
    Drawable)."""

    FLAG_ACTIVE = 0x1
    
    def __init__(self, flags=0):
        self.flags = flags
        self.slaves = []

    def SetFlag(self, flag):
        self.flags |= flag

    def RemoveFlag(self, flag):
        self.flags &= ~flag

    def QueryFlag(self, flag):
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
    
    def GetBoundingBoxAbs(self):
        """Get a xy,xy bounding box."""
        r = self.GetBoundingBox()
        return r and (r[0],r[1],r[0]+r[2],r[1]+r[3])

    def OnRemoveFromRenderer(self):
        """Called by Renderer when the Drawable has actually
        been removed from the list of all active drawables.
        Note that calling Renderer.RemoveDrawable() does not
        immediately lead to removal of the entity because 
        the operation may be deferred a bit."""
        self.RemoveFlag(Drawable.FLAG_ACTIVE)
        for d in self.slaves:
            Renderer.RemoveDrawable(d)
    
    def OnAddToRenderer(self):
        """Called by Renderer when the Drawable has actually
        been add to the list of all active drawables.
        Note that calling Renderer.AddDrawable() does not
        immediately lead to registration of the entity because 
        the operation may be deferred a bit."""
        self.SetFlag(Drawable.FLAG_ACTIVE)
        for d in self.slaves:
            Renderer.AddDrawable(d)
    
    def AddSlaveDrawable(self,drawable):
        """Add a slave to the drawable object. The slave 
        is automatically enabled and disabled with the 
        drawable itself."""
        self.slaves.append(drawable)
        Renderer.AddDrawable(drawable) if self.QueryFlag(Drawable.FLAG_ACTIVE) else Renderer.RemoveDrawable(drawable)
        
    def RemoveSlaveDrawable(self,drawable):
        """Remove a specific slave drawable from the object."""
        try:
            self.slaves.remove(drawable)
            Renderer.RemoveDrawable(drawable)
        except ValueError:
            # safeguard against unsafe use of slaves
            print("Slave drawable {0} on drawable {1} is not known as such".format(drawable,self))
            pass
        
    def OnChangeResolution(self,newres):
        """Called when the display resolution (the window size
        in windowed mode) is changed. newres is the new
        resolution, in pixels."""
        pass

    def Draw(self):
        """To be implemented to perform any drawing operations
        for the drawable entity (a drawable should represent 
        something that can be drawn, shouldn't it?)"""
        pass
    
    def ProcessEvents(self):
        """Called once per frame like Draw(), but in reverse order (
        descending draw order). Use this to process and swallow
        any incoming events."""
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

    app = None
    drawables, drawables_add, drawables_rem = set(), set(), set()
    drawables_active = []                                     
    clear_color = sf.Color.White
    event = None
    loop_running = False
    fidx = -1
    frame_cnt = 0
    
    bgimg = None
    bgxpos = 0
    bgymax = 1

    @staticmethod
    def Initialize():
        """Initialize the rendering infrastructure and
        create a window"""

        #Renderer._CheckRequirements()
        print("Creating window ...")
        settings = sf.WindowSettings()
        settings.DepthBits = 0
        settings.StencilBits = 0  
        settings.AntialiasingLevel = defaults.antialiasing_level
        
        print("Running: {0}, {1}, {2}".format(platform.platform(),platform.machine(),platform.architecture()[0])) 
            
        # Create main window
        dm = sf.VideoMode.GetDesktopMode()
        if defaults.fullscreen is True:
        
            p[4] = 4
            defaults.resolution = dm.Width, dm.Height
            Renderer.app = sf.RenderWindow(dm, defaults.caption, sf.Style.Fullscreen, settings)
        else:
            tb = (sf.Style.Resize|sf.Style.Close if defaults.resizable else sf.Style.Close) if defaults.show_window_caption else sf.Style._None
            Renderer.app = sf.RenderWindow(sf.VideoMode(
                    min(defaults.resolution[0], dm.Width),
                    min(defaults.resolution[1], dm.Height)
                ),
                defaults.caption + " v{0}.{1} ({2} Bit Build)".format(defaults.version,defaults.revision, platform.architecture()[0][0:2]), tb, settings)


        # load the icon manually from a PNG - I don't know how to pass a proper ICON to SFML
        from textures import TextureCache
        icon = TextureCache.Get(os.path.join(defaults.data_dir,'icon','YIANG.png'))
        assert icon.GetWidth() == 16 and icon.GetHeight() == 16
        
        import array
        aico = array.array('B')
        
        for y in range(16):
            for x in range(16):
                col = icon.GetPixel(x,y)
                aico.append(col.r)
                aico.append(col.g)
                aico.append(col.b)
                aico.append(col.a)
        
        Renderer.app.SetIcon(16, 16, aico.tostring() )
        if defaults.framerate_limit > 0:
            Renderer.app.SetFramerateLimit(defaults.framerate_limit)

        print("Updating derived settings ...")
        defaults.update_derived()
    
        
        print("-"*60)
        
    @staticmethod
    def SetBGImage(id=-1):
        Renderer.bgimg = None if id==-1 or id is None else Renderer.GetBGImage(id) 
        
    @staticmethod
    def GetBGImage(id=-1):
        from textures import TextureCache
        return TextureCache.GetFromBG("bg{0}.jpg".format(id))
    
    @staticmethod
    def SetBGXPos(p):
        Renderer.bgxpos = p
        
    @staticmethod
    def SetBGYMax(p):
        Renderer.bgymax = p

    @staticmethod
    def _CheckRequirements():
        """Check if hardware requirements to run the game are met,
        does not return if not"""
    
        if sf.PostFX.CanUsePostFX() is False:
            print("Need to support postprocessing effects, buy better hardware!")
            import sys
            sys.exit(-100)
            
    @staticmethod
    def _DoSingleFrame():
        """ """
        event = sf.Event()
        Renderer.draw_counter, Renderer.inrange = 0, 0
        Renderer.events = set()
        
        if defaults.slowdown_level > 0:
            import time
            time.sleep((0.01,0.025,0.05)[defaults.slowdown_level-1])
        
        while Renderer.app.GetEvent(event):
            #Close window : exit
            if event.Type == sf.Event.Closed: # XXX propagate this to users?
                Renderer.app.Close()

                Renderer.loop_running = False
                return True
            
            elif event.Type == sf.Event.Resized:
                #glViewport(0, 0, Event.Size.Width, Event.Size.Height);
                view = sf.View()
                view.SetFromRect(sf.FloatRect(0,0,event.Size.Width, event.Size.Height))
                Renderer.app.SetView(view)
                
                defaults.resolution = event.Size.Width, event.Size.Height
                for drawable in Renderer.drawables:
                    drawable.OnChangeResolution(defaults.resolution)

            Renderer.events.add(event)
            event = sf.Event()
        
        # draw background image, if applicable
        if Renderer.bgimg:
            s = sf.Sprite(Renderer.bgimg)
            s.Move(-Renderer.bgxpos*(Renderer.bgimg.GetWidth()-defaults.resolution[0]) ,0)
            
            sc = Renderer.bgymax*defaults.resolution[1]/Renderer.bgimg.GetHeight()
            s.SetScale(sc,sc)
            Renderer.app.Draw(s)
        else:
            Renderer.app.Clear(Renderer.clear_color)

        drawable = None
        sorted_drawables = sorted(Renderer.drawables, key=lambda x: x.GetDrawOrder())
        try:
            for drawable in reversed( sorted_drawables ):
                drawable.ProcessEvents()
                
            for drawable in sorted_drawables:
                drawable.Draw()
        except NewFrame:
            pass
        except Exception as ex:
            print("[Responsible seems to be a {0} instance]".format(type(drawable)))
            raise

        # update the drawables list, handle dependencies of changed drawables, notify the drawables.
        cpy = set(Renderer.drawables_add)
        Renderer.drawables_add = set()
        
        for entity in cpy:
            Renderer.drawables.add(entity)
            if hasattr(entity, "__drawable_deps__"):
                for dep in entity.__drawable_deps__:
                    try:
                        Renderer.drawables.remove(dep)
                        dep.OnRemoveFromRenderer()
                    except KeyError:
                        pass
                    
            entity.OnAddToRenderer()

        cpy = set(Renderer.drawables_rem)
        Renderer.drawables_rem = set()
        for entity in cpy:
            try:
                Renderer.drawables.remove(entity)
                if hasattr(entity, "__drawable_deps__"):
                     for dep in entity.__drawable_deps__:
                         Renderer.drawables.add(dep)
                         dep.OnAddToRenderer()
                         
                     delattr(entity, "__drawable_deps__")
            except KeyError:
                pass
            
            entity.OnRemoveFromRenderer()

        # toggle front and backbuffer
        Renderer.app.Display()
        Renderer.frame_cnt += 1
        
    @staticmethod
    def IsMainloopRunning():
        return Renderer.loop_running and Renderer.app.IsOpened() 

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
            
            cnt, profiles = 0,0
            while Renderer.app.IsOpened() is True:
                
                # profile rendering (10 frames in a row)
                if defaults.profile_rendering is True and cnt == 600:
                    cnt = 0
                    profiles += 1
                    import cProfile
            
                    fname = filename=os.path.join(defaults.profile_dir,
                        "render_{0}.cprof".format(profiles))
                    
                    def Do10Frames():
                        for i in range(10):
                            if Renderer.app.IsOpened() is False:
                                break
                            Renderer._DoSingleFrame()
                        
                    try:
                        cProfile.runctx("Do10Frames()", globals(), locals(), fname)
                        import pstats
                        stats = pstats.Stats(fname)
                        stats.strip_dirs().sort_stats('time').print_stats(20)
                    except OSError: # folder doesn't exist
                        print("Cannot profile, create 'profile' directory first")
            
                else:
                    Renderer._DoSingleFrame()
                    cnt += 1
                    Renderer.fidx += 1

        except _QuitNow:
            pass

        Renderer.loop_running = False
        return False
    
    @staticmethod
    def DrawTiled(img,alpha,x0,y0,x1,y1):
        x,y = img.GetWidth()-1,img.GetHeight()-1
        t = sf.Sprite(img)
        t.SetColor(sf.Color(0xff,0xff,0xff,alpha))
        a = Renderer.app
        
        # -0.5 to guarantee pixel-exact mapping
        x0,x1,y0,y1 = x0-0.5,x1-0.5,y0-0.5,y1-0.5
        
        for yy in range(math.ceil((y1-y0)/y)):
            for xx in range(math.ceil((x1-x0)/x)):
                xxx,yyy = x0+x*xx,y0+y*yy
                dx,dy = x1-xxx, y1-yyy
                
                # XXX - get rid of those seams ..
                t.SetSubRect(sf.IntRect(0,0, int(min(x,dx))+1, int(min(y,dy))+1))
                t.SetPosition(xxx,yyy)
                a.Draw(t)
                
    
    @staticmethod
    def GetFrameIndex():
        return Renderer.fidx

    @staticmethod
    def GetEvents():
        return Renderer.events
    
    @staticmethod
    def SwallowEvents():
        a = Renderer.events
        Renderer.events = []
        return a

    @staticmethod
    def AddDrawable(drawable, substitutes=None):
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
            assert not hasattr(drawable, "__drawable_deps__")
            # hijack the instance a bit
            drawable.__drawable_deps__ = [substitutes] if isinstance(substitutes, Drawable) \
                else substitutes

    @staticmethod
    def RemoveDrawable(drawable, handle_dependencees=True):
        Renderer.drawables_rem.add(drawable)
        
        if handle_dependencees is False:
            drawable.__drawable_deps__ = []

    @staticmethod
    def ClearDrawables():
        Renderer.drawables_rem = Renderer.drawables_add.copy()
        
    @staticmethod
    def GetDrawables():
        return Renderer.drawables

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
        
        

        
    

    

    

# vim: ai ts=4 sts=4 et sw=4