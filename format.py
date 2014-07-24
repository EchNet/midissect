#
# Given a dictionary of code labels, format a code value, preferring its label,
# if given.
#
class Enum(object):
    def __init__(self, dictionary):
        self.dictionary = dictionary
    def format(self, code):
        formatted = "{0:d}".format(code)
        if code in self.dictionary:
            formatted = self.dictionary[code] + " (" + formatted + ")"
        return formatted

#
# Maintain indentation level.
#
class Printer(object):
    def __init__(self):
        self.indentation = ""
    def indent(self):
        self.indentation += "  "
    def unindent(self):
        self.indentation = self.indentation[2:]
    def println(self, str):
        print self.indentation + str
