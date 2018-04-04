from math import ceil


BCn_formats = [
    0x1a, 0x1b, 0x1c, 0x1d,
    0x1e, 0x1f, 0x20,
]

ASTC_formats = [
    0x2d, 0x2e, 0x2f, 0x30,
    0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38,
    0x39, 0x3a,
]

blk_dims = {  # format -> (blkWidth, blkHeight)
    0x2d: (4, 4), 0x2e: (5, 4),
    0x2f: (5, 5), 0x30: (6, 5),
    0x31: (6, 6), 0x32: (8, 5),
    0x33: (8, 6), 0x34: (8, 8),
    0x35: (10, 5), 0x36: (10, 6),
    0x37: (10, 8), 0x38: (10, 10),
    0x39: (12, 10), 0x3a: (12, 12),
}

bpps = {  # format -> bytes_per_pixel
    0x0b: 0x04, 0x07: 0x02, 0x02: 0x01, 0x09: 0x02, 0x1a: 0x08,
    0x1b: 0x10, 0x1c: 0x10, 0x1d: 0x08, 0x1e: 0x10, 0x1f: 0x10,
    0x20: 0x10, 0x2d: 0x10, 0x2e: 0x10, 0x2f: 0x10, 0x30: 0x10,
    0x31: 0x10, 0x32: 0x10, 0x33: 0x10, 0x34: 0x10, 0x35: 0x10,
    0x36: 0x10, 0x37: 0x10, 0x38: 0x10, 0x39: 0x10, 0x3a: 0x10,
}


def _swizzle(width, height, format_, size_range, data, dataSize, toSwizzle):
    if (format_ >> 8) in BCn_formats:
        width = (width + 3) // 4
        height = (height + 3) // 4

    elif (format_ >> 8) in ASTC_formats:
        blkWidth, blkHeight = blk_dims[format_ >> 8]
        width = (width + blkWidth  - 1) // blkWidth
        height = (height + blkHeight - 1) // blkHeight

    assert 0 <= size_range <= 5

    block_height = 1 << size_range

    bpp = bpps[format_ >> 8]
    result = bytearray(dataSize)

    for y in range(height):
        for x in range(width):
            pos = getAddrBlockLinear(x, y, width, bpp, 0, block_height)
            pos_ = (y * width + x) * bpp

            if pos_ + bpp <= dataSize and pos + bpp <= dataSize:
                if toSwizzle:
                    result[pos:pos + bpp] = data[pos_:pos_ + bpp]

                else:
                    result[pos_:pos_ + bpp] = data[pos:pos + bpp]

    return result


def deswizzle(width, height, format_, size_range, data):
    return _swizzle(width, height, format_, size_range, data, len(data), 0)


def swizzle(width, height, format_, size_range, data):
    return _swizzle(width, height, format_, size_range, data, len(data), 1)


def getAddrBlockLinear(x, y, image_width, bytes_per_pixel, base_address, block_height):
    """
    From the Tegra X1 TRM
    """
    image_width_in_gobs = ceil(image_width * bytes_per_pixel / 64)

    GOB_address = (base_address
                   + (y // (8 * block_height)) * 512 * block_height * image_width_in_gobs
                   + (x * bytes_per_pixel // 64) * 512 * block_height
                   + (y % (8 * block_height) // 8) * 512)

    x *= bytes_per_pixel

    Address = (GOB_address + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64
               + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16))

    return Address
