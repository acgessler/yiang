#ifndef INCLUDED_LRU_CACHE_H
#define INCLUDED_LRU_CACHE_H

#include <cassert>
#include <cstddef>
#include <hash_map>

// Non-thread safe LRU cache for a function f(K) -> V, supporting
// re-use of evicted values. All operations are O(1) (if hashing
// K is constant time) and the code is C++03 compatible (given a
// <hash_map>). Move semantics would certainly enable a speedup.
//
// To use, supply the function that gets called for a cache miss:
//
// ValueFetcher::operator(const K& key, V* evicted, V*& out)
//
// |out| receives the new value to associate with |key|, to be
// allocated using new. 
//
// |*evicted| is the value being evicted to make room for this
// cache entry. |evicted| is NULL if the cache is not all full yet.
// If |evicted| is non-NULL, it must be deleted by the implementation
// or re-used as |out|.
//


template <typename K, typename V, typename ValueFetcher>
class LRUCache {
public:
	// Construct with given cache |size| (capacity, fixed for life time)
	// and optionally a ValueFetcher instance to use for retrieving
	// values for cache misses.
	LRUCache(size_t size, const ValueFetcher& fetcher = ValueFetcher()) 
		: size(size), youngest(), oldest(), fetcher(fetcher) {
		assert(size > 0);
	}

	~LRUCache() {
		// Manually deletion, this is C++03 code.
		for (CacheMap::iterator it = cache.begin(), end = cache.end(); it != end; ++it) {
			delete (*it).second.value;
		}
	}

	size_t GetSize() const {
		return size;
	}

	size_t GetSizeUsed() const {
		return cache.size();
	}

	// The returned reference is valid until the next call to Get()
	// and any modifications to it modify the original value.
	//
	// |*out_cached_before| receives true iff the value for |k| was
	// retrieved from cache, i.e. a cache hit.
	V& Get(const K& k, bool* out_cached_before = NULL) {
		const CacheMap::iterator it = cache.find(k);

		// Cache miss
		if (it == cache.end()) {
			V* evict = NULL;
			assert(cache.size() <= size);

			// Cache full, do LRU replacement
			//
			// Make sure to erase the oldest element before adding a
			// new element to avoid re-hashes to a size much larger
			// than the maximum capacity.
			if (cache.size() == size) {
				assert(oldest != NULL);
				assert(cache.find(oldest->key) != cache.end());

				evict = oldest->value;				
				const std::string& key = oldest->key;

				oldest = oldest->younger;
				if (oldest != NULL) {
					oldest->older = NULL;
				}

				cache.erase(cache.find(key));
			}

			assert(cache.size() <= size);

			CacheEntry& entry = cache[k];
			entry.key = k;
			fetcher(k, evict, entry.value);

			// Put this into the list as the youngest entry
			if (youngest == NULL) {
				oldest = &entry;
			}
			else {
				youngest->younger = &entry;
			}
			entry.older = youngest;
			youngest = &entry;

			if (out_cached_before != NULL) {
				*out_cached_before = false;
			}

			return *entry.value;
		}

		if (out_cached_before != NULL) {
			*out_cached_before = true;
		}
		
		CacheEntry& entry = it->second;

		// Make this cache entry the youngest element
		if (entry.younger == NULL) {
			return *entry.value;
		}

		CacheEntry* const younger = entry.younger;
		entry.younger = NULL;

		// Remove the entry from its current position
		if (entry.older != NULL) {
			entry.older->younger = younger;
		}
		else {
			oldest = younger;
		}
		younger->older = entry.older;

		// Fix previous youngest
		entry.older = youngest;
		youngest->younger = &entry;

		// Relink head link
		youngest = &entry;
		return *entry.value;
	}

private:
	// Entries in the hashmap directly hold a double-linked list
	// arranging cache items by age.
	struct CacheEntry {
		CacheEntry()
			: older(), younger() {} 
		V* value;

		// TODO: find a way to avoid having to store the key
		K key;
		CacheEntry* older;
		CacheEntry* younger;
	};

	size_t size;

	// MSVC 9 unfortunately has hash_map in stdext:: and
	// it doesn't have unordered_map yet.

	// LRUCache requires that insertion and deletion does
	// not invalidate references to cache elements, except
	// for the element being modified. Iterator validity
	// is not required, i.e. C++11 unordered_map would
	// therefore work.
#ifdef _MSC_VER
	typedef stdext::hash_map<K, CacheEntry> CacheMap;
#else
	typedef std::hash_map<K, CacheEntry> CacheMap;
#endif

	CacheMap cache;

	CacheEntry* youngest;
	CacheEntry* oldest;

	ValueFetcher fetcher;
};

#endif // INCLUDED_LRU_CACHE_H

