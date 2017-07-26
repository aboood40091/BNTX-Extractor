# Original algorithm by gdkchan
# Ported and improved (a tiny bit) by Stella/AboodXD

BCn_formats = [0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20]
bpps = {0xb: 4, 7: 2, 2: 1, 9: 2, 0x1a: 8, 0x1b: 16, 0x1c: 16, 0x1d: 8, 0x1e: 16, 0x1f: 16, 0x20: 16}
xBases = {0xb: 2, 7: 3, 2: 4, 9: 3, 0x1a: 1, 0x1b: 0, 0x1c: 0, 0x1d: 1, 0x1e: 0, 0x1f: 0, 0x20: 0}


def roundSize(size):
    if (size & 0x0f) != 0:
        size &= ~0x0f
        size +=  0x10

    return size


def pow2RoundUp(v):
    v -= 1

    v |= (v+1 >>  1)
    v |= (v >>  2)
    v |= (v >>  4)
    v |= (v >>  8)
    v |= (v >> 16)

    return v + 1


def countZeros(v):
    numZeros = 0

    for i in range(32):
        if (v & (1 << i)) != 0:
            break

        numZeros += 1

    return numZeros


def deswizzle(width, height, format_, data):
    pos_ = 0

    origin_width = width
    origin_height = height

    if (format_ >> 8) in BCn_formats:
        origin_width = (origin_width + 3) // 4
        origin_height = (origin_height + 3) // 4
        
        width = roundSize(width)
        height = roundSize(height)

        xb = countZeros((pow2RoundUp(width) + 3) // 4)
        yb = countZeros((pow2RoundUp(height) + 3) // 4)

        width = (width + 3) // 4
        height = (height + 3) // 4

    else:
        width = roundSize(width)
        height = roundSize(height)

        xb = countZeros(pow2RoundUp(width))
        yb = countZeros(pow2RoundUp(height))

    result = bytearray(data)

    bpp = bpps[format_ >> 8]

    xBase = xBases[format_ >> 8]

    for y in range(origin_height):
        for x in range(origin_width):
            pos = getAddr(x, y, xb, yb, width, xBase) * bpp

            pos %= len(data)

            result[pos_:pos_ + bpp] = data[pos:pos + bpp]

            pos_ += bpp

    return result

def getAddr(x, y, xb, yb, width, xBase):
    size    = xb + yb
    xCnt    = xBase
    yCnt    = 1
    xUsed   = 0
    yUsed   = 0
    bit     = 0
    address = 0

    while (bit < xBase + 9) and (xUsed + xCnt < xb):
        xMask = (1 << xCnt) - 1
        yMask = (1 << yCnt) - 1

        address |= (x & xMask) << bit
        address |= (y & yMask) << bit + xCnt

        x >>= xCnt
        y >>= yCnt

        xUsed += xCnt
        yUsed += yCnt

        bit += xCnt + yCnt

        xCnt = min(xb - xUsed, 1)
        yCnt = min(yb - yUsed, yCnt << 1)

    width >>= xUsed

    address |= (x + y * width) << bit

    return address
