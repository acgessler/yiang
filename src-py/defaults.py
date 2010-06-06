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

import os

# -----------------------------------------------------------------------------
# configurable metrics, altered by config/game.txt upon startup
resolution = [1280,720]
fullscreen = False
letter_size = [8,12]
letter_height_intro = 10
letter_height_status = 36
letter_height_lives = 9
letter_height_game_over = 15
caption = "Yet another Jump'n'Run (an unfair one)"
danger_signs_ttl = 30
tiles_size = [5,3]
move_speed = [5,4]
gravity = -15 # tiles/m*s^2
jump_vel = 9 # tiles/m*s
debug_updown_move = False
debug_keys = True
debug_prevent_fall_down = False
debug_draw_bounding_boxes = False
move_map_speed = 0.1
lives = 4
enable_log = True
log_file = "log.txt"
game_over_fade_time = 2.0
framerate_limit = 60
min_respawn_distance = 2.5
right_scroll_distance = 9
respawn_origin_distance = 2.0

# -----------------------------------------------------------------------------
# these are not intended to be modified, although no one keeps
# you from changing them. you have been warned.
root_dir = ".."
data_dir = os.path.join(root_dir,"data")
config_dir = os.path.join(root_dir,"config")
font_monospace = os.path.join(data_dir,"fonts","courier_new_bold.ttf")
font_lives = font_monospace
font_menu = os.path.join(data_dir,"fonts","VeraSE.ttf")
font_status = font_menu
font_game_over = font_menu
credits_string = "(c) 2010 Alexander Christoph Gessler"

# -----------------------------------------------------------------------------
# derived values, do not change. you have been warned.
cells = None
cells_intro = None
tiles = None
tiles_size_px = None

# -----------------------------------------------------------------------------
def update_derived():
    """Update any properties in the `derived` section.
    Must be called at least once before one of them is
    used"""
    
    global cells
    global tiles
    global cells_intro
    global tiles_size_px

    # derived values, do not change
    cells = (resolution[0]//letter_size[0],resolution[1]//letter_size[1])
    cells_intro = ((resolution[0]*4)//(letter_height_intro*2),resolution[1]//letter_height_intro)
    tiles = (cells[0]//tiles_size[0],cells[1]//tiles_size[1])
    tiles_size_px = (letter_size[0]*tiles_size[0],letter_size[1]*tiles_size[1])

def merge_config(file):
    """Merge the current configuration with the settings
    read from an external file. Each line is passed to
    eval(), errors are ignored.

    Parameters:
    file -- The file to be read

    Throws:
    --
    """
    try:
        with open(file,"rt") as f:
            lines = [t for t in [m.strip("\n ") for m in f.readlines()] if len(t) and t[0] != "#"]
            for line in lines:
                try:
                    exec(line,globals(),globals())
                except Exception as e:
                    print("Error parsing "+file+": "+str(e))
                
    except IOError:
        print("Could not open configuration file: "+file)
        return

    print("Processed "+file)
        





        
    
