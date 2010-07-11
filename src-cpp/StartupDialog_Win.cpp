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

// STL/Boost
#include <string>
#include <fstream>
#include <map>
#include <boost/algorithm/string/trim.hpp>

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

static std::wstring temp_file;
// ------------------------------------------------------------------------------------
void FlushSettings(const std::map<std::wstring,std::wstring>& settings)
{
	// WCHAR temp[MAX_PATH];
	// GetTempPathW(MAX_PATH,temp);
	// GetTempFileNameW(temp,L"yiang",0,temp);

	std::wofstream of(temp_file.c_str());
	if (!of) {
		MessageBoxW(NULL,L"Failure writing settings",L"YIANG Launcher",MB_ICONERROR|MB_OK);
		return;
	}

	for(std::map<std::wstring,std::wstring>::const_iterator it = settings.begin(); it != settings.end(); ++it) {
		if ((*it).second.length()) {
			of << (*it).first << "=" << (*it).second << std::endl;
		}
	}

}

// ------------------------------------------------------------------------------------
void LoadSettings(std::map<std::wstring,std::wstring>& settings)
{
	std::wifstream of(temp_file.c_str());
	std::wstring line;
	while (std::getline(of,line)) {
		boost::trim(line);
		if (!line.length()) {
			continue;
		}
		const std::wstring::size_type s = line.find(L"=");
		if (s == std::wstring::npos) {
			continue;
		}
		settings[line.substr(0,s)] = line.substr(s+1);
	}
}

// ------------------------------------------------------------------------------------
INT_PTR CALLBACK DialogProc(
  __in  HWND hwndDlg,
  __in  UINT uMsg,
  __in  WPARAM wParam,
  __in  LPARAM lParam )
{
	static std::map<std::wstring,std::wstring> props;

	switch (uMsg) 
	{
	case WM_INITDIALOG:

		// XXX workaround, WinDlg doesn't load the bitmap automatically.
		SendDlgItemMessage(hwndDlg,IDB_SPLASHB, STM_SETIMAGE, IMAGE_BITMAP, LPARAM(
			LoadImage(GetModuleHandleW(NULL), MAKEINTRESOURCEW(IDB_SPLASH), IMAGE_BITMAP, 0, 0, 0)
		)); 

		LoadSettings(props);

		if( props[L"fullscreen"] != L"False") {
			CheckDlgButton(hwndDlg,IDC_FS,BST_CHECKED);	
		}
		else {
			if( props[L"resolution"]== L"[1024,768]" ) {
				CheckDlgButton(hwndDlg,IDC_WND1024,BST_CHECKED);	
			} 
			else if( props[L"resolution"]== L"[1280,1024]" ) {
				CheckDlgButton(hwndDlg,IDC_WND1280,BST_CHECKED);	
			} 
			else { // if( props[L"resolution"]== L"[1024,768]" ) {
				CheckDlgButton(hwndDlg,IDC_WND1200,BST_CHECKED);	
			} 
		}

		if( props[L"no_ppfx"] == L"True") {
			CheckDlgButton(hwndDlg,IDC_NOPPFX,BST_CHECKED);	
		}
		if( props[L"no_halos"] == L"True") {
			CheckDlgButton(hwndDlg,IDC_LOWEND,BST_CHECKED);	
		}
		if( props[L"no_bg_music"] == L"True") {
			CheckDlgButton(hwndDlg,IDC_NOMUSIC,BST_CHECKED);	
		}
		if( props[L"no_bg_sound"] == L"True") {
			CheckDlgButton(hwndDlg,IDC_NOSOUND,BST_CHECKED);	
		}

		break;

	case WM_CLOSE:
		EndDialog(hwndDlg,1);
		break;

	case WM_COMMAND:

		switch (LOWORD(wParam))
		{
		case IDC_FS:
			if (HIWORD(wParam) == BN_CLICKED && IsDlgButtonChecked(hwndDlg,IDC_FS) == BST_CHECKED) {
				props[L"fullscreen"] = L"True";
			}
			break;
		case IDC_WND1024:
			if (HIWORD(wParam) == BN_CLICKED && IsDlgButtonChecked(hwndDlg,IDC_WND1024) == BST_CHECKED) {
				props[L"resolution"] = L"[1024,768]";
				props[L"fullscreen"] = L"False";
			}
			break;
		case IDC_WND1200:
			if (HIWORD(wParam) == BN_CLICKED && IsDlgButtonChecked(hwndDlg,IDC_WND1200) == BST_CHECKED) {
				props[L"resolution"] = L"[1200,750]";
				props[L"fullscreen"] = L"False";
			}
			break;
		case IDC_WND1280:
			if (HIWORD(wParam) == BN_CLICKED && IsDlgButtonChecked(hwndDlg,IDC_WND1280) == BST_CHECKED) {
				props[L"resolution"] = L"[1280,1024]";
				props[L"fullscreen"] = L"False";
			}
			break;
		case IDC_NOMUSIC:
			if (HIWORD(wParam) == BN_CLICKED) {
				props[L"no_bg_music"] =  IsDlgButtonChecked(hwndDlg,IDC_NOMUSIC)==BST_CHECKED ? L"True" : L"False";
			}
			break;
		case IDC_NOSOUND:
			if (HIWORD(wParam) == BN_CLICKED) {
				props[L"no_bg_sound"] =  IsDlgButtonChecked(hwndDlg,IDC_NOSOUND)==BST_CHECKED ? L"True" : L"False";
			}
			break;
		case IDC_NOPPFX:
			if (HIWORD(wParam) == BN_CLICKED) {
				props[L"no_ppfx"] =  IsDlgButtonChecked(hwndDlg,IDC_NOPPFX)==BST_CHECKED ? L"True" : L"False";
			}
			break;
		case IDC_LOWEND:
			if (HIWORD(wParam) == BN_CLICKED) {
				props[L"no_halos"] =  IsDlgButtonChecked(hwndDlg,IDC_LOWEND)==BST_CHECKED ? L"True" : L"False";
			}
			break;
		case IDOK: 
			if (HIWORD(wParam) == BN_CLICKED) {
				FlushSettings(props);
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
void ShowStartupDialog (const std::wstring& out_config) 
{
	temp_file = out_config;

	InitCommonControls();
	if ( DialogBoxW(NULL,MAKEINTRESOURCEW(IDD_DIALOG1),NULL,DialogProc)) {
		TerminateProcess(GetCurrentProcess(),-1);
	}
}

