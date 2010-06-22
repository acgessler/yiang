
# this is for linux, where the system-wide, regular PySFML is used. 
# On Windows, PySFML is embedded and put into a single module ('sf')
# for simplicity (or unawareness of the necessity to port the app
# at a later time ...). Therefore, on Windoes one may import 'sf'
# but this module is silently skipped because there is already an
# init stub entry with this name.

from PySFML.sf import *
