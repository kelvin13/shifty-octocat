#import cProfile
#import interface

#cProfile.run('interface.main()')

import freetype
import timeit
import kevin

from text_t import character as ch

t = '<p class="h1"><f class="strong">Marie-Joseph Paul Yves Roch </f class="strong"></p><p><f class="strong">Gilbert du Motier de Lafayette, Marquis de Lafayette</f class="strong"> (<f class="emphasis">6 September 1757 – 20 May 1834</f class="emphasis">), in the U.S. often known simply as <f class="strong">Lafayette</f class="strong">, was a French aristocrat and military officer who fought for the United States in the American Revolutionary War. A close friend of George Washington, Alexander Hamilton, and Thomas Jefferson, Lafayette was a key figure in the French Revolution of 1789 and the July Revolution of 1830. Born in Chavaniac, in the province of Auvergne in south central France, Lafayette came from a wealthy landowning family. He followed its martial tradition, and was commissioned an officer at age 13. He became convinced that the American cause in its revolutionary war was noble, and travelled to the New World seeking glory in it. There, he was made a major general, though initially the 19-year-old was not given troops to command. Wounded during the Battle of Brandywine, he still managed to organize an orderly retreat. He served with distinction in the Battle of Rhode Island. In the middle of the war, he returned home to lobby for an increase in French support. He again sailed to America in 1780, and was given senior positions in the Continental Army. In 1781, troops in Virginia under his command blocked forces led by Cornwallis until other American and French forces could position themselves for the decisive Siege of Yorktown.</p><p>Lafayette returned to France and, in 1787, was appointed to the Assembly of Notables convened in response to the fiscal crisis. He was elected a member of the <f class="emphasis">Estates-General</f class="emphasis"> of 1789, where representatives met from the three traditional orders of French society—the clergy, the nobility, and the commoners. He helped write the <f class="emphasis">Declaration of the Rights of Man and of the Citizen</f class="emphasis">, with the assistance of Thomas Jefferson. After the storming of the Bastille, Lafayette was appointed commander-in-chief of the National Guard, and tried to steer a middle course through the French Revolution. In August 1792, the radical factions ordered his arrest. Fleeing through the Austrian Netherlands, he was captured by Austrian troops and spent more than five years in prison.</p><p>Lafayette returned to France after Napoleon Bonaparte secured his release in 1797, though he refused to participate in Napoleon\'s government. After the Bourbon Restoration of 1814, he became a liberal member of the Chamber of Deputies, a position he held for most of the remainder of his life. In 1824, President James Monroe invited Lafayette to the United States as the nation\'s guest; during the trip, he visited all twenty-four states in the union at the time, meeting a rapturous reception. During France\'s July Revolution of 1830, Lafayette declined an offer to become the French dictator. Instead, he supported Louis-Philippe as king, but turned against him when the monarch became autocratic. Lafayette died on 20 May 1834, and is buried in Picpus Cemetery in Paris, under soil from Bunker Hill. For his accomplishments in the service of both France and the United States, he is sometimes known as "The Hero of the Two Worlds".</p><p>Lafayette was born on 6 September 1757 to Michel Louis Christophe Roch Gilbert Paulette du Motier, Marquis de La Fayette, colonel of grenadiers, and Marie Louise Jolie de La Rivière, at the château de Chavaniac, in Chavaniac, near Le Puy-en-Velay, in the province of Auvergne (now Haute-Loire).[2][a]</p><p>Lafayette\'s lineage appears to be one of the oldest in Auvergne. Members of the family were noted for their contempt for danger.[3] His ancestor Gilbert de Lafayette III, a Marshal of France, was a companion-at-arms who in 1429 led Joan of Arc\'s army in Orléans. Lafayette\'s great-grandfather (his mother\'s paternal grandfather) was the Comte de La Rivière, until his death in 1770 commander of the Mousquetaires du Roi, or Black Musketeers, King Louis XV\'s personal horse guard.[4] According to legend, another ancestor acquired the crown of thorns during the Sixth Crusade.[5] Lafayette\'s uncle Jacques-Roch died fighting the Austrians and the marquis title passed to his brother Michel.[6]</p><p>Lafayette\'s father died on 1 August 1759. Michel de Lafayette was struck by a cannonball while fighting a British-led coalition at the Battle of Minden in Westphalia.[7] Lafayette became marquis and Lord of Chavaniac, but the estate went to his mother.[7] Devastated by the loss of her husband, she went to live in Paris with her father and grandfather.[4] Lafayette was raised by his paternal grandmother, Mme de Chavaniac, who had brought the château into the family with her dowry.[6]</p><p>In 1768, when Lafayette was 11, he was summoned to Paris to live with his mother and great-grandfather at the comte\'s apartments in the Luxembourg Palace. The boy was sent to school at the Collège du Plessis, part of the University of Paris, and it was decided that he would carry on the family martial tradition.[8] The comte, the boy\'s great-grandfather, enrolled the boy in a program to train future Musketeers.[9] Lafayette\'s mother and her grandfather died, on 3 and 24 April 1770 respectively, leaving Lafayette an income of 25,000 livres. Upon the death of an uncle, the 12-year-old Lafayette inherited a handsome yearly income of 120,000 livres.[7]</p><p>In May 1771, Lafayette was commissioned a sous-lieutenant in the Musketeers. His duties were mostly ceremonial (he continued his studies as usual), and included marching in military parades, and presenting himself to King Louis.[10] The next year, Jean-Paul-François de Noailles, Duc d\'Ayen, was looking to marry off some of his five daughters. The young Lafayette, aged 14, seemed a good match for his 12-year-old daughter, Marie Adrienne Françoise, and the duc spoke to the boy\'s guardian (Lafayette\'s uncle, the new comte) to negotiate a deal.[11] However, the arranged marriage was opposed by the duc\'s wife, who felt the couple, and especially her daughter, were too young. The matter was settled by agreeing not to mention the marriage plans for two years, during which time the two spouses-to-be would meet from time to time, seemingly accidentally.[12] The scheme worked; the two fell in love, and were happy together from the time of their marriage in 1774 until her death in 1807.[13]</p><p>After the marriage contract was signed in 1773, Lafayette lived with his young wife in his father-in-law\'s house in Versailles. He continued his education, both at the riding school at Versailles (his fellow students included the future Charles X) and at the prestigious Académie de Versailles. He was given a commission as a lieutenant in the Noailles Dragoons in April 1773,[14] the transfer from the royal regiment being done at the request of Lafayette\'s father-in-law.[15]<br><br><br></p><p><f class="strong">Finding a cause</f class="strong"></p><p>Statue of Lafayette in front of the Governor Palace in Metz, where he decided to join the American cause.</p>'

from ctypes import ArgumentError as cARG
class _FFace(freetype.Face):
    def __init__(self, path):
        freetype.Face.__init__(self, path)
        
        self._widths = {
                '<br>': 0,
                '<p>': 0,
                '</p>' : 0,
                '<f>': 0,
                '</f>': 0
                }

        self._ordinals = {
                'other': -1,
                '<br>': -2,
                '<p>': -3,
                '</p>': -4,
                
                '<f>': -5,
                '</f>': -6
                }

    def advance_pixel_width(self, character):
        try:
            return self._widths[character]
        except KeyError:
            p = self.get_advance(self.get_char_index(character), True)/self.units_per_EM
            self._widths[character] = p
            return p
    
    def character_index(self, character):
        try:
            return self._ordinals[character]
        except KeyError:
            i = self.get_char_index(character)
            self._ordinals[character] = i
            return i
        

#    def _ch(self, entity):
#        if not isinstance(entity, str):
#            entity = entity[0]
#        return entity
    
#    def _old_advance_width(self, character):
 #   
  #      if len(character) == 1:
   #         avw = self.get_advance(self.get_char_index(character), True)
#
 #       elif character == '<br>':
  #          avw = 0
   #     elif character == '<p>':
    #        avw = 0
     #   
      #  elif character in ['<f>', '</f>']:
       #     avw = 0
        #else:
         #   avw = 1000
          #      
        #return avw

j = _FFace("/home/kelvin/.fonts/Proforma-Book.otf")

tt = kevin.deserialize(t)
tt = [ch(b) for b in tt]

ordinalmap = {
        'other': -1,
        '<br>': -2,
        '<p>': -3,
        '</p>': -4,
        
        '<f>': -5,
        '</f>': -6
        }

def character_index(fontmetrics, c):
    try:
        return (fontmetrics.get_char_index(c))
    except TypeError:
        return ordinalmap[c]

def glyph_width(fontmetrics, size, c):
    return fontmetrics.advance_pixel_width(c)*size

def r():
    for c in tt:
        j.advance_width(c)

def q():
    for c in tt:
        j.character_index(c)

def s():
    for c in tt:
        glyph_width(j, 13, c)

print(timeit.timeit("s()", number=1000, setup="from __main__ import s"))
