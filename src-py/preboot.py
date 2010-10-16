#!echo "This file is not executable"
# -*- coding: UTF_8 -*-

#/////////////////////////////////////////////////////////////////////////////////
# Yet Another Jump'n'Run Game, unfair this time.
# (c) 2010 Alexander Christoph Gessler
#
# HIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO self.event SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND 
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ///////////////////////////////////////////////////////////////////////////////////


import sys, os


#
# Do *not* load any other modules here. It is essential that the initialization
# order is as follows:
#
# - os, sys, ... (Python core)
# - defaults
# - preboot
# - log
# - fshack
# - main/editor
# - ... doesn't care ...
#


# Read game.txt (or any other file specified via cmd), which is the master config file
import defaults
defaults.merge_config(sys.argv[1] if len(sys.argv)>1 else os.path.join(defaults.config_dir,"game.txt"))

from log import Log
Log.Enable(defaults.enable_log)

import fshack
fshack.Enable()

import gettext
lang = gettext.translation("yiang", defaults.locale_dir, languages=[defaults.master_locale])
if not lang:
    lang = gettext.translation("yiang", defaults.locale_dir, languages=['en'])
    if not lang:
        assert False
    
lang.install()





