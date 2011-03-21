///////////////////////////////////////////////////////////////////////////////////
// Yet Another Jump'n'Run Game
// (c) 2010 Alexander Christoph Gessler
//
// HIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
// ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
///////////////////////////////////////////////////////////////////////////////////


// Implements a Python import hook to fetch files from the resource
// section of the module (Windows only). This is a stripped version
// of the import hook of my 3D engine, which is itself basing on
// Python's zip import hook. It handles source code files (py) as well,
// while this code works only for precompiled pyc's.

#ifndef _MSC_VER
#	error Windows & MSVC only
#endif

// #define VERBOSE

// standard headers
#define _CRT_SECURE_NO_WARNINGS

#include <assert.h>
#include <stdlib.h>

// Python headers
#include <Python.h>

#include <structmember.h>
#include <osdefs.h>
#include <marshal.h>

#include "ResourceFetcher.h"

#define IS_PACKAGE  0x2

#define MAX_MODULE_NAME 256
#define qf_MAX_PATH 256 // arbitrary choice, doesn't matter too much

namespace {
struct st_qf_searchorder {
	wchar_t suffix[14];
	int type;
};

struct st_qf_prefixorder {
	wchar_t prefix[32];
};

// --------------------------------------------------------------------------------------------
/* qf_searchorder defines how we search for a module */
// --------------------------------------------------------------------------------------------
static st_qf_searchorder qf_searchorder[] = {
	{L"\\__init__.pyc", IS_PACKAGE},
	{L".pyc", 0},
	{L"", 0}
};

// --------------------------------------------------------------------------------------------
/* mgl_prefixorder defines path prefixes to search for modules */
// --------------------------------------------------------------------------------------------
static st_qf_prefixorder qf_prefixorder[] = {
	{L""}, 
//	{L"../src-py/"}, 
};

/* qfimporter object definition and support */
struct qfImporter {
	PyObject_HEAD
};

static PyObject *qfImportError;
}

/* forward decls */
static PyObject *get_module_code(qfImporter *self, wchar_t *fullname,bool *p_ispackage, wchar_t *p_modpath);
static PyObject *get_data(unsigned int rid);
#define qfImporter_Check(op) PyObject_TypeCheck(op, &qfImporter_Type)

// --------------------------------------------------------------------------------------------
/* qfimporter.__init__  */
// --------------------------------------------------------------------------------------------
static int qfimporter_init(qfImporter *self, PyObject *args, PyObject *kwds)
{	
	if (!_PyArg_NoKeywords("qfimporter()", kwds)) {
		return -1;
	}

	wchar_t* path;
	if (!PyArg_ParseTuple(args, "u:qfimporter", &path)) {
		return -1;
	}

	return 0;
}

// --------------------------------------------------------------------------------------------
/* GC support. */
// --------------------------------------------------------------------------------------------
int qfimporter_traverse(PyObject *obj, visitproc visit, void *arg)
{	
	return 0;
}

// --------------------------------------------------------------------------------------------
/* Python destructor. */
// --------------------------------------------------------------------------------------------
void qfimporter_dealloc(qfImporter *self)
{	
	PyObject_GC_UnTrack(self);
	Py_TYPE(self)->tp_free((PyObject *)self);
}

// --------------------------------------------------------------------------------------------
/* Python tostring(). */
// --------------------------------------------------------------------------------------------
PyObject * qfimporter_repr(qfImporter *self)
{	
	return PyUnicode_FromFormat("<qfimporter object \"%p\">",self);
}

// --------------------------------------------------------------------------------------------
/* Given a (sub)modulename, write the potential file path in the
   archive (without extension) to the path buffer. Return the
   length of the resulting string. */
// --------------------------------------------------------------------------------------------
int make_filename(wchar_t *name, wchar_t *path)
{	
	size_t len;
	wchar_t *p;

	/* self.prefix + name [+ SEP + "__init__"] + ".py[co]" */
	if (wcslen(name) + 13 >= qf_MAX_PATH) {
		PyErr_SetString(qfImportError, "path too long");
		return -1;
	}

	wcscpy(path, name);
	for (p = path; *p; p++) {
		if (*p == L'.')
			*p = SEP;
	}
	len = wcslen(name);
//	assert(len < INT_MAX);
	return (int)len;
}

enum zi_module_info {
	MI_ERROR,
	MI_NOT_FOUND,
	MI_MODULE,
	MI_PACKAGE
};

// --------------------------------------------------------------------------------------------
/* Return some information about a module. */
// --------------------------------------------------------------------------------------------
enum zi_module_info get_module_info(qfImporter *self, wchar_t *fullname, unsigned int* rid = NULL)
{	
	wchar_t path[qf_MAX_PATH + 1], tmp[qf_MAX_PATH + 1];
	int len;
	st_qf_searchorder *zso;
	st_qf_prefixorder *ma;

	len = make_filename(fullname, path);
	if (len < 0) {
		return MI_ERROR;
	}

	ma = qf_prefixorder; // for (ma = qf_prefixorder; *ma->prefix; ma++)
	{
		wcscpy(tmp,ma->prefix);
		size_t lenn = wcslen(ma->prefix);

		wcscpy(tmp+lenn,path);
		lenn += len;

		for (zso = qf_searchorder; *zso->suffix; zso++) {
	
			wcscpy(tmp + lenn, zso->suffix);
			unsigned int r = NameToId(tmp);

#ifdef VERBOSE
			printf("NameToID: %S is %i\n",tmp,r);
#endif

			if (r) {

				if (rid) {
					*rid  = r;
				}

#ifdef VERBOSE
	printf("get_module_info yields %s: %S\n",(zso->type & IS_PACKAGE 
		? "MI_PACKAGE" : "MI_MODULE"),fullname);
#endif
				return zso->type & IS_PACKAGE ? MI_PACKAGE : MI_MODULE;
			}
		}
	}

#ifdef VERBOSE
	printf("get_module_info yields MI_NOT_FOUND: %S\n",fullname);
#endif
	return MI_NOT_FOUND;
}

// --------------------------------------------------------------------------------------------
/* Check whether we can satisfy the import of the module named by
   'fullname'. Return self if we can, None if we can't. */
// --------------------------------------------------------------------------------------------
PyObject * qfimporter_find_module(PyObject *obj, PyObject *args)
{	
	qfImporter *self = (qfImporter *)obj;
	PyObject *path = NULL;
	wchar_t *fullname;
	zi_module_info mi;

	if (!PyArg_ParseTuple(args, "u|O:qfimporter.find_module",&fullname, &path)) {
		return NULL;
	}

#ifdef VERBOSE
	printf("find_module %S\n",fullname);
#endif

	mi = get_module_info(self, fullname);
	if (mi == MI_ERROR)
		return NULL;
	if (mi == MI_NOT_FOUND) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	Py_INCREF(self);
	return (PyObject *)self;
}

// --------------------------------------------------------------------------------------------
/* Load and return the module named by 'fullname'. */
// --------------------------------------------------------------------------------------------
PyObject *qfimporter_load_module(PyObject *obj, PyObject *args)
{	
	qfImporter *self = (qfImporter *)obj;
	PyObject *code, *mod, *dict, *fname;
	wchar_t fullname[MAX_MODULE_NAME], modpath[qf_MAX_PATH+1];
	bool ispackage;

	if (!PyArg_ParseTuple(args, "O:qfimporter.load_module",&fname)) {
		return NULL;
	}

	if (!PyUnicode_Check(fname)) {
		return NULL;
	}

	fullname[PyUnicode_AsWideChar(reinterpret_cast<PyUnicodeObject*>(fname),
		fullname,MAX_MODULE_NAME-1)
	] = 0;

#ifdef VERBOSE
	printf("load_module %S\n",fullname);
#endif

# if 0
	// check sys.modules
	PyObject* smod = PySys_GetObject("modules");
	if (!smod || !PyDict_Check(smod)) {
		return NULL;
	}
	PyObject *pob;
	if((pob=PyDict_GetItem(smod,fname))) {
		Py_INCREF(pob);
		return pob;
	}
#endif

	char ascii[qf_MAX_PATH+1];
	wcstombs (ascii,fullname, qf_MAX_PATH);

	code = get_module_code(self, fullname, &ispackage, modpath);
	if (code == NULL) {
		return NULL;
	}

	mod = PyImport_AddModule(ascii);
	if (mod == NULL) {
		Py_DECREF(code);
		return NULL;
	}
# if 0
	PyDict_SetItem(smod,fname,mod);
#endif
	dict = PyModule_GetDict(mod);

	/* mod.__loader__ = self */
	if (PyDict_SetItemString(dict, "__loader__", (PyObject *)self) != 0) {
		goto error;
	}

	if (ispackage) {


		/* modpath includes the __init__.pyc trailing file name */
		wchar_t* mtmp = modpath;
		mtmp[wcslen(mtmp)-11] = L'\0';

		/* add __path__ to the module *before* the code gets
		   executed */
		PyObject *pkgpath;
		pkgpath = Py_BuildValue("[u]", modpath);
		if (pkgpath == NULL)
			goto error;

		int err = PyDict_SetItemString(dict, "__path__", pkgpath);
		Py_DECREF(pkgpath);
		if (err != 0)
			goto error;
	}
	
#ifdef VERBOSE
	printf("exec %s\n",ascii);
#endif

	//wcstombs(tmp_ascii1,modpath,qf_MAX_PATH); // same fixme
	mod = PyImport_ExecCodeModule(ascii, code);
	Py_DECREF(code);
	return mod;
error:
	Py_DECREF(code);
	Py_DECREF(mod);
	return NULL;
}

// --------------------------------------------------------------------------------------------
/* Return a string matching __file__ for the named module */
// --------------------------------------------------------------------------------------------
PyObject *qfimporter_get_filename(PyObject *obj, PyObject *args)
{	
	qfImporter *self = (qfImporter *)obj;
	PyObject *code;
	wchar_t *fullname, modpath[qf_MAX_PATH+1];

	if (!PyArg_ParseTuple(args, "u:qfimporter._get_filename",&fullname)) {
		return NULL;
	}

	/* Deciding the filename requires working out where the code
	   would come from if the module was actually loaded */
	code = get_module_code(self, fullname, NULL, modpath);
	if (code == NULL) {
		return NULL;
	}

	Py_DECREF(code); /* Only need the path info */
	return PyUnicode_FromWideChar(modpath,-1);
}

// --------------------------------------------------------------------------------------------
/* Return a bool signifying whether the module is a package or not. */
// --------------------------------------------------------------------------------------------
PyObject *qfimporter_is_package(PyObject *obj, PyObject *args)
{	
	qfImporter *self = (qfImporter *)obj;
	wchar_t *fullname;
	zi_module_info mi;

	if (!PyArg_ParseTuple(args, "u:qfimporter.is_package",&fullname)) {
		return NULL;
	}

	mi = get_module_info(self, fullname);
	if (mi == MI_ERROR) {
		return NULL;
	}
	if (mi == MI_NOT_FOUND) {
		PyErr_SetString(qfImportError, "can't find module"); // fixme
		printf("Failure to find module %s",fullname);
		return NULL;
	}
	return PyBool_FromLong(mi == MI_PACKAGE);
}

// --------------------------------------------------------------------------------------------
/* Get data for a given, fully qualified module */
// --------------------------------------------------------------------------------------------
PyObject *qfimporter_get_data(PyObject *obj, PyObject *args)
{	
	qfImporter *self = (qfImporter *)obj;
	wchar_t *path;

	if (!PyArg_ParseTuple(args, "u:qfimporter.get_data", &path)) {
		return NULL;
	}

	unsigned int rid;
	zi_module_info mi = get_module_info(self, path,&rid);
	if (mi == MI_ERROR) {
		return NULL;
	}

	if (mi == MI_NOT_FOUND) {
		PyErr_SetString(qfImportError, "can't find module"); // fixme
		printf("Failure to find module %s",path);
		return NULL;
	}

	PyObject * p = get_data(rid);
	return p;
}

// --------------------------------------------------------------------------------------------
/* Get the byte code for a particular module, given a fully qualified module
   name as input parameter */
// --------------------------------------------------------------------------------------------
PyObject *qfimporter_get_code(PyObject *obj, PyObject *args)
{	
	qfImporter *self = (qfImporter *)obj;
	wchar_t *fullname;

	if (!PyArg_ParseTuple(args, "u:qfimporter.get_code", &fullname)) {
		return NULL;
	}

	return get_module_code(self, fullname, NULL, NULL);
}

// --------------------------------------------------------------------------------------------
/* Given a buffer, return the long that is represented by the first
   4 bytes, encoded as little endian. This partially reimplements
   marshal.c:r_long() */
// --------------------------------------------------------------------------------------------
long get_long(unsigned char *buf)
{
	long x;
	x =  buf[0];
	x |= (long)buf[1] <<  8;
	x |= (long)buf[2] << 16;
	x |= (long)buf[3] << 24;
#if SIZEOF_LONG > 4
	/* Sign extension for 64-bit machines */
	x |= -(x & 0x80000000L);
#endif
	return x;
}

// --------------------------------------------------------------------------------------------
/* Given the contents of a .py[co] file in a buffer, unmarshal the data
   and return the code object. Return None if it the magic word doesn't
   match (we do this instead of raising an exception as we fall back
   to .py if available and we don't want to mask other errors).
   Returns a new reference. */
// --------------------------------------------------------------------------------------------
PyObject * unmarshal_code(wchar_t *pathname, PyObject *data)
{	
	PyObject *code;
	char *buf = PyBytes_AsString(data);
	Py_ssize_t size = PyBytes_Size(data);

	if (size <= 9) {
		printf("Encountered invalid pyc file: %s",pathname);
		PyErr_SetString(qfImportError,"bad pyc data");
		return NULL;
	}

	const long a = get_long((unsigned char *)buf);
	const long b = PyImport_GetMagicNumber();
	if (a != b) {
		printf("# %S has bad magic: %x, but should be %x\n", pathname,a , b);
		Py_INCREF(Py_None);
		return Py_None;  /* signal caller to try alternative */
	}

	code = PyMarshal_ReadObjectFromString(buf+8, size-8);
	if (code == NULL)
		return NULL;
	if (!PyCode_Check(code)) {
		Py_DECREF(code);
		printf("compiled module %.200s is not a code object",pathname);
		PyErr_Format(PyExc_TypeError, "Not a code object");
		return NULL;
	}

	return code;
}

// --------------------------------------------------------------------------------------------
/* PyDoc stuff - copied from qfimport.c */
// --------------------------------------------------------------------------------------------
PyDoc_STRVAR(doc_find_module,
	"find_module(fullname, path=None) -> self or None.\n\
	\n\
	Search for a module specified by 'fullname'. 'fullname' must be the\n\
	fully qualified (dotted) module name. It returns the qfimporter\n\
	instance itself if the module was found, or None if it wasn't.\n\
	The optional 'path' argument is ignored -- it's there for compatibility\n\
	with the importer protocol.");

PyDoc_STRVAR(doc_load_module,
	"load_module(fullname) -> module.\n\
	\n\
	Load the module specified by 'fullname'. 'fullname' must be the\n\
	fully qualified (dotted) module name. It returns the imported\n\
	module, or raises qfImportError if it wasn't found.");

PyDoc_STRVAR(doc_get_data,
	"get_data(pathname) -> string with file data.\n\
	\n\
	Return the data associated with 'pathname'. Raise IOError if\n\
	the file wasn't found.");

PyDoc_STRVAR(doc_is_package,
	"is_package(fullname) -> bool.\n\
	\n\
	Return True if the module specified by fullname is a package.\n\
	Raise qfImportError is the module couldn't be found.");

PyDoc_STRVAR(doc_get_code,
	"get_code(fullname) -> code object.\n\
	\n\
	Return the code object for the specified module. Raise qfImportError\n\
	is the module couldn't be found.");

PyDoc_STRVAR(doc_get_source,
	"get_source(fullname) -> source string.\n\
	\n\
	Return the source code for the specified module. Raise qfImportError\n\
	is the module couldn't be found, return None if the archive does\n\
	contain the module, but has no source for it.");

PyDoc_STRVAR(doc_get_filename,
	"_get_filename(fullname) -> filename string.\n\
	\n\
	Return the filename for the specified module.");

PyDoc_STRVAR(qfimporter_doc,
	"qfimporter() -> qfimporter object\n\
	\n\
	Create a new qfimporter instance. \n\
	\n\
	The 'archive' attribute of qfimporter objects contains the name of the\n\
	qffile targeted.");

// --------------------------------------------------------------------------------------------
/* qfimporter method table */
// --------------------------------------------------------------------------------------------
static PyMethodDef qfimporter_methods[] = {
	{"find_module", qfimporter_find_module, METH_VARARGS,
		doc_find_module},
	{"load_module", qfimporter_load_module, METH_VARARGS,
	 doc_load_module},
	{"get_data", qfimporter_get_data, METH_VARARGS,
	 doc_get_data},
	{"get_code", qfimporter_get_code, METH_VARARGS,
	 doc_get_code},
	{"_get_filename", qfimporter_get_filename, METH_VARARGS,
	 doc_get_filename},
	{"is_package", qfimporter_is_package, METH_VARARGS,
	 doc_is_package},
	{NULL,		NULL}	/* sentinel */
};

// none remaining, I refactored them away
static PyMemberDef qfimporter_members[] = {
	{NULL}
};

#define DEFERRED_ADDRESS(ADDR) 0

// --------------------------------------------------------------------------------------------
/* Declaration of qfImporter */
// --------------------------------------------------------------------------------------------
static PyTypeObject qfImporter_Type = {
	PyVarObject_HEAD_INIT(DEFERRED_ADDRESS(&PyType_Type), 0)
	"qfimport.qfimporter",
	sizeof(qfImporter),
	0,					/* tp_itemsize */
	(destructor)qfimporter_dealloc,	/* tp_dealloc */
	0,					/* tp_print */
	0,					/* tp_getattr */
	0,					/* tp_setattr */
	0,					/* tp_reserved */
	(reprfunc)qfimporter_repr,		/* tp_repr */
	0,					/* tp_as_number */
	0,					/* tp_as_sequence */
	0,					/* tp_as_mapping */
	0,					/* tp_hash */
	0,					/* tp_call */
	0,					/* tp_str */
	PyObject_GenericGetAttr,		/* tp_getattro */
	0,					/* tp_setattro */
	0,					/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE |
	Py_TPFLAGS_HAVE_GC,		/* tp_flags */
	qfimporter_doc,			/* tp_doc */
	qfimporter_traverse,			/* tp_traverse */
	0,					/* tp_clear */
	0,					/* tp_richcompare */
	0,					/* tp_weaklistoffset */
	0,					/* tp_iter */
	0,					/* tp_iternext */
	qfimporter_methods,			/* tp_methods */
	qfimporter_members,			/* tp_members */
	0,					/* tp_getset */
	0,					/* tp_base */
	0,					/* tp_dict */
	0,					/* tp_descr_get */
	0,					/* tp_descr_set */
	0,					/* tp_dictoffset */
	(initproc)qfimporter_init,		/* tp_init */
	PyType_GenericAlloc,			/* tp_alloc */
	PyType_GenericNew,			/* tp_new */
	PyObject_GC_Del,			/* tp_free */
};

// --------------------------------------------------------------------------------------------
/* Get the contents of a particular file as Python byte buffer */
// --------------------------------------------------------------------------------------------
PyObject *get_data(unsigned int rid)
{	
	size_t size;
	char* res = FetchResource(rid,&size);

	PyObject* data = PyBytes_FromStringAndSize(res, size);
	delete[] res;
	if (data == NULL) {
		return NULL;
	}

	return data;
}

// --------------------------------------------------------------------------------------------
/** 
 ** Return the code object for the module named by 'fullname' from the
 ** qf archive as a new reference.
 **/
// --------------------------------------------------------------------------------------------
PyObject * get_code_from_data(qfImporter *self, bool ispackage, unsigned int rid, wchar_t* modpath)
{	
	PyObject *data, *code;

	data = get_data(rid);
	if (data == NULL)
		return NULL;

	code = unmarshal_code(modpath, data);
	if (!code) {
		printf("Failure to obtain code object for %s",modpath);
	}

	Py_DECREF(data);
	return code;
}

// --------------------------------------------------------------------------------------------
/**
 ** Get the code object assoiciated with the module specified by'fullname'. 
 **/
// --------------------------------------------------------------------------------------------
PyObject * get_module_code(qfImporter *self, wchar_t *fullname, bool *p_ispackage, wchar_t *p_modpath)
{
	wchar_t path[MAXPATHLEN + 1],tmp[qf_MAX_PATH + 1];
	int len;
	st_qf_searchorder *zso;
	st_qf_prefixorder *ma;
	len = make_filename(fullname, path);
	if (len < 0)
		return NULL;

	PyObject* code;

	ma = qf_prefixorder; // for (ma = qf_prefixorder; *ma->prefix; ma++) 
	{

		wcscpy(tmp,ma->prefix);
		size_t lenn = wcslen(ma->prefix);

		wcscpy(tmp+lenn,path);
		lenn += len;

		for (zso = qf_searchorder; *zso->suffix; zso++) {
			wcscpy(tmp + lenn, zso->suffix);
			const unsigned int rid = NameToId(tmp);

			if (rid) {
				const bool ispackage  = 0 != (zso->type & IS_PACKAGE);

				if (p_ispackage != NULL)
					*p_ispackage = ispackage;

				code = get_code_from_data(self, ispackage,rid, tmp);

				if (code == Py_None) {
					/* bad magic number or non-matching mtime
					in byte code, try next */
					Py_DECREF(code);
					continue;
				}
				if (code != NULL && p_modpath != NULL)
					wcscpy(p_modpath,tmp);

				return code;
			}
		}
	}

	PyErr_SetString(qfImportError, "can't find the requested module");
	return NULL;
}

// --------------------------------------------------------------------------------------------
/* Module init */
// --------------------------------------------------------------------------------------------
PyDoc_STRVAR(qfimport_doc,"qfimport provides support for importing Python modules from qf archives.\n\
\n\
This module exports two objects:\n\
- qfimporter: a class; its constructor takes a path to a qf archive.\n\
- qfImportError: exception raised by qfimporter objects. It's a\n\
  subclass of ImportError, so it can be caught as ImportError, too.\n\
\n\
It is usually not needed to use the qfimport module explicitly; it is\n\
used by the builtin import mechanism for sys.path items that are paths\n\
to qf archives.");

static struct PyModuleDef qfimportmodule = {
	PyModuleDef_HEAD_INIT,
	"qfimport",
	qfimport_doc,
	-1,
	NULL,
	NULL,
	NULL,
	NULL,
	NULL
};

// --------------------------------------------------------------------------------------------
/* Initialize the import meta plugin */
// --------------------------------------------------------------------------------------------
PyMODINIT_FUNC PyInit_qfimport(void)
{	/*  OK */
	PyObject *mod;
	if (PyType_Ready(&qfImporter_Type) < 0) {
		assert(false);
		return NULL;
	}

	mod = PyModule_Create(&qfimportmodule);
	if (mod == NULL) {
		assert(false);
		return NULL;
	}

	qfImportError = PyErr_NewException("_import.qfImportError",PyExc_ImportError, NULL);
	if (qfImportError == NULL) {
		assert(false);
		return NULL;
	}

	Py_INCREF(qfImportError);
	if (PyModule_AddObject(mod, "qfImportError",qfImportError) < 0) {
		assert(false);
		return NULL;
	}

	Py_INCREF(&qfImporter_Type);
	if (PyModule_AddObject(mod, "qfimporter",(PyObject *)&qfImporter_Type) < 0) {
		assert(false);
		return NULL;
	}
	printf("Registering python module \'qfimport\'\n");
	return mod;
}
