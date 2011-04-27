#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [defaults.py]
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

import os

#
# Do *not* load any other modules here. It is essential that the initialization
# order is as follows:
#
# - os, sys, ... (Python core)
# - defaults
# - preboot
# - log
# - main/editor
# - ... doesn't care ...
#

# -----------------------------------------------------------------------------
# configurable metrics, altered by config/game.txt upon startup

version = 2.0
revision = 607
server_name = "www.yiang-thegame.com"
master_locale="de"
allow_network_use=False
resolution = [1280, 850]
fullscreen = False
resizable = False
letter_size = [6.5, 11.5]
letter_height_intro = 13
letter_height_menu = 52
letter_height_status = 20
letter_height_lives = 9
letter_height_lives_numeric = 48
lifebar_numeric_treshold = 8
letter_height_game_over = 17 
letter_height_messagebox = 18
letter_height_debug_info = 15
letter_height_machines = 14
letter_height_credits = 24
letter_height_worldmap_status = 20
letter_height_gui = 14
caption = "YIANG |"
danger_signs_ttl = 100
tiles_size = [5, 3]
move_speed = [5, 4]
gravity = 15 # tiles/m*s^2
jump_vel = 9.5 # tiles/m*s
debug_updown_move = False
debug_keys = True
debug_prevent_fall_down = False
debug_draw_bounding_boxes = False
debug_draw_info = False
debug_godmode = False
debug_scroll_both = False
move_map_speed_slow = 0.1
move_map_speed = 0.20
move_map_speed_fast = 0.3
lives = 6
enable_log = True
log_file = "log.txt"
game_over_fade_time = 2.0
enter_level_fade_time = 1.4
enter_worldmap_fade_time = 2.0
messagebox_fade_time = 2.0
loading_time = 10.0
loading_fool_player = False
death_sprites = 130
min_death_sprites = 5
death_sprites_player = 330
min_death_sprites_player = 10
pain_sprites_player = 10
min_pain_sprites_player = 2
max_useless_sprites = 2000
max_framerate_for_sprites = 30

framerate_limit = 60
min_respawn_distance = 2.0
right_scroll_distance = 9
left_scroll_distance = 8
top_scroll_distance = 4
bottom_scroll_distance = 9
respawn_origin_distance = 8.0
teleport_origin_distance = 8.0
speed_scale_per_round = 1.5
antialiasing_level = 2
player_caution_border = [2, 12]
draw_clamp_to_pixel = True # may be ignored on Windows
debug_trace_keypoints = False
show_window_caption = True
enable_menu_image_bg = False
cull_distance_rel = 1.5
swapout_distance_rel = [0.25,0.4]
fade_stop = 0.40
fade_start = 1.0 - fade_stop
blur_stop = 0.0
blur_start = 1.0 - blur_stop
blur_multiplier = 1.0
dither = True
enable_menu_background_danger_stubs = False
status_bar_top_tiles = 3.0
level_window_size_rel = [0.15,0.2]
perks_overlay_start = 2.0
perks_overlay_spacing = 1.0
perks_overlay_letter_height = 15
audio_randomize_playlist = False
levelup_score_base = 0.08
organ_transplant_dollar_in = 1.0
ammo_transplant_dollar_in = 0.2
ammo_transplant_ammo_plus = 10
no_bg_music = False
no_bg_sound = False
audio_volume_scale = 0.8
def_user_profile = "Wurzelgnom"
no_intro = True
no_logo = True

postfx_flash_length = 1
postfx_flash_intensity = 0.08
postfx_focus_length = 0.8

load_optimized_levels = True

# Disable threading. This implies disabling loading screens.
no_threading = False

# don't render background bitmaps (halos)
# this is what the configuration GUI calls 
# 'optimize for low-end systems'
no_halos = False

# completely disable postprocessing
no_ppfx = False

# time the player is protected against harm 
# after respawning, in seconds
respawn_protection_time = 2.0

# time the player is protected against harm 
# after a teleport, in seconds
teleport_protection_time = 1.5

# profile any calls to LevelLoader.Load(), 
# writes cProfile results to the profile directory
# and dumps the 20 hottest locations to the console
profile_level_loading = False

# profile rendering. This is done by observing
# every 600st frame for a level (~10s).
# writes cProfile results to the profile directory
# and dumps the 20 hottest locations to the console
profile_rendering = False

# Draw the HUD (minimap) in world maps. Disable if
# this causes problems with your screen setup (i.e.
# the player is no longer visible)
world_draw_hud = True

# Relative size of the minimap, x-axis
# Note: the minimap is never minified.
minimap_size = 0.2

# Base alpha value for uncovered areas of the minimap
minimap_alpha = 0x80

# Maximum delta t - dt's over this limit are silently ignored
delta_t_treshold = 0.2

# Disable periods if very high distortion (their freuqncy is level-dependent)
no_distortion = True

# Minimum velocity for 'pain, pain, cry' messages to  appear
pain_treshold = 15

# Frame rate limiting, up to 4 steps.
slowdown_level = 0

# Size of a single collision tap, in tiles. If the player moves
# by n times this distance in a single frame, collision detection
# is performed multiple times.
collision_tap_size = 0.1

max_velocity_x,max_velocity_y = 20,25
update_tickrate = 60

# -----------------------------------------------------------------------------
# these are not intended to be modified, although no one keeps
# you from changing them. you have been warned.
root_dir = ".."
locale_dir = os.path.join(root_dir, "locale")
udata_dir = os.path.join(root_dir, "userdata")
data_dir = os.path.join(root_dir, "data")
profile_dir = os.path.join(root_dir, "profile")
config_dir = os.path.join(root_dir, "config")
font_monospace = os.path.join(data_dir, "fonts", "VeraMoBd.ttf")
font_lives = font_monospace
font_menu = os.path.join(data_dir, "fonts", "Herbiflora.ttf")
font_status = os.path.join(data_dir, "fonts", "AndBasR.ttf")
font_debug_info = font_monospace
font_game_over = font_status
font_messagebox = font_status
font_gui = font_status
font_machines = os.path.join(data_dir, "fonts", "VeraMono.ttf")
credits_string = "(c) 2010 Alexander Christoph Gessler"
resolution_base = [1280, 850]

homepage_url = "http://"+server_name
highscore_json_url = "http://"+server_name+"/php/highscore.php"

# -----------------------------------------------------------------------------
# derived values (not configurable settings!), do not change. you have been warned.
cells = None
cells_intro = None
tiles = None
tiles_size_px = None
cull_distance = None
scale = None
max_game_tiles_y = None
level_window_size_abs = None
cur_user_profile = None
cur_user_profile_dir = None

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
 #   cull_distance_sqr = (cull_distance_rel * tiles[0]) ** 2 + (cull_distance_rel * tiles[1]) ** 2
 #   swapout_distance_sqr = (swapout_distance_rel * tiles[0]) ** 2 + (swapout_distance_rel * tiles[1]) ** 2
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
        

def GetColorName(col):
    if col.a == 0:
        return _("Invisible")
        
    if col.r > 60:
        if col.g > 60:
            if col.b > 60:
                return _("Gray") if col.r+col.b+col.g!=255*3 else _("White")
            else:
                return _("Yellow")
        else:         
            if col.b > 60:
                return _("Pink")
            else:
                return _("Red")
    else:
        if col.g > 60:
            if col.b > 60:
                return _("Azure")
            else:
                return _("Green")
        else:         
            if col.b > 60:
                return _("Blue")
            else:
                return _("Black")
    assert False
    

# vim: ai ts=4 sts=4 et sw=4
