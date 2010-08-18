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

// Publicly visible interface of the yiang.dll module.

#ifndef _MSC_VER
#	error Windows & MSVC only
#endif

// standard headers
#define _CRT_SECURE_NO_WARNINGS

#include <assert.h>
#include <stdlib.h>

// Python headers
#include <Python.h>

#include <Windows.h>
#include "PyCache.h"

// --------------------------------------------------------------------------------------------
/* Register the import hook with Python */
// --------------------------------------------------------------------------------------------
void SetupImportHook() 
{
	PyObject* path_hooks = PySys_GetObject("path_hooks");
	PyObject* qfimport = PyImport_ImportModule("qfimport");

	if (qfimport == NULL || path_hooks == NULL) {
		/* No qf import module -- not ok */
		Py_XDECREF(qfimport);
		Py_XDECREF(path_hooks);
		printf("qfimport module is not available\n");
	}
	else {
		PyObject *qfimporter = PyObject_GetAttrString(qfimport,
			"qfimporter");
		Py_DECREF(qfimport);
		if (qfimporter == NULL) {
			/* No qfimporter object -- not okay */
			printf("qfimporter class is not available\n");
		}
		else {
			/* sys.path_hooks.append(qfimporter) */
			int err = PyList_Append(path_hooks, qfimporter);
			Py_DECREF(qfimporter);
			if (err) {
				printf("Failure to install custom import hook\n");
			}
			printf("Installing custom import hook\n");
		}
	}
}

// --------------------------------------------------------------------------------------------
/* Entry stub */
// --------------------------------------------------------------------------------------------
BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
					 )
{
	switch (ul_reason_for_call)
	{
	case DLL_PROCESS_ATTACH:
	case DLL_THREAD_ATTACH:
	case DLL_THREAD_DETACH:
	case DLL_PROCESS_DETACH:
		break;
	}
	return TRUE;
}

