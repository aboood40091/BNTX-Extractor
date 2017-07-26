#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2016-2017 Stella/AboodXD

"""dds.py: DDS Header generator."""

def generateHeader(num_mipmaps, w, h, format_, size, compressed):
    hdr = bytearray(128)

    if format_ == 28:  # RGBA8
        fmtbpp = 4
        has_alpha = 1
        rmask = 0x000000ff
        gmask = 0x0000ff00
        bmask = 0x00ff0000
        amask = 0xff000000

    elif format_ == 24:  # RGB10A2
        fmtbpp = 4
        has_alpha = 1
        rmask = 0x000003ff
        gmask = 0x000ffc00
        bmask = 0x3ff00000
        amask = 0xc0000000

    elif format_ == 85:  # RGB565
        fmtbpp = 2
        has_alpha = 0
        rmask = 0x0000f800
        gmask = 0x000007e0
        bmask = 0x0000001f
        amask = 0x00000000

    elif format_ == 86:  # RGB5A1
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x00007c00
        gmask = 0x000003e0
        bmask = 0x0000001f
        amask = 0x00008000

    elif format_ == 115:  # RGBA4
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x00000f00
        gmask = 0x000000f0
        bmask = 0x0000000f
        amask = 0x0000f000

    elif format_ == 61:  # L8
        fmtbpp = 1
        has_alpha = 0
        rmask = 0x000000ff
        gmask = 0x000000ff
        bmask = 0x000000ff
        amask = 0x00000000

    elif format_ == 49:  # L8A8
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x000000ff
        gmask = 0x000000ff
        bmask = 0x000000ff
        amask = 0x0000ff00

    elif format_ == 112:  # L4A4
        fmtbpp = 1
        has_alpha = 1
        rmask = 0x0000000f
        gmask = 0x0000000f
        bmask = 0x0000000f
        amask = 0x000000f0

    flags = 0x00000001 | 0x00001000 | 0x00000004 | 0x00000002

    caps = 0x00001000

    if num_mipmaps == 0:
        num_mipmaps = 1
    elif num_mipmaps != 1:
        flags |= 0x00020000
        caps |= 0x00000008 | 0x00400000

    if not compressed:
        flags |= 0x00000008

        if (fmtbpp == 1 and not has_alpha) or format_ == 49:  # LUMINANCE
            pflags = 0x00020000

        elif fmtbpp == 1 and has_alpha:
            pflags = 0x00000002

        else:  # RGB
            pflags = 0x00000040

        if has_alpha and fmtbpp != 1:
            pflags |= 0x00000001

        size = w * fmtbpp

    else:
        flags |= 0x00080000
        pflags = 0x00000004

        if format_ == "ETC1":
            fourcc = b'ETC1'
        elif format_ == "BC1":
            fourcc = b'DXT1'
        elif format_ == "BC2":
            fourcc = b'DXT3'
        elif format_ == "BC3":
            fourcc = b'DXT5'
        elif format_ == "BC4U":
            fourcc = b'ATI1'
        elif format_ == "BC4S":
            fourcc = b'BC4S'
        elif format_ == "BC5U":
            fourcc = b'ATI2'
        elif format_ == "BC5S":
            fourcc = b'BC5S'
        elif format_ in ["BC6H_UF16", "BC6H_SF16", "BC7", "BC7_SRGB"]:
            fourcc = b'DX10'

    hdr[:4] = b'DDS '
    hdr[4:4 + 4] = 124 .to_bytes(4, 'little')
    hdr[8:8 + 4] = flags.to_bytes(4, 'little')
    hdr[12:12 + 4] = h.to_bytes(4, 'little')
    hdr[16:16 + 4] = w.to_bytes(4, 'little')
    hdr[20:20 + 4] = size.to_bytes(4, 'little')
    hdr[28:28 + 4] = num_mipmaps.to_bytes(4, 'little')
    hdr[76:76 + 4] = 32 .to_bytes(4, 'little')
    hdr[80:80 + 4] = pflags.to_bytes(4, 'little')

    if compressed:
        hdr[84:84 + 4] = fourcc
    else:
        hdr[88:88 + 4] = (fmtbpp << 3).to_bytes(4, 'little')

        hdr[92:92 + 4] = rmask.to_bytes(4, 'little')
        hdr[96:96 + 4] = gmask.to_bytes(4, 'little')
        hdr[100:100 + 4] = bmask.to_bytes(4, 'little')
        hdr[104:104 + 4] = amask.to_bytes(4, 'little')

    hdr[108:108 + 4] = caps.to_bytes(4, 'little')

    if format_ == "BC6H_UF16":
        hdr += bytearray(b"\x5F\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC6H_SF16":
        hdr += bytearray(b"\x60\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC7":
        hdr += bytearray(b"\x62\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC7_SRGB":
        hdr += bytearray(b"\x63\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    return hdr
