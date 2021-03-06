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

#ifndef _MSC_VER
#	error Windows & MSVC only
#endif

#include <Windows.h>
#include "ResourceFetcher.h"

#include <hash_map>
#include <string>
#include <assert.h>

// machine-generated resource table
#include "../vc9/yiang.h"
using namespace PyCacheTable;

// --------------------------------------------------------------------------------------------
/* Map a resource name to the corresponding ID. Return 0 on failure. */
// --------------------------------------------------------------------------------------------
unsigned int NameToId(const wchar_t* name)
{
	assert (name);
	typedef stdext::hash_map<std::wstring,unsigned int> Map;

	static Map map;
	if (!map.size()) {
		for (Entry* e = entries; e->name ; ++e) {
			map[std::wstring( e->name )] = e->index;
		}
	}

	Map::const_iterator it = map.find(std::wstring( name ));
	return it == map.end() ? 0 : (*it).second;
}


// --------------------------------------------------------------------------------------------
/* Fetch a resource from the current module, given a resource ID. Use delete[] to cleanup. */
// --------------------------------------------------------------------------------------------
char* FetchResource(unsigned int id, size_t* size)
{
	assert (id);

	HMODULE hmod = ::GetModuleHandleW(L"yiang.dll");
	HRSRC hr = ::FindResource(hmod,
		MAKEINTRESOURCEW(id),
		RT_RCDATA);

	if (!hr) {
		return NULL;
	}

	HGLOBAL hg = ::LoadResource(hmod,hr);
	void* const data = ::LockResource(hg);
	const size_t isize = ::SizeofResource(hmod,hr);

	char* out = new char[isize]();
	memcpy(out,data,isize);

	if (size) {
		*size = isize;
	}
	return out;
}

