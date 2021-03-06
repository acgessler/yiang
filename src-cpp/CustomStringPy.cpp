////////////////////////////////////////////////////////////
//
// PySFML - Python binding for SFML (Simple and Fast Multimedia Library)
// Copyright (C) 2007, 2008 Rémi Koenig (remi.k2620@gmail.com)
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

#include "CustomStringPy.hpp"
#include "../contrib/SFML-1.6/python/src/Font.hpp"
#include "../contrib/SFML-1.6/python/src/Color.hpp"
#include "../contrib/SFML-1.6/python/src/Rect.hpp"

#include "../contrib/SFML-1.6/python/src/compat.hpp"


extern PyTypeObject PySfDrawableType;
extern PyTypeObject PySfFontType;


static void
PySfCustomString_dealloc(PySfCustomString *self)
{
	Py_CLEAR(self->font);
	delete self->obj;
	free_object(self);
}

static PyObject *
PySfCustomString_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PySfCustomString *self;
	self = (PySfCustomString *)type->tp_alloc(type, 0);
	if (self != NULL)
	{
		self->font = NULL;
		self->IsCustom = false;
		self->obj = new sf_yiang::CustomString();
	}
	return (PyObject *)self;
}

static PyObject *
PySfCustomString_SetText(PySfCustomString* self, PyObject *args)
{
	char *Text, *EncodingStr=NULL;
	int Length;
	std::string Encoding;
	if (PyArg_ParseTuple(args, "u:String.SetText", &Text))
	{
#if Py_UNICODE_SIZE == 4
		self->obj->SetText((sf::Uint32 *)Text);
#else
		self->obj->SetText((sf::Uint16 *)Text);
#endif
	}
	else if (PyArg_ParseTuple(args, "s|#s:String.SetText", &Text, &Length, &EncodingStr))
	{
		PyErr_Clear();
		if (EncodingStr == NULL)
			self->obj->SetText(sf::Unicode::UTF8String((sf::Uint8 *)Text));
		else
		{
			Encoding.assign(EncodingStr);
			if (Encoding == "utf8")
				self->obj->SetText(sf::Unicode::UTF8String((sf::Uint8 *)Text));
			else if (Encoding == "utf16")
				self->obj->SetText(sf::Unicode::UTF16String((sf::Uint16 *)(Text+2)));
			else if (Encoding == "utf32")
				self->obj->SetText(sf::Unicode::UTF32String((sf::Uint32 *)(Text+4)));
			else
			{
				PyErr_Format(PyExc_TypeError, "String.SetText() Encoding %s not supported", EncodingStr);
				return NULL;
			}
		}
	}
	else
	{
		PyErr_BadArgument();
		return NULL;
	}
	Py_RETURN_NONE;
}

static PyObject *
PySfCustomString_SetFont(PySfCustomString* self, PyObject *args)
{
	PySfFont *Font = (PySfFont *)args;
	if (!PyObject_TypeCheck(Font, &PySfFontType))
	{
		PyErr_SetString(PyExc_ValueError, "String.SetFont() Argument must be a sf.Font");
		return NULL;
	}
	Py_CLEAR(self->font);
	Py_INCREF(args);
	self->font = Font;
	self->obj->SetFont(*(Font->obj));
	Py_RETURN_NONE;
}

static PyObject *
PySfCustomString_SetSize(PySfCustomString* self, PyObject *args)
{
	self->obj->SetSize(PyFloat_AsDouble(args));
	Py_RETURN_NONE;
}

static PyObject *
PySfCustomString_SetImmediateModeRendering(PySfCustomString* self, PyObject *args)
{
	self->obj->SetImmediateModeRendering(PyBool_AsBool(args));
	Py_RETURN_NONE;
}

static PyObject *
PySfCustomString_SetOptimizedRenderingPrior(PySfCustomString* self, PyObject *args)
{
	self->obj->SetOptimizedRenderingPrior(PyBool_AsBool(args));
	Py_RETURN_NONE;
}

static PyObject *
PySfCustomString_SetOptimizedRenderingPosterior(PySfCustomString* self, PyObject *args)
{
	self->obj->SetOptimizedRenderingPosterior(PyBool_AsBool(args));
	Py_RETURN_NONE;
}

static PyObject *
PySfCustomString_GetSize(PySfCustomString* self)
{
	return PyFloat_FromDouble(self->obj->GetSize());
}

static PyObject *
PySfCustomString_SetStyle(PySfCustomString* self, PyObject *args)
{
	self->obj->SetStyle(PyLong_AsUnsignedLong(args));
	Py_RETURN_NONE;
}

static PyObject *
PySfCustomString_GetStyle(PySfCustomString* self)
{
	return PyLong_FromUnsignedLong(self->obj->GetStyle());
}

static PyObject *
PySfCustomString_GetText(PySfCustomString* self)
{
#if Py_UNICODE_SIZE == 4
	sf::Unicode::UTF32String Text(self->obj->GetText());
#else
	sf::Unicode::UTF16String Text(self->obj->GetText());
#endif
	return PyUnicode_FromUnicode((const Py_UNICODE*)Text.c_str(), Text.length());
}

static PyObject *
PySfCustomString_GetFont(PySfCustomString* self)
{
	if (self->font == NULL)
	{
		PySfFont *Font = GetNewPySfFont();
		Font->obj = (sf::Font *)&(sf::Font::GetDefaultFont());
		Font->Owner = false;
		return (PyObject *)Font;
	}
	else
	{
		Py_INCREF(self->font);
		return (PyObject *)(self->font);
	}
}

static PyObject *
PySfCustomString_GetRect(PySfCustomString* self)
{
	PySfFloatRect *Rect;

	Rect = GetNewPySfFloatRect();
	Rect->Owner = true;
	Rect->obj = new sf::FloatRect (self->obj->GetRect());
	PySfFloatRectUpdateSelf(Rect);

	return (PyObject *)Rect;
}

static PyObject *
PySfCustomString_GetCharacterPos(PySfCustomString* self, PyObject *args)
{
	sf::Vector2f Pos = self->obj->GetCharacterPos(PyLong_AsUnsignedLong(args));
	return Py_BuildValue("ff", Pos.x, Pos.y);
}

static int
PySfCustomString_init(PySfCustomString *self, PyObject *args, PyObject *kwds)
{
	const char *kwlist[] = {"Text", "Font", "Size", NULL};
	float Size = 30.f;
	PyObject *Text=NULL;
	PySfFont *Font = NULL;
	if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO!f:String.__new__", (char **)kwlist, &Text, &PySfFontType, &Font, &Size))
		return -1;

	if (Text != NULL)
	{
		if (PyUnicode_Check(Text))
		{
#if Py_UNICODE_SIZE == 4
			self->obj->SetText((sf::Uint32 *)PyUnicode_AS_UNICODE(Text));
#else
			self->obj->SetText((sf::Uint16 *)PyUnicode_AS_UNICODE(Text));
#endif
		}
#ifdef IS_PY3K
		else if (PyBytes_Check(Text))
			self->obj->SetText(sf::Unicode::UTF8String((sf::Uint8 *)PyBytes_AsString(Text)));
#else
		else if (PyString_Check(Text))
			self->obj->SetText(sf::Unicode::UTF8String((sf::Uint8 *)PyString_AsString(Text)));
#endif
		else
		{
			PyErr_SetString(PyExc_TypeError, "String.__init__() first argument must be str");
			return -1;
		}
	}
	if (Font) PySfCustomString_SetFont(self, (PyObject *)Font);
	self->obj->SetSize(Size);
	return 0;
}


static PyMethodDef PySfCustomString_methods[] = {
	{"GetCharacterPos", (PyCFunction)PySfCustomString_GetCharacterPos, METH_O, "GetCharacterPos(Index)\n\
Return the visual position (a tuple of two floats) of the Index-th character of the string, in coordinates relative to the string (note : translation, center, rotation and scale are not applied)\n\
	Index : Index of the character"},
	{"SetText", (PyCFunction)PySfCustomString_SetText, METH_VARARGS, "SetText(UnicodeText) or SetText(Text, Encoding='utf8')\nSet the text. Valid encodings are 'utf8', 'utf16' and 'utf32'.\n	Text : New text"},
	{"GetText", (PyCFunction)PySfCustomString_GetText, METH_NOARGS, "GetText()\nGet the text as an unicode string."},
	{"SetFont", (PyCFunction)PySfCustomString_SetFont, METH_O, "SetFont(Font)\nSet the font of the string.\n	Font : font to use"},
	{"GetFont", (PyCFunction)PySfCustomString_GetFont, METH_NOARGS, "GetFont()\nGet the font used by the string."},
	{"SetSize", (PyCFunction)PySfCustomString_SetSize, METH_O, "SetSize(Size)\nSet the size of the string.\n	Size : New size, in pixels"},
	{"GetSize", (PyCFunction)PySfCustomString_GetSize, METH_NOARGS, "GetSize()\nGet the size of the characters."},
	{"SetStyle", (PyCFunction)PySfCustomString_SetStyle, METH_O, "SetStyle(TextSize)\nSet the style of the text. The default style is Regular.\n	TextSize : New text style, (combination of Style values)"},
	{"GetStyle", (PyCFunction)PySfCustomString_GetStyle, METH_NOARGS, "GetStyle()\nGet the style of the text."},
	{"GetRect", (PyCFunction)PySfCustomString_GetRect, METH_NOARGS, "GetRect()\nGet the string rectangle on screen."},
	{"SetImmediateModeRendering", (PyCFunction)PySfCustomString_SetImmediateModeRendering, METH_O, "Enable/disable immediate mode fallback"},
	{"SetOptimizedRenderingPrior", (PyCFunction)PySfCustomString_SetOptimizedRenderingPrior, METH_O, "Enable/disable optimized batch rendering"},
	{"SetOptimizedRenderingPosterior", (PyCFunction)PySfCustomString_SetOptimizedRenderingPosterior, METH_O, "Enable/disable optimized batch rendering"},
	{NULL}  /* Sentinel */
};

PyTypeObject PySfCustomStringType = {
	head_init
	"CustomString",				/*tp_name*/
	sizeof(PySfCustomString),		/*tp_basicsize*/
	0,						/*tp_itemsize*/
	(destructor)PySfCustomString_dealloc, /*tp_dealloc*/
	0,						/*tp_print*/
	0,						/*tp_getattr*/
	0,						/*tp_setattr*/
	0,						/*tp_compare*/
	0,						/*tp_repr*/
	0,						/*tp_as_number*/
	0,						/*tp_as_sequence*/
	0,						/*tp_as_mapping*/
	0,						/*tp_hash */
	0,						/*tp_call*/
	0,						/*tp_str*/
	0,						/*tp_getattro*/
	0,						/*tp_setattro*/
	0,						/*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
	"sf.String defines a graphical 2D text, that can be drawn on screen.\n\
Default constructor : String ()\nConstruct the string from an unicode or an ascii string : String(Text, Font=sf.Font.GetDefaultFont(), Size=30.)\n	Text : Text assigned to the string\n	Font : Font used to draw the string (SFML built-in font by default)\n	Size : Characters size (30 by default)", /* tp_doc */
	0,						/* tp_traverse */
	0,						/* tp_clear */
	0,						/* tp_richcompare */
	0,						/* tp_weaklistoffset */
	0,						/* tp_iter */
	0,						/* tp_iternext */
	PySfCustomString_methods,		/* tp_methods */
	0,						/* tp_members */
	0,						/* tp_getset */
	&PySfDrawableType,		/* tp_base */
	0,						/* tp_dict */
	0,						/* tp_descr_get */
	0,						/* tp_descr_set */
	0,						/* tp_dictoffset */
	(initproc)PySfCustomString_init, /* tp_init */
	0,						/* tp_alloc */
	PySfCustomString_new,			/* tp_new */
};



void PySfCustomString_InitConst()
{

}

