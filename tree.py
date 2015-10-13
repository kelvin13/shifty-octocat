from state import constants

from interface import karlie
from interface import taylor
from interface import menu


def take_event(x, y, event, key=False, char=None, region=['document', 'document'], geometry=None):

    if key:
        if region[0] == 'document':
            return taylor.becky.key_input(event, char)
                
        elif region[0] == 'properties':
            return karlie.klossy.key_input(event, char)
                
    else:
        # Changing regions
        
        if x > geometry[0] - constants.propertieswidth:
            if region[1] != 'properties':
                region[1] = 'properties'
            if event == 'press' and region[0] != 'properties':
                region[0] = 'properties'

        else:
            if region[1] != 'document':
#                noticeboard.refresh.push_change()

                if event == 'motion':
                    karlie.klossy.hover(x, y)
                region[1] = 'document'
            if event == 'press' and region[0] != 'document':
                # if we're going from properties to document, dump properties
                if region[0] == 'properties':
                    karlie.klossy.press(x, y)
                region[0] = 'document'


        if menu.menu.menu():
            if menu.menu.in_bounds(x, y):
                if event == 'motion':
                    menu.menu.hover(y)
                    x, y = -1, -1
                    
                if event == 'press':
                    menu.menu.press(y)
                    return
            
            menu.menu.test_change()

        #############
        
        if event == 'press':
            menu.menu.destroy()
            if region[0] == 'document':
                taylor.becky.press(x, y)
                    
            elif region[0] == 'properties':
                karlie.klossy.press(x, y)
                
        elif event == 'press_motion':
            if region[0] == 'document':
                taylor.becky.press_motion(x, y)
                    
            elif region[0] == 'properties':
                karlie.klossy.press_motion(x)
                
        elif event == 'release':
            if region[0] == 'document':
                taylor.becky.release(x, y)
                
        elif event == 'motion':
#            controls.update(x, y)
            if region[1] == 'properties':
                karlie.klossy.hover(x, y)
            else:
                taylor.becky.hover(x, y)
