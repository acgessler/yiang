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

import sf

# Python core
import sys
import os

# Our stuff
import defaults

from fonts import FontCache
from keys import KeyMapping
from game import Game
from log import Log
from renderer import Renderer,Drawable
from highscore import HighscoreManager
from audio import BerlinerPhilharmoniker
from achievements import Achievements

class EditorOverlay(Drawable):
    
    def __init__(self):
        Drawable.__init__(self)
        self.cursor_img  = sf.Image()
        self.cursor_img.LoadFromFile(os.path.join(defaults.data_dir,"textures","cursor.png"))
        
        self.cursor = sf.Sprite(self.cursor_img)
        Renderer.app.ShowMouseCursor(False)
    
    def Draw(self):
        inp = Renderer.app.GetInput()
        mx,my = inp.GetMouseX(),inp.GetMouseY()

        w,h =self.cursor_img.GetWidth(),self.cursor_img.GetHeight()
        self.cursor.SetPosition(mx-w/2,my-h/2)
        Renderer.app.Draw(self.cursor)

def main():
    """Main entry point to the editor application"""

    # Read game.txt, which is the master config file
    defaults.merge_config(sys.argv[1] if len(sys.argv)>1 else os.path.join(defaults.config_dir,"game.txt"))
    Log.Enable(defaults.enable_log)

    print("Startup ...")
    KeyMapping.LoadFromFile(os.path.join(defaults.config_dir,"key_bindings.txt"))

    Renderer.Initialize()
    
    # Perform dummy initializations of some subsystems which are
    # needed for running a Game, but are not necessarily
    # useful for the editor
    HighscoreManager.InitializeDummy()
    Achievements.InitializeDummy()
    BerlinerPhilharmoniker.InitializeDummy()
    
    # Run the game as usual but push the EditorOverlay on top of it
    game = Game(Renderer.app)
    game.LoadLevel(1)
    Renderer.AddDrawable(game)
    Renderer.AddDrawable(EditorOverlay())
    
    Renderer.DoLoop()
    Renderer.Terminate()
    

        
        
        
        
        
        
        