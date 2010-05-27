
import defaults
import sf

class FontCache:
    """Tiny utility to cache all fonts we're using to avoid creating redundant instances.
    I assume SFML caches internally as well, but this way we can safe some additional
    overhead, also fonts are easier to track."""

    cached = {}

    def get(height,face=""):
        if not face:
            face = defaults.font_monospace

        font = FontCache.cached.get((face,height),None) 
        if not font is None:
            return font

        font = sf.Font()
        if not font.LoadFromFile(face,height) is True:
            print("Failure creating font "+(face,height))
            # XXX substitute default font?

        FontCache.cached[(face,height)] = font
        return font

    

    
