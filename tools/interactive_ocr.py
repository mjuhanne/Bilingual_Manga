"""
This script is used to parse BilingualManga.org OCR files into Interactive OCR
"""

import os
import json
import sys
import datetime
from helper import *
from bm_learning_engine_helper import *

metadata_cache_file = base_dir + "json/metadata_cache.json"
learning_data_filename = base_dir + 'lang/user/learning_data.json'
learning_data = dict()
counter_word_ids = dict()

if len(sys.argv)>2:
    chapter_id = sys.argv[1]
    output_file_name = sys.argv[2]
else:
    #raise Exception("Input and output files not given!")
    #input_file_name = "parsed_ocr/bafybeie5tsllsjaequc65c3enuusqili743xwyg4744v4zmcgqqhm5dqvu.json"
    chapter_id ="QmVQdJevsvmScYo3eEr2tRuXKynS7NWjagkjK5eSm9QiRt"
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

# During every page change in MangaReader causes a new OCR file fetch via interactive_ocr.py.
# Because we decorate it ith word stage data and history, we like to cache the 
# chapter/volume names here to avoid the need to process the 70+MB admin.manga_data.json 
# every page flip
metadata_cache = {'chapter_metadata':{}}

if os.path.exists(metadata_cache_file):
    with open(metadata_cache_file,"r",encoding="utf-8") as f:
        metadata_cache = json.loads(f.read())

def get_metadata(source_chapter_id):
    if source_chapter_id not in metadata_cache['chapter_metadata']:

        read_manga_data()
        read_manga_metadata()

        chapter_metadata = dict()
        for cid,id in get_chapter_id_to_title_id().items():
            name = "%s (%s)" % (
                get_title_by_id(id),
                get_chapter_name_by_id(cid),
            )
            chapter_metadata[cid] = dict()
            chapter_metadata[cid]['name'] = name
        metadata_cache['chapter_metadata'] = chapter_metadata

        # just in case we need more info later
        metadata_cache['version'] = CURRENT_METADATA_CACHE_VERSION 

        with open(metadata_cache_file,"w",encoding="utf-8") as f:
            f.write(json.dumps(metadata_cache))

    return metadata_cache['chapter_metadata'][source_chapter_id]
    
def get_chapter_info(event_metadata):
    comment = ''
    cid = ''
    if 'ci' in event_metadata:
        cid = learning_data['chapter_ids'][event_metadata['ci']]
    elif 'cid' in event_metadata:
        cid = event_metadata['cid']
    if cid != '':
        ch_metadata = get_metadata(cid)
        comment = ch_metadata['name']
    if (event_metadata['src'] == SOURCE_USER):
        comment += ' / page %d' % (event_metadata['p'])
    if 'comment' in event_metadata:
        comment += event_metadata['comment']
    return comment


def load_counter_word_ids():
    global counter_word_ids
    with open(counter_word_id_file,"r",encoding="utf-8") as f:
        data = f.read()
        lines = data.split('\n')
        for line in lines:
            d = line.split('\t')
            if len(d)>1:
                word_id = d[0]
                k_elem = d[1]
                counter_word_ids[k_elem] = word_id
    #print("Counter word id file doesn't exist")


def get_possible_counter_word_id(word_id):
    seq,_,word = get_word_id_components(word_id)
    i = 0
    while i<len(word) and is_numerical(word[i]):
        i += 1
    if i > 0:
        root_word = word[i:]
        if root_word in counter_word_ids:
            return counter_word_ids[root_word]
    else:
        if word[0] == '第':
            return counter_word_ids['第']
    return word_id

def get_word_id_stage_and_history(word_id):
    stage = STAGE_UNKNOWN
    history = []
    last_timestamp = 0
    if word_id in learning_data['words']:
        wd = learning_data['words'][word_id]
        stage = wd['s']
        history = wd['h']
        for h in history:
            h['m']['comment'] = get_chapter_info(h['m'])
        last_timestamp = history[-1]['t']

    last_history_from_user = False
    if word_id in user_set_words:
        user_set_history = user_set_words[word_id]
        user_timestamp = user_set_history[-1]['t']
        if user_timestamp > last_timestamp:
            # the learning stage was changed by the user after the
            # last learning_data update so propagate the change
            stage = user_set_words[word_id][-1]['s']
            metadata = user_set_history[-1]['m']
            metadata['src'] = SOURCE_USER
            metadata['comment'] = get_chapter_info(metadata)
            history = history + [user_set_history[-1]]
            last_history_from_user = True
    return stage, history, last_history_from_user

def TRACE_EVENT(e):
    d = datetime.datetime.fromtimestamp(e['t'])
    if 'src' in e['m']:
        src = source_labels[e['m']['src']]
    else:
        src = ''
    s = '%s [Stage: %s(%d) Source: %s]' % (d, learning_stage_labels[e['s']].upper(), e['s'], src)
    return s


def get_user_set_words_by_seq(target_seq):
    wid_history = dict()
    for wid,history in user_set_words.items():
        seq,word = get_seq_and_word_from_word_id(wid)
        if seq == target_seq:
            wid_history[wid] = history
    return wid_history

def pretty_print_word_history(word_id,stage,history,last_history_from_user):

    print("%s [%s]" % (word_id, learning_stage_labels[stage].upper()))
    if last_history_from_user:
        print("\t(last from user)")
    for h in history:
        print("\t%s" % TRACE_EVENT(h))
    seq,word = get_seq_and_word_from_word_id(word_id)
    user_wid_history = get_user_set_words_by_seq(seq)
    for wid,history in user_wid_history.items():
        print("\tUSER %s %s" % (wid,TRACE_EVENT(history[-1])))

def manually_update_word_id_refs(page_id, block_id, item_id, text, word_id_refs, word_id_list, current_block, verbose):
    if chapter_id in ocr_corrections['word_id_errata']:
        for change in ocr_corrections['word_id_errata'][chapter_id]:
            if page_id == change['pr'] and block_id == change['bid'] and item_id == change['iid']:
                if text == change['w']:
                    wid = change['wid']
                    if wid in word_id_list:
                        widx = word_id_list.index(wid)
                        if widx in word_id_refs:
                            word_id_refs.pop(word_id_refs.index(widx))
                        word_id_refs.insert(0,widx)

                    if verbose:
                        print("Updated %s word id to %s in block %s" % (text,wid,str(current_block)))
                else:
                    print("Mismatch in manual word id update!")
                    print("Current block: ",current_block)
                    print("Errata: ",change)

def create_interactive_ocr(input_file, output_file):

    f = open(input_file, "r", encoding="utf-8")
    f_data = f.read()
    f.close()
    
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

                        manually_update_word_id_refs(page_id, block_id, item_i, lex_item, word_id_refs, pages['parsed_data']['word_id_list'], parsed_lines, debug_this_block)

                        word_id_index_list = ','.join([str(w) for w in word_id_refs])

                        new_line +=  '<span wil="' + word_id_index_list + '" ii="' + str(item_i) + '">' + lex_item + '</span>'

                        if debug_this_block and j == 0 and len(word_id_refs)>0:
                            debug_refs.update([word_id_refs[0]])
                        item_i += 1

                block['lines'][i] = new_line
                i += 1

    # insert learning settings, word learning stages and history
    pages['settings'] = learning_settings
    pages['word_learning_stages'] = []
    pages['word_history'] = []
    stage_history_cache = dict()

    for i, word_id_with_sense in enumerate(pages['parsed_data']['word_id_list']):

        word_id = strip_sense_from_word_id(word_id_with_sense)
        if word_id in stage_history_cache:
            stage, history = stage_history_cache[word_id]
        else:

            stage, history, last_history_from_user = get_word_id_stage_and_history(word_id)

            if i in debug_refs:
                pretty_print_word_history(word_id,stage,history,last_history_from_user)

            root_word_id = get_possible_counter_word_id(word_id)

            if word_id != root_word_id:
                root_word_id = strip_sense_from_word_id(root_word_id)

                root_stage, root_history, root_last_history_from_user = get_word_id_stage_and_history(root_word_id)
                if i in debug_refs:
                    pretty_print_word_history(root_word_id,root_stage,root_history,root_last_history_from_user)

                overwrite = False
                if root_stage > stage:
                    if root_stage == STAGE_FORGOTTEN:
                        if stage < STAGE_KNOWN:
                            overwrite = True
                    else:
                        overwrite = True
                else:
                    if stage == STAGE_FORGOTTEN and root_stage == STAGE_KNOWN:
                        overwrite = True

                if overwrite:
                    # TODO: add history info about stage update due to root word
                    if i in debug_refs:
                        print("%s stage changed from %d to %d due to %s" % (word_id,stage,root_stage, root_word_id))
                    stage = root_stage
                    history = root_history

            stage_history_cache[word_id] = (stage,history)

        pages['word_learning_stages'].append(stage)
        pages['word_history'].append(history)

    f = open(output_file, "w", encoding="utf-8")
    f.write(json.dumps(pages, ensure_ascii=False))
    f.close()
    print("Created " + output_file_name)


print("Interactive OCR (%s) (%s)" % (str(debug_block_id), str(debug_page_ref)))

try:

    if os.path.exists(learning_data_filename):
        with open(learning_data_filename,"r",encoding="utf-8") as f:
            learning_data = json.loads(f.read())
    else:
        print("Learning data not calculated! Update!")

    user_set_words = get_user_set_words()
    user_settings = read_user_settings()
    learning_settings = get_learning_settings()
    load_counter_word_ids()

    create_interactive_ocr(input_file_name, output_file_name)
except Exception as e:
    print(e,file=sys.stderr)