from state import constants, noticeboard

from meredith import datablocks, box, meta

from IO import tree

def save():
    from edit import cursor, caramel
    from interface import taylor
    FT = ''.join(('<head><meta charset="UTF-8"></head>\n<title>', meta.filedata.filename, '</title>\n\n',
                  tree.serialize([datablocks.DOCUMENT, datablocks.TSTYLES, datablocks.BSTYLES, cursor.fcursor, caramel.delight, taylor.becky.view]), '\n'))
    with open(meta.filedata['filepath'], 'w') as fi:
        fi.write(FT)

def load(name):
    with open(name, 'r') as fi:
        meta.filedata = meta.Metadata(name)
        doc = fi.read()
    
    datablocks.TTAGS, datablocks.BTAGS = tree.deserialize('<texttags/><blocktags/>')
    datablocks.DOCUMENT, datablocks.TSTYLES, datablocks.BSTYLES, * SETTINGS = tree.deserialize(doc)
    document = datablocks.DOCUMENT
    
    import keyboard
    from state.contexts import Text
    from edit import cursor, caramel
    
    # aim editor objects
    keyboard.keyboard = keyboard.Keyboard(constants.shortcuts)
    
    cursor.fcursor, caramel.delight, VIEW = unpack_peripheral_data(SETTINGS)
    cursor.fcursor.reset_functions(document, tree.serialize, tree.deserialize)
    caramel.delight.reset_functions(document)
    VIEW.reset_functions(document.map_X, document.map_Y)
    
    document.layout_all()
    Text.update()

    # start undo tracking
    from IO import un
    un.history = un.UN(tree.miniserialize, tree.deserialize)
    box.Box.before = un.history.save
    
    from interface import karlie, taylor
    
    taylor.becky = taylor.Document_view(save, document, VIEW)
    noticeboard.refresh_properties_type.push_change(VIEW.mode)
    karlie.klossy = karlie.Properties(VIEW.mode, partition=1 )

    un.history.save()

default_peripheral_data = (('textcursor', '<textcursor plane="0" i="0" j="0"/>'), 
    ('framecursor', '<framecursor section="0" frame="0"/>'), 
    ('view'       , '<view h="0" k="0" hc="0" kc="0" zoom="11" mode="text"/>'))

def unpack_peripheral_data(settings):
    nodes = {type(node).name: node for node in settings}
    for name, default_node in default_peripheral_data:
        if name in nodes:
            yield nodes[name]
        else:
            yield tree.deserialize(default_node)[0]
