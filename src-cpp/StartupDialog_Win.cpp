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

// Implements the startup dialog which allows the player to choose his
// preferred video and audio settings.

#ifndef _MSC_VER
#	error Compile this only on Windows
#endif

#define _CRT_SECURE_NO_WARNINGS
#define WIN32_LEAN_AND_MEAN


// WinAPI includes
#include <Windows.h>
#include <Commctrl.h>

// resource IDs
#include "../vc9/resource1.h"

// STL
#include <map>

// ------------------------------------------------------------------------------------
// Windows CommonControls 6.0 Manifest Extensions  
#pragma comment (lib, "Comctl32.lib")

#if defined _M_IX86
#	define MGL_BUILD_X86
#	pragma comment(linker,"/manifestdependency:\"type='win32'   "		\
	"name='Microsoft.Windows.Common-Controls' version='6.0.0.0' "		\
	"processorArchitecture='x86' publicKeyToken='6595b64144ccf1df'"		\
	"language='*'\"")
#elif defined _M_IA64
#	define MGL_BUILD_IA64
#	pragma comment(linker,"/manifestdependency:\"type='win32'   "		\
	"name='Microsoft.Windows.Common-Controls' version='6.0.0.0' "		\
	"processorArchitecture='ia64' publicKeyToken='6595b64144ccf1df'"	\
	"language='*'\"")
#elif defined _M_X64
#	define MGL_BUILD_AMD64
#	pragma comment(linker,"/manifestdependency:\"type='win32'   "		\
	"name='Microsoft.Windows.Common-Controls' version='6.0.0.0' "		\
	"processorArchitecture='amd64' publicKeyToken='6595b64144ccf1df'"	\
	"language='*'\"")
#else
#	pragma comment(linker,"/manifestdependency:\"type='win32'   "		\
	"name='Microsoft.Windows.Common-Controls' version='6.0.0.0' "		\
	"processorArchitecture='*' publicKeyToken='6595b64144ccf1df'"		\
	"language='*'\"")
#endif


// ------------------------------------------------------------------------------------
INT_PTR CALLBACK DialogProc(
  __in  HWND hwndDlg,
  __in  UINT uMsg,
  __in  WPARAM wParam,
  __in  LPARAM lParam )
{
	static std::map<std::string,std::string> props;

	switch (uMsg) 
	{
	case WM_INITDIALOG:
		break;

	case WM_CLOSE:
		EndDialog(hwndDlg,1);
		break;

	case WM_COMMAND:

		switch (LOWORD(wParam))
		{
		case IDOK: 
			if (HIWORD(wParam) == BN_CLICKED) {
				EndDialog(hwndDlg,0);
			}
			break;
		case IDCANCEL: 
			if (HIWORD(wParam) == BN_CLICKED) {
				EndDialog(hwndDlg,1);
			}
			break;
		};
		break;

	default:
		return FALSE;
	};

	return TRUE;
}

// ------------------------------------------------------------------------------------
void ShowStartupDialog () 
{
	InitCommonControls();
	if ( DialogBoxW(NULL,MAKEINTRESOURCEW(IDD_DIALOG1),NULL,DialogProc)) {
		TerminateProcess(GetCurrentProcess(),-1);
	}
}

