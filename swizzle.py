# Original algorithm by gdkchan
# Ported and improved (a tiny bit) by Stella/AboodXD

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

xBases = {1: 4, 2: 3, 4: 2, 8: 1, 16: 0}

padds = {1: 64, 2: 32, 4: 16, 8: 8, 16: 4}


def roundSize(size, pad):
    mask = pad - 1
    if size & mask:
        size &= ~mask
        size +=  pad

    return size


def pow2RoundUp(v):
    v -= 1

    v |= (v+1) >> 1
    v |= v >>  2
    v |= v >>  4
    v |= v >>  8
    v |= v >> 16

    return v + 1


def isPow2(v):
    return v and not v & (v - 1)


def countZeros(v):
    numZeros = 0

    for i in range(32):
        if v & (1 << i):
            break

        numZeros += 1

    return numZeros


def deswizzle(width, height, format_, data):
    pos_ = 0

    bpp = bpps[format_ >> 8]

    origin_width = width
    origin_height = height

    if (format_ >> 8) in BCn_formats:
        origin_width = (origin_width + 3) // 4
        origin_height = (origin_height + 3) // 4

    elif (format_ >> 8) in ASTC_formats:
        blkWidth, blkHeight = blk_dims[format_ >> 8]
        origin_width = (origin_width + blkWidth  - 1) // blkWidth
        origin_height = (origin_height + blkHeight - 1) // blkHeight

    xb = countZeros(pow2RoundUp(origin_width))
    yb = countZeros(pow2RoundUp(origin_height))

    hh = pow2RoundUp(origin_height) >> 1;

    if not isPow2(origin_height) and origin_height <= hh + hh // 3 and yb > 3:
        yb -= 1

    width = roundSize(origin_width, padds[bpp])

    result = bytearray(data)

    xBase = xBases[bpp]

    for y in range(origin_height):
        for x in range(origin_width):
            pos = getAddr(x, y, xb, yb, width, xBase) * bpp

            result[pos_:pos_ + bpp] = data[pos:pos + bpp]

            pos_ += bpp

    return result

def getAddr(x, y, xb, yb, width, xBase):
    xCnt    = xBase
    yCnt    = 1
    xUsed   = 0
    yUsed   = 0
    address = 0

    while (xUsed < xBase + 2) and (xUsed + xCnt < xb):
        xMask = (1 << xCnt) - 1
        yMask = (1 << yCnt) - 1

        address |= (x & xMask) << xUsed + yUsed
        address |= (y & yMask) << xUsed + yUsed + xCnt

        x >>= xCnt
        y >>= yCnt

        xUsed += xCnt
        yUsed += yCnt

        xCnt = min(xb - xUsed, 1)
        yCnt = min(yb - yUsed, yCnt << 1)

    address |= (x + y * (width >> xUsed)) << (xUsed + yUsed)

    return address
