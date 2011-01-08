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

// Main entry point, initializes Python and calls editor.py

#ifdef _MSC_VER
#define _CRT_SECURE_NO_WARNINGS

#define WIN32_LEAN_AND_MEAN
#include <Windows.h>

#include <string>
#include <fstream>

// Python C API, PySFML module initialization stub
#include <Python.h>
#pragma comment (lib, "Python31.lib")
#pragma comment (lib, "pysfml.lib")
#pragma comment (lib, "yiang.lib")

#include "PyCache.h"

#else

#include <python3.1/Python.h>

#endif

PyMODINIT_FUNC PyInit_sf(void);

// --------------------------------------------------------------------------------------------
int PyMain(int argc, wchar_t* argv[])
{
	// bootstrapping script, hands control over to editor.py
	static char start_script_name[] =  "__launch_stub__.py";
	const char* start_stub = 
		"import sys\n" 
		"import traceback\n"
		"sys.path.append(\'../src-py\')\n"
		"try:\n"
		"\timport editor\n"
		"\teditor.main()\n"
		"except Exception as e:\n"
		"\tprint(e)\n"
		"\ttraceback.print_exc()\n"
		"\tprint(traceback.extract_stack())"
	;
#ifdef _MSC_VER
	PyImport_AppendInittab("sf", & PyInit_sf);
	PyImport_AppendInittab("qfimport", & PyInit_qfimport);
#endif

	Py_Initialize(); 

#ifdef _MSC_VER
	
	if (!std::ifstream("../src-py/main.py")) {
		PySys_WriteStdout("Enable import hook to read embedded scripts\n");
		SetupImportHook();
	}
	else {
		PySys_WriteStdout("Fetching scripts from source folder\n");
	}

#endif

	PySys_SetArgv(argc, argv);

	const int ret = PyRun_SimpleString(start_stub);

	if (PyErr_Occurred()) {
		PyErr_Print();
		PyErr_Clear();
	}

	Py_Finalize();
	return ret;
}


#include <stdlib.h>

int main(int argc, char* argv[])
{
	wchar_t** const dat = new wchar_t*[argc]();
	for(int i = 0; i < argc; ++i) {

		const size_t len = strlen(argv[i]);
		dat[i] = new wchar_t[len+1]();

		mbstowcs(dat[i],argv[i],len);
	}
	
	const int ret = PyMain(argc,dat);

	for(int i = 0; i < argc; ++i) {
		delete[] dat[i];
	}
	delete[] dat;
	return ret;
}




/* vi: set shiftwidth=4 tabstop=4: */ 
