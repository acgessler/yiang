#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [mathutil.py]
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


# XXX we need a dedicated vector class, actually. Currently I'm using
# 2d tuples or lists to pass them around, but the lack of overloaded
# operators is disturbing.

def Length(vec):
    """Return the length of a 2D vector """
    return (vec[0]*vec[0]+vec[1]*vec[1])**0.5


def Normalize(vec):
    """Return a normalized copy of a 2D vector"""
    len = Length(vec)
    assert len

    return (vec[0]/len,vec[1]/len)


def PointToBoxSqrEst(point,xywh):
    """Find a quick estimate for the squared distance from a given 
    point to an axis-aligned box, given as xywh tuple"""
    x = max( abs(point[0]-xywh[0]),abs(point[0]-xywh[0]-xywh[2]) )
    y = max( abs(point[1]-xywh[1]),abs(point[1]-xywh[1]-xywh[3]) )
    return x**2+y**2


def PointToBoxEst(point,xywh):
    """Find a quick estimate for the distance from a given 
    point to an axis-aligned box, given as xywh tuple"""
    return PointToBoxSqrEst(point,xywh)**0.5


def DoLineSegmentIntersection(b,a,c,d):
    """Check if the two line segments a-b and c-d collide,
    return the point of intersection or None.
    Each of the parameters is a 2-tuple (x,y)."""
    e = b[0]-a[0],b[1]-a[1]
    f = d[0]-c[0],d[1]-c[1]

    dd = -f[0] * e[1] + e[0] * f[1] 
    if dd<1e-5: # parallel lines
        return None 
    
    s = (-e[1] * (a[0] - c[0]) + e[0] * (a[1] - c[1])) / dd
    t = ( f[0] * (a[1] - c[1]) - f[1] * (a[0] - c[0])) / dd
    
    return (a[0]+t*e[0],a[1]+t*e[1]) if (0.0 <= s <= 1.0) and (0.0 <= t <= 1.0) else None

# Collision constants for the various Collide....WithRectangle functions()
COLLIDE_NONE, COLLIDE_LEFT,COLLIDE_RIGHT,COLLIDE_UPPER,COLLIDE_LOWER = 0x0,0x1,0x2,0x4,0x8
    
def CollideLineSegmentWithRectangle(line, rectangle):
    """Check if a rectangle (x1,y1,x2,y2) and a line segment
    (x1,y1,x2,y2) collide. Return a 2-tuple: (COLLIDE_XXX,
    pos) where the first item is one of the COLLIDE_XXX
    constants ORed together. The second item is only valid
    if the collision type is not COLLIDE_NONE. It is the
    location of the intersection as 2-tuple."""
    offsets = ((COLLIDE_LEFT, 0, 1, 0, 3),
        (COLLIDE_RIGHT, 2, 1, 2, 3),
        (COLLIDE_UPPER, 0, 1, 2, 1),
        (COLLIDE_LOWER, 0, 3, 2, 3))
        
    for type, x0, y0, x1, y1 in offsets:
        pos = DoLineSegmentIntersection((line[0], line[1]), (line[2], line[3]), (rectangle[x0], rectangle[y0]), (rectangle[x1], rectangle[y1]))
        if not pos is None:
            return (type, pos)
            
    return (Entity.COLLIDE_NONE, None)
    
    
def CollideMovingRectangleWithRectangle(origin, vec, rectangle, myrect):
    """Check if a rectangle (x1,y1,x2,y2) and our rect (myrect)
    (x1,y1,x2,y2)'s movement vector vec collide. origin is 
    the movement origin of the rectangle, that is the old
    'position' of it. If no collision occurs, origin+vec
    would be the new position of the rectangle.
    Return a 2-tuple: (COLLIDE_XXX, pos) where the first item 
    is one of the COLLIDE_XXX constants ORed together. The 
    second item is only valid if the collision type is not 
    COLLIDE_NONE. It is the location of the intersection 
    as 2-tuple."""
    offsets = ((COLLIDE_LEFT, 0, 1, 0, 3),
        (COLLIDE_RIGHT, 2, 1, 2, 3),
        (COLLIDE_UPPER, 0, 1, 2, 1),
        (COLLIDE_LOWER, 0, 3, 2, 3))
    
    # XXX CLEAN UP!!!
        
    # first collide our movement vector with this rectangle itself
    # to find our frontier point. This point serves along with the
    # movement vector as origin for the actual collision check.
    
    o = (myrect[2]+myrect[0])/2,(myrect[3]+myrect[1])/2
    for type, x0, y0, x1, y1 in offsets:
        #print(o,(myrect[x0], myrect[y0]), (myrect[x1], myrect[y1]))
        pos = DoLineSegmentIntersection(o, (o[0]+vec[0]*100000,o[1]+vec[1]*100000), (myrect[x0], myrect[y0]), (myrect[x1], myrect[y1]))
        if not pos is None:
            break
    else:
        assert False
        return (COLLIDE_NONE, None)
        
    npos = pos[0]+vec[0],pos[1]+vec[1]
        
    for skip_type, x0, y0, x1, y1 in offsets:
        rpos = DoLineSegmentIntersection(pos, npos, (rectangle[x0], rectangle[y0]), (rectangle[x1], rectangle[y1]))
        if not rpos is None:
            #print(pos,rpos,npos)
            return (type, (origin[0] + rpos[0] - pos[0], origin[1] + rpos[1] - pos[1]))
            
    return (COLLIDE_NONE, None)
    
    
    

# vim: ai ts=4 sts=4 et sw=4