import bisect
from itertools import groupby
from bulletholes.counter import TCounter as Counter
from model.wonder import character
from fonts import styles

from pyphen import pyphen
pyphen.language_fallback('en_US')

hy = pyphen.Pyphen(lang='en_US')

# linebreaking characters
_BREAK_WHITESPACE = set((' '))
_BREAK_ONLY_AFTER = set('-.,/')
_BREAK_AFTER_ELSE_BEFORE = set('–—')

_BREAK = _BREAK_WHITESPACE | _BREAK_ONLY_AFTER | _BREAK_AFTER_ELSE_BEFORE

_BREAK_P = _BREAK | set(('</p>',))

_APOSTROPHES = set("'’")

class _Glyphs_line(dict):
    def I(self, x, y):
        x -= self['x']
        y -= self['y']
        i = bisect.bisect(self['_X_'], x)
        if i:
            try:
                # compare before and after glyphs
                x1, x2 = self['_X_'][i - 1 : i + 1]
                if x2 - x > x - x1:
                    i -= 1
            except ValueError:
                i -= 1
        return i + self['i']

    def deposit(self, repository):
        x = self['x']
        y = self['y']
        p_i = self['PP'][1]
        hyphen = self['hyphen']

        if hyphen is not None:
            glyphs = self['GLYPHS'] + [hyphen]
        else:
            glyphs = self['GLYPHS']
        
        for glyph in glyphs:
            if glyph[0] < 0:
                if glyph[0] == -6:
                    repository['_annot'].append( (glyph[0], x, y + self['leading'], p_i, glyph[3]))
                elif glyph[0] == -13:
                    repository['_images'].append( (glyph[6], glyph[1] + x, glyph[2] + y) )
                else:
                    repository['_annot'].append((glyph[0], glyph[1] + x, glyph[2] + y) + (p_i, glyph[3]))
            else:
                K = (glyph[0], glyph[1] + x, glyph[2] + y)
                N = glyph[3]['hash']
                try:
                    repository[N][1].append(K)
                except KeyError:
                    repository[N] = (glyph[3], [K])

def cast_liquid_line(letters, startindex, width, leading, P, F, hyphenate=False):
    LINE = _Glyphs_line({
            'i': startindex,
            
            'width': width,           
            'leading': leading,

            'hyphen': None,
            
            'P_BREAK': False,
            'F': F
            })
    
    # list that contains glyphs
    GLYPHS = []
    x = 0
    y = 0

    # retrieve font style
    fstat = F.copy()
    FSTYLE = styles.PARASTYLES.project_f(P, F)

    # blank pegs
    glyphwidth = 0
    gx = 0
    gy = 0
    effective_peg = None
    
    # style brackets
    brackets = {}
    for f, count in F.items():
        for V in [f.name] + f.groups:
            if V not in brackets:
                brackets[V] = [[0, False] for c in range(count)]
            else:
                brackets[V] += [[0, False] for c in range(count)]

    root_for = set()
    front = x

    for letter in letters:
        CHAR = character(letter)

        if CHAR == '<f>':
            T = letter[1]
            TAG = T.name
            
            # increment tag count
            F[T] += 1
            fstat = F.copy()
            
            # calculate pegging
            G = FSTYLE['pegs'].elements
            if T in G:                
                gx, gy = G[T]
                gx = gx * glyphwidth
                gy = gy * leading
                effective_peg = T
                
                y -= gy
                x += gx
            
            elif effective_peg not in G:
                effective_peg = None
            
            if root_for:
                for group in T.groups:
                    if group in root_for:
                        x = brackets[group][-1][0]
                        root_for = set()
            
            # collapsibility
            for V in [TAG] + T.groups:
                if V not in brackets:
                    brackets[V] = [[x, False]]
                else:
                    brackets[V].append([x, False])
            
            FSTYLE = styles.PARASTYLES.project_f(P, F)
            GLYPHS.append((-4, x, y, FSTYLE, fstat, x))
            
        elif CHAR == '</f>':
            T = letter[1]
            TAG = T.name
            
            # increment tag count
            F[T] -= 1
            fstat = F.copy()

            # depeg
            if T is effective_peg:
                y += gy

            for V in [TAG] + T.groups:
                try:
                    if brackets[V][-1][1]:
                        del brackets[V][-1]
                    brackets[V][-1][1] = True
                except IndexError:
                    print('line begins with close tag character')
            root_for.update(set(T.groups))
            
            # calculate pegging
            G = FSTYLE['pegs'].elements
            if TAG in G:
                if front > x:
                    x = front
                else:
                    front = x
            
            FSTYLE = styles.PARASTYLES.project_f(P, F)
            GLYPHS.append((-5, x, y, FSTYLE, fstat, x))
            
        elif CHAR == '<p>':
            if GLYPHS:
                break
            else:
                # we don’t load the style because the outer function takes care of that
                GLYPHS.append((
                        -2,                      # 0
                        x - FSTYLE['fontsize'],  # 1
                        y,                       # 2
                        
                        FSTYLE,                  # 3
                        fstat,                   # 4
                        x - FSTYLE['fontsize']   # 5
                        ))
        
        elif CHAR == '</p>':
            LINE['P_BREAK'] = True
            GLYPHS.append((-3, x, y, FSTYLE, fstat, x))
            break
        
        elif CHAR == '<br>':
            root_for = set()
            GLYPHS.append((-6, x, y, FSTYLE, fstat, x))
            break

        else:
            root_for = set()
            if CHAR == '<image>':
                IMAGE = letter[1]
                glyphwidth = IMAGE[1]
                                                                 # additional fields
                GLYPHS.append((-13, x, y - leading, FSTYLE, fstat, x + glyphwidth, IMAGE))

            else:
                glyphwidth = FSTYLE['fontmetrics'].advance_pixel_width(CHAR) * FSTYLE['fontsize']
                GLYPHS.append((
                        FSTYLE['fontmetrics'].character_index(CHAR),    # 0
                        x,                                              # 1
                        y,                                              # 2
                        
                        FSTYLE,                                         # 3
                        fstat,                                          # 4
                        x + glyphwidth                                  # 5
                        ))
            
            x += glyphwidth

            # work out line breaks
            if x > width:
                n = len(GLYPHS)
                if CHAR not in _BREAK_WHITESPACE:

                    LN = letters[:n]

                    try:
                        if CHAR in _BREAK_ONLY_AFTER:
                            i = next(i + 1 for i, v in zip(range(n - 2, 0, -1), reversed(LN[:-1])) if v in _BREAK)
                        elif CHAR in _BREAK_AFTER_ELSE_BEFORE:
                            i = len(LN) - 1
                        else:
                            i = next(i + 1 for i, v in zip(range(n - 1, 0, -1), reversed(LN)) if v in _BREAK)
                    
                    except StopIteration:
                        del GLYPHS[-1]
                        i = 0
                    
                    ### AUTO HYPHENATION
                    if hyphenate:
                        try:
                            j = i + next(i for i, v in enumerate(letters[i:]) if v in _BREAK_P)
                        except StopIteration:
                            j = i + 1989
                        except TypeError:
                            j = i
                        
                        word = ''.join([c if len(c) == 1 and c.isalpha() else "'" if c in _APOSTROPHES else ' ' for c in letters[i:j] ])

                        leading_spaces = len(word) - len(word.lstrip(' '))

                        for pair in hy.iterate(word.strip(' ')):
                            k = len(pair[0]) + leading_spaces
                            # no sense checking hyphenations that don’t fit
                            if k >= n - i:
                                continue
                            # prevent too-short hyphenations
                            elif len(pair[0].replace(' ', '')) < 2 or len(pair[1].replace(' ', '')) < 2:
                                continue
                            
                            # check if the hyphen overflows

                            h_F = GLYPHS[i - 1 + k][4]
                            HFS = styles.PARASTYLES.project_f(P, h_F)
                                
                            if GLYPHS[i - 1 + k][5] + HFS['fontmetrics'].advance_pixel_width('-') * HFS['fontsize'] < width:
                                i = i + k

                                LINE['hyphen'] = (
                                        HFS['fontmetrics'].character_index('-'), 
                                        GLYPHS[i - 1][5], # x
                                        GLYPHS[i - 1][2], # y
                                        HFS,
                                        h_F
                                        )
                                break
                    ####################
                    if i:
                        del GLYPHS[i:]

                elif letters[n] == '</p>':
                    continue
                break
                
            else:
                x += FSTYLE['tracking']

    LINE['j'] = startindex + len(GLYPHS)
    LINE['GLYPHS'] = GLYPHS
    # cache x's
    LINE['_X_'] = [g[1] for g in GLYPHS]
    
    try:
        LINE['F'] = GLYPHS[-1][4]
    except IndexError:
        pass
    
    return LINE

class Toplevel_bounds(object):
    def __init__(self, channels):
        self.channels = channels
    
#    def activate(self, c):
#        channel = self.channels[c]
#        self.y = channel.railings[0][0][1]
#        self._bottom = channel.railings[0][-1][1]
#        self.page = channel.page
#        self._channel = channel
#        self.c = c
    
    def test(self, c, y, displacement):
        if y > self.channels[c].railings[1][-1][1] and c < len(self.channels) - 1:
            c += 1
            y = self.channels[c].railings[0][0][1] + displacement
            
        x1 = self.channels[c].edge(0, y)[0]
        x2 = self.channels[c].edge(1, y)[0]
        
        return x1, x2, y, c, self.channels[c].page
    
    def copy(self):
        return type(self)(self.channels)
        

def typeset_liquid(bounds, LIQUID, SLUGS, l, i, c=0, y=None, nest=0):
    if not l:
        SLUGS.clear()
        # which happens if nothing has yet been rendered
        P = LIQUID[0][1]
        PSTYLE = styles.PARASTYLES.project_p(P)
        P_i = 0
        F = Counter()
        
        R = 0
        if y is None:
            y = bounds.channels[c].railings[0][0][1]
    
    else:
        # ylevel is the y position of the first line to print
        # here we are removing the last existing line so we can redraw that one as well
        CURRENTLINE = SLUGS.pop()
        LASTLINE = SLUGS[-1]
        
        if LASTLINE['P_BREAK']:
            P = LIQUID[i][1]
            P_i = i
            F = Counter()

        else:
            P, P_i = LASTLINE['PP']
            F = LASTLINE['F'].copy()
        PSTYLE = styles.PARASTYLES.project_p(P)
        
        R = CURRENTLINE['R']
        
        c = CURRENTLINE['c']
        y = CURRENTLINE['y'] - PSTYLE['leading']
    
    page = bounds.channels[c].page
    K_x = None
    
    displacement = PSTYLE['leading']

    while True:
        y += displacement
        
        # see if the lines have overrun the portals
        x1, x2, y, c, page = bounds.test(c, y, displacement)

        # calculate indentation

        if R in PSTYLE['indent_range']:
            D, SIGN, K = PSTYLE['indent']
            if K:
                if K_x is None:
                    INDLINE = cast_liquid_line(
                        LIQUID[P_i : P_i + K + 1], 
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
        x1 += L_indent
        x2 -= R_indent
        if x1 > x2:
            x1, x2 = x2, x1
        LINE = cast_liquid_line(
                LIQUID[i : i + 1989], 
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

            if i > len(LIQUID) - 1:
                SLUGS.append(LINE)
                # this is the end of the document
                break
            
            y += PSTYLE['margin_bottom']

            if LIQUID[i][0] == '<table>':
                TBL = LIQUID[i]
                TBL.fill(bounds.copy(), c, y)
                i += 1
            
            P = LIQUID[i][1]
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
        SLUGS.append(LINE)

    _line_startindices = [line['i'] for line in SLUGS]
    _line_yl = { cc: list(h[:2] for h in list(g)) for cc, g in groupby( ((LINE['y'], LINE['l'], LINE['c']) for LINE in SLUGS if LINE['GLYPHS']), key=lambda k: k[2]) }
    
    return _line_startindices, _line_yl
