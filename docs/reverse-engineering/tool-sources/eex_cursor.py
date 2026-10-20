"""Bounds-checked equivalents of the EEX primitive cursor readers."""
class Cursor:
    def __init__(self, data, offset=0, end=None):
        self.data = data
        self.pos = offset
        self.end = len(data) if end is None else end
        if not 0 <= offset <= self.end <= len(data):
            raise ValueError('invalid cursor span')

    def integer(self, size):
        if self.pos + size > self.end:
            raise ValueError('truncated EEX integer')
        value = int.from_bytes(self.data[self.pos:self.pos+size], 'little')
        self.pos += size
        return value

    def string(self):
        zero = self.data.find(b'\0', self.pos, self.end)
        if zero < 0:
            raise ValueError('unterminated EEX string')
        raw = self.data[self.pos:zero]
        self.pos = zero + 1
        return raw

    def parameter(self, tag):
        actual = self.integer(2)
        if tag == 1:
            return actual
        if actual != tag:
            return 0x80000000 if tag in (4, 5) else 0x8000
        if tag == 5:
            return self.string()
        return self.integer(4 if tag == 4 else 2)
