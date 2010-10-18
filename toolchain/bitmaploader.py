

# From http://ant.simianzombie.com/?p=1024
# Being a prototype to the woopsi BitmapLoader, it should be BSD-licensed.
# XXX ask the author :-)

import os

class Bitmap:
	"""Class that can load BMP files and extract all header information and colours
	for each pixel.  Format support:
	
	Header types:
		V1 (O/S2) - Supported
		V2 (O/S2) - Unsupported
		V3 (Windows) - Supported
		V4 (Windows) - Partially supported (treated as V3)
		V5 (Windows) - Partially supported (treated as V3)
		
	Compression types:
		BI_RGB - Supported
		BI_RLE8 - Unsupported
		BI_RLE4 - Unsupported
		BI_BITFIELDS - Unsupported
		BI_JPEG - Unsupported
		BI_PNG - Unsupported
	
	Bits per pixel:
		1 - Supported
		4 - Supported
		8 - Supported
		16 - Supported (untested)
		24 - Supported
		32 - Unsupported
	
	"""
	
	# Constants - compression methods
	BI_RGB = 0
	BI_RLE8 = 1
	BI_RLE4 = 2
	BI_BITFIELDS = 3
	BI_JPEG = 4
	BI_PNG = 5
	
	# Constants - header types
	BITMAPCOREHEADER = 12
	BITMAPCOREHEADER2 = 64
	BITMAPINFOHEADER = 40
	BITMAPV4HEADER = 108
	BITMAPV5HEADER = 124

	__filename = ""
	__data = ""
	
	# Standard header
	__bmp_header_size = 14
	__identifier = ""
	__size = 0
	__offset = 0
	
	# DIB V3 header
	__dib_header_size = 0
	width = 0
	height = 0
	__color_planes = 0
	__bits_per_pixel = 0
	__compression_method = 0
	__image_size = 0
	__horizontal_resolution = 0
	__vertical_resolution = 0
	__colors_in_palette = 0
	__important_colors_used = 0
	
	# Palette
	__palette_offset = 0
	
	def __init__(self, filename):
		"""Constructor."""
		self.__filename = filename
		self.__load(filename)
		
	def __load(self, filename):
		"""Load the specified bitmap."""
		with open(filename, mode="rb") as file:
			self.__data = file.read()
			self.__parse_bmp_header(self.__data[0:14])
			self.__parse_dib_header(self.__data[14:])
		
	def __parse_bmp_header(self, data):
		"""Parse the bitmap header and extract data."""
		self.__identifier = data[0:2]
		self.__size = str_to_integer(data[2:6])
		self.__offset = str_to_integer(data[10:14])
	
	def __parse_dib_header(self, data):
		"""Parse the DIB header and extract data."""
		self.__dib_header_size = str_to_integer(data[0:4])
		
		# Palette offset can be inferred from already known data
		self.__palette_offset = self.__bmp_header_size + self.__dib_header_size
		
		# Choose DIB header version from its size and parse appropriately
		if self.__dib_header_size == self.BITMAPCOREHEADER:
			self.__parse_v1_dib_header(data[4:])
			
		elif self.__dib_header_size == self.BITMAPCOREHEADER2:
			raise RuntimeError("V2 header not implemented")
			
		elif self.__dib_header_size == self.BITMAPINFOHEADER:
			self.__parse_v3_dib_header(data[4:])
			
		elif self.__dib_header_size == self.BITMAPV4HEADER:
		
			# DIB V4 is V3 plus extra data - treat as V3 and ignore extras
			self.__parse_v3_dib_header(data[4:])
			
		elif self.__dib_header_size == self.BITMAPV5HEADER:
			
			# DIB V5 is V4 plus extra data - treat as V3 and ignore extras
			self.__parse_v3_dib_header(data[4:])
			
	def __parse_v1_dib_header(self, data):
		"""Parse a version 1 DIB header and extract data."""
		self.width = str_to_integer(data[0:2])
		self.height = str_to_integer(data[2:4])
		self.__color_planes = str_to_integer(data[4:6])
		self.__bits_per_pixel = str_to_integer(data[6:8])
	
	def __parse_v3_dib_header(self, data):
		"""Parse a version 3 DIB header and extract data."""
		self.width = str_to_integer(data[0:4])
		self.height = str_to_integer(data[4:8])
		self.__color_planes = str_to_integer(data[8:10])
		self.__bits_per_pixel = str_to_integer(data[10:12])
		self.__compression_method = str_to_integer(data[12:16])
		self.__image_size = str_to_integer(data[16:20])
		self.__horizontal_resolution = str_to_integer(data[20:24])
		self.__vertical_resolution = str_to_integer(data[24:28])
		self.__colors_in_palette = str_to_integer(data[28:32])
		self.__important_colors_used = str_to_integer(data[32:36])
	
	def get_pixel_color(self, x, y):
		"""Get the colour of the pixel at the specified co-ordinates."""
		
		if self.__bits_per_pixel == 1:
		
			# Get the colour from the palette
			return self.__get_pixel_color1(x, y)
		elif self.__bits_per_pixel == 4:
		
			# Get the colour from the palette
			return self.__get_pixel_color4(x, y)
		elif self.__bits_per_pixel == 8:
		
			# Get the colour from the palette
			return self.__get_pixel_color8(x, y)
		elif self.__bits_per_pixel == 16:
		
			# Get the color of the pixel as a single integer
			return self.__get_pixel_color16(x, y)
		elif self.__bits_per_pixel == 24:
		
			# Get the color of the pixel as a single integer
			return self.__get_pixel_color24(x, y)
			
	def __get_pixel_color1(self, x, y):
		"""Get colour of specified pixel from a monochrome bitmap."""
		
		# Calculate the width of each row in bytes including the padding added to align
		# to 4-byte boundaries
		aligned_width = (self.width // 8) + 1
		mod_width = aligned_width % 4
		
		if mod_width != 0:
			aligned_width += 4 - mod_width
			
		# Calculate the offset of the pixel from the start of the data.
		pixel_offset = self.__offset + (self.__image_size - ((y + 1) * aligned_width)) + (x // 8)
		
		# Extract the bit from the pixel
		pixel_data = self.__data[pixel_offset]
		mask = 1 << (7 - (x % 8))
		pixel_data = (pixel_data & mask)

		return self.get_palette_color(1 if pixel_data else 0)
		
	def __get_pixel_color4(self, x, y):
		"""Get the colour of the specified pixel from a 16-colour bitmap."""
	
		# Calculate the width of each row in bytes including the padding added to align
		# to 4-byte boundaries
		aligned_width = self.width // 2
		mod_width = aligned_width % 4
		
		if mod_width != 0:
			aligned_width += 4 - mod_width
			
		# Calculate the offset of the pixel from the start of the data.
		# Rows of pixels are stored upside down, so the offset is calculated
		# from the end of the data backwards
		pixel_offset = self.__offset + (self.__image_size - ((y + 1) * aligned_width)) + (x // 2)
		
		# Each byte contains two pixels packed together as nibbles - extract
		# the correct nibble
		mask = 0xF << ((x % 2) * 4)
		pixel_data = (self.__data[pixel_offset] & mask) >> ((x % 2) * 4)
		
		return self.get_palette_color(pixel_data)
		
	def __get_pixel_color8(self, x, y):
		"""Get the colour of the specified pixel from a 256-colour bitmap."""

		# Calculate the width of each row in bytes including the padding added to align
		# to 4-byte boundaries
		aligned_width = self.width
		mod_width = aligned_width % 4
		
		if mod_width != 0:
			aligned_width += 4 - mod_width
			
		# Calculate the offset of the pixel from the start of the data.
		# Rows of pixels are stored upside down, so the offset is calculated
		# from the end of the data backwards
		pixel_offset = self.__offset + (self.__image_size - ((y + 1) * aligned_width)) + x
		
		# Get the data at the specified index
		return self.get_palette_color(self.__data[pixel_offset])

	def __get_pixel_color16(self, x, y):
		"""Get the colour of the specified pixel from a 16-bit bitmap."""
		
		# Calculate the number of bytes in each pixel
		pixel_byte_width = self.__bits_per_pixel // 8
		
		# Calculate the width of each row in bytes including the padding added to align
		# to 4-byte boundaries
		aligned_width = self.width * pixel_byte_width
		mod_width = aligned_width % 4
		
		if mod_width != 0:
			aligned_width += 4 - mod_width
		
		# Calculate the offset of the pixel from the start of the data.
		# Rows of pixels are stored upside down, so the offset is calculated
		# from the end of the data backwards
		pixel_offset = self.__offset + (self.__image_size - ((y + 1) * aligned_width)) + (x * pixel_byte_width)

		# Extract the bytes of data comprising the pixel
		return self.__data[pixel_offset:pixel_offset + pixel_byte_width]
		
	def __get_pixel_color24(self, x, y):
		"""Get the colour of the specified pixel from a 24-bit bitmap."""
		
		# Calculate the number of bytes in each pixel
		pixel_byte_width = self.__bits_per_pixel // 8
		
		# Calculate the width of each row in bytes including the padding added to align
		# to 4-byte boundaries
		aligned_width = self.width * pixel_byte_width
		mod_width = aligned_width % 4
		
		if mod_width != 0:
			aligned_width += 4 - mod_width
		
		# Calculate the offset of the pixel from the start of the data.
		# Rows of pixels are stored upside down, so the offset is calculated
		# from the end of the data backwards
		pixel_offset = self.__offset + (self.__image_size - ((y + 1) * aligned_width)) + (x * pixel_byte_width)

		# Extract the bytes of data comprising the pixel
		return self.__data[pixel_offset:pixel_offset + pixel_byte_width]
		
	def get_palette_color(self, index):
		"""Get the colour stored in the palette at the specified index."""
		colorOffset = self.__palette_offset + (index * 4)
		color = self.__data[colorOffset:colorOffset + 3]
		return color
		
	def get_pixel_red(self, x, y):
		"""Get the red component of the pixel at the specified co-ordinates."""
		# Get the red component of the pixel
		return ord(self.get_pixel_color(x, y)[0:1])
		
	def get_pixel_green(self, x, y):
		"""Get the green component of the pixel at the specified co-ordinates."""
		# Get the green component of the pixel
		return ord(self.get_pixel_color(x, y)[1:2])
		
	def get_pixel_blue(self, x, y):
		"""Get the blue component of the pixel at the speciied co-ordinates."""
		# Get the blue component of the pixel
		return ord(self.get_pixel_color(x, y)[2:3])

			
	def output(self):
		"""Print various information about the bitmap."""
		print("BMP Header") 
		print(" - Identifier:            ", self.__identifier)
		print(" - Size:                  ", self.__size)
		print(" - Offset:                ", self.__offset)
		print("DIB Header")
		print(" - Size:                  ", self.__dib_header_size)
		print(" - Width:                 ", self.width)
		print(" - Height:                ", self.height)
		print(" - Color Planes:          ", self.__color_planes)
		print(" - Bits Per Pixel:        ", self.__bits_per_pixel)
		print(" - Compression Method:    ", self.__compression_method)
		print(" - Image Size:            ", self.__image_size)
		print(" - Horizontal Resolution: ", self.__horizontal_resolution)
		print(" - Vertical Resolution:   ", self.__vertical_resolution)
		print(" - Colors in Palette:     ", self.__colors_in_palette)
		print(" - Important Colors Used: ", self.__important_colors_used)
		print("More Info")
		print(" - Name:                  ", self.__filename)
		print(" - Palette offset:        ", self.__palette_offset)
		

def str_to_integer(data):
	"""Convert a stream of bytes representing a number into a single integer."""
	value = 0
	i = 0
	
	for char in data:
		value += (char << i)
		i += 8
	
	return value
