from itertools import chain

from edit import cursor

from IO import un

class Keyboard(dict):
    def __init__(self, shortcuts):
        _OPEN = set(k[0] for k in shortcuts)
        self._CLOSE = set(k[1] for k in shortcuts)
        self._special_names = set(_OPEN) | set(self._CLOSE)
        
        dict.__init__(self, chain.from_iterable(((key1, name), (key2, name)) for key1, key2, name in shortcuts))
        
    def type_document(self, name, char):
        CURSOR = cursor.fcursor.i
        
        # Non replacing
        if name == 'Left':
            un.history.undo_save(0)
            cursor.fcursor.i = max(0, CURSOR - 1)
            cursor.fcursor.j = cursor.fcursor.i
                
        elif name == 'Right':
            un.history.undo_save(0)
            
            cursor.fcursor.i = min(CURSOR + 1, len(cursor.fcursor.text) - 1)
            cursor.fcursor.j = cursor.fcursor.i
            
        elif name == 'Up':
            un.history.undo_save(0)
            
            cursor.fcursor.hop(False)
            cursor.fcursor.j = cursor.fcursor.i
            
        elif name == 'Down':
            un.history.undo_save(0)
            
            cursor.fcursor.hop(True)
            cursor.fcursor.j = cursor.fcursor.i

        elif name in ['Home', 'End']:
            un.history.undo_save(0)

            i, j = cursor.fcursor.front_and_back()
            if name == 'Home':
                cursor.fcursor.i = i
                cursor.fcursor.j = i
            else:
                cursor.fcursor.i = j
                cursor.fcursor.j = j

        elif name == 'All':
            un.history.undo_save(0)
            
            cursor.fcursor.expand_cursors()
        
        # replacing
        elif name in ['BackSpace', 'Delete']:
            if cursor.fcursor.i != cursor.fcursor.j:
                un.history.undo_save(3)
                cursor.fcursor.delete()
            elif name == 'BackSpace':            
                un.history.undo_save(-1)
                cursor.fcursor.delete(da=-1)

            else:
                un.history.undo_save(-1)
                cursor.fcursor.delete(db=1)
        
        elif name == 'paragraph':
            un.history.undo_save(2)
            P1 = cursor.fcursor.PLANE.content[CURSOR[0]].copy_empty()
            if len(CURSOR) == 2:
                cursor.fcursor.insert([P1, P1])
            else:
                cursor.fcursor.insert([P1])
            
        elif name == 'Return':
            un.history.undo_save(1)
            cursor.fcursor.insert_chars(['<br/>'])
        elif name == 'Ctrl Alt':
            un.history.undo_save(1)
            cursor.fcursor.insert(kevin.deserialize('<mi char="' + char + '"/>', fragment=True))
            
        elif name == 'Paste':
            if char:
                un.history.undo_save(3)
                cursor.fcursor.insert(kevin.deserialize(char, fragment=True))
        
        elif name == 'Copy':
            sel = cursor.fcursor.take_selection()
            if sel:
                return kevin.serialize(sel)
        
        elif name == 'Cut':
            sel = cursor.fcursor.take_selection()
            if sel:
                un.history.undo_save(3)
                cursor.fcursor.insert([])
            
                return kevin.serialize(sel)

        elif name in self._special_names:
            if name in self._CLOSE:
                B = False
                F = CloseFontpost
            else:
                B = True
                F = OpenFontpost
            if cursor.fcursor.take_selection():
                un.history.undo_save(3)
                if not cursor.fcursor.bridge(self[name], B):
                    un.history.pop()
            else:
                un.history.undo_save(1)
                cursor.fcursor.insert([F({'class': self[name]})])
        else:
            un.history.undo_save(13)
            cursor.fcursor.insert_chars([char])
