import bisect
from model import olivia
from model.wonder import words, character, _breaking_chars

def outside_tag(sequence):
    for i in reversed(range(len(sequence) - 1)):

        if (character(sequence[i]), sequence[i + 1]) == ('<p>', '</p>'):
            del sequence[i:i + 2]

    return sequence

class FCursor(object):
    def __init__(self, ftext, i, j):
        self._ftx = ftext
        self.text = ftext.text
        self.i = i
        self.j = j

    def skip(self, i, jump):
        i += jump
        # prevent overruns
        i = min(len(self.text) - 1, max(1, i))
        if character(self.text[i]) == '<p>':
            direction = 1
            if jump < 0:
                direction = -1
            while True:
                i += direction
                if character(self.text[i]) != '<p>':
                    break
        return i

    def _sort_cursors(self):
        self.i, self.j = sorted((self.i, self.j))

    # get line number given character index
    def index_to_line(self, index):
        return bisect.bisect(self._ftx._line_startindices, index) - 1
    
    # get x position of specific glyph
    def text_index_x(self, i):
        line = self._ftx._SLUGS[self.index_to_line(i)]
        try:
            glyph = line['GLYPHS'][i - line['i']]
        except IndexError:
            glyph = line['GLYPHS'][-1]

        return glyph[1] + line['x']
    
    def paint(self):
        i, j = sorted((self.i, self.j))

        l1 = self.index_to_line(i)
        l2 = self.index_to_line(j)

        start = self.text_index_x(i)
        stop = self.text_index_x(j)

        # chained multipage
        if type(self._ftx) is olivia.Chained_text:
            PAGES = {}
            for page, V in self._ftx._sorted_pages.items():
                lines, lineindexes = V['_lines'] 
                if l2 >= lineindexes[0] and l1 <= lineindexes[-1]:
                    bs1 = max(0, bisect.bisect(lineindexes, l1) - 1)
                    bs2 = bisect.bisect(lineindexes, l2)
                    PAGES[page] = lines[bs1:bs2]

        # single page
        else:
            lines = self._ftx._SLUGS
            lineindexes = [line['l'] for line in lines]
            bs1 = max(0, bisect.bisect(lineindexes, l1) - 1)
            bs2 = bisect.bisect(lineindexes, l2)
            PAGES = {lines[0]['page']: lines[bs1:bs2]}
        
        ftags = {'<f>', '</f>'}
        signs = ((character(self.text[self.i - 1]) in ftags, character(self.text[self.i]) in ftags) , 
                (character(self.text[self.j - 1]) in ftags, character(self.text[self.j]) in ftags))
        return PAGES, l1, l2, start, stop, signs
    
    def take_selection(self):
        if self.i == self.j:
            return False
        else:
            self._sort_cursors()
            return self.text[self.i:self.j]

    def delete(self, start=None, end=None, da=0, db=0):
        self._sort_cursors()

        if start is None:
            start = self.i + da
            
        if end is None:
            end = self.j + db

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
        self._ftx.misspellings = [pair if pair[1] < start else (pair[0] + offset, pair[1] + offset, pair[2]) if pair[0] > end else (0, 0, None) for pair in self._ftx.misspellings]

        self._ftx._dbuff(self.index_to_line( min(self.i, self.j) ))
        self.i = self.skip(self.i + da, 0)
        self.j = self.i

    def insert(self, segment):
        if self.take_selection():
            self.delete(self.i, self.j)
        
        s = len(segment)
        self.text[self.i:self.j] = segment
        self._ftx._dbuff(self.index_to_line( min(self.i, self.j) ))
        self.i = self.skip(self.i + s, 0)
        self.j = self.i
        
        # fix spelling lines
        self._ftx.misspellings = [pair if pair[1] < self.i else (pair[0] + s, pair[1] + s, pair[2]) if pair[0] > self.i else (pair[0], pair[1] + s, pair[2]) for pair in self._ftx.misspellings]

    def expand_cursors(self):
        # order
        self._sort_cursors()
        
        if character(self.text[self.i - 1]) == '<p>' and character(self.text[self.j]) == '</p>':
            self.i = 1
            self.j = len(self.text) - 1
        else:
            self.j += self.text[self.j:].index('</p>')
            self.i -= next(i for i, v in enumerate(self.text[self.i::-1]) if character(v) == '<p>') - 1

    def expand_cursors_word(self):
        try:
            # select block of spaces
            if self.text[self.i] == ' ':
                I = next(i for i, c in enumerate(self.text[self.j::-1]) if c != ' ') - 1
                self.i -= I
                
                J = next(i for i, c in enumerate(self.text[self.j:]) if c != ' ')
                self.j += J
            
            # select block of words
            elif character(self.text[self.j]) not in _breaking_chars:
                I = next(i for i, c in enumerate(self.text[self.j::-1]) if character(c) in _breaking_chars) - 1
                self.i -= I
                
                J = next(i for i, c in enumerate(self.text[self.j:]) if character(c) in _breaking_chars)
                self.j += J
            
            # select block of punctuation
            else:
                I = next(i for i, c in enumerate(self.text[self.j::-1]) if character(c) not in _breaking_chars or c == ' ') - 1
                self.i -= I
                
                # there can be only breaking chars at the end (</p>)
                try:
                    J = next(i for i, c in enumerate(self.text[self.j:]) if character(c) not in _breaking_chars or c == ' ')
                    self.j += J
                except StopIteration:
                    self.j = len(self.text) - 1

        except ValueError:
            pass

    def bridge(self, tag, sign):
        S = self.take_selection()
        if S and '</p>' not in S:
            
            DA = 0
            
            I = self.i
            J = self.j

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
                self.i = I + drift_i
                self.j = J + drift_j
                
                self._ftx._dbuff(self.index_to_line( min(self.i, self.j) ))
                
                # redo spelling for this paragraph
                self._ftx.misspellings = [pair if pair[1] < P_1 else
                        (pair[0] + DA, pair[1] + DA, pair[2]) if pair[0] > P_2 else
                        (0, 0, 0) for pair in self._ftx.misspellings ]
                # paragraph has changed
                self._ftx.misspellings += words(self.text[P_1:P_2 + DA] + ['</p>'], startindex=P_1, spell=True)[1]
                
                return True
            else:
                return False

    def pp_at(self):
        return self._ftx._SLUGS[self.index_to_line(self.i)]['PP']

    def styling_at(self):
        line = self._ftx._SLUGS[self.index_to_line(self.i)]
        try:
            glyph = line['GLYPHS'][self.i - line['i']]
        except IndexError:
            glyph = line['GLYPHS'][-1]

        return line['PP'], glyph[3]

    def front_and_back(self):
        return self._ftx.line_indices(self.index_to_line(self.i))

fcursor = None