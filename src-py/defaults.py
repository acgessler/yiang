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

version = 0.1
revision = 183
resolution = [1280, 850]
fullscreen = False
letter_size = [8, 13]
letter_height_intro = 12
letter_height_menu = 100
letter_height_status = 36
letter_height_lives = 9
letter_height_game_over = 15
letter_height_debug_info = 15
letter_height_machines = 14
letter_height_credits = 25
caption = "YIANG | {0}             [HGREV {1}]".format(version,revision)
danger_signs_ttl = 30
tiles_size = [5, 3]
move_speed = [5, 4]
gravity = -15 # tiles/m*s^2
jump_vel = 9 # tiles/m*s
debug_updown_move = False
debug_keys = True
debug_prevent_fall_down = False
debug_draw_bounding_boxes = False
debug_draw_info = False
debug_godmode = False
debug_scroll_both = False
move_map_speed = 0.25
lives = 6
enable_log = True
log_file = "log.txt"
game_over_fade_time = 2.0
framerate_limit = 60
min_respawn_distance = 2.0
right_scroll_distance = 9
respawn_origin_distance = 2.0
speed_scale_per_level = 1.025
antialiasing_level = 2
player_caution_border = [2, 7]
draw_clamp_to_pixel = True
debug_trace_keypoints = False
show_window_caption = True
enable_menu_image_bg = False
cull_distance_rel = 1.5
swapout_distance_rel = 3.0 
fade_stop = 0.25
fade_start = 0.75
dither = True
enable_menu_background_danger_stubs = False
death_sprites = 60
status_bar_top_tiles = 2.5
level_window_size_rel = [0.4,1.0]
perks_overlay_start = 2.0
perks_overlay_spacing = 1.0
perks_overlay_letter_height = 15
audio_randomize_playlist = True
levelup_score_base = 15.0
organ_transplant_dollar_in = 1.0
no_bg_music = False
audio_volume_scale = 0.5

# -----------------------------------------------------------------------------
# these are not intended to be modified, although no one keeps
# you from changing them. you have been warned.
root_dir = ".."
data_dir = os.path.join(root_dir, "data")
config_dir = os.path.join(root_dir, "config")
font_monospace = os.path.join(data_dir, "fonts", "VeraMoBd.ttf")
font_lives = font_monospace
font_menu = os.path.join(data_dir, "fonts", "VeraSE.ttf")
font_status = font_menu
font_debug_info = font_monospace
font_game_over = font_menu
font_machines = os.path.join(data_dir, "fonts", "courier_new.ttf")
credits_string = "(c) 2010 Alexander Christoph Gessler"
resolution_base = [1280, 850]

# -----------------------------------------------------------------------------
# derived values, do not change. you have been warned.
cells = None
cells_intro = None
tiles = None
tiles_size_px = None
cull_distance = None
scale = None
max_game_tiles_y = None
level_window_size_abs = None

# -----------------------------------------------------------------------------
def update_derived():
    """Update any properties in the `derived` section.
    Must be called at least once before one of them is
    used. This mostly updates properties which depend
    on screen resolution, etc..."""
    
    global cells
    global tiles
    global cells_intro
    global tiles_size_px
    global cull_distance_sqr
    global swapout_distance_sqr
    global scale
    global letter_size
    global max_game_tiles_y
    global level_window_size_abs

    # this is a mess and we ought to clean up here ..
    scale = (resolution[0] / resolution_base[0], resolution[1] / resolution_base[1])
    letter_size = (int(letter_size[0] * scale[1]), int(letter_size[1] * scale[1]))
    cells = (resolution[0] // letter_size[0], resolution[1] // letter_size[1])
    cells_intro = ((resolution[0] * 4) // (letter_height_intro * 2), resolution[1] // letter_height_intro)
    tiles = (cells[0] // tiles_size[0], cells[1] // tiles_size[1])
    tiles_size_px = (letter_size[0] * tiles_size[0], letter_size[1] * tiles_size[1] + 1)
    cull_distance_sqr = (cull_distance_rel * tiles[0]) ** 2 + (cull_distance_rel * tiles[1]) ** 2
    swapout_distance_sqr = (swapout_distance_rel * tiles[0]) ** 2 + (swapout_distance_rel * tiles[1]) ** 2
    max_game_tiles_y = int(tiles[1]-status_bar_top_tiles)
    level_window_size_abs = (level_window_size_rel[0]*tiles[0],level_window_size_rel[1]*tiles[1])
    
    # leave the other font heights unscaled

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
        with open(file, "rt") as f:
            lines = [t for t in [m.strip("\n ") for m in f.readlines()] if len(t) and t[0] != "#"]

            # convinience substitutions 
            replace = {
                ".x" : "[0]",
                ".y" : "[1]",
            }
    
            for line in lines:
                for k, v in replace.items():
                    line = line.replace(k, v)
                    
                try:
                    exec(line, globals(), globals())
                except Exception as e:
                    print("Error parsing " + file + ": " + str(e))
                
    except IOError:
        print("Could not open configuration file: " + file)
        return

    print("Processed " + file)
        





        
    
