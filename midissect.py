#
# midissect, main module
#
# usage:
#     python midissect.py filename.mid > filename.dump
#
if __name__ == "__main__":
    import sys
    from midiio import MidiFileReader
    from mdump import FileDumper
    filename = sys.argv[1]
    reader = MidiFileReader(filename) 
    dumper = FileDumper(reader)
    dumper.dump()
