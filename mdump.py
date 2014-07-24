import format

HEADER_ID = "".join(chr(x) for x in [ 0x4d, 0x54, 0x68, 0x64 ])
TRACK_ID = "".join(chr(x) for x in [ 0x4d, 0x54, 0x72, 0x6b ])

FORMAT_TYPE_ENUM = format.Enum({
    0: "single track",
    1: "multi-track",
    2: "multi-pattern"
})

EVENT_TYPE_ENUM = format.Enum({
    0x8: "Note Off",
    0x9: "Note On",
    0xa: "Note Aftertouch",
    0xb: "Controller",
    0xc: "Program Change",
    0xd: "Channel Aftertouch",
    0xe: "Pitch Bend"
})

META_EVENT_TYPE_ENUM = format.Enum({
    0: "Sequence Number",
    1: "Text Event",
    2: "Copyright Notice",
    3: "Sequence/Track Name",
    4: "Instrument Name",
    5: "Lyrics",
    6: "Marker",
    7: "Cue Point",
    32: "MIDI Channel Prefix",
    47: "End of Track",
    81: "Set Tempo",
    84: "SMPTE Offset",
    88: "Time Signature",
    89: "Key Signature",
    127: "Sequencer-Specific"
})

def formatByteString(bytes):
    return "".join(elem.encode("hex") for elem in bytes)

class Dumper(object):
    def __init__(self, reader, printer):
        self.reader = reader
        self.printer = printer

class Chunk(Dumper):
    def __init__(self, parent, id):
        super(Chunk, self).__init__(parent.reader, parent.printer)
        self.id = formatByteString(id)
        self.size = self.reader.readDword()
        self.reader.guardPos = self.reader.currentPos + self.size

class HeaderChunk(Chunk):
    def __init__(self, parent, id):
        super(HeaderChunk, self).__init__(parent, id)
    def dump(self):
        self.printer.println("HEADER ({0:s}) size {1:d}".format(self.id, self.size))
        self.printer.indent()
        # TODO: guard against a size less than 6.
        self.printer.println("Format Type: " + FORMAT_TYPE_ENUM.format(self.reader.readWord()))
        self.printer.println("Number of Tracks: {0:d}".format(self.reader.readWord()))
        self.printer.println("Time Division: {0:s}".format(self.formatTimeDivision(self.reader.readWord())))
        self.printer.unindent()
    def formatTimeDivision(self, timeDivision):
        nUnits = timeDivision & ~0x8000 
        units = "frames per second" if timeDivision & 0x8000 else "ticks per beat"
        return "{0:#x} = {1:d} {2:s}".format(timeDivision, nUnits, units)

class TrackChunk(Chunk):
    def __init__(self, parent, id):
        super(TrackChunk, self).__init__(parent, id)
    def dump(self):
        self.printer.println("TRACK ({0:s}) size {1:d}".format(self.id, self.size))
        self.printer.indent()
        while self.reader.currentPos < self.reader.guardPos:
            # Tracks are composed of events. 
            # Each event has a time delta:
            deltaTime = self.reader.readVariableLengthValue()
            # Each has type info:
            eventTypeInfo = self.reader.readByte()
            if eventTypeInfo == 255:
                # Type info of 255 indicates a meta-event:
                metaType = self.reader.readByte()
                metaLength = self.reader.readVariableLengthValue()
                self.printer.println("  @t+{0:d} meta-event {1:s}".format(deltaTime, META_EVENT_TYPE_ENUM.format(metaType)))
                self.printer.indent();
                self.dumpMetaEvent(metaType, metaLength)
                self.printer.unindent();
            else:
                # Otherwise, it's a channel event, and event type info includes
                # a type ID and a MIDI channel number
                eventType = (eventTypeInfo >> 4) & 0xf
                eventChannel = eventTypeInfo & 0xf
                parameter1 = self.reader.readByte()
                parameter2 = None
                if eventType != 0xc:
                    parameter2 = self.reader.readByte()
                self.printer.println("@t+{0:d} {1:s} ch{2:d}".format(deltaTime, EVENT_TYPE_ENUM.format(eventType), eventChannel))
                self.printer.indent();
                self.dumpFields(eventType, parameter1, parameter2)
                self.printer.unindent();
        self.printer.unindent()
    def dumpMetaEvent(self, metaType, metaLength):
        text = self.reader.read(metaLength)
        if metaType == 4:
            self.printer.println("Text: {0:s}".format(text))
    def dumpFields(self, eventType, parameter1, parameter2):
        if eventType == 0x8 or eventType == 0x9 or eventType == 0xa:
            self.printer.println("Note Number: {0:d}".format(parameter1))
        elif eventType == 0xb:
            self.printer.println("Controller Number: {0:d}".format(parameter1))
        elif eventType == 0xc:
            self.printer.println("Program Number: {0:d}".format(parameter1))
        elif eventType == 0xd:
            self.printer.println("Aftertouch Value: {0:d}".format(parameter1))
        elif eventType == 0xe:
            self.printer.println("Pitch Value (LSB): {0:d}".format(parameter1))
        else:
            self.printer.println("Parameter 1: {0:d}".format(parameter1))

        if eventType == 0x8 or eventType == 0x9:
            self.printer.println("Velocity: {0:d}".format(parameter2))
        elif eventType == 0xa:
            self.printer.println("Aftertouch Value: {0:d}".format(parameter2))
        elif eventType == 0xb:
            self.printer.println("Controller Value: {0:d}".format(parameter2))
        elif eventType == 0xe:
            self.printer.println("Pitch Value (MSB): {0:d}".format(parameter2))
        elif eventType != 0xc and eventType != 0xd:
            self.printer.println("Parameter 2: {0:d}".format(parameter2))

class FileDumper(Dumper):
    def __init__(self, reader):
        super(FileDumper, self).__init__(reader, format.Printer())
    def dump(self):
        while True:
            self.reader.guardPos = 0
            chunkId = self.reader.read(4, True)
            if len(chunkId) == 0: break
            if chunkId == HEADER_ID:
                HeaderChunk(self, chunkId).dump()
            elif chunkId == TRACK_ID:
                TrackChunk(self, chunkId).dump()
            else:
                raise StandardError("Non-MIDI chunk ID @ " + self.reader.formatCurrentPos(-8));
