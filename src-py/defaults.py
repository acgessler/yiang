
import os






# configurable metrics, altered by config/game.txt upon startup
resolution = [1280,720]
fullscreen = False
letter_height = 12
letter_height_intro = 10
letter_height_status = 14
caption = "Yet another Jump'n'Run (an unfair one)"
danger_signs_ttl = 30

# these are not intended to be modified, although no one keeps
# you from changing them.
root_dir = ".."
data_dir = os.path.join(root_dir,"data")
config_dir = os.path.join(root_dir,"config")
font_monospace = os.path.join(data_dir,"fonts","courier_new_bold.ttf")
font_status = os.path.join(data_dir,"fonts","courier_new_bold.ttf")
credits_string = "(c) 2010 Alexander Christoph Gessler"

# derived values, do not change
cells = None
cells_intro = None







def update_derived():
    """Update any properties in the `derived` section.
    Must be called at least once"""
    
    global cells
    global cells_intro

    # derived values, do not change
    cells = ((resolution[0]*4)//(letter_height*2),resolution[1]//letter_height)
    cells_intro = ((resolution[0]*4)//(letter_height_intro*2),resolution[1]//letter_height_intro)


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
        





        
    
