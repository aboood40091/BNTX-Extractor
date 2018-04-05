from cpython cimport array
from cython cimport view
from libc.math cimport ceil
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy


ctypedef unsigned char u8
ctypedef unsigned int u32


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
    0x1a: (4, 4), 0x1b: (4, 4), 0x1c: (4, 4),
    0x1d: (4, 4), 0x1e: (4, 4), 0x1f: (4, 4),
    0x20: (4, 4), 0x2d: (4, 4), 0x2e: (5, 4),
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


cdef u32 DIV_ROUND_UP(u32 n, u32 d):
    return (n + d - 1) // d


cdef u32 round_up(u32 x, u32 y):
    return ((x - 1) | (y - 1)) + 1


cpdef bytearray deswizzle(u32 width, u32 height, u32 format_, u32 tileMode, u32 alignment, int size_range, data_):
    assert 0 <= size_range <= 5

    cdef:
        u32 block_height = 1 << size_range

        u32 formatUpper = format_ >> 8
        u32 bpp = bpps[formatUpper]

        u32 blkWidth, blkHeight, min_pitch, pitch

    if formatUpper in blk_dims:
        blkWidth, blkHeight = blk_dims[formatUpper]
        width = DIV_ROUND_UP(width, blkWidth)
        height = DIV_ROUND_UP(height, blkHeight)

    if tileMode == 0:
        min_pitch = DIV_ROUND_UP(width * bpp, 8)
        pitch = round_up(min_pitch, alignment * 64)

    else:
        pitch = width

    cdef:
        u32 dataSize = len(data_)

        array.array dataArr = array.array('B', data_)
        u8 *data = dataArr.data.as_uchars
        u8 *result = <u8 *>malloc(width * height * bpp)

        u32 x, y, z, pos, pos_

    try:
        for y in range(height):
            for x in range(width):
                if tileMode == 0:
                    pos = (y * pitch + x) * bpp

                else:
                    pos = getAddrBlockLinear(x, y, width, bpp, 0, block_height)

                pos_ = (y * width + x) * bpp

                if pos + bpp <= dataSize:
                    for z in range(bpp):
                        result[pos_ + z] = data[pos + z]

        return bytearray(<u8[:width * height * bpp]>result)

    finally:
        free(result)


cdef u32 getAddrBlockLinear(u32 x, u32 y, u32 image_width, u32 bytes_per_pixel, u32 base_address, u32 block_height):
    """
    From the Tegra X1 TRM
    """
    cdef:
        u32 image_width_in_gobs = <u32>ceil(image_width * bytes_per_pixel / 64)

        u32 GOB_address = (base_address
                           + (y // (8 * block_height)) * 512 * block_height * image_width_in_gobs
                           + (x * bytes_per_pixel // 64) * 512 * block_height
                           + (y % (8 * block_height) // 8) * 512)

    x *= bytes_per_pixel

    cdef u32 Address = (GOB_address + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64
                        + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16))

    return Address
