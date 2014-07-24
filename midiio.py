#
# MIDI file I/O utilities.
#
class MidiFileReader(object):

    #
    # Open the file.
    #
    def __init__(self, filename):
        self.file = open(filename, "rb") 
        self.guardPos = 0

    def read(self, nbytes = 1, eofPermitted = False):
        if self.guardPos > 0 and self.currentPos + nbytes > self.guardPos:
            raise StandardError("Chunk data not properly terminated @ " + self.formatPos(self.guardPos))
        chunk = self.file.read(nbytes)
        if not eofPermitted and len(chunk) < nbytes:
            raise StandardError("Unexpected end of file @ " + self.formatCurrentPos())
        return chunk

    #
    # The byte offset of the current read position in the file.
    #
    @property
    def currentPos(self):
        return self.file.tell()

    #
    # Format the current file read position.
    #
    def formatCurrentPos(self, offset = 0):
        return formatPos(currentPos + offset)

    #
    # Format a file read position.
    #
    def formatPos(self, pos):
        return "{0:d} ({0:#x})".format(pos)

    #
    # Read one unsigned byte from the file.
    #
    def readByte(self):
        return ord(self.read()[0])

    #
    # Read one 16-bit unsigned integer value from the file.
    #
    def readWord(self, nbytes = 2):
        accum = 0
        for i in xrange(0, nbytes):
            accum = accum << 8 | self.readByte()
        return accum

    #
    # Read one 32-bit unsigned integer value from the file.
    #
    def readDword(self):
        return self.readWord(4)

    #
    # Read a MIDI-encoded variable length integer value from the file.
    #
    def readVariableLengthValue(self):
        accum = 0
        while True:
            byte = self.readByte()
            accum |= byte & ~0x80
            if byte & 0x80:
                newAccum = int(accum << 7)
                if (newAccum >> 7) != accum:
                    raise StandardError("32-bit integer overflow @ " + self.formatPos(currentPos - 1))
                accum = newAccum
            else:
                break
        return accum

if __name__ == "__main__":
    import sys
    filename = sys.argv[1]
    fileReader = MidiFileReader(filename)
