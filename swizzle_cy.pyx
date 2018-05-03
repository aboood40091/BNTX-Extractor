from cpython cimport array
from cython cimport view
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy


ctypedef unsigned char u8
ctypedef unsigned int u32


cpdef u32 DIV_ROUND_UP(u32 n, u32 d):
    return (n + d - 1) // d


cdef u32 round_up(u32 x, u32 y):
    return ((x - 1) | (y - 1)) + 1


cdef bytearray _swizzle(u32 width, u32 height, u32 blkWidth, u32 blkHeight, u32 bpp, u32 tileMode, u32 alignment, int size_range, bytes data_, int toSwizzle):
    assert 0 <= size_range <= 5
    cdef u32 block_height = 1 << size_range

    width = DIV_ROUND_UP(width, blkWidth)
    height = DIV_ROUND_UP(height, blkHeight)

    cdef:
        u32 pitch
        u32 surfSize

    if tileMode == 0:
        pitch = round_up(width * bpp, 32)
        surfSize = round_up(pitch * height, alignment)

    else:
        pitch = round_up(width * bpp, 64)
        surfSize = round_up(pitch * round_up(height, block_height * 8), alignment)

    cdef:
        array.array dataArr = array.array('B', data_)
        u8 *data = dataArr.data.as_uchars
        u8 *result = <u8 *>malloc(surfSize)

        u32 x, y, pos, pos_

    try:
        for y in range(height):
            for x in range(width):
                if tileMode == 0:
                    pos = y * pitch + x * bpp

                else:
                    pos = getAddrBlockLinear(x, y, width, bpp, 0, block_height)

                pos_ = (y * width + x) * bpp

                if pos + bpp <= surfSize:
                    if toSwizzle:
                        memcpy(result + pos, data + pos_, bpp)

                    else:
                        memcpy(result + pos_, data + pos, bpp)

        return bytearray(<u8[:surfSize]>result)

    finally:
        free(result)


cpdef deswizzle(u32 width, u32 height, u32 blkWidth, u32 blkHeight, u32 bpp, u32 tileMode, u32 alignment, int size_range, data):
    return _swizzle(width, height, blkWidth, blkHeight, bpp, tileMode, alignment, size_range, bytes(data), 0)


cpdef swizzle(u32 width, u32 height, u32 blkWidth, u32 blkHeight, u32 bpp, u32 tileMode, u32 alignment, int size_range, data):
    return _swizzle(width, height, blkWidth, blkHeight, bpp, tileMode, alignment, size_range, bytes(data), 1)


cdef u32 getAddrBlockLinear(u32 x, u32 y, u32 image_width, u32 bytes_per_pixel, u32 base_address, u32 block_height):
    """
    From the Tegra X1 TRM
    """
    cdef:
        u32 image_width_in_gobs = DIV_ROUND_UP(image_width * bytes_per_pixel, 64)

        u32 GOB_address = (base_address
                           + (y // (8 * block_height)) * 512 * block_height * image_width_in_gobs
                           + (x * bytes_per_pixel // 64) * 512 * block_height
                           + (y % (8 * block_height) // 8) * 512)

    x *= bytes_per_pixel

    cdef u32 Address = (GOB_address + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64
                        + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16))

    return Address
