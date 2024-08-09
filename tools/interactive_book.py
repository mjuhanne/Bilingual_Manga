"""
This script is used to process parsed "OCR" files into Interactive book text
"""

import os
import json
import sys
import datetime
from helper import *
from bm_learning_engine_helper import *
from interactive_text_helper import *
from bs4 import BeautifulSoup

if len(sys.argv)>2:
    chapter_id = sys.argv[1]
    output_file_name = sys.argv[2]
else:
    #raise Exception("Input and output files not given!")
    #input_file_name = "parsed_ocr/bafybeie5tsllsjaequc65c3enuusqili743xwyg4744v4zmcgqqhm5dqvu.json"
    chapter_id ="6696a9de5346852c2184aed4"
    output_file_name = "test.html"

parsed_input_file = "parsed_ocr/" + chapter_id + ".json"

# Page ref and block_id is used just for debugging
if len(sys.argv)>3:
    debug_page_ref = sys.argv[3]
else:
    debug_page_ref = None
if len(sys.argv)>4:
    debug_block_id = int(sys.argv[4])
else:
    debug_block_id = None

#debug_page_ref = 'DEATH-NOTE05_135'
#debug_block_id = 7

def create_interactive_book(input_files, parsed_input_file, output_file):

    f = open(parsed_input_file, "r", encoding="utf-8")
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

            # 'lines' is a list consisting of a single line (actually a paragraph)
            block['og_lines'] = block['lines'].copy()

            if (block_id == debug_block_id or debug_block_id == 'ALL') and (debug_page_ref == page_id or debug_page_ref == 'ALL'):
                print("Debug block: %s" % str(block))
                debug_this_block = True
            else:
                debug_this_block = False
            
            # check for ruby
            parsed_line_ruby_idx = None
            if 'ruby' in block:
                parsed_line_ruby_idx = 0

            parsed_lines = block['jlines']
            i = 0
            item_i = 0
            p_ch_count = 0
            for line_num,line in enumerate(parsed_lines):

                new_line = ''
                for item in line:
                    for j, (lex_item,word_id_refs) in enumerate(item.items()):

                        manually_update_word_id_refs(title_id, chapter_id, page_id, block_id, item_i, lex_item, word_id_refs, pages['parsed_data']['word_id_list'], parsed_lines, debug_this_block)

                        word_id_index_list = ','.join([str(w) for w in word_id_refs])

                        ruby = ''
                        if parsed_line_ruby_idx != None:
                            ruby_item = block['ruby'][parsed_line_ruby_idx]
                            if ruby_item['s'] == p_ch_count:
                                ruby = ruby_item['rt']
                                parsed_line_ruby_idx += 1
                                if parsed_line_ruby_idx == len(block['ruby']):
                                    parsed_line_ruby_idx = None
                        
                        p_ch_count += len(lex_item)

                        if ruby != '':
                            lex_item = '<ruby>%s<rt>%s</rt></ruby>' % (lex_item,ruby)

                        new_line +=  '<span wil="' + word_id_index_list + '" ii="' + str(item_i) + '">' + lex_item + '</span>'

                        if debug_this_block and j == 0 and len(word_id_refs)>0:
                            debug_refs.update([word_id_refs[0]])
                            print("Debugging ",lex_item)
                            for ref in word_id_refs:
                                print("\t%d:%s" %(ref,pages['parsed_data']['word_id_list'][ref]))
                        item_i += 1

                block['lines'][i] = new_line

                i += 1

    insert_learning_data(pages, debug_refs)

    f = open(output_file, "w", encoding="utf-8")
    f.write(json.dumps(pages, ensure_ascii=False))
    f.close()
    print("Created " + output_file_name)


print("Interactive book (%s) (%s) (%s)" % (output_file_name, str(debug_block_id), str(debug_page_ref)))

create_interactive_book([], parsed_input_file, output_file_name)
