from helper import *
from bm_learning_engine_helper import *
import datetime
from motoko_mongo import *

learning_data = database[COLLECTION_USER_LEARNING_DATA].find_one({'user_id':DEFAULT_USER_ID})
wordlist_cursor = database[COLLECTION_USER_WORD_LEARNING_STATUS].find({'user_id':DEFAULT_USER_ID},{'_id':False,'user_id':False})
learning_data['words'] = {item['wid']:{'s':item['s'],'lf':item['lf']} for item in wordlist_cursor}

user_set_words = get_user_set_words()
user_settings = read_user_settings()
load_counter_word_ids()

OCR_CORRECTIONS_FILE = base_dir + "json/ocr_corrections.json"

if os.path.exists(OCR_CORRECTIONS_FILE):
    f = open(OCR_CORRECTIONS_FILE, "r", encoding="utf-8")
    f_data = f.read()
    f.close()    
    ocr_corrections = json.loads(f_data)
else:
    ocr_corrections = {'block_errata' : {}, 'word_id_errata': {}}


def get_metadata(source_chapter_id):
    chapter_data = database[COLLECTION_CHAPTERDATA].find_one({'ch_id':source_chapter_id})
    if chapter_data is None:
        raise Exception("Chapter %s not found in lookup table!" % source_chapter_id)
    title_metadata = database[COLLECTION_TITLEDATA].find_one({'_id':chapter_data['title_id']})
    title = get_title_from_metadata(title_metadata)
    return {
        'id' : chapter_data['title_id'],
        'name' : "%s (%s)" % (title, chapter_data['ch_name'])
    }


def get_chapter_info(event_metadata):
    comment = ''
    cid = ''
    if 'cid' in event_metadata:
        cid = event_metadata['cid']
    if cid != '':
        ch_metadata = get_metadata(cid)
        comment = ch_metadata['name']
    if (event_metadata['src'] == SOURCE_USER):
        comment += ' / page %d' % (event_metadata['p'])
    if 'comment' in event_metadata:
        comment += event_metadata['comment']
    return comment, cid


def get_word_id_stage(word_id):
    stage = STAGE_UNKNOWN
    if word_id in learning_data['words']:
        wd = learning_data['words'][word_id]
        stage = wd['s']

    return stage

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

def pretty_print_word_history(ref,word_id,stage,history,last_history_from_user):

    print("%d : %s [%s]" % (ref, word_id, learning_stage_labels[stage].upper()))
    if last_history_from_user:
        print("\t(last from user)")
    for h in history:
        print("\t%s" % TRACE_EVENT(h))
    seq,word = get_seq_and_word_from_word_id(word_id)
    user_wid_history = get_user_set_words_by_seq(seq)
    for wid,history in user_wid_history.items():
        print("\tUSER %s %s" % (wid,TRACE_EVENT(history[-1])))

def do_manually_update_word_id_refs(changes, page_id, block_id, item_id, text, word_id_refs, word_id_list, current_block, verbose):
    for change in changes:
        if (page_id == change['pr'] or change['pr'] == 'ALL'):
            if 'bid' not in change or (block_id == change['bid']):
                if 'iid' not in change or item_id == change['iid']:
                    if 'w' not in change or text == change['w']:
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

def manually_update_word_id_refs(title_id, chapter_id, page_id, block_id, item_id, text, word_id_refs, word_id_list, current_block, verbose):
    if chapter_id in ocr_corrections['word_id_errata']:
        do_manually_update_word_id_refs(ocr_corrections['word_id_errata'][chapter_id], 
            page_id, block_id, item_id, text, word_id_refs, word_id_list, current_block, verbose)
    if title_id in ocr_corrections['word_id_errata']:
        do_manually_update_word_id_refs(ocr_corrections['word_id_errata'][title_id], 
            page_id, block_id, item_id, text, word_id_refs, word_id_list, current_block, verbose)
    if 'ALL' in ocr_corrections['word_id_errata']:
        do_manually_update_word_id_refs(ocr_corrections['word_id_errata']['ALL'],
            page_id, block_id, item_id, text, word_id_refs, word_id_list, current_block, verbose)


def insert_learning_data(pages, debug_refs):

    # insert learning settings, word learning stages and history
    pages['settings'] = get_learning_settings()
    pages['word_learning_stages'] = []
    stage_cache = dict()

    for i, word_id_with_sense in enumerate(pages['parsed_data']['word_id_list']):

        word_id = strip_sense_from_word_id(word_id_with_sense)
        if word_id in stage_cache:
            stage = stage_cache[word_id]
        else:

            stage = get_word_id_stage(word_id)

            # set all numerical 'words' known
            seq,word = get_seq_and_word_from_word_id(word_id)
            if is_numerical(word):
                stage = STAGE_KNOWN

            if i in debug_refs:
                print("TODO! Print word history")
                #pretty_print_word_history(i,word_id,stage,history,last_history_from_user)

            # set words (e.g. 一枚) consisting of a numerical + counter word
            # as KNOWN if the counter word (枚) is also KNOWN
            root_word_id = get_possible_counter_word_id(word_id)

            if word_id != root_word_id:
                root_word_id = strip_sense_from_word_id(root_word_id)

                root_stage = get_word_id_stage(root_word_id)
                if i in debug_refs:
                    print("TODO! Print word history")
                    #pretty_print_word_history(i,root_word_id,root_stage,root_history,root_last_history_from_user)

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

            stage_cache[word_id] = stage

        pages['word_learning_stages'].append(stage)
