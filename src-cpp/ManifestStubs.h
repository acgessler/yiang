
#pragma once

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