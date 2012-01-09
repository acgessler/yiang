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

// Main entry point, initializes Python and calls main.py

#ifdef _MSC_VER
#   define _CRT_SECURE_NO_WARNINGS

#   define WIN32_LEAN_AND_MEAN
#   include <Windows.h>

// CommandLineToArgvW, GetCommandLineW
#   include <Shellapi.h>
// ShCreateDirectory()
#   include <Shlobj.h>

#   include <fstream>
#   include <string>

// Python C API, PySFML module initialization stub

#   include <Python.h>

#   pragma comment (lib, "Python31.lib")
#   pragma comment (lib, "pysfml.lib")
#   pragma comment (lib, "yiang.lib")

#   include "PyCache.h"


#else

#   include <python3.1/Python.h>
#   define USE_C_MAIN

#endif

PyMODINIT_FUNC PyInit_sf(void);

#ifdef _MSC_VER
#   include "StartupDialog.h"
#endif

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
		"\tmain.main()\n"
		"except Exception as e:\n"
		"\tprint(e)\n"
		"\ttraceback.print_exc()\n"
		"\tprint(traceback.extract_stack())\n"
		"\traise"
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

	if (PyErr_Occurred() || ret == -1) {

#ifdef _MSC_VER
		MessageBoxA(NULL,"Our apologies - YIANG just crashed and we know this should not have happened.\n\n"
			"If you want to help us fix this issue, " 
			"please send a copy of the log file (in the folder where game.exe resides) "
			"along with a description of the steps that led to the crash to bugs@yiang-thegame.com",
			"Crash Report", MB_OK);
#endif

		PyErr_Print();
		PyErr_Clear();
	}

	Py_Finalize();
	return ret;
}

//#undef USE_WINMAIN
#ifndef USE_C_MAIN

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

	std::wstring old_config;

	if (argc == 1 || argc == 2 && std::wstring(argv[1]) == L"--c") {
		TCHAR szPath[MAX_PATH];

		SHGetFolderPath(NULL, 
			CSIDL_APPDATA|CSIDL_FLAG_CREATE, 
			NULL, 
			0, 
			szPath);

		old_config = std::wstring(szPath) + L"\\yiang";
		SHCreateDirectory(NULL,old_config.c_str());

		if (!std::wifstream((old_config+L"\\donotask").c_str()) || argc == 2) {

			// if no configuration file is specified, show our startup GUI
			old_config += L"\\custom_config.txt";
			ShowStartupDialog(old_config);
		}
		else old_config += L"\\custom_config.txt";

		LPWSTR* const old = argv;
		argv = ::CommandLineToArgvW( //
			(old[0] + (L" " + old_config)).c_str(),
			&argc);

		LocalFree(old);
	}

	const int ret = PyMain(argc,argv);
	LocalFree(argv);

	return ret;
}

#else

#include <stdlib.h>

int main(int argc, char* argv[])
{
	// on Windows only for debugging purposes to avoid writing a log viewer
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

#endif


/* vi: set shiftwidth=4 tabstop=4: */ 
