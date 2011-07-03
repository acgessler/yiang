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
#include "ManifestStubs.h"

// WinAPI includes
#include <Windows.h>
#include <Commctrl.h>

// ShCreateDirectory()
#include <Shlobj.h>

// resource IDs
#include "../vc9/resource1.h"

// STL/Boost
#include <string>
#include <fstream>
#include <map>
#include <boost/algorithm/string/trim.hpp>


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
		settings[boost::trim_right_copy( line.substr(0,s) )] = boost::trim_left_copy( line.substr(s+1) );
	}
}

#define RES_LARGE   L"[1600,900]"
#define RES_MEDIUM  L"[1378,775]"
#define RES_SMALL   L"[900,600]"

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

		{
			const int sx = ::GetSystemMetrics(SM_CXSCREEN), sy = ::GetSystemMetrics(SM_CYSCREEN);
			if( !props[L"fullscreen"].length() || props[L"fullscreen"] == L"True") {
				CheckDlgButton(hwndDlg,IDC_FS,BST_CHECKED);	
				props[L"fullscreen"] = L"True";
			}
			else {
				// XXX get rid of those magic constants
				if( props[L"resolution"]== RES_SMALL || sx < 1378 || sy < 775) {
					CheckDlgButton(hwndDlg,IDC_WND1024,BST_CHECKED);
				} 
				else if( props[L"resolution"]== RES_MEDIUM  || sx < 1600 || sy < 900) {
					CheckDlgButton(hwndDlg,IDC_WND1280,BST_CHECKED);	
				} 
				else {
					CheckDlgButton(hwndDlg,IDC_WND1200,BST_CHECKED);	
				} 
			}
			if (sx < 1600 || sy < 900) {
				EnableWindow(GetDlgItem(hwndDlg,IDC_WND1200),FALSE);
				if (sx < 1378 || sy < 775) {
					EnableWindow(GetDlgItem(hwndDlg,IDC_WND1280),FALSE);
				} 
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

		CheckDlgButton(hwndDlg,IDC_NOTASKAGAIN, std::wifstream((temp_file+L"\\..\\donotask").c_str()) 
			? BST_CHECKED : BST_UNCHECKED);

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
				props[L"resolution"] = RES_SMALL;
				props[L"fullscreen"] = L"False";
			}
			break;
		case IDC_WND1200:
			if (HIWORD(wParam) == BN_CLICKED && IsDlgButtonChecked(hwndDlg,IDC_WND1200) == BST_CHECKED) {
				props[L"resolution"] = RES_LARGE;
				props[L"fullscreen"] = L"False";
			}
			break;
		case IDC_WND1280:
			if (HIWORD(wParam) == BN_CLICKED && IsDlgButtonChecked(hwndDlg,IDC_WND1280) == BST_CHECKED) {
				props[L"resolution"] = RES_MEDIUM;
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

		case IDC_NOTASKAGAIN:
			if (HIWORD(wParam) == BN_CLICKED) {
				std::wstring old_config;
				TCHAR szPath[MAX_PATH];

				SHGetFolderPath(NULL, 
					CSIDL_APPDATA|CSIDL_FLAG_CREATE, 
					NULL, 
					0, 
					szPath);

				old_config = std::wstring(szPath) + L"\\yiang";
				SHCreateDirectory(NULL,old_config.c_str());

				old_config += L"\\donotask";
				if (IsDlgButtonChecked(hwndDlg,IDC_NOTASKAGAIN) == BST_CHECKED) {
					std::wofstream(old_config.c_str());
				}
				else {
					DeleteFileW(old_config.c_str());
				}
			}
			break;
		}

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

