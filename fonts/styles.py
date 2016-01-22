import itertools
from bulletholes.counter import TCounter as Counter

from fonts import fonts
from state import constants
from freetype import ft_errors

def _sign_counter(counter):
    return ''.join(K.name + str(V) for K, V in sorted(counter.items(), key=lambda T: T[0].name))

def _new_name(name, namelist):
    if name in namelist:
        if not (len(name) > 3 and name[-4] == '.' and len([c for c in name[-3:] if c in '1234567890']) == 3):
            name = name + '.001'
        
        serialnumber = int(name[-3:])
        while True:
            if name not in namelist:
                break
            serialnumber += 1
            name = name[:-3] + str(serialnumber).zfill(3)
    return name

class Layer(dict):
    def __init__(self, DNA):
        dict.__init__(self, DNA)
        self.Z = {A: None for A in DNA}
        self.members = []
    
    def overlay(self, D, B):
        for A, V in D.items():
            self[A] = V
            self.Z[A] = B

class Active_list(list):
    def __init__(self, active, template, * args, ** kwargs):
        self.active = active
        self.template = template
        list.__init__(self, * args, ** kwargs)

class _DB(object):
    def __init__(self, name, library):
        self._LIBRARY = library
        self.name = _new_name(name, self._LIBRARY)

    def rename(self, name):
        name = _new_name(name, self._LIBRARY)
        self._LIBRARY[name] = self._LIBRARY.pop(self.name)
        self.name = name

    def clone(self):
        name = _new_name(self.name, self._LIBRARY)
        self._LIBRARY[name] = self._copy(name)
        return self._LIBRARY[name]

    def _copy(self, name):
        return type(self)(self.polaroid(), name)

class _DB_with_dict(_DB):
    def __init__(self, elements, active, name, library):
        _DB.__init__(self, name, library)
        self.active = active
        self.elements = elements

    def _delete_element(self, key=None):
        if key is None or self.active == key:
            del self.elements[self.active]
            if self.elements:
                keys = list(sorted(self.elements.keys()))
                if self.active == keys[0]:
                    self.active = keys[-1]
                else:
                    self.active = keys[0]
            else:
                self.active = None
        else:
            del self.elements[key]

class DB_Pegs(_DB_with_dict):
    def __init__(self, pegs=('', {}), name='New peg set'):
        ACT = None
        E = {FTAGS[k]: v for k, v in pegs[1].items()}
        _DB_with_dict.__init__(self, E, ACT, name, PEGS)

        if pegs[0]:
            self.applies_to = set(pegs[0])
        else:
            self.applies_to = None

    def add_slot(self, key=None):
        self.elements[key] = [0, 0]
        self.active = self.elements[key]
    
    def delete_slot(self, key=None):
        self._delete_element(key)

    def polaroid(self):
        D = {k.name: v.copy() for k, v in self.elements.items()}
        if self.applies_to:
            C = ''.join(self.applies_to)
        else:
            C = ''
        return (C, D)

class P_Library(list):
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self._projections = {}
        self._font_projections = {}
        
        self.active = None
        
        self.update_f = self._font_projections.clear
    
    def project_p(self, P):
        hp = _sign_counter(P)
        try:
            return self._projections[hp]
        except KeyError:
            # iterate through stack
            projection = Layer(P_DNA)
            for B in (b for b in self if b.tags <= P):
                projection.overlay(B.attributes, B)
                projection.members.append(B)
            
            self._projections[hp] = projection
            return projection
    
    def project_f(self, P, F):
        hf = _sign_counter(F)
        hp = _sign_counter(P)

        # add tag groups
        F = F + Counter(itertools.chain.from_iterable((FTAGS[G] for G in T.groups) for T, n in F.items() if n))
            
        try:
            return self._font_projections[(hp, hf)]
        except KeyError:
            # iterate through stack
            projection = Layer(F_DNA)

            for B in (b for b in self if b.tags <= P):
                for C in (c for c in B.layerable if c.tags <= F and c.F is not None):
                    projection.overlay(C.F.attributes, C)
                    projection.members.append(C)

            # set up fonts
            try:
                projection['fontmetrics'] = fonts.Memo_font(projection['path'])
                projection['font'] = fonts.get_cairo_font(projection['path'])
            except ft_errors.FT_Exception:
                path = F_DNA['path']
                projection['color'] = F_DNA['color']
                projection['fontmetrics'] = fonts.Memo_font(path)
                projection['font'] = fonts.get_cairo_font(path)
            
            projection['hash'] = hash(hp + hf)
            
            self._font_projections[(hp, hf)] = projection
            return projection
    
    def update_p(self):
        self._projections.clear()
        self._font_projections.clear()

class DB_Fontstyle(_DB):
    def __init__(self, fdict={}, name='New fontclass'):
        _DB.__init__(self, name, library=FONTSTYLES)

        if 'pegs' in fdict:
            fdict['pegs'] = PEGS[fdict['pegs']]
        self.attributes = fdict
        
#        ('path', 'fontsize', 'tracking', 'color')
    def polaroid(self):
        fdict = self.attributes.copy()
        if 'pegs' in fdict:
            fdict['pegs'] = fdict['pegs'].name
        return fdict

class _F_container(object):
    def __init__(self, F=None, count=Counter()):
        self.F = F
        self.tags = count
    
    def copy(self):
        return type(self)(F, self.tags.copy())

class DB_Parastyle(object):
    def __init__(self, pdict={}, count=Counter()):
        self.tags = count
        if 'fontclasses' in pdict:
            E = pdict.pop('fontclasses')
            # link fontstyle objects
            self.layerable = Active_list(None, _F_container(), (_F_container(FONTSTYLES[F], Counter(FTAGS[T] for T in tags)) for tags, F in E))
        else:
            self.layerable = Active_list(None, _F_container())
        self.attributes = pdict
        
#        ('leading', 'indent', 'indent_range', 'margin_bottom', 'margin_top', 'margin_left', 'margin_right', 'hyphenate')
    def polaroid(self):
        pdict = self.attributes.copy()
        if self.layerable:
            pdict['fontclasses'] = [({T.name: V for T, V in F.tags.items()} , F.F.name) for F in self.layerable]
        return pdict, {T.name: V for T, V in self.tags.items()}

    def copy(self):
        P = self.polaroid()[0]
        return type(self)(P, self.tags.copy())

class Tag(_DB):
    def __init__(self, library, name, groups, is_group = False):
        _DB.__init__(self, name, library)
        self.groups = groups
        self.is_group = is_group
    def polaroid(self):
        return (self.name, self.groups)
    

class T_Library(dict):
    def __init__(self, * args, ** kwargs):
        dict.__init__(self, * args, ** kwargs)
        self.active = None

    def populate(self, L):
        self.clear()
        D = {T[0]: Tag(self, * T) for T in L}
        groups = set(itertools.chain.from_iterable(G for T, G in L))
        D.update({G: Tag(self, G, [G], True) for G in groups})
        self.update(D)
    
    def add_slot(self):
        if self.active is not None:
            current = self.active.name
        else:
            current = 'New tag.000'
        name = _new_name(current, self)
        self[name] = Tag(self, name, [])
    
    def delete_slot(self, key):
        del self[key]

P_DNA = {}
F_DNA = {}

PEGS = {}

FTAGS = T_Library()
PTAGS = T_Library()
FONTSTYLES = {}
PARASTYLES = P_Library()

ISTYLES = {}

# interface styles
def _create_interface():
    font_projections = {}
    FD = TREES(DB_Fontstyle, constants.interface_fstyles)
    P = [_F_container(FD[F], Counter(tags)) for tags, F in constants.interface_pstyle]
    ui_styles = ((), ('title',), ('strong',), ('label',))
    for U in ui_styles:
        F = Counter(U)
        # iterate through stack
        projection = F_DNA.copy()

        for C in (c.F for c in P if c.tags <= F):
            projection.update(C.attributes)

        # set up fonts
        try:
            projection['fontmetrics'] = fonts.Memo_font(projection['path'])
            projection['font'] = fonts.get_cairo_font(projection['path'])
        except ft_errors.FT_Exception:
            path = F_UNDEFINED.u_path
            projection['fontmetrics'] = fonts.Memo_font(path)
            projection['font'] = fonts.get_cairo_font(path)
        
        font_projections[U] = projection
    return font_projections

def TREES(DB_TYPE, tree):
    return {name: DB_TYPE(v, name) for name, v in tree.items()}

def faith(woods):
    FTAGS.populate(woods['FTAGLIST'])
    PTAGS.populate(woods['PTAGLIST'])
    PEGS.clear()
    FONTSTYLES.clear()
    PARASTYLES.clear()

    PEGS.update(TREES(DB_Pegs, woods['PEGS']))

    FONTSTYLES.update(TREES(DB_Fontstyle, woods['FONTSTYLES']))
    PARASTYLES[:] = [DB_Parastyle(P, Counter({PTAGS[T]: V for T, V in count.items()})) for P, count in woods['PARASTYLES']]

def daydream():
    # set up emergency undefined classes
    _G_DNA = DB_Pegs(('', {}), '_undefined')
    
    F_DNA.update({'fontsize': 13,
            'path': 'fonts/FreeMono.ttf',
            'pegs': _G_DNA,
            'tracking': 0,
            'color': (1, 0.15, 0.2, 1)})
    
    P_DNA.update({'hyphenate': False,
            'indent': (0, 0, 0),
            'indent_range': {0},
            'leading': 22,
            'margin_bottom': 0,
            'margin_left': 0,
            'margin_right': 0,
            'margin_top': 0})

    ISTYLES.update(_create_interface())