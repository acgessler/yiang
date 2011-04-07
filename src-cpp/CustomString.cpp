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
#include "CustomString.hpp"
#include <SFML/Graphics/Image.hpp>
#include <SFML/Graphics/GraphicsContext.hpp>
#include <locale>
#include <assert.h>

namespace sf_yiang
{
////////////////////////////////////////////////////////////
/// Default constructor
////////////////////////////////////////////////////////////
CustomString::CustomString() :
myFont          (&Font::GetDefaultFont()),
mySize          (30.f),
myStyle         (Regular),
myNeedRectUpdate(true)
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

	assert(myStyle & );
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


////////////////////////////////////////////////////////////
/// /see sfDrawable::Render
////////////////////////////////////////////////////////////
void CustomString::Render(RenderTarget&) const
{
    // First get the internal UTF-32 string of the text
    const Unicode::UTF32String& Text = myText;

    // No text, no rendering :)
    if (Text.empty())
        return;

    // Set the scaling factor to get the actual size
    float CharSize =  static_cast<float>(myFont->GetCharacterSize());
    float Factor   = mySize / CharSize;
    GLCheck(glScalef(Factor, Factor, 1.f));

    // Bind the font texture
    myFont->GetImage().Bind();

    // Initialize the rendering coordinates
    float X = 0.f;
    float Y = CharSize;


    // Draw one quad for each character
    glBegin(GL_QUADS);
    for (std::size_t i = 0; i < Text.size(); ++i)
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
            case L'\t' : X += Advance  * 4;    continue;
            case L'\v' : Y += CharSize * 4;    continue;
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
