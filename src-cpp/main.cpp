///////////////////////////////////////////////////////////////////////////////////
// Yet Another Jump'n'Run Game, unfair this time.
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

// Main entry point, initializes Python and calls main.py

#define _CRT_SECURE_NO_WARNINGS

#define WIN32_LEAN_AND_MEAN
#include <Windows.h>

// CommandLineToArgvW, GetCommandLineW
#include <Shellapi.h>

// SFML libs
#pragma comment (lib, "sfml-graphics.lib")
#pragma comment (lib, "sfml-window.lib")
#pragma comment (lib, "sfml-audio.lib")
#pragma comment (lib, "sfml-system.lib")

// fixup code for some missing SFML symbols
#include "fixers.h"


// Python C API, PySFML module initialization stub
#include <Python.h>
#pragma comment (lib, "Python31.lib")

PyMODINIT_FUNC PyInit_sf(void);

#if 0
// --------------------------------------------------------------------------------------------
FILE* FindScript(const char* name)
{
	FILE* fp;

	static const std::string base_src = "./../src-py/", base_bin = "./../bin-py/";
	return !(fp = fopen((base_src+name).c_str(),"rt")) && !(fp = fopen((base_bin+name).c_str(),"rb")), fp;
}
#endif

// --------------------------------------------------------------------------------------------
int PyMain(int argc, wchar_t* argv[])
{
	// bootstrapping script, hands control over to main.py
	static char start_script_name[] =  "__launch_stub__.py";
	const char* start_stub = 
		"import sys\n" 
		"import traceback\n"
		"sys.path.append(\'../src-py\')\n"
		"try:\n"
		"\timport main\n"
		"except Exception as e:\n"
		"\tprint(e)\n"
		"\ttraceback.print_exc()\n"
	;

	PyImport_AppendInittab("sf", & PyInit_sf);
	Py_Initialize();   

	PySys_SetArgv(argc, argv);

	const int ret = PyRun_SimpleString(start_stub);

	if (PyErr_Occurred()) {
		PyErr_Print();
		PyErr_Clear();
	}

	Py_Finalize();
	return ret;
}

#ifdef USE_WINMAIN

// --------------------------------------------------------------------------------------------
int WINAPI WinMain(
  __in  HINSTANCE hInstance,
  __in  HINSTANCE hPrevInstance,
  __in  LPSTR lpCmdLine,
  __in  int nCmdShow
){
	// Entry point for Win32 applications. Reconstruct argc and argv first.
	int argc;
	LPWSTR* argv = ::CommandLineToArgvW(
		::GetCommandLineW(),
		&argc
	);

	return PyMain(argc,argv);
}

#else

int main(int argc, char* argv)
{
	// on Windows only for debugging purposes to get a console easily

	static wchar_t* name[] = {L"game.exe"};
	return PyMain(1,name);
}

#endif


/* vi: set shiftwidth=4 tabstop=4: */ 
