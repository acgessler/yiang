///////////////////////////////////////////////////////////////////////////////////
// MGL Framework Source Module (v0.1)
// [game_main.cpp]
// (c) Alexander Gessler, 2009
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

#define WIN32_LEAN_AND_MEAN
#include <Windows.h>

// CommandLineToArgvW, GetCommandLineW
#include <Shellapi.h>
#include <Python.h>

// SFML libs
#pragma comment (lib, "sfml-graphics.lib")
#pragma comment (lib, "sfml-window.lib")
#pragma comment (lib, "sfml-audio.lib")
#pragma comment (lib, "sfml-system.lib")

// Python 3.1
#pragma comment (lib, "Python31.lib")


PyMODINIT_FUNC PyInit_sf(void);
#include "fixers.h"

// --------------------------------------------------------------------------------------------
int PyMain(int argc, wchar_t* argv[])
{
	PyImport_AppendInittab("sf", & PyInit_sf);
	Py_Initialize();    

	PySys_SetArgv(argc, argv);

	//PyObj PyRun_File;
	return 0;
}

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


/* vi: set shiftwidth=4 tabstop=4: */ 
