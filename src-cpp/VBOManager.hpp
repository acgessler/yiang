#ifndef INCLUDED_VBO_MANAGER_H
#define INCLUDED_VBO_MANAGER_H

#include <string>
#include <iostream>

#include "GLXW/glxw.h"
#include "LRUCache.hpp"

// VBOManager caches vertices for text sprites ("tiles") in VBOs.
// The VBO cache is accessed by a string key and partitioned into multiple
// cache levels which store differently sized VBOs.


// Upon requesting the cache entry for a string key, a VBOTile instance
// is returned.
//
// - A suitable VBO may or may not be available.
// - The VBO may still hold the data for the key (from a previous use)
//   or it may need to be re-filled. This can happen if the key has
//   never been cached before, or it has been evicted from the cache.
struct VBOTile {
	VBOTile() : vbo(), offset(), size(), dirty(true), quad_count(), vao() {}
	~VBOTile() {
		if (vbo != 0) {
			std::cerr << "(likely not logged) Destroying VBO with size " << size << std::endl;
			glDeleteBuffers(1, &vbo);
		}
	}

	// Maintained by VBOManager
	//

	// A valid GL VBO, or 0 if VBO creation fails
	GLuint vbo;

	// Offset into the VBO at which data for this
	// tile starts.
	size_t offset;

	// Bytes occupied by the tile
	size_t size;


	// Maintained by clients
	//

	// Whether the VBO slice contains stale data
	bool dirty;
	unsigned int quad_count;

	GLuint vao;
};

void EnsureGlxwInit();

// Call EnsureGlxwInit() before any use
class VBOManager {
public:

	VBOManager();
	~VBOManager();

public:

	// Get a VBO-cache slice of at least |size_required| bytes for a
	// given string |key|.
	// 
	// As a caller, use |dirty| to determine whether the data
	// in the VBO slice is stale and needs to be refreshed.
	//
	// After doing so, set |dirty = false|.
	//
	// Returns NULL if no cache capacity is available for the size
	// requested.
	VBOTile* Get(const std::string& key, size_t size_required);

	// Get the number of bytes of VBO storage required to hold the
	// vertices for drawing a given |str|.
	//
	// This includes storage for 32 Bit RGBA vertex colors,
	// 3D vertex positions and 2D texture coordinates.
	//
	// The only kind of control character supported is \n.
	size_t GetVBOSizeForString(const std::string& str) const;

private:

	enum {
		// Number of cache levels
		CACHE_LEVEL_COUNT = 3
	};

	enum {
		// Each character requires four 2D position vectors,
		// four texture coordinates and one 32 bit RGBA color,
		// i.e. (4 * 5) * 4 == 80 Bytes.
		BYTES_PER_CHARACTER_EXPECTED = 80
	};

	enum {
		// 1 << CACHE_SIZE_FIRST_LEVEL_SHIFT_OFFSET is the bytes size of
		// the first cache level (i.e. |caches[0]|).
		//
		// The first level is intended to cache normal-size
		// tiles, i.e. a 5x3 block of characters.
		//
		// A whole tile therefore requires at least 96 * 15 = 1200 Bytes,
		// so 2048 == 2^11 is the lowest cache size.
		CACHE_SIZE_FIRST_LEVEL_SHIFT_OFFSET = 11
	};

	enum {
		// After the first cache level, each level has 4x the size
		// of the previous level.
		CACHE_SIZE_LEVEL_SHIFT = 2
	};

	enum {
		// Number of tiles to cache per level
		CACHE_PER_LEVEL_CAPACITY = 250
	};

	struct ReuseOrCreateVBOPolicy;

	typedef LRUCache<std::string, VBOTile, ReuseOrCreateVBOPolicy> VBOCacheLevel;
	VBOCacheLevel* caches[CACHE_LEVEL_COUNT];
};

#endif // INCLUDED_VBO_MANAGER_H
