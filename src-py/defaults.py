
# configurable metrics
window_dim = (1280,720)
fullscreen = False
letter_height = 12
letter_height_intro = 14
caption = "Yet another Jump'n'Run (an unfair one)"


# derived values, do not change
cells = None
cells_intro = None

def update_derived():
    global cells
    global cells_intro

    # derived values, do not change
    cells = (window_dim[0]//letter_height,window_dim[1]//letter_height)
    cells_intro = (window_dim[0]//letter_height,window_dim[1]//letter_height_intro)
