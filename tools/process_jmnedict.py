from xml.dom import minidom
from helper import *
from jp_parser_helper import *

original_jmnedict_file = base_dir + "lang/JMnedict.xml"
simple_jmnedict_file = base_dir + "lang/JMnedict_e.tsv"

print("Loading JMnedict...")
import xml.etree.ElementTree as ET
tree = ET.parse(original_jmnedict_file)
root = tree.getroot()

print("Parsing XML...")
entries = root.findall('entry')

print("Converting %d entries..." % len(entries))


o_f = open(simple_jmnedict_file,"w",encoding="utf-8")


for elem in entries:
    ent_seq = None
    readings = []
    kanji_elements = []

    elem_freq = dict()
    elem_pri_elems = dict()

    freq = 100

    ent_seq = elem.find('ent_seq').text

    pri_dict = {'spec1':99}

    r_elems = elem.findall('r_ele')
    for r_elem in r_elems:
        reb_elem = r_elem.find('reb')
        reb = reb_elem.text
        readings.append(reb)
        r_pri_els = r_elem.findall('re_pri')
        for r_pri_el in r_pri_els:
            pr = r_pri_el.text
            if pr in pri_dict:
                freq = pri_dict[pr]
            else:
                print("Unknown priority element %s on seq %s" % (pr,ent_seq))

    k_elems = elem.findall('k_ele')
    for k_elem in k_elems:
        keb_elem = k_elem.find('keb')
        keb = keb_elem.text
        kanji_elements.append(keb)
        k_pri_els = k_elem.findall('ke_pri')
        for k_pri_el in k_pri_els:
            pr = k_pri_el.text
            if pr in pri_dict:
                freq = pri_dict[pr]
            else:
                print("Unknown priority element %s on seq %s" % (pr,ent_seq))

    trans_det = ''
    trans_elems = elem.findall('trans')
    for trans_elem in trans_elems:
        trans_det_elem = trans_elem.find('trans_det')
        trans_det = trans_det_elem.text

    row = "%s\t%s\t%s\t%s\t%s\n" % \
        (ent_seq, ','.join(kanji_elements), ','.join(readings), freq,trans_det)

    o_f.write(row)
o_f.close()

print("Wrote %d entries" % (len(entries)))
