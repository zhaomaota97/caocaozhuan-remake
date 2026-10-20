"""Original 32-bit LCG and bounded/percentage draws from Ekd5.exe."""


class GameRng:
    def __init__(self, seed):
        self.state=seed & 0xffffffff

    def draw(self):
        self.state=(self.state*0x41c64e6d+0x3039) & 0xffffffff
        return (self.state>>16) & 0x7fff

    def bounded(self, bound):
        return self.draw()%bound if bound>1 else 0

    def chance(self, percent):
        return self.bounded(100)<percent
