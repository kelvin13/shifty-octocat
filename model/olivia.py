import bisect

from itertools import groupby

from fonts import styles

from state import noticeboard

from model import kevin
from model.wonder import words, character, _breaking_chars

from model.cat import cast_liquid_line, typeset_liquid, Toplevel_bounds

def outside_tag(sequence):
    for i in reversed(range(len(sequence) - 1)):

        if (character(sequence[i]), sequence[i + 1]) == ('<p>', '</p>'):
            del sequence[i:i + 2]

    return sequence

class Cursor(object):
    def __init__(self, i):
        self.cursor = i
    
    def skip(self, jump, text):
        self.cursor += jump
        # prevent overruns
        if self.cursor > len(text) - 1:
            self.cursor = len(text) - 1
        if character(text[self.cursor]) == '<p>':
            direction = 1
            if jump < 0:
                direction = -1
            while True:
                self.cursor += direction
                if character(text[self.cursor]) != '<p>':
                    break

    def set_cursor(self, index, text):
        self.cursor = index
        self.skip(0, text)

class Text(object):
    def __init__(self, text, channels, cursor, select):
        self.text = kevin.deserialize(text)
        self.channels = channels
        
        self._SLUGS = []
        
        self._sorted_pages = {}
        
        # create cursor objects
        self.cursor = Cursor(cursor)
        self.select = Cursor(select)
        
        # STATS
        self.word_count = '—'
        self.misspellings = []
        
    def _TYPESET(self, l, i):
        if not l:
            self._SLUGS = []
            # which happens if nothing has yet been rendered
            c = 0
            P = self.text[0][1]
            PSTYLE = styles.PARASTYLES.project_p(P)
            P_i = 0
            F = Counter()
            
            R = 0
            y = self.channels.channels[c].railings[0][0][1]
        
        else:
            # ylevel is the y position of the first line to print
            # here we are removing the last existing line so we can redraw that one as well
            CURRENTLINE = self._SLUGS.pop()
            LASTLINE = self._SLUGS[-1]
            
            if LASTLINE['P_BREAK']:
                P = self.text[i][1]
                P_i = i
                F = Counter()

            else:
                P, P_i = LASTLINE['PP']
                F = LASTLINE['F'].copy()
            PSTYLE = styles.PARASTYLES.project_p(P)
            
            R = CURRENTLINE['R']
            
            c = CURRENTLINE['c']
            y = CURRENTLINE['y'] - PSTYLE['leading']
        
        page = self.channels.channels[c].page
        K_x = None
        
        displacement = PSTYLE['leading']

        while True:
            y += displacement
            
            # see if the lines have overrun the portals
            if y > self.channels.channels[c].railings[1][-1][1] and c < len(self.channels.channels) - 1:
                c += 1
                y = self.channels.channels[c].railings[0][0][1]
                
                page = self.channels.channels[c].page
                continue

            # calculate indentation

            if R in PSTYLE['indent_range']:
                D, SIGN, K = PSTYLE['indent']
                if K:
                    if K_x is None:
                        INDLINE = cast_liquid_line(
                            self.text[P_i : P_i + K + 1], 
                            0, 
                            
                            1989, 
                            0,
                            P,
                            F.copy(), 
                            
                            hyphenate = False
                            )
                        K_x = INDLINE['GLYPHS'][-1][5] * SIGN
                    
                    L_indent = PSTYLE['margin_left'] + D + K_x
                else:
                    L_indent = PSTYLE['margin_left'] + D
            else:
                L_indent = PSTYLE['margin_left']
            
            R_indent = PSTYLE['margin_right']

            # generate line objects
            x1 = self.channels.channels[c].edge(0, y)[0] + L_indent
            x2 = self.channels.channels[c].edge(1, y)[0] - R_indent
            if x1 > x2:
                x1, x2 = x2, x1
            LINE = cast_liquid_line(
                    self.text[i : i + 1989], 
                    i, 
                    
                    x2 - x1, 
                    PSTYLE['leading'],
                    P,
                    F.copy(), 
                    
                    hyphenate = PSTYLE['hyphenate']
                    )
            # stamp line data
            LINE['R'] = R # line number (within paragraph)
            LINE['x'] = x1
            LINE['y'] = y
            LINE['l'] = l
            LINE['c'] = c
            LINE['page'] = page
            LINE['PP'] = (P, P_i)
            
            # get the index of the last glyph printed so we know where to start next time
            i = LINE['j']
            
            if LINE['P_BREAK']:

                if i > len(self.text) - 1:
                    self._SLUGS.append(LINE)
                    # this is the end of the document
                    break
                
                y += PSTYLE['margin_bottom']

                P = self.text[i][1]
                PSTYLE = styles.PARASTYLES.project_p(P)
                P_i = i
                F = Counter()
                R = 0
                K_x = None
                
                y += PSTYLE['margin_top']

                displacement = PSTYLE['leading']

            else:
                F = LINE['F']
                R += 1
            
            l += 1
            self._SLUGS.append(LINE)

        self._line_startindices = [line['i'] for line in self._SLUGS]
        self._line_yl = { cc: list(h[:2] for h in list(g)) for cc, g in groupby( ((LINE['y'], LINE['l'], LINE['c']) for LINE in self._SLUGS if LINE['GLYPHS']), key=lambda k: k[2]) }

    def _recalculate(self):
        # clear sorts
        self._sorted_pages = {}
        
        # avoid recalculating lines that weren't affected
        try:
            l = self.index_to_line( min(self.select.cursor, self.cursor.cursor) ) - 1
            if l < 0:
                l = 0
            i = self._SLUGS[l]['i']
            self._SLUGS = self._SLUGS[:l + 1]
            
            bounds = Toplevel_bounds(self.channels.channels)
            self._line_startindices, self._line_yl = typeset_liquid(bounds, self.text, self._SLUGS, l, i)
        except AttributeError:
            self.deep_recalculate()

    def deep_recalculate(self):
        # clear sorts
        self._SLUGS.clear()
        self._sorted_pages.clear()

        bounds = Toplevel_bounds(self.channels.channels)
        self._line_startindices, self._line_yl = typeset_liquid(bounds, self.text, self._SLUGS, 0, 0)

    def _target_row(self, x, y, c):
        
        yy, ll = zip( * self._line_yl[c])
        # find the clicked line
        lineindex = None
        if y >= yy[-1]:
            lineindex = len(yy) - 1
        else:
            lineindex = bisect.bisect(yy, y)

        return ll[lineindex]
    
    def target_glyph(self, x, y, l=None, c=None):
        if l is None:
            l = self._target_row(x, y, c)
        return self._SLUGS[l].I(x, y)

    # get line number given character index
    def index_to_line(self, index):
        return bisect.bisect(self._line_startindices, index) - 1

    def take_selection(self):
        if self.cursor.cursor == self.select.cursor:
            return False
        else:
            self._sort_cursors()

            return self.text[self.cursor.cursor:self.select.cursor]

    def delete(self, start=None, end=None, da=0, db=0):

        self._sort_cursors()

        if start is None:
            start = self.cursor.cursor + da
            
        if end is None:
            end = self.select.cursor + db


        if [character(e) for e in self.text[start:end]] == ['</p>', '<p>']:
            del self.text[start:end]
            
            offset = start - end
        
        else:
            # delete every PAIRED paragraph block
            ptags = [ e for e in self.text[start:end] if character(e) in ('<p>', '</p>') ]
            del self.text[start:end]

            outside = outside_tag(ptags)
            if outside:
                if (outside[0], character(outside[1])) == ('</p>', '<p>'):
                    style = next(c[1] for c in self.text[start::-1] if character(c) == '<p>')
                    if style == outside[1][1]:
                        del outside[0:2]
                        
                self.text[start:start] = outside

            offset = start - end + len(outside)
        
        # fix spelling lines
        self.misspellings = [pair if pair[1] < start else (pair[0] + offset, pair[1] + offset, pair[2]) if pair[0] > end else (0, 0, None) for pair in self.misspellings]

        self._recalculate()
        self.cursor.set_cursor(start, self.text)
        self.select.cursor = self.cursor.cursor

    def insert(self, segment):
        if self.take_selection():
            self.delete(self.cursor.cursor, self.select.cursor)
        
        s = len(segment)
        self.text[self.cursor.cursor:self.cursor.cursor] = segment
        self._recalculate()
        self.cursor.skip(s, self.text)
        self.select.cursor = self.cursor.cursor
        
        # fix spelling lines
        self.misspellings = [pair if pair[1] < self.cursor.cursor else (pair[0] + s, pair[1] + s, pair[2]) if pair[0] > self.cursor.cursor else (pair[0], pair[1] + s, pair[2]) for pair in self.misspellings]
    
    def bridge(self, tag, sign):
        S = self.take_selection()
        if S and '</p>' not in S:
            
            DA = 0
            
            I = self.cursor.cursor
            J = self.select.cursor

            P_1 = I - next(i for i, c in enumerate(self.text[I - 1::-1]) if character(c) == '<p>')
            P_2 = J + self.text[J:].index('</p>') + 1

            if sign:
                CAP = ('</f>', '<f>')
                
                self.text.insert(P_1, (CAP[0], tag))
                DA += 1
                
                P_2 += 1
                I += 1
                J += 1
            else:
                CAP = ('<f>', '</f>')
            
            paragraph = self.text[P_1:P_2]
            
            # if selection falls on top of range
            if character(self.text[I - 1]) == CAP[0]:
                I -= next(i for i, c in enumerate(self.text[I - 2::-1]) if character(c) != CAP[0]) + 1

            if character(self.text[J]) == CAP[1]:
                J += next(i for i, c in enumerate(self.text[J + 1:]) if character(c) != CAP[1]) + 1

            if sign:
                ftags = [(i + P_1, e[0]) for i, e in enumerate(paragraph) if e == (CAP[1], tag) or e == (CAP[0], tag)] + [(P_2, CAP[1])] + [(None, None)]
            else:
                ftags = [(i + P_1, e[0]) for i, e in enumerate(paragraph) if e == (CAP[1], tag) or e == (CAP[0], tag)] + [(None, None)]
            
            pairs = []
            for i in reversed(range(len(ftags) - 2)):
                if (ftags[i][1], ftags[i + 1][1]) == CAP:
                    pairs.append((ftags[i][0], ftags[i + 1][0]))
                    del ftags[i:i + 2]
            
            # ERROR CHECKING
            if ftags != [(None, None)]:
                print ('INVALID TAG SEQUENCE, REMNANTS: ' + str(ftags))
            
            instructions = []
            drift_i = 0
            drift_j = 0

            for pair in pairs:
                if pair[1] <= I or pair[0] >= J:
                    pass
                elif pair[0] >= I and pair[1] <= J:
                    instructions += [(pair[0], False), (pair[1], False)]
                    DA -= 2
                    
                    drift_j += -2
                elif I < pair[1] <= J:
                    instructions += [(pair[1], False), (I, True, (CAP[1], tag) )]
                    if not sign:
                        drift_i += 1
                elif I <= pair[0] < J:
                    instructions += [(pair[0], False), (J, True, (CAP[0], tag) )]
                    if not sign:
                        drift_j += -1
                elif pair[0] < I and pair[1] > J:
                    instructions += [(I, True, (CAP[1], tag) ), (J, True, (CAP[0], tag) )]
                    DA += 2
                    
                    if sign:
                        drift_j += 2
                    else:
                        drift_i += 1
                        drift_j += 1

            if instructions:
                activity = True
                
                instructions.sort(reverse=True)
                for instruction in instructions:
                    if instruction[1]:
                        self.text.insert(instruction[0], instruction[2])
                    else:
                        del self.text[instruction[0]]
            else:
                activity = False
            
            if sign:
                if self.text[P_1] == (CAP[0], tag):
                    del self.text[P_1]
                    DA -= 1
                    
                    drift_i -= 1
                    drift_j -= 1

                else:
                    self.text.insert(P_1, (CAP[1], tag) )
                    DA += 1
                    
                    drift_j += 1

            
            if activity:
                self.cursor.cursor = I + drift_i
                self.select.cursor = J + drift_j
                
                self._recalculate()
                
                # redo spelling for this paragraph
                self.misspellings = [pair if pair[1] < P_1 else
                        (pair[0] + DA, pair[1] + DA, pair[2]) if pair[0] > P_2 else
                        (0, 0, 0) for pair in self.misspellings ]
                # paragraph has changed
                self.misspellings += words(self.text[P_1:P_2 + DA] + ['</p>'], startindex=P_1, spell=True)[1]
                
                return True
            else:
                return False
                
    def _sort_cursors(self):
        if self.cursor.cursor > self.select.cursor:
            self.cursor.cursor, self.select.cursor = self.select.cursor, self.cursor.cursor
    
    def expand_cursors(self):
        # order
        self._sort_cursors()
        
        if character(self.text[self.cursor.cursor - 1]) == '<p>' and character(self.text[self.select.cursor]) == '</p>':
            self.cursor.cursor = 1
            self.select.cursor = len(self.text) - 1
        else:
            self.select.cursor += self.text[self.select.cursor:].index('</p>')
            self.cursor.cursor = self.pp_at()[1] + 1
    
    def expand_cursors_word(self):

        try:
            # select block of spaces
            if self.text[self.select.cursor] == ' ':
                I = next(i for i, c in enumerate(self.text[self.select.cursor::-1]) if c != ' ') - 1
                self.cursor.cursor -= I
                
                J = next(i for i, c in enumerate(self.text[self.select.cursor:]) if c != ' ')
                self.select.cursor += J
            
            # select block of words
            elif character(self.text[self.select.cursor]) not in _breaking_chars:
                I = next(i for i, c in enumerate(self.text[self.select.cursor::-1]) if character(c) in _breaking_chars) - 1
                self.cursor.cursor -= I
                
                J = next(i for i, c in enumerate(self.text[self.select.cursor:]) if character(c) in _breaking_chars)
                self.select.cursor += J
            
            # select block of punctuation
            else:
                I = next(i for i, c in enumerate(self.text[self.select.cursor::-1]) if character(c) not in _breaking_chars or c == ' ') - 1
                self.cursor.cursor -= I
                
                # there can be only breaking chars at the end (</p>)
                try:
                    J = next(i for i, c in enumerate(self.text[self.select.cursor:]) if character(c) not in _breaking_chars or c == ' ')
                    self.select.cursor += J
                except StopIteration:
                    self.select.cursor = len(self.text) - 1

        except ValueError:
            pass


    ### FUNCTIONS USEFUL FOR DRAWING AND INTERFACE
    
    def line_indices(self, l):
        return self._SLUGS[l]['i'], self._SLUGS[l]['j']

    # get x position of specific glyph
    def text_index_x(self, i):
        line = self._SLUGS[self.index_to_line(i)]
        try:
            glyph = line['GLYPHS'][i - line['i']]
        except IndexError:
            glyph = line['GLYPHS'][-1]

        return glyph[1] + line['x']

    def stats(self, spell):
        if spell:
            self.word_count, self.misspellings = words(self.text, spell=True)
        else:
            self.word_count = words(self.text)
    
    def styling_at(self):
        i = self.cursor.cursor
        line = self._SLUGS[self.index_to_line(i)]
        try:
            glyph = line['GLYPHS'][i - line['i']]
        except IndexError:
            glyph = line['GLYPHS'][-1]

        return line['PP'], glyph[3]
    
    def pp_at(self):
        return self._SLUGS[self.index_to_line(self.cursor.cursor)]['PP']

    def extract_glyphs(self, refresh=False):
        if refresh:
            self._sorted_pages = {}

        if not self._sorted_pages:
            for page, pageslugs in ((p, list(ps)) for p, ps in groupby((line for line in self._SLUGS), key=lambda line: line['page'])):
                if page not in self._sorted_pages:
                    self._sorted_pages[page] = {'_annot': [], '_images': [], '_lines': ([], [])}
                sorted_page = self._sorted_pages[page]
                sorted_page['_lines'][0].extend(pageslugs)
                sorted_page['_lines'][1].extend(line['l'] for line in pageslugs)
                
                for line in pageslugs:
                    line.deposit(sorted_page)

        return self._sorted_pages
