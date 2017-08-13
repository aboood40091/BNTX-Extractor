#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BNTX Extractor
# Version 0.4
# Copyright © 2017 Stella/AboodXD

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


formats = {0x0b01: 'R8_G8_B8_A8_UNORM',
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

BCn_formats = [0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20]

ASTC_formats = [0x2d, 0x2e, 0x2f, 0x30,
                0x31, 0x32, 0x33, 0x34,
                0x35, 0x36, 0x37, 0x38,
                0x39, 0x3a]

blk_dims = {0x2d: (4, 4), 0x2e: (5, 4), 0x2f: (5, 5), 0x30: (6, 5),
            0x31: (6, 6), 0x32: (8, 5), 0x33: (8, 6), 0x34: (8, 8),
            0x35: (10, 5), 0x36: (10, 6), 0x37: (10, 8), 0x38: (10, 10),
            0x39: (12, 10), 0x3a: (12, 12)}

bpps = {0xb: 4, 7: 2, 2: 1, 9: 2, 0x1a: 8,
        0x1b: 16, 0x1c: 16, 0x1d: 8, 0x1e: 16,
        0x1f: 16, 0x20: 16, 0x2d: 16, 0x2e: 16,
        0x2f: 16, 0x30: 16, 0x31: 16, 0x32: 16,
        0x33: 16, 0x34: 16, 0x35: 16, 0x36: 16,
        0x37: 16, 0x38: 16, 0x39: 16, 0x3a: 16}


def bytes_to_string(byte):
    string = b''
    char = byte[:1]
    i = 1

    while char != b'\x00':
        string += char
        if i == len(byte): break  # Prevent it from looping forever

        char = byte[i:i + 1]
        i += 1

    return (string.decode('utf-8'))


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
        super().__init__(bom + '4siqI2H3I2iI2i6I3iI3q')

    def data(self, data, pos):
        (self.magic,
         self.size_,
         self.size_2,
         self.unk10,
         self.unk14,
         self.numMips,
         self.unk18,
         self.format_,
         self.unk20,
         self.width,
         self.height,
         self.unk2C,
         self.numFaces,
         self.numChannels,
         self.unk38,
         self.unk3C,
         self.unk40,
         self.unk44,
         self.unk48,
         self.unk4C,
         self.imageSize,
         self.blkSize,
         self.compSel,
         self.type_,
         self.nameAddr,
         self.unk68,
         self.ptrAddr) = self.unpack_from(data, pos)

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

    if bytes_to_string(header.magic) != "BNTX":
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

        nameLen = struct.unpack(bom + 'H', f[info.nameAddr:info.nameAddr+2])[0]
        name = bytes_to_string(f[info.nameAddr+2:info.nameAddr+2+nameLen])

        print("")
        print("Image " + str(i+1) + " name: " + name)

        compSel = []
        compSels = {0: "0", 1: "1", 2: "Red", 3: "Green", 4: "Blue", 5: "Alpha"}
        for i in range(4):
            value = (info.compSel >> (8 * (3-i))) & 0xff
            if value == 0: value = len(compSel) + 2
            compSel.append(value)

        types = {0: "1D", 1: "2D", 2: "3D", 3: "Cubemap", 8: "CubemapFar"}
        if info.type_ not in types:
            types[info.type_] = "Unknown"

        print("Number of Mipmaps: " + str(info.numMips - 1))
        if info.format_ in formats:
            print("Format: " + formats[info.format_])
        else:
            print("Format: " + str(info.format_))
        print("Width: " + str(info.width))
        print("Height: " + str(info.height))
        print("Number of faces: " + str(info.numFaces))
        print("Number of channels: " + str(info.numChannels))
        print("Image Size: " + str(info.imageSize))
        print("Alignment?: " + str(info.blkSize))
        if info.numChannels:
            if info.numChannels >= 1:
                print("Channel 1: " + compSels[compSel[3]])
            if info.numChannels >= 2:
                print("Channel 2: " + compSels[compSel[2]])
            if info.numChannels >= 3:
                print("Channel 3: " + compSels[compSel[1]])
            if info.numChannels >= 4:
                print("Channel 4: " + compSels[compSel[0]])
        print("Image type: " + types[info.type_])
        dataAddr = struct.unpack(bom + 'q', f[info.ptrAddr:info.ptrAddr+8])[0]

        tex = TexInfo()
        tex.name = name
        tex.numMips = info.numMips
        tex.width = info.width
        tex.height = info.height
        tex.format = info.format_
        tex.numFaces = info.numFaces
        tex.numChannels = info.numChannels
        tex.compSel = compSel
        tex.blkSize = info.blkSize
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
            elif tex.format == 0x2001:
                format_ = "BC7"
            elif tex.format == 0x2006:
                format_ = "BC7_SRGB"

            result = swizzle.deswizzle(tex.width, tex.height, tex.format, tex.data)

            if (tex.format >> 8) in BCn_formats:
                size = ((tex.width + 3) >> 2) * ((tex.height + 3) >> 2) * bpps[tex.format >> 8]
            elif (tex.format >> 8) in ASTC_formats:
                blkWidth, blkHeight = blk_dims[tex.format >> 8]
                size = ((tex.width + blkWidth - 1) // blkWidth) * ((tex.height + blkHeight - 1) // blkHeight) * bpps[tex.format >> 8]
            else:
                size = tex.width * tex.height * bpps[tex.format >> 8]

            assert len(result) >= size

            result = result[:size]

            if (tex.format >> 8) in ASTC_formats:
                with open(tex.name + ".astc", "wb+") as output:
                    output.write(b'\x13\xAB\xA1\x5C')
                    output.write(blkWidth.to_bytes(1, "little"))
                    output.write(blkHeight.to_bytes(1, "little"))
                    output.write(b'\x01')
                    output.write(tex.width.to_bytes(3, "little"))
                    output.write(tex.height.to_bytes(3, "little"))
                    output.write(1 .to_bytes(3, "little"))
                    output.write(result)

            else:
                hdr = dds.generateHeader(1, tex.width, tex.height, format_, list(reversed(tex.compSel)), size, (tex.format >> 8) in BCn_formats)

                with open(tex.name + ".dds", "wb+") as output:
                    output.write(hdr)
                    output.write(result)
        else:
            print("")
            print("Can't convert: " + tex.name)
            if tex.format not in formats:
                print("Format is not supported.")
            else:
                print("Unsupported number of faces.")


def main():
    print("BNTX Extractor v0.4")
    print("(C) 2017 Stella/AboodXD")

    input_ = sys.argv[1]

    with open(input_, "rb") as inf:
        inb = inf.read()

    textures = readBNTX(inb)
    saveTextures(textures)


if __name__ == '__main__':
    main()
