#!/usr/bin/env python

##@file bmp2hex.py
#  @ingroup util
#	A script for converting a 1-bit bitmap to HEX for use in an Arduino sketch.
#
#	The BMP format is well publicized. The byte order of the actual bitmap is a
#	little unusual. The image is stored bottom to top, left to right. In addition,
#	The pixel rows are rounded to DWORDS which are 4 bytes long. SO, to convert this
#   to left to right, top to bottom, no byte padding. We have to do some calculations
#	as we loop through the rows and bytes of the image. See below for more
#
#	Usage: 
#	>>>bmp2hex.py [-i] [-r] [-n] [-d] [-x] [-w <bytes>] [-b <size-bytes>] <infile> <tablename>
#	
#	@param infile		The file to convert.
#	@param tablename	The name of the table to create
#	@param raw			"-r", bitmap written as raw table [optional]
#	@param invert		"-i", to invert image pixel colors [optional] 
#	@param tablewidth	"-w <bytes>, The number of characters for each row of the output table [optional]
#	@param sizebytes	"-b <bytes>, Bytes = 0, 1, or 2. 0 = auto. 1 = 1-byte for sizes. 2 = 2-byte sizes (big endian) [optional]
#	@param named		"-n", use a names structure [optional]
#	@param double		"-d", use double bytes rather than single ones [optional]
#	@param xbm			"-x", use XBM format (bits reversed in byte) [optional]
#	@param version		"-v", returns version number
#	
#	@author Robert Gallup 2016-02
#
#	Author:    Robert Gallup (bg@robertgallup.com)
#	License:   MIT Opensource License
#
#	Copyright 2016-2018 Robert Gallup 
#

import sys, array, os, textwrap, math, random, argparse

class DEFAULTS(object):
	STRUCTURE_NAME = 'GFXMeta'
	VERSION = '2.3'

def main ():

	# Default parameters
	infile = ""
	tablename = ""
	tablewidth = 16
	sizebytes = 0
	invert = False
	raw = False
	named = False
	double = False
	xbm = False
	version = False
	k210 = False
	k210bin = False

	# Set up parser and handle arguments
	parser = argparse.ArgumentParser()
	# parser.add_argument ("infile", help="The BMP file(s) to convert", type=argparse.FileType('r'), nargs='+', default=['-'])
	parser.add_argument ("infile", help="The BMP file(s) to convert", type=argparse.FileType('r'), nargs='*', default=['-'])
	parser.add_argument ("-r", "--raw", help="Outputs all data in raw table format", action="store_true")
	parser.add_argument ("-k", "--k210", help="Outputs as K210 AI RGB format", action="store_true")
	parser.add_argument ("-kbin", "--k210bin", help="Outputs as K210 RGB565 (pix swap) format", action="store_true")
	parser.add_argument ("-i", "--invert", help="Inverts bitmap pixels", action="store_true")
	parser.add_argument ("-w", "--width", help="Output table width in hex bytes [default: 16]", type=int)
	parser.add_argument ("-b", "--bytes", help="Byte width of BMP sizes: 0=auto, 1, or 2 (big endian) [default: 0]", type=int)
	parser.add_argument ("-n", "--named", help="Uses named structure (" + DEFAULTS.STRUCTURE_NAME + ") for data", action="store_true")
	parser.add_argument ("-d", "--double", help="Defines data in 'words' rather than bytes", action="store_true")
	parser.add_argument ("-x", "--xbm", help="Uses XBM bit order (low order bit is first pixel of byte)", action="store_true")
	parser.add_argument ("-v", "--version", help="Returns the current bmp2hex version", action="store_true")
	args = parser.parse_args()

	# Required arguments
	infile = args.infile

	# Options
	if args.raw:
		raw = args.raw
	if args.invert:
		invert = args.invert
	if args.width:
		tablewidth = args.width
	if args.bytes:
		sizebytes = args.bytes % 3
	if args.named:
		named = args.named
	if args.double:
		double = args.double
	if args.xbm:
		xbm = args.xbm
	if args.version:
		print ('// bmp2hex version ' + DEFAULTS.VERSION)
	if args.k210:
		k210 = args.k210
	if args.k210bin:
		k210bin = args.k210bin
		
	# Output named structure, if requested
	if (named):
		print ('struct ' + DEFAULTS.STRUCTURE_NAME + ' {')
		print ('  unsigned   int width;')
		print ('  unsigned   int height;')
		print ('  unsigned   int bitDepth;')
		print ('             int baseline;')
		print ('  ' + ('uint8_t   *', 'uint16_t  *')[double] + 'pixel_data;')
		print ('};')
		print ('')

	# Do the work
	for f in args.infile:
		if f == '-':
			sys.exit()
		bmp2hex(f.name, tablewidth, sizebytes, invert, raw, named, double, xbm, k210, k210bin)

# Utility function. Return a long int from array (little endian)
def getLONG(a, n):
	return (a[n+3] * (2**24)) + (a[n+2] * (2**16)) + (a[n+1] * (2**8)) + (a[n])

# Utility function. Return an int from array (little endian)
def getINT(a, n):
	return ((a[n+1] * (2**8)) + (a[n]))

# Reverses pixels in byte
def reflect(a):
	r = 0
	for i in range(8):
		r <<= 1
		r |= (a & 0x01)
		a >>= 1
	return (r)

# Main conversion function
def bmp2hex(infile, tablewidth, sizebytes, invert, raw, named, double, xbm, k210, k210bin):

	# Set the table name to the uppercase root of the file name
	tablename = os.path.splitext(infile)[0].upper()

	# Convert tablewidth to characters from hex bytes
	tablewidth = int(tablewidth) * 6

	# Initilize output buffer
	outstring =  ''
	outR =  ''
	outG =  ''
	outB =  ''

	# Open File
	fin = open(os.path.expanduser(infile), "rb")
	uint8_tstoread = os.path.getsize(os.path.expanduser(infile))
	valuesfromfile = array.array('B')
	try:
		valuesfromfile.fromfile(fin, uint8_tstoread)
	finally:
		fin.close()

	# Get bytes from file
	values=valuesfromfile.tolist()

	# Exit if it's not a Windows BMP
	if ((values[0] != 0x42) or (values[1] != 0x4D)):
		sys.exit ("Error: Unsupported BMP format. Make sure your file is a Windows BMP.")

	# Calculate width, heigth
	dataOffset	= getLONG(values, 10)	# Offset to image data
	pixelWidth  = getLONG(values, 18)	# Width of image
	pixelHeight = getLONG(values, 22)	# Height of image
	bitDepth	= getINT (values, 28)	# Bits per pixel
	dataSize	= getLONG(values, 34)   # Size of raw data

	# Calculate line width in bytes and padded byte width (each row is padded to 4-byte multiples)
	byteWidth	= int(math.ceil(float(pixelWidth * bitDepth)/8.0))
	paddedWidth	= int(math.ceil(float(byteWidth)/4.0)*4.0)

	# For auto (sizebytes = 0), set sizebytes to 1 or 2, depending on size of the bitmap
	if (sizebytes==0):
		if (pixelWidth>255) or (pixelHeight>255):
			sizebytes = 2
		else:
			sizebytes = 1

	# The invert byte is set based on the invert command line flag (but, the logic is reversed for 1-bit files)
	invertbyte = 0xFF if invert else 0x00
	if (bitDepth == 1):
		invertbyte = invertbyte ^ 0xFF

	# Output the hex table declaration
	# Format depending on "raw" flag
	if k210:
		print("const unsigned char gImage_image[]  __attribute__((aligned(128))) ={")
	elif k210bin:
		#RGB565 bin, swap pixel
		k210bin = True	#dummy
	else:
		if (raw):
			print ('PROGMEM unsigned char const ' + tablename + ' [] = {')
			if (not (sizebytes%2)):
				print ("{0:#04X}".format((pixelWidth>>8) & 0xFF) + ", " + "{0:#04X}".format(pixelWidth & 0xFF) + ", " + \
					  "{0:#04X}".format((pixelHeight>>8) & 0xFF) + ", " + "{0:#04X}".format(pixelHeight & 0xFF) + ",")
			else:
				print ("{0:#04X}".format(pixelWidth & 0xFF) + ", " + "{0:#04X}".format(pixelHeight & 0xFF) + ",")

		elif (named):
			print ('PROGMEM ' + 'uint8_t const ' + tablename + '_PIXELS[] = {')

		elif (xbm):
			print ('#define ' + tablename + '_width ' + str(pixelWidth))
			print ('#define ' + tablename + '_height ' + str(pixelHeight))
			print ('PROGMEM uint8_t const ' + tablename + '_bits[] = {')

		else:
			print ('PROGMEM const struct {')
			print ('  unsigned int   width;')
			print ('  unsigned int   height;')
			print ('  unsigned int   bitDepth;')
			print ('  uint8_t        pixel_data[{0}];'.format(byteWidth * pixelHeight))
			print ('} ' + tablename + ' = {')
			print ('{0}, {1}, {2}, {{'.format(pixelWidth, pixelHeight, bitDepth))

	# Generate HEX bytes for pixel data in output buffer
	try:
		if k210bin:
			if (byteWidth//3)%2 != 0:
				raise Exception("Invalid width!")
			file = open(tablename + '.bin','wb')
			for i in range(pixelHeight):
				for j in range (byteWidth//6):
					ndx = dataOffset + ((pixelHeight-1-i) * paddedWidth) + j*6
					pix0_b = values[ndx+0] ^ invertbyte
					pix0_g = values[ndx+1] ^ invertbyte
					pix0_r = values[ndx+2] ^ invertbyte
					pix1_b = values[ndx+3] ^ invertbyte
					pix1_g = values[ndx+4] ^ invertbyte
					pix1_r = values[ndx+5] ^ invertbyte
					
					pix0 = (pix0_b>>3)|((pix0_g>>2)<<5)|((pix0_r>>3)<<(5+6))
					pix1 = (pix1_b>>3)|((pix1_g>>2)<<5)|((pix1_r>>3)<<(5+6))
					b0 = pix1&0xff;
					b1 = pix1>>8;
					b2 = pix0&0xff;
					b3 = pix0>>8;
					bs = bytes([b0, b1, b2, b3])
					#print("%x %x,"%(pix0,pix1))
					#print("%x %x %x %x"%(pix1&0xff, pix1>>8, pix0&0xff, pix0>>8))
					#print("%c%c%c%c"%(pix1&0xff, pix1>>8, pix0&0xff, pix0>>8))
					#tmp = struct.pack('BBBB',)
					file.write(bs)
			file.close()
			exit(0)
		else:
			for i in range(pixelHeight):
				for j in range (byteWidth):
					ndx = dataOffset + ((pixelHeight-1-i) * paddedWidth) + j
					v = values[ndx] ^ invertbyte
					if (xbm):
						v = reflect(v)
						# print ("{0:#04x}".format(v))
					outstring += "{0:#04x}".format(v) + ", "
					if (j%3 == 0):  #B
						outB += "{0:#04x}".format(v) + ", "
					elif (j%3 == 1): #G
						outG += "{0:#04x}".format(v) + ", " 
					else: #R
						outR += "{0:#04x}".format(v) + ", "
					
	# Wrap the output buffer. Print. Then, finish.
	finally:
		outstring = textwrap.fill(outstring[:-2], tablewidth)
		outR = textwrap.fill(outR[:-1], tablewidth)
		outG = textwrap.fill(outG[:-1], tablewidth)
		outB = textwrap.fill(outB[:-1], tablewidth)
		if k210:
			print ("  //R")
			print (outR)
			print ("  //G")
			print (outG)
			print ("  //B")
			print (outB)
		else:
			print (outstring)
		
		if k210:
			print ('};')
		elif k210bin:
			print("convert end")
		else:
			if (named):
				print ('};')
				print (DEFAULTS.STRUCTURE_NAME + ' const ' + tablename + ' = {{{0}, {1}, {2}, 0, '.format(pixelWidth, pixelHeight, bitDepth) + \
					 ('(uint8_t *)', '(uint16_t *)')[double] + tablename + "_PIXELS};\n\n")
			else:
				if (not (raw or xbm)):
					print ("}")
				print ("};")


# Only run if launched from commandline
if __name__ == '__main__': main()