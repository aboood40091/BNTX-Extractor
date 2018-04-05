#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BNTX Extractor
# Version 0.6
# Copyright © 2017-2018 AboodXD

# This file is part of BNTX Extractor.

# BNTX Extractor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BNTX Extractor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""bntx_extract.py: Decode BNTX images."""

import struct, sys

import dds
import swizzle


formats = {
    0x0b01: 'R8_G8_B8_A8_UNORM',
    0x0b06: 'R8_G8_B8_A8_SRGB',
    0x0701: 'R5_G6_B5_UNORM',
    0x0201: 'R8_UNORM',
    0x0901: 'R8_G8_UNORM',
    0x1a01: 'BC1_UNORM',
    0x1a06: 'BC1_SRGB',
    0x1b01: 'BC2_UNORM',
    0x1b06: 'BC2_SRGB',
    0x1c01: 'BC3_UNORM',
    0x1c06: 'BC3_SRGB',
    0x1d01: 'BC4_UNORM',
    0x1d02: 'BC4_SNORM',
    0x1e01: 'BC5_UNORM',
    0x1e02: 'BC5_SNORM',
    0x1f01: 'BC6H_UF16',
    0x1f02: 'BC6H_SF16',
    0x2001: 'BC7_UNORM',
    0x2006: 'BC7_SRGB',
    0x2d01: 'ASTC4x4',
    0x2d06: 'ASTC4x4 SRGB',
    0x2e01: 'ASTC5x4',
    0x2e06: 'ASTC5x4 SRGB',
    0x2f01: 'ASTC5x5',
    0x2f06: 'ASTC5x5 SRGB',
    0x3001: 'ASTC6x5',
    0x3006: 'ASTC6x5 SRGB',
    0x3101: 'ASTC6x6',
    0x3106: 'ASTC6x6 SRGB',
    0x3201: 'ASTC8x5',
    0x3206: 'ASTC8x5 SRGB',
    0x3301: 'ASTC8x6',
    0x3306: 'ASTC8x6 SRGB',
    0x3401: 'ASTC8x8',
    0x3406: 'ASTC8x8 SRGB',
    0x3501: 'ASTC10x5',
    0x3506: 'ASTC10x5 SRGB',
    0x3601: 'ASTC10x6',
    0x3606: 'ASTC10x6 SRGB',
    0x3701: 'ASTC10x8',
    0x3706: 'ASTC10x8 SRGB',
    0x3801: 'ASTC10x10',
    0x3806: 'ASTC10x10 SRGB',
    0x3901: 'ASTC12x10',
    0x3906: 'ASTC12x10 SRGB',
    0x3a01: 'ASTC12x12',
    0x3a06: 'ASTC12x12 SRGB'
}

BCn_formats = swizzle.BCn_formats
ASTC_formats = swizzle.ASTC_formats
blk_dims = swizzle.blk_dims


def bytes_to_string(data, end=0):
    if not end:
        end = data.find(b'\0')
        if end == -1:
            return data.decode('utf-8')

    return data[:end].decode('utf-8')


class BNTXHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '8si2Hi2xh2i')

    def data(self, data, pos):
        (self.magic,
         self.version,
         self.bom,
         self.revision,
         self.fileNameAddr,
         self.strAddr,
         self.relocAddr,
         self.fileSize) = self.unpack_from(data, pos)


class NXHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4sI3qI')

    def data(self, data, pos):
        (self.magic,
         self.count,
         self.infoPtrAddr,
         self.dataBlkAddr,
         self.dictAddr,
         self.strDictSize) = self.unpack_from(data, pos)


class BRTIInfo(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4siq2b3H3I5i6I4i3q')

    def data(self, data, pos):
        (self.magic,
         self.size_,
         self.size_2,
         self.tileMode,
         self.dim,
         self.flags,
         self.swizzle,
         self.numMips,
         self.unk18,
         self.format_,
         self.unk20,
         self.width,
         self.height,
         self.unk2C,
         self.numFaces,
         self.sizeRange,
         self.unk38,
         self.unk3C,
         self.unk40,
         self.unk44,
         self.unk48,
         self.unk4C,
         self.imageSize,
         self.alignment,
         self.compSel,
         self.type_,
         self.nameAddr,
         self.parentAddr,
         self.ptrsAddr) = self.unpack_from(data, pos)


class TexInfo:
    pass


def readBNTX(f):
    pos = 0

    if f[0xc:0xe] == b'\xFF\xFE':
        bom = '<'

    elif f[0xc:0xe] == b'\xFE\xFF':
        bom = '>'

    else:
        raise ValueError("Invalid BOM!")

    header = BNTXHeader(bom)
    header.data(f, pos)
    pos += header.size

    if bytes_to_string(header.magic, 4) != "BNTX":
        raise ValueError("Invalid file header!")

    print("")
    print("File name: " + bytes_to_string(f[header.fileNameAddr:header.fileNameAddr+12]))

    nx = NXHeader(bom)
    nx.data(f, pos)
    pos += nx.size

    print("")
    print("Textures count: " + str(nx.count))

    textures = []

    for i in range(nx.count):
        pos = nx.infoPtrAddr + i * 8

        pos = struct.unpack(bom + 'q', f[pos:pos+8])[0]

        info = BRTIInfo(bom)
        info.data(f, pos)

        nameLen = struct.unpack(bom + 'H', f[info.nameAddr:info.nameAddr + 2])[0]
        name = bytes_to_string(f[info.nameAddr + 2:info.nameAddr + 2 + nameLen], nameLen)

        print("")
        print("Image " + str(i + 1) + " name: " + name)

        compSel = []
        compSels = {0: "0", 1: "1", 2: "Red", 3: "Green", 4: "Blue", 5: "Alpha"}
        for i in range(4):
            value = (info.compSel >> (8 * (3 - i))) & 0xff
            if value == 0:
                value = len(compSel) + 2

            compSel.append(value)

        types = {0: "1D", 1: "2D", 2: "3D", 3: "Cubemap", 8: "CubemapFar"}
        if info.type_ not in types:
            types[info.type_] = "Unknown"

        tileModes = {0: "TILING_MODE_PITCH", 1: "TILING_MODE_TILED"}

        print("TileMode: " + tileModes[info.tileMode])
        print("Dimensions: " + str(info.dim))
        print("Flags: " + str(info.flags))
        print("Swizzle: " + str(info.swizzle))
        print("Number of Mipmaps: " + str(info.numMips - 1))

        if info.format_ in formats:
            print("Format: " + formats[info.format_])

        else:
            print("Format: " + str(info.format_))

        print("Width: " + str(info.width))
        print("Height: " + str(info.height))
        print("Number of faces: " + str(info.numFaces))
        print("Size Range: " + str(info.sizeRange))
        print("Block Height: " + str(1 << info.sizeRange))
        print("Image Size: " + str(info.imageSize))
        print("Alignment: " + str(info.alignment))
        print("Channel 1: " + compSels[compSel[3]])
        print("Channel 2: " + compSels[compSel[2]])
        print("Channel 3: " + compSels[compSel[1]])
        print("Channel 4: " + compSels[compSel[0]])
        print("Image type: " + types[info.type_])

        dataAddr = struct.unpack(bom + 'q', f[info.ptrsAddr:info.ptrsAddr + 8])[0]
        mipOffsets = {0: 0}

        for i in range(1, info.numMips):
            mipOffset = struct.unpack(bom + 'q', f[info.ptrsAddr + (i * 8):info.ptrsAddr + (i * 8) + 8])[0]
            mipOffsets[i] = mipOffset - dataAddr

        tex = TexInfo()
        tex.name = name
        tex.tileMode = info.tileMode
        tex.numMips = info.numMips
        tex.mipOffsets = mipOffsets
        tex.width = info.width
        tex.height = info.height
        tex.format = info.format_
        tex.numFaces = info.numFaces
        tex.sizeRange = info.sizeRange
        tex.compSel = compSel
        tex.alignment = info.alignment
        tex.type = info.type_
        tex.data = f[dataAddr:dataAddr+info.imageSize]

        textures.append(tex)

    return textures


def saveTextures(textures):
    for tex in textures:
        if tex.format in formats and tex.numFaces < 2:
            if (tex.format >> 8) == 0xb:
                format_ = 28

            elif tex.format == 0x701:
                format_ = 85

            elif tex.format == 0x201:
                format_ = 61

            elif tex.format == 0x901:
                format_ = 49

            elif (tex.format >> 8) == 0x1a:
                format_ = "BC1"

            elif (tex.format >> 8) == 0x1b:
                format_ = "BC2"

            elif (tex.format >> 8) == 0x1c:
                format_ = "BC3"

            elif tex.format == 0x1d01:
                format_ = "BC4U"

            elif tex.format == 0x1d02:
                format_ = "BC4S"

            elif tex.format == 0x1e01:
                format_ = "BC5U"

            elif tex.format == 0x1e02:
                format_ = "BC5S"

            elif tex.format == 0x1f01:
                format_ = "BC6H_UF16"

            elif tex.format == 0x1f02:
                format_ = "BC6H_SF16"

            elif (tex.format >> 8) == 0x20:
                format_ = "BC7"

            result = swizzle.deswizzle(tex.width, tex.height, tex.format, tex.tileMode, tex.alignment, tex.sizeRange, tex.data)
            size = len(result)

            if (tex.format >> 8) in ASTC_formats:
                blkWidth, blkHeight = blk_dims[tex.format >> 8]

                outBuffer = b''.join([
                    b'\x13\xAB\xA1\x5C', blkWidth.to_bytes(1, "little"),
                    blkHeight.to_bytes(1, "little"), b'\1',
                    tex.width.to_bytes(3, "little"),
                    tex.height.to_bytes(3, "little"), b'\1\0\0',
                    result,
                ])

                with open(tex.name + ".astc", "wb+") as output:
                    output.write(outBuffer)

            else:
                hdr = dds.generateHeader(1, tex.width, tex.height, format_, list(reversed(tex.compSel)), size, (tex.format >> 8) in BCn_formats)

                with open(tex.name + ".dds", "wb+") as output:
                    output.write(b''.join([hdr, result]))

        else:
            print("")
            print("Can't convert: " + tex.name)

            if tex.format not in formats:
                print("Format is not supported.")

            else:
                print("Unsupported number of faces.")


def main():
    print("BNTX Extractor v0.6")
    print("(C) 2017-2018 AboodXD")

    input_ = sys.argv[1]

    with open(input_, "rb") as inf:
        inb = inf.read()

    textures = readBNTX(inb)
    saveTextures(textures)


if __name__ == '__main__':
    main()
