
#include <algorithm>
#include <iostream>

#include "VBOManager.hpp"

// Cache-miss function that re-uses the VBOs used by evicted entries
struct VBOManager::ReuseOrCreateVBOPolicy {
	ReuseOrCreateVBOPolicy(size_t size) : size(size){}

	void operator() (const std::string& str, VBOTile* evicted, VBOTile*& out) const {
		// Always re-use evicted tiles
		if (evicted != NULL) {
			assert(evicted->size == size);
			out = evicted;
			out->dirty = true;
			return;
		}
	
		out = new VBOTile();
		out->size = size;

		// Clear errors upfront
		glGetError();

		glGenBuffers(1, &out->vbo);
		glBindBuffer(GL_ARRAY_BUFFER, out->vbo);

		// Initialize the VBO with the correct size to enable
		// subsequent glBufferSubData() and glMapBuffer calls.
		glBufferData(GL_ARRAY_BUFFER, size, NULL, GL_STREAM_DRAW);
		glBindBuffer(GL_ARRAY_BUFFER, 0);
		
		const GLenum err = glGetError();
		if (err != GL_NO_ERROR) {
			// Set output VBO to 0, this ensures that users
			// will not attempt to use it.
			out->vbo = 0;

			// Unfortunately this wont go to log
			std::cerr << "(likely not logged) Failure allocating VBO of size " << size <<
				", GLGetError: " << err << std::endl;
		}
		std::cerr << "(likely not logged) Allocating VBO with size " << size << std::endl;
	}

	size_t size;
};


// -----------------------------------------------------------------------------
VBOManager::VBOManager()
{
	size_t size = 1u << CACHE_SIZE_FIRST_LEVEL_SHIFT_OFFSET;
	for (size_t i = 0; i < CACHE_LEVEL_COUNT; ++i) {
		caches[i] = new VBOCacheLevel(CACHE_PER_LEVEL_CAPACITY, ReuseOrCreateVBOPolicy(size));
		size <<= CACHE_SIZE_LEVEL_SHIFT;
	}
}

// -----------------------------------------------------------------------------
VBOManager::~VBOManager()
{
	for (size_t i = 0; i < CACHE_LEVEL_COUNT; ++i) {
		delete caches[i];
	}
}

// -----------------------------------------------------------------------------
VBOTile* VBOManager::Get(const std::string& key, size_t size_required) {
	// Find the first cache size that fits the string
	size_t index = 0;
	size_t size = 1u << CACHE_SIZE_FIRST_LEVEL_SHIFT_OFFSET;

	while (size < size_required) {
		size <<= CACHE_SIZE_LEVEL_SHIFT;
		++index;
	}

	if (index >= CACHE_LEVEL_COUNT) {
		return NULL;
	}
	assert(size >= size_required);
	return &caches[index]->Get(key);
}

// -----------------------------------------------------------------------------
size_t VBOManager::GetVBOSizeForString(const std::string& str) const
{
	// Line breaks and spaces don't incur any rendering
	size_t size = 0;
	for (size_t i = 0, e = str.length();  i < e; ++i) {
		if (str[i] == ' ' || str[i] == '\n') {
			continue;
		}
		size += BYTES_PER_CHARACTER_EXPECTED;
	}
	return size;
}

// -----------------------------------------------------------------------------
void EnsureGlxwInit()
{
	// No need for thread-safety
	static bool done = false;
	if (!done) {
		glxwInit();
		done = true;
	}
}