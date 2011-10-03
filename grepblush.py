#!/usr/bin/env python

"""
Take lines from stdin or another file and color them according to
regular expression rules before passing them to stdout.
"""

import sys
import optparse
import re

from optparse import OptionParser

# The special color names allowed in the match file, and their
# corresponding bash color codes.
SPECIAL_BASH_COLORS = {
    'red': '0;31',
    'yellow': '1;33',
    'green': '0;32',
    'blue': '0;34',
    'purple': '0;35',
    'light_gray': '0;37'
}

def bash_color(color):
    """
    Return the unescaped bash color code if color is one of SPECIAL_BASH_COLORS.

    Otherwise, just return color.
    """
    if color in SPECIAL_BASH_COLORS:
        return SPECIAL_BASH_COLORS[color]
    else:
        return color

def parse_matchline(line):
    """
    Parse the supplied line into:

    (regex)=(color)

    Raise an Exception if the line cannot be parsed.

    Compile the regex, use bash_color to determine the appropriate
    code for color, and return a tuple of form:

    (compiled_regex, bash_color_code)
    """

    # use rpartition so that the regex can contain ='s.
    (regex, sep, color) = line.rpartition("=")

    # the regex or the color could theoretically be empty, acting as a
    # default, so we choose to allow a line with just an =.  But a
    # line where the sep wasn't found is an error.=
    if not sep:
        raise Exception("Could not parse match line: {0}".format(line))

    return (re.compile(regex), bash_color(color))

def parse_matchfile(parser, options, args):
    """
    Parse the lines in the matchfile named by args[0] according to the
    logic in parse_matchline.

    If the file cannot be read, or if a line is malformed, call the
    parser's error function with an appropriate error message (and
    exit).

    On success, return a list of tuples of the form:
    [(compiled_regexp, bash_color_code), ...]
    """

    patterns = []

    matchfile_name = args[0]
    fil = None

    try:
        fil = open(matchfile_name, 'r')
    except IOError as(errno, strerror):
        err_str = "I/O error while opening match file {0} ({1}): {2}".format(matchfile_name, 
                                                                             errno, 
                                                                             strerror)
        parser.error(err_str)
    
    try:
        for (line_num, line) in enumerate(fil):
            patterns.append(parse_matchline(line.rstrip()))
    except Exception as e:
        parser.error("Error parsing matchfile line {0}: {1}".format(line_num, e))
    fil.close()

    return patterns

def open_input(parser, options, args):
    fil_name = None
    fil = None

    try:
        if options.input == '-':
            fil_name = 'stdin'
            fil = sys.stdin
        else:
            fil_name = options.input
            fil = open(fil_name, 'r')
    except IOError as(errno, strerror):
        err_str = "I/O error while opening input file {0} ({1}): {2}".format(fil_name, 
                                                                             errno, 
                                                                             strerror)
        parser.error(err_str)

    return fil

if __name__ == '__main__':
    parser = OptionParser(usage="%prog [options] MATCHFILE\n\n" + \
                              "MATCHFILE should contain lines of the form:\n\n" + \
                              "regex=colorcode\n\n" + \
                              "Where colorcode is an unescaped bash color code (e.g. 1;36 for light cyan) " + \
                              "or one of (red,yellow,green,blue,purple)\n\n" + \
                              "In case of overlapping matches, earlier lines take precedence.")
    parser.add_option("-f", "--file", help="Input file (stdin if '-', which is the default)",
                      dest="input", metavar="FILE", default="-")
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        parser.error("MATCHFILE is required.")

    regexes_and_colors = parse_matchfile(parser, options, args)
    fil = open_input(parser, options, args)
    
    for line in fil:
        color = None
        for (regex, re_color) in regexes_and_colors:
            if regex.match(line):
                color = re_color
                break
        if color:
            # the \033[0m resets the color after a formatted line.
            line = "\033[{0}m{1}\033[0m".format(color, line)
        sys.stdout.write(line)
            
