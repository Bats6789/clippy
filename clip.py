r"""
DO NOT DELETE THE AUTHOR COPYRIGHT
©Connor Talbot 2021 - https://github.com/con-dog/clippy

clip.py - Animate and color a given directory of .txt files.

The text files in the directory provided should be 'frames' in a sequence
to give the impression of animation. For steps to make your own, visit the
GitHub link ReadMe. Its very easy!

Example:
In the directory: "clip/art/sea/boats/small_boat_1" there are a few text files
under a subfolder called "ascii":
small_boat_1a, small_boat_1b, small_boat_1c, ... small_boat_1f etc

 clip
    ├───art
    ├───animals
    ...
    ...
    └───sea
        └───boats
            └───small_boat_1
                ├───ascii
                |       └───small_boat_1a.txt
                |       └───small_boat_1b.txt
                |       ...
                |       ...
                |       └───small_boat_1h.txt
                └───color

Stepping through these clearly shows a boat (and a bird) moving frame by frame

small_boat_1a.txt
-----------------
.................
........~...v....
.........../|....
.....v..../_|__..
.........\-----/.
~~~~~~~~~`~~~~~~'

small_boat_1b.txt
-----------------
.................
.......~...v.....
........../|...\,
....v..../_|__...
........\-----/..
~~~~~~~~`~~~~~~'~

.....
.....

small_boat_1h.txt
-----------------
... /`\..........
...v.............
../|.............
./_|__...........
\-----/..........
`~~~~~~'~~~~~~~~~


Any art samples you create should be of a frame-by-frame nature as above ordered
alphabetically with lowercase lettering. Frame play order is dictated by
this alphabetical order.

All files shall be saved to a relevant directory under the "art" directory in
the repo.

Note that you can also color in your art, but you have to create another txt
file in another subfolder called "color" that holds the color mappings to
accompany the art file for each frame eg:
small_boat_1a.txt, small_boat_1a_color.txt, .... etc
''

For ASCII art ideas visit https://www.asciiart.eu/ and credit the original
author if copying
"""

import argparse
from contextlib import ExitStack
import glob
import os
import re
import sys
import time

# COLORS: FOREGROUND = F, BACKGROUND = B, Value = ANSI value
COLORS = {
    'F_BLK': '\033[30m', 'B_BLK': '\033[40m',  # BLACK
    'F_RED': '\033[31m', 'B_RED': '\033[41m',  # RED
    'F_GRN': '\033[32m', 'B_GRN': '\033[42m',  # GREEN
    'F_YLW': '\033[33m', 'B_YLW': '\033[43m',  # YELLOW
    'F_BLU': '\033[34m', 'B_BLU': '\033[44m',  # BLUE
    'F_MGT': '\033[35m', 'B_MGT': '\033[45m',  # MAGENTA
    'F_CYA': '\033[36m', 'B_CYA': '\033[46m',  # CYAN
    'F_WHT': '\033[37m', 'B_WHT': '\033[47m',  # WHITE
    'F_CLP': '\033[38;5;68m', 'B_CLP': '\033[48;5;68m',  # CLIPPY
    'F_PYT': '\033[38;5;33m', 'B_PYT': '\033[48;5;33m',
    'F_BWN': '\033[38;5;130m', 'B_BWN': '\033[48;5;130m',  # BROWN
    'F_GRY': '\033[38;5;153m', 'B_GRY': '\033[48;5;153m',  # GRAY
    'F_TRQ': '\033[38;5;50m', 'B_TRQ': '\033[48;5;50m',  # TURQUOISE
    'F_NVY': '\033[38;5;33m', 'B_NVY': '\033[48;5;33m',  # NAVY
    'F_STN': '\033[38;5;153m', 'B_STN': '\033[48;5;153m',  # STONE
    'F_MRN': '\033[38;5;160m', 'B_MRN': '\033[48;5;160m',  # MORNING
    'F_ONG': '\033[38;5;202m', 'B_ONG': '\033[48;5;202m',  # ORANGE
    'F_DSK': '\033[38;5;203m', 'B_DSK': '\033[48;5;203m',  # DUSK
    'F_SND': '\033[38;5;229m', 'B_SND': '\033[48;5;229m',  # SAND
}

# DEFAULT COLORS AND PLACEHOLDER CHARACTER
DEFAULT_FG = COLORS['F_WHT']
DEFAULT_BG = COLORS['B_BLK']
PLACEHOLDER_CHAR = '.'
PLACEHOLDER_COLOR = F"{COLORS['F_BLK']}{COLORS['B_BLK']}"
PLACEHOLDER = F'{PLACEHOLDER_COLOR}{PLACEHOLDER_CHAR}'
RESTORE_STATE = '\033[0m'

# CURSOR ANSI ESCAPE PATTERNS
CURSOR_UP = '\033[1A'  # moves cursor up one line
CURSOR_DOWN = '\033[1B'  # moves cursor up one line
CURSOR_RESET = '\033[u'  # resets the cursor
CURSOR_OFF = '\033[?25l'  # makes cursor invisible
CURSOR_ON = '\033[?25h'  # makes cursor visible
CURSOR_SAVE_POS = '\033[s'  # saves cursor position
CURSOR_RESTORE_POS = '\033[u'  # returns cursor to last saved position


def make_cli_parser():
    """Make the modules default argparser"""
    parser = argparse.ArgumentParser(
        description='Animate and color ASCII art in the cli',
        usage='use "%(prog)s --help" for more information',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'path', metavar='path', type=str,
        help="""If your folder is 'small_boat_1', then you would pass:

art/sea/boats/small_boat_1

eg: Directory structure of clippy is like so:

    C:.
    └───art
    ├───animals
    ├───buildings
    │   ├───castles
    │   │   └───castle_1
    │   └───houses
    │       └───small_home_1
    ...
    ...
    ...
    └───sea
        └───boats
            └───small_boat_1
                ├───ascii
                └───color

"""
    )

    parser.add_argument(
        'speed', metavar='speed', type=int, help='the play speed from 1-100'
    )

    parser.add_argument(
        'cycles', metavar='cycles', type=int, help='the number of times to '
        'cycle the animation from 1-1000'
    )

    parser.add_argument(
        '-c', '--color', dest='color', action='store_true',
        help='pass this flag to color the ASCII art'
    )

    parser.set_defaults(color=False)
    args = parser.parse_args()
    return args


class ClipException(Exception):
    """Raise Exception if Clip class methods are misused"""
    pass


class Clip:
    """A class to manage all aspects of a clip."""

    def __init__(self, source_folder, play_speed, play_cycles, color=False):
        """Initialize instance of Tile"""
        if os.name == 'nt':
            os.system('color')  # Required to work, enables ANSI codes
            os.system('cls')  # Clear cli
        else:
            os.system('clear')
        sys.stdout.write(CURSOR_OFF)
        self.ascii_files = None
        self.frames = []
        self.color_files = None
        self.frame_color_maps = []
        self._source_folder = source_folder
        self.play_speed = 5.1 - (play_speed / 20)
        self.play_cycles = play_cycles
        self._color = color
        self.ascii_sub = os.path.join(self.source_folder, 'ascii')
        self.color_sub = os.path.join(self.source_folder, 'color')
        if not os.path.isdir(self.ascii_sub):
            raise ClipException("""
                    Your folder specified by path, must contain a subfolder
                    called 'ascii'. This ascii subfolder must contain at least
                    1 txt file. Your folder hierarchy should look similar to:

                    C:.
                    └───art
                        ├───animals
                        ├───buildings
                        │   └───castles
                        ...     └───my_folder
                                    └───ascii
                                        └───my_art_1.txt
                                        └───my_art_2.txt
                                        ...
                                        ...
                                        └───my_art_n.txt

                    """)
        if not isinstance(self.play_cycles, int):
            raise ClipException('play cycles must be an integer')
        if (self.play_cycles < 1) or (self.play_cycles > 1000):
            raise ClipException('play cycles must be an integer from 1-1000')
        if not isinstance(play_speed, int):
            raise ClipException('Speed must be an integer from 1-100')
        if (play_speed < 1) or (play_speed > 100):
            raise ClipException('Speed must be an integer from 1-100')
        if (not isinstance(self._color, bool)):
            raise ClipException('colorless by default - pass "True" for color')
        if color:
            if not os.path.isdir(self.color_sub):
                raise ClipException("""
                        When passing color flag, folder specified by path, must
                        contain a subfolder called 'color'.
                        """)
            if len(os.listdir(self.ascii_sub)) != len(os.listdir(self.color_sub)):
                raise ClipException("""
                        When passing color flag, the subfolders 'ascii' and
                        'color' must contain an equal number of txt files to
                        ensure color mappings are correct.
                        """)

    @property
    def source_folder(self):
        """Instance read only property"""
        return self._source_folder

    @property
    def color(self):
        """Instance read only property"""
        return self._color

    def get_frames(self):
        """Get all the frame art from the ascii sub-directory in alphabetical
        order."""
        # get all /ascii/*.txt files in dir. These are the ascii frames
        filenames = glob.glob(os.path.join(self.ascii_sub, '*.txt'))
        with ExitStack() as stack:  # dynamically handle multi file opens/closes
            self.ascii_files = [stack.enter_context(open(f)) for f in filenames]
            if self.ascii_files:
                self.frames = []
                for f in self.ascii_files:  # iterate over the frame files list
                    frame = []
                    lines = f.read().splitlines()
                    for line in lines:
                        row = list(line)  # becomes a [row][column] structure
                        frame.append(row)
                    self.frames.append(frame)

    def set_char_base_color(self):
        """Loop over each frames characters, and set them to defaults"""
        for f, frame in enumerate(self.frames):
            for r, row in enumerate(frame):
                for c, char in enumerate(self.frames[f][r]):
                    if char != PLACEHOLDER_CHAR:
                        self.frames[f][r][c] = f'{DEFAULT_FG}{DEFAULT_BG}{char}'
                    else:
                        self.frames[f][r][c] = PLACEHOLDER

    def get_frame_color_maps(self):
        """Get all the color mappings from the color sub-directory in
        alphabetical order."""
        # get all /color/*.txt files in dir. These are the color mappings
        filenames = glob.glob(os.path.join(self.color_sub, '*.txt'))
        with ExitStack() as stack:  # dynamically handle multi file opens/closes
            self.color_files = [stack.enter_context(open(f)) for f in filenames]
            if self.color_files:
                self.frame_color_maps = []
                for f in self.color_files:  # iterate over the frame files list
                    lines = f.read().splitlines()
                    # Remove any empty lines. Required for regex
                    frame_color_map = list(line for line in lines if line)
                    self.frame_color_maps.append(frame_color_map)
            else:
                raise ClipException('Path must include txt files!')

    def color_cells(self):
        """Color the cells by mapping the frames color map to that frames
        characters"""
        map_regex = re.compile(r'''
            \[(\d*)\]  # group 1: Match [digit/s] for row
            \[(\d*)\]  # group 2: Match [digit/s] for column
            [\s=\s]*  # get everything around equals sign
            (\w*[^,])  # group 3: match the 1st color (not optional)
            (,[\s]*(\w*))?  # group 5: match an optional second color
            ''', re.VERBOSE
                               )
        # need the index of the frame_color_map to map to the corresponding
        # frame in self.frames
        for frame_index, frame_color_map in enumerate(self.frame_color_maps):
            for char_color_map in frame_color_map:
                mo = map_regex.search(char_color_map)
                row = int(mo.group(1))
                column = int(mo.group(2))
                color_1_text = mo.group(3)
                color_2_text = mo.group(5)
                # just get the ASCII character, not its color!
                char = self.frames[frame_index][row][column][-1]

                # map colors string to COLORS variables constants values
                color_1 = COLORS.get(color_1_text, '')
                color_2 = COLORS.get(color_2_text, '')

                updated_char = f"{color_1}{color_2}{char}"
                self.frames[frame_index][row][column] = updated_char

    def play_clip(self):
        """Loop through a clips frames to display it to screen at the given
        speed"""
        sys.stdout.flush()
        for frame in self.frames:
            for row in frame:  # Iterate over each frames rows
                for char in row:
                    sys.stdout.write(char)
                sys.stdout.write('\n')  # newline after all cells in row shown
            sys.stdout.write(CURSOR_SAVE_POS)  # save cursor position
            # Move cursor back to top of display and draw next frame
            sys.stdout.write(CURSOR_UP * len(frame))
            time.sleep(self.play_speed)

    def loop_clip(self):
        """Loop through the clip the given number of cycles"""
        while self.play_cycles > 1:
            self.play_clip()
            self.play_cycles -= 1
        sys.stdout.write(CURSOR_RESTORE_POS)  # restore cursor to saved position

    def run(self):
        """Call instance functions to animate the frames to the screen and cycle
        the animation"""
        self.get_frames()
        self.set_char_base_color()
        if self.color:
            self.get_frame_color_maps()
            self.color_cells()
        self.play_clip()
        self.loop_clip()
        sys.stdout.write(CURSOR_ON)
        sys.stdout.write(RESTORE_STATE)


def clippy(path, speed, cycles, color):
    """main function for module"""
    clip = Clip(path, speed, cycles, color)
    clip.run()


if __name__ == '__main__':
    args = make_cli_parser()
    clippy(args.path, args.speed, args.cycles, args.color)
