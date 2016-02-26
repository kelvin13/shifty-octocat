from style import styles
from edit import cursor, caramel
from state import noticeboard

class Text_context(object):
    def __init__(self):
        self.pp = None
        self.p = None
        self.f = None
        self.char = None
        
        self.ct = None
        self.c = None
        
        self.changed = set()

    def done(self, U):
        if U in self.changed:
            self.changed.remove(U)

    def update(self):
        PP, FSTYLE = cursor.fcursor.styling_at()
        C = cursor.fcursor.text[cursor.fcursor.i]
        
        if PP is not self.pp:
            self.changed.update({'paragraph'})
            self.pp = PP
            self.p = styles.PARASTYLES.project_p(PP)
        
        if FSTYLE != self.f:
            self.changed.update({'font'})
            self.f = FSTYLE
        
        if C is not self.char:
            self.changed.update({'character'})
            self.char = C

    def update_channels(self):
        ct, c = caramel.delight.at()
        if c != self.c or ct is not self.ct:
            self.changed.update({'channels'})
            self.c = c
            self.ct = ct

    def update_force(self):
        PP, FSTYLE = cursor.fcursor.styling_at()
        C = cursor.fcursor.text[cursor.fcursor.i]
        
        self.changed.update({'paragraph'})
        self.pp = PP
        self.p = styles.PARASTYLES.project_p(PP)
    
        self.changed.update({'font'})
        self.f = FSTYLE
    
        self.changed.update({'character'})
        self.char = C
        
        self.ct, self.c = caramel.delight.at()
        self.changed.update({'channels'})

Text = Text_context()
