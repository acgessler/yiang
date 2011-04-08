#ifndef INCLUDED_GPUSTREAMING_H
#define INCLUDED_GPUSTREAMING_H

/* Standalone part of my SFML hack to implement stream-to-vbo for all sf::String's*/

#include <Windows.h>
#include <GL/gl.h>


class TextStreamer 
{
public:

	TextStreamer (size_t initial);
	~TextStreamer();

public:

	void AddVertex(float x, float y);
	void AddTexcoord(float u, float v);

	void Flush();

private:

	GLuint vbo;
	void* data, *next, *end;
	size_t cur_size;
	size_t vertex_count;
};


#endif // INCLUDED_GPUSTREAMING_H
