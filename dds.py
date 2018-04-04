#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2016-2017 AboodXD

"""dds.py: DDS Header generator."""

dx10_formats = ["BC4U", "BC4S", "BC5U", "BC5S", "BC6H_UF16", "BC6H_SF16", "BC7"]

def generateHeader(num_mipmaps, w, h, format_, compSel, size, compressed):
    hdr = bytearray(128)

    luminance = False
    RGB = False

    has_alpha = True

    if format_ == 28:  # ABGR8
        RGB = True
        compSels = {2: 0x000000ff, 3: 0x0000ff00, 4: 0x00ff0000, 5: 0xff000000, 1: 0}
        fmtbpp = 4
        

    elif format_ == 24:  # A2RGB10
        RGB = True
        compSels = {2: 0x3ff00000, 3: 0x000ffc00, 4: 0x000003ff, 5: 0xc0000000, 1: 0}
        fmtbpp = 4

    elif format_ == 85:  # RGB565
        RGB = True
        compSels = {2: 0x0000f800, 3: 0x000007e0, 4: 0x0000001f, 5: 0, 1: 0}
        fmtbpp = 2
        has_alpha = False

    elif format_ == 86:  # A1RGB5
        RGB = True
        compSels = {2: 0x00007c00, 3: 0x000003e0, 4: 0x0000001f, 5: 0x00008000, 1: 0}
        fmtbpp = 2

    elif format_ == 115:  # ARGB4
        RGB = True
        compSels = {2: 0x00000f00, 3: 0x000000f0, 4: 0x0000000f, 5: 0x0000f000, 1: 0}
        fmtbpp = 2

    elif format_ == 61:  # L8
        luminance = True
        compSels = {2: 0x000000ff, 3: 0, 4: 0, 5: 0, 1: 0}
        fmtbpp = 1
        if compSel[3] != 2:
            has_alpha = False

    elif format_ == 49:  # A8L8
        luminance = True
        compSels = {2: 0x000000ff, 3: 0x0000ff00, 4: 0, 5: 0, 1: 0}
        fmtbpp = 2

    elif format_ == 112:  # A4L4
        luminance = True
        compSels = {2: 0x0000000f, 3: 0x000000f0, 4: 0, 5: 0, 1: 0}
        fmtbpp = 1

    flags = 0x00000001 | 0x00001000 | 0x00000004 | 0x00000002

    caps = 0x00001000

    if num_mipmaps == 0:
        num_mipmaps = 1
    elif num_mipmaps != 1:
        flags |= 0x00020000
        caps |= 0x00000008 | 0x00400000

    if not compressed:
        flags |= 0x00000008

        a = False

        if compSel[0] != 2 and compSel[1] != 2 and compSel[2] != 2 and compSel[3] == 2: # ALPHA
            a = True
            pflags = 0x00000002

        elif luminance:  # LUMINANCE
            pflags = 0x00020000

        elif RGB:  # RGB
            pflags = 0x00000040

        else: # Not possible...
            return b''

        if has_alpha and not a:
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
        elif format_ in dx10_formats:
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

        hdr[92:92 + 4] = compSels[compSel[0]].to_bytes(4, 'little')
        hdr[96:96 + 4] = compSels[compSel[1]].to_bytes(4, 'little')
        hdr[100:100 + 4] = compSels[compSel[2]].to_bytes(4, 'little')
        hdr[104:104 + 4] = compSels[compSel[3]].to_bytes(4, 'little')

    hdr[108:108 + 4] = caps.to_bytes(4, 'little')

    if format_ == "BC4U":
        hdr += bytearray(b"\x50\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC4S":
        hdr += bytearray(b"\x51\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC5U":
        hdr += bytearray(b"\x53\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC5S":
        hdr += bytearray(b"\x54\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC6H_UF16":
        hdr += bytearray(b"\x5F\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC6H_SF16":
        hdr += bytearray(b"\x60\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC7":
        hdr += bytearray(b"\x62\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    return hdr
