def DIV_ROUND_UP(n, d):
    return (n + d - 1) // d


def round_up(x, y):
    return ((x - 1) | (y - 1)) + 1


def deswizzle(width, height, blkWidth, blkHeight, bpp, tileMode, alignment, size_range, data):
    assert 0 <= size_range <= 5
    block_height = 1 << size_range

    width = DIV_ROUND_UP(width, blkWidth)
    height = DIV_ROUND_UP(height, blkHeight)

    if tileMode == 0:
        min_pitch = DIV_ROUND_UP(width * bpp, bpp)
        pitch = round_up(min_pitch, alignment * 64)

    else:
        pitch = round_up(width, 64)

    dataSize = len(data)
    result = bytearray(width * height * bpp)

    for y in range(height):
        for x in range(width):
            if tileMode == 0:
                pos = (y * pitch + x) * bpp

            else:
                pos = getAddrBlockLinear(x, y, width, bpp, 0, block_height)

            pos_ = (y * width + x) * bpp

            if pos + bpp <= dataSize:
                result[pos_:pos_ + bpp] = data[pos:pos + bpp]

    return result


def getAddrBlockLinear(x, y, image_width, bytes_per_pixel, base_address, block_height):
    """
    From the Tegra X1 TRM
    """
    image_width_in_gobs = DIV_ROUND_UP(image_width * bytes_per_pixel, 64)

    GOB_address = (base_address
                   + (y // (8 * block_height)) * 512 * block_height * image_width_in_gobs
                   + (x * bytes_per_pixel // 64) * 512 * block_height
                   + (y % (8 * block_height) // 8) * 512)

    x *= bytes_per_pixel

    Address = (GOB_address + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64
               + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16))

    return Address
