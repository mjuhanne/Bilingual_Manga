"""
This script is used to parse BilingualManga.org OCR files into Interactive OCR
"""

import os
import json
import sys
from helper import *
from bm_learning_engine_helper import *
from interactive_text_helper import *

if len(sys.argv)>2:
    chapter_id = sys.argv[1]
    output_file_name = sys.argv[2]
else:
    #raise Exception("Input and output files not given!")
    #input_file_name = "parsed_ocr/bafybeie5tsllsjaequc65c3enuusqili743xwyg4744v4zmcgqqhm5dqvu.json"
    chapter_id ="bafybeiepscsbazdxxpiaerafmskwz4xzu4wknh2h76q64m423ochfjmmaq"
    output_file_name = "test.json"

input_file_name = "parsed_ocr/" + chapter_id + ".json"

# Page ref and block_id is used just for debugging
if len(sys.argv)>3:
    debug_page_ref = sys.argv[3]
else:
    debug_page_ref = None
if len(sys.argv)>4:
    debug_block_id = int(sys.argv[4])
else:
    debug_block_id = None

OCR_CORRECTIONS_FILE = base_dir + "json/ocr_corrections.json"

if os.path.exists(OCR_CORRECTIONS_FILE):
    f = open(OCR_CORRECTIONS_FILE, "r", encoding="utf-8")
    f_data = f.read()
    f.close()    
    ocr_corrections = json.loads(f_data)
else:
    ocr_corrections = {'block_errata' : {}, 'word_id_errata': {}}

#debug_page_ref = 'DEATH-NOTE05_135'
#debug_block_id = 7

def create_interactive_ocr(input_file, output_file):

    f = open(input_file, "r", encoding="utf-8")
    f_data = f.read()
    f.close()
    
    metadata = get_metadata(chapter_id)
    title_id = metadata['id']

    pages = json.loads(f_data)

    # the lists and settings are kept as separate 'pages'. Ugly, but works.
    ignored_pages = ['parsed_data',
                     #'word_learning_stages','word_history','settings',
                     'version','parser_version']

    debug_refs = set()

    for page_id,blocks in pages.items():

        if page_id in ignored_pages:
            continue

        for block_id, block in enumerate(blocks):

            block['og_lines'] = block['lines'].copy()

            if (block_id == debug_block_id or debug_block_id == 'ALL') and (debug_page_ref == page_id or debug_page_ref == 'ALL'):
                print("Debug block: %s" % str(block))
                debug_this_block = True
            else:
                debug_this_block = False
            
            parsed_lines = block['jlines']
            i = 0
            item_i = 0
            for line in parsed_lines:

                new_line = ''
                for item in line:
                    for j, (lex_item,word_id_refs) in enumerate(item.items()):

                        manually_update_word_id_refs(title_id, chapter_id, page_id, block_id, item_i, lex_item, word_id_refs, pages['parsed_data']['word_id_list'], parsed_lines, debug_this_block)

                        word_id_index_list = ','.join([str(w) for w in word_id_refs])

                        new_line +=  '<span wil="' + word_id_index_list + '" ii="' + str(item_i) + '">' + lex_item + '</span>'

                        if debug_this_block and j == 0 and len(word_id_refs)>0:
                            debug_refs.update([word_id_refs[0]])
                            print("Debugging ",lex_item)
                            for ref in word_id_refs:
                                print("\t%d:%s" %(ref,pages['parsed_data']['word_id_list'][ref]))
                        item_i += 1

                block['lines'][i] = new_line
                i += 1

    # insert learning settings, word learning stages and history
    insert_learning_data(pages, debug_refs)

    f = open(output_file, "w", encoding="utf-8")
    f.write(json.dumps(pages, ensure_ascii=False))
    f.close()
    print("Created " + output_file_name)


print("Interactive OCR (%s) (%s)" % (str(debug_block_id), str(debug_page_ref)))

try:
    create_interactive_ocr(input_file_name, output_file_name)
except Exception as e:
    print(e,file=sys.stderr)