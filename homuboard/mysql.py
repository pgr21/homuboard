def mysql323(buf):
    nr = 1345345333
    nr2 = 0x12345671
    add = 7

    for b in buf:
        if b == b' ' or b == b'\t': continue

        nr ^= (((nr & 63) + add) * b + (nr << 8)) & 0xffffffff
        nr2 = (nr2 + ((nr2 << 8) ^ nr)) & 0xffffffff
        add = (add + b) & 0xffffffff

    return '{:08x}{:08x}'.format(nr & 0x7fffffff, nr2 & 0x7fffffff)
