// Modified version of sf.String using our VBO-based rendering logic.
// Dropped any overhead that YIANG does not need. Lots of obsolete
// SFML comments are still there, just ignore them.

////////////////////////////////////////////////////////////
//
// SFML - Simple and Fast Multimedia Library
// Copyright (C) 2007-2009 Laurent Gomila (laurent.gom@gmail.com)
//
// This software is provided 'as-is', without any express or implied warranty.
// In no event will the authors be held liable for any damages arising from the use of this software.
//
// Permission is granted to anyone to use this software for any purpose,
// including commercial applications, and to alter it and redistribute it freely,
// subject to the following restrictions:
//
// 1. The origin of this software must not be misrepresented;
//    you must not claim that you wrote the original software.
//    If you use this software in a product, an acknowledgment
//    in the product documentation would be appreciated but is not required.
//
// 2. Altered source versions must be plainly marked as such,
//    and must not be misrepresented as being the original software.
//
// 3. This notice may not be removed or altered from any source distribution.
//
////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////
// Headers
////////////////////////////////////////////////////////////


// Use GLXW because it loads the core profile correctly (including
// the VAO functions, which GLEW refuses to properly load even
// with glewExperimental=true).
//
// Since we (and SFML) also still need deprecated functions (i.e. immediate
// mode, ffp), some hacks are necessary to properly make Gl available.

#include "CustomString.hpp"
#include <SFML/Graphics/Image.hpp>

// *Not* include this - it brings in GLEW
//#include <SFML/Graphics/GraphicsContext.hpp>


// This includes GLXW (GL Core)
#include "VBOManager.hpp"

// Manually re-declare legacy APIs. Including GL.h does not work,
// it would clash with GL Core macros
extern "C" {

WINGDIAPI void APIENTRY glTexCoordPointer (GLint size, GLenum type, GLsizei stride, const GLvoid *pointer);
WINGDIAPI void APIENTRY glVertexPointer (GLint size, GLenum type, GLsizei stride, const GLvoid *pointer);
WINGDIAPI void APIENTRY glColorPointer (GLint size, GLenum type, GLsizei stride, const GLvoid *pointer);
WINGDIAPI void APIENTRY glDisableClientState (GLenum array);
WINGDIAPI void APIENTRY glEnableClientState (GLenum array);
WINGDIAPI void APIENTRY glScalef (GLfloat x, GLfloat y, GLfloat z);
WINGDIAPI void APIENTRY glBegin (GLenum mode);
WINGDIAPI void APIENTRY glTexCoord2f (GLfloat s, GLfloat t);
WINGDIAPI void APIENTRY glVertex2f (GLfloat x, GLfloat y);
WINGDIAPI void APIENTRY glEnd (void);

}

#define GL_VERTEX_ARRAY                   0x8074
#define GL_TEXTURE_COORD_ARRAY            0x8078
#define GL_COLOR_ARRAY                    0x8076

#include <assert.h>
#include <locale>
#include <limits>
#include <iostream>

namespace {

	// Global VBO cache instance used to cache the vertices for
	// drawing text tiles.
VBOManager g_vboManager;
	
}

namespace sf_yiang
{
////////////////////////////////////////////////////////////
/// Default constructor
////////////////////////////////////////////////////////////
CustomString::CustomString() :
myFont          (&Font::GetDefaultFont()),
mySize          (30.f),
myStyle         (Regular),
myNeedRectUpdate(true),
use_immediate_mode_rendering()
{

}


////////////////////////////////////////////////////////////
/// Construct the string from any kind of text
////////////////////////////////////////////////////////////
CustomString::CustomString(const Unicode::Text& Text, const Font& CharFont, float Size) :
myFont          (&CharFont),
mySize          (Size),
myStyle         (Regular),
myNeedRectUpdate(true)
{
    SetText(Text);
}


////////////////////////////////////////////////////////////
/// Set the text (from any kind of string)
////////////////////////////////////////////////////////////
void CustomString::SetText(const Unicode::Text& Text)
{
    myNeedRectUpdate = true;
    myText = Text;
}


////////////////////////////////////////////////////////////
/// Set the font of the string
////////////////////////////////////////////////////////////
void CustomString::SetFont(const Font& CharFont)
{
    if (myFont != &CharFont)
    {
        myNeedRectUpdate = true;
        myFont = &CharFont;
    }
}


////////////////////////////////////////////////////////////
/// Set the size of the string
////////////////////////////////////////////////////////////
void CustomString::SetSize(float Size)
{
    if (mySize != Size)
    {
        myNeedRectUpdate = true;
        mySize = Size;
    }
}


////////////////////////////////////////////////////////////
/// Set the style of the text
/// The default style is Regular
////////////////////////////////////////////////////////////
void CustomString::SetStyle(unsigned long TextStyle)
{
    if (myStyle != TextStyle)
    {
        myNeedRectUpdate = true;
        myStyle = TextStyle;
    }

//	assert(myStyle & );
}


////////////////////////////////////////////////////////////
/// Get the text (the returned text can be converted implicitely to any kind of string)
////////////////////////////////////////////////////////////
const Unicode::Text& CustomString::GetText() const
{
    return myText;
}


////////////////////////////////////////////////////////////
/// Get the font used by the string
////////////////////////////////////////////////////////////
const Font& CustomString::GetFont() const
{
    return *myFont;
}


////////////////////////////////////////////////////////////
/// Get the size of the characters
////////////////////////////////////////////////////////////
float CustomString::GetSize() const
{
    return mySize;
}


////////////////////////////////////////////////////////////
/// Get the style of the text
////////////////////////////////////////////////////////////
unsigned long CustomString::GetStyle() const
{
    return myStyle;
}


////////////////////////////////////////////////////////////
/// Return the visual position of the Index-th character of the string,
/// in coordinates relative to the string
/// (note : translation, center, rotation and scale are not applied)
////////////////////////////////////////////////////////////
sf::Vector2f CustomString::GetCharacterPos(std::size_t Index) const
{
    // First get the UTF32 representation of the text
    const Unicode::UTF32String& Text = myText;

    // Adjust the index if it's out of range
    if (Index > Text.length())
        Index = Text.length();

    // The final size is based on the text size
    float FactorX  = mySize / myFont->GetCharacterSize();
    float AdvanceY = mySize;

    // Compute the position
    sf::Vector2f Position;
    for (std::size_t i = 0; i < Index; ++i)
    {
        // Get the current character and its corresponding glyph
        Uint32       CurChar  = Text[i];
        const Glyph& CurGlyph = myFont->GetGlyph(CurChar);
        float        AdvanceX = CurGlyph.Advance * FactorX;

        switch (CurChar)
        {
            // Handle special characters
            case L' ' :  Position.x += AdvanceX;                 break;
            case L'\t' : Position.x += AdvanceX * 4;             break;
            case L'\v' : Position.y += AdvanceY * 4;             break;
            case L'\n' : Position.y += AdvanceY; Position.x = 0; break;

            // Regular character : just add its advance value
            default : Position.x += AdvanceX; break;
        }
    }

    return Position;
}


////////////////////////////////////////////////////////////
/// Get the string rectangle on screen
////////////////////////////////////////////////////////////
FloatRect CustomString::GetRect() const
{
    if (myNeedRectUpdate)
        const_cast<CustomString*>(this)->RecomputeRect();

    FloatRect Rect;
    Rect.Left   = (myBaseRect.Left   - GetCenter().x) * GetScale().x + GetPosition().x;
    Rect.Top    = (myBaseRect.Top    - GetCenter().y) * GetScale().y + GetPosition().y;
    Rect.Right  = (myBaseRect.Right  - GetCenter().x) * GetScale().x + GetPosition().x;
    Rect.Bottom = (myBaseRect.Bottom - GetCenter().y) * GetScale().y + GetPosition().y;

    return Rect;
}

void BindZeroVAO() {
	static GLuint vao = 0;
	if (vao == 0) {
		glGenVertexArrays(1, &vao);
		glBindVertexArray(vao);

		// Restore GL state for SFML to resume
		glBindBuffer(GL_ARRAY_BUFFER, 0);
		glDisableClientState(GL_COLOR_ARRAY);
		glDisableClientState(GL_TEXTURE_COORD_ARRAY);
		glDisableClientState(GL_VERTEX_ARRAY);
		return;
	}
	glBindVertexArray(vao);
}


////////////////////////////////////////////////////////////
/// /see sfDrawable::Render
////////////////////////////////////////////////////////////
void CustomString::Render(RenderTarget&) const
{
	EnsureGlxwInit();

	// This is modified from the original String::Render() code from
	// SFML. It uses the VBO cache to retrieve cached VBOs and to
	// (re-)populate them as needed.
    const Unicode::UTF32String& Text = myText;
	if (Text.empty()) {
        return;
	}

    // Set the scaling factor to get the actual size
    float CharSize =  static_cast<float>(myFont->GetCharacterSize());
    float Factor   = mySize / CharSize;
	glScalef(Factor, Factor, 1.f);

    // Bind the font texture
    myFont->GetImage().Bind();

    // Initialize the rendering coordinates
    float X = 0.f;
    float Y = CharSize;

	std::string copy_text;
	copy_text.resize(Text.size());
	for (size_t i = 0, e = Text.size(); i < e; ++i) {
		copy_text[i] = static_cast<char>(Text[i]);
	}

	// Extract a 32bit RGBA color
	union {
		Uint32 color;
		char color_channels[4];
	};
	const sf::Color& float_color = GetColor();
	color_channels[0] = float_color.r;
	color_channels[1] = float_color.g;
	color_channels[2] = float_color.b;
	color_channels[3] = float_color.a;

	// Derive an unique key by adding the color at the end
	// of the string. This is a terrible hack, so avoiding
	// unintended null-termination by ORing a 1 does
	// not make it worse.
	std::string key = copy_text;
	key.push_back(float_color.r | 1);
	key.push_back(float_color.g | 1);
	key.push_back(float_color.b | 1);
	key.push_back(float_color.a | 1);

	VBOTile* const tile = use_immediate_mode_rendering ? NULL :
		g_vboManager.Get(key, g_vboManager.GetVBOSizeForString(copy_text));
	if (tile == NULL || tile->vbo == 0) {
		// Draw one quad for each character
		glBegin(GL_QUADS);
		for (std::size_t i = 0, e = Text.size(); i < e; ++i)
		{
			// Get the current character and its corresponding glyph
			Uint32           CurChar  = Text[i];
			const Glyph&     CurGlyph = myFont->GetGlyph(CurChar);
			int              Advance  = CurGlyph.Advance;
			const IntRect&   Rect     = CurGlyph.Rectangle;
			const FloatRect& Coord    = CurGlyph.TexCoords;

			// Handle special characters
			switch (CurChar)
			{
				case L' ' :  X += Advance;         continue;
				case L'\n' : Y += CharSize; X = 0; continue;
				// Note: The original SFML code handles those as well:
				//case L'\t' : X += Advance  * 4;    continue;
				//case L'\v' : Y += CharSize * 4;    continue;
			}

			// Draw a textured quad for the current character
			glTexCoord2f(Coord.Left,  Coord.Top);    glVertex2f(X + Rect.Left,    Y + Rect.Top);
			glTexCoord2f(Coord.Left,  Coord.Bottom); glVertex2f(X + Rect.Left,    Y + Rect.Bottom);
			glTexCoord2f(Coord.Right, Coord.Bottom); glVertex2f(X + Rect.Right,   Y + Rect.Bottom);
			glTexCoord2f(Coord.Right, Coord.Top);    glVertex2f(X + Rect.Right,   Y + Rect.Top);

			// Advance to the next character
			X += Advance;
		}
		glEnd();
		return;
	}
	
	assert(tile->vbo != NULL);
	
	if (tile->dirty) {
		// Record a new VAO
		if( tile->vao != 0) {
			glDeleteVertexArrays(1, &tile->vao);
		}
		glGenVertexArrays(1, &tile->vao);
		glBindVertexArray(tile->vao);

		glBindBuffer(GL_ARRAY_BUFFER, tile->vbo);
		float* const data = static_cast<float*>(glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY));
		if (data == NULL) {
			// Retry next time, leave |dirty==true|
			std::cerr << "(likely not logged) glMapBuffer() failed" << std::endl;
			return;
		}

		tile->quad_count = 0;
		float* cursor = data;

		// Copy-paste logic from above to have it be efficient.
		// Copy data to the VBO instead of emitting immediate mode calls.
		for (std::size_t i = 0, e = Text.size(); i < e; ++i)
		{
			Uint32           CurChar  = Text[i];
			const Glyph&     CurGlyph = myFont->GetGlyph(CurChar);
			int              Advance  = CurGlyph.Advance;
			const IntRect&   Rect     = CurGlyph.Rectangle;
			const FloatRect& Coord    = CurGlyph.TexCoords;

			// Handle special characters
			switch (CurChar)
			{
			case L' ' :  X += Advance;         continue;
			case L'\n' : Y += CharSize; X = 0; continue;
			// Note: The original SFML code handles those as well:
			//case L'\t' : X += Advance  * 4;    continue;
			//case L'\v' : Y += CharSize * 4;    continue;
			}

			// Draw a textured quad for the current character

			// glTexCoord2f(Coord.Left,  Coord.Top);    glVertex2f(X + Rect.Left,    Y + Rect.Top);
			*cursor++ = Coord.Left;
			*cursor++ = Coord.Top;
			*cursor++ = X + Rect.Left;
			*cursor++ = Y + Rect.Top;
			*cursor++ = *reinterpret_cast<float*>(&color);

			// glTexCoord2f(Coord.Left,  Coord.Bottom); glVertex2f(X + Rect.Left,    Y + Rect.Bottom);
			*cursor++ = Coord.Left;
			*cursor++ = Coord.Bottom;
			*cursor++ = X + Rect.Left;
			*cursor++ = Y + Rect.Bottom;
			*cursor++ = *reinterpret_cast<float*>(&color);

			// glTexCoord2f(Coord.Right, Coord.Bottom); glVertex2f(X + Rect.Right,   Y + Rect.Bottom);
			*cursor++ = Coord.Right;
			*cursor++ = Coord.Bottom;
			*cursor++ = X + Rect.Right;
			*cursor++ = Y + Rect.Bottom;
			*cursor++ = *reinterpret_cast<float*>(&color);

			// glTexCoord2f(Coord.Right, Coord.Top);    glVertex2f(X + Rect.Right,   Y + Rect.Top);
			*cursor++ = Coord.Right;
			*cursor++ = Coord.Top;
			*cursor++ = X + Rect.Right;
			*cursor++ = Y + Rect.Top;
			*cursor++ = *reinterpret_cast<float*>(&color);

			// Advance to the next character
			X += Advance;
			++tile->quad_count;
		}

		assert (std::distance(data, cursor) <= tile->size);
		glUnmapBuffer(GL_ARRAY_BUFFER);

		// Drop the dirty flag from the tile
		tile->dirty = false;

		// Use legacy APIs because T&L is still done using fixed-function
		// pipeline. Using vertexAttrib* would not supply the semantics
		// of each stream.
		glEnableClientState(GL_COLOR_ARRAY);
		glEnableClientState(GL_TEXTURE_COORD_ARRAY);
		glEnableClientState(GL_VERTEX_ARRAY);

		const int VERTEX_SIZE = 5 * 4;
		glTexCoordPointer(2, GL_FLOAT, VERTEX_SIZE, reinterpret_cast<void*>(0));
		glVertexPointer(2, GL_FLOAT, VERTEX_SIZE, reinterpret_cast<void*>(8));
		glColorPointer(4, GL_UNSIGNED_BYTE, VERTEX_SIZE, reinterpret_cast<void*>(16));
	}
	else {
		glBindVertexArray(tile->vao);
	}
	
	glDrawArrays(GL_QUADS, 0, tile->quad_count * 4);

	// Restore GL state for SFML to resume
	BindZeroVAO();
}


////////////////////////////////////////////////////////////
/// Recompute the bounding rectangle of the text
////////////////////////////////////////////////////////////
void CustomString::RecomputeRect()
{
    // First get the internal UTF-32 string of the text
    const Unicode::UTF32String& Text = myText;

    // Reset the "need update" state
    myNeedRectUpdate = false;

    // No text, empty box :)
    if (Text.empty())
    {
        myBaseRect = FloatRect(0, 0, 0, 0);
        return;
    }

    // Initial values
    float CurWidth  = 0;
    float CurHeight = 0;
    float Width     = 0;
    float Height    = 0;
    float Factor    = mySize / myFont->GetCharacterSize();

    // Go through each character
    for (std::size_t i = 0; i < Text.size(); ++i)
    {
        // Get the current character and its corresponding glyph
        Uint32         CurChar  = Text[i];
        const Glyph&   CurGlyph = myFont->GetGlyph(CurChar);
        float          Advance  = CurGlyph.Advance * Factor;
        const IntRect& Rect     = CurGlyph.Rectangle;

        // Handle special characters
        switch (CurChar)
        {
            case L' ' :  CurWidth += Advance;                    continue;
            case L'\t' : CurWidth += Advance * 4;                continue;
            case L'\v' : Height   += mySize  * 4; CurHeight = 0; continue;

            case L'\n' :
                Height += mySize;
                CurHeight = 0;
                if (CurWidth > Width)
                    Width = CurWidth;
                CurWidth = 0;
                continue;
        }

        // Advance to the next character
        CurWidth += Advance;

        // Update the maximum height
        float CharHeight = (myFont->GetCharacterSize() + Rect.Bottom) * Factor;
        if (CharHeight > CurHeight)
            CurHeight = CharHeight;
    }

    // Update the last line
    if (CurWidth > Width)
        Width = CurWidth;
    Height += CurHeight;


    // Finally update the rectangle
    myBaseRect.Left   = 0;
    myBaseRect.Top    = 0;
    myBaseRect.Right  = Width;
    myBaseRect.Bottom = Height;
}

} // namespace sf
