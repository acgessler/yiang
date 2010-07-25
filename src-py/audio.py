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
            class MusicWrapper:
                
                def __init__(self,music):
                    self.music = music
    
                def __getattr__(self,name):
                    return getattr(self.music,name)
                
                def SetVolume(self,volume):
                    self.music.SetVolume(defaults.audio_volume_scale*100*volume)
                    return self
    
            sound = MusicWrapper(sound)
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
                    return self
                    
                def SetVolume(self,volume):
                    self.sound.SetVolume(defaults.audio_volume_scale*100*volume)
                    return self
            
            sound = SoundWrapper(sound)

        print("Caching sound {0} [{1},music: {2}]".format(name,filename,music))
        SoundEffectCache.cached[name] = sound
        return sound


class BerlinerPhilharmoniker:
    """The background orchestra which we're paying for. Actually
    it's a bit too expensive, but it is definitely worth the
    effort."""
    playlist = {}
    status_cache = {}
    current_index = -1
    current_music = None
    current_music_name = ""
    section = "default"
    
    @classmethod
    def Initialize(cls):
        """
        try:
            with open(os.path.join(defaults.config_dir,"playlist.txt"),"rt") as o:
                cls.playlist = [o.strip("\n \t") for o in o.readlines()]   
            print("Got {0} play list entries from playlist.txt".format(len(cls.playlist)))         
        except IOError:
            print("Failure reading playlist.txt, disabling background music")
        """
        import configparser
        
        config = configparser.RawConfigParser()
        config.read(os.path.join(defaults.config_dir,"playlist.cfg"))
        
        pieces = 0
        for elem in config.sections():
            
            e = cls.playlist[elem] = []
            for k,v in config.items(elem):
                e.append(v)
                pieces += 1
                
        print("Got {0} sections with totally {1} pieces from playlist.cfg".format(len(cls.playlist),pieces))         
        
    @classmethod    
    def SetAudioSection(cls,name):
        """Set the current audio track section. The class loops all
        the tracks within the current section until another
        section is choosen. Raise KeyError if this audio section
        is not known"""
        if name == cls.section:
            return # keep running section intact
            
        cls.status_cache.setdefault(cls.section,{})["current"] = cls.current_music
        cls.status_cache[cls.section]["current_idx"] = cls.current_index
            
        cls.section = name
        old = cls.current_music
        
        if cls.section in cls.status_cache:
            cls.current_music = cls.status_cache[cls.section]["current"]
            cls.current_index = cls.status_cache[cls.section]["current_idx"]
            #if cls.current_music:
            #    cls.current_music.Play()
        else:
            cls.current_music = None
            cls.current_index = 0
            
        if old and cls.current_music_name != cls.playlist[name][cls.current_index]:
            old.Stop()
        
        s = cls.playlist[name]
        print("Set audio section: {0}".format(name))
    
    @classmethod
    def Process(cls):
        if cls.current_music is None:
            cls.current_music = sf.Music()
            
        if cls.current_music.GetStatus() == sf.Sound.Stopped:
            try:
                if len(cls.playlist[cls.section]) == 0:
                    print("Audio section {0} is empty".format(cls.section))
                    return
            except KeyError:
                print("Audio section {0} does not exist".format(cls.section))
                return
                   
            cls.current_index = random.randint(0,len(cls.playlist[cls.section])-1) if defaults.audio_randomize_playlist is True \
                else (cls.current_index +1) % len(cls.playlist[cls.section])
            path = cls.playlist[cls.section][cls.current_index]
            cls.current_music_name = path
             
            #if path.find("/") == -1 and path.find("\\") == -1:
            #    path = os.path.join(defaults.data_dir,"sounds",path)
                
            cls.current_music = SoundEffectCache.Get(path)
            if cls.current_music is None:#cls.current_music.OpenFromFile(path) is False:
                print("Can't load track {2}-{0} \ {1} from playlist, this is a bit sad".format(cls.current_index,path,cls.section))
                return
            
            print("Load track {2}-{0} \ {1}".format(cls.current_index,path,cls.section))
            cls.current_music.Play()
            
    
        
        
        
        
        
        
        
        