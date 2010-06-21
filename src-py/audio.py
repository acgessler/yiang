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

# Python core
import os
import random

# PySFML
import sf

# My stuff
import defaults


class SoundEffectCache:
    """Tiny utility to cache all sound effects which we use."""
    cached = {}
    music_ext = [".ogg"]

    @staticmethod
    def Get(name):
        assert name

        sound = SoundEffectCache.cached.get(name,None) 
        if not sound is None:
            return sound
        
        print("Loading sound {0}".format(name))

        music = os.path.splitext(name)[-1] in SoundEffectCache.music_ext    
        sound = music and sf.Music() or sf.SoundBuffer()
        
        filename = os.path.join(defaults.data_dir,"sounds", name+(".wav" if name.find(".") == -1 else ""))
        if music is True:
            if not sound.OpenFromFile(filename):
                print("Failure creating music {0} [{1}]".format(name,filename))
                return None
            
            sound.SetVolume(defaults.audio_volume_scale*100)
        else:
            if not sound.LoadFromFile(filename):
                print("Failure creating sound {0} [{1}]".format(name,filename))
                return None
            
            class SoundWrapper:
                def __init__(self,buffer):
                    self.sound = sf.Sound()
                    self.sound.SetBuffer(buffer)
                    self.sound.SetVolume(defaults.audio_volume_scale*100)
                    
                def Play(self):
                    self.sound.Play()
            
            sound = SoundWrapper(sound)

        print("Caching sound {0} [{1},music: {2}]".format(name,filename,music))
        SoundEffectCache.cached[name] = sound
        return sound


class BerlinerPhilharmoniker:
    """The background orchestra which we're paying for. Actually
    it's a bit too expensive, but it is definitely worth the
    effort."""
    playlist = []
    current_index = 0
    current_music = None
    
    @classmethod
    def Initialize(cls):
        try:
            with open(os.path.join(defaults.config_dir,"playlist.txt"),"rt") as o:
                cls.playlist = [o.strip("\n \t") for o in o.readlines()]   
            print("Got {0} play list entries from playlist.txt".format(len(cls.playlist)))         
        except IOError:
            print("Failure reading playlist.txt, disabling background music")
    
    @classmethod
    def Process(cls):
        if cls.current_music is None:
            cls.current_music = sf.Music()
            
        if cls.current_music.GetStatus() == sf.Sound.Stopped:
            cls.current_index = random.randint(0,len(cls.playlist)-1) if defaults.audio_randomize_playlist is True \
                else (cls.current_index +1) % len(cls.playlist)
            path = cls.playlist[cls.current_index]
            if path.find("/") == -1 and path.find("\\") == -1:
                path = os.path.join(defaults.data_dir,"sounds",path)
                
            #print("Try")
            if cls.current_music.OpenFromFile(path) is False:
                print("Can't load track {0} \ {1} from playlist, this is a bit sad".format(cls.current_index,path))
                return
            
            print("Load track {0} \ {1}".format(cls.current_index,path))
            cls.current_music.Play()
            
    
        
        
        
        
        
        
        
        