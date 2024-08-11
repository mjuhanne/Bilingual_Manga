from helper import *
from bm_learning_engine_helper import *
import datetime

metadata_cache_file = base_dir + "json/metadata_cache.json"
learning_data_filename = base_dir + 'lang/user/learning_data.json'
learning_data = dict()

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

if os.path.exists(learning_data_filename):
    with open(learning_data_filename,"r",encoding="utf-8") as f:
        learning_data = json.loads(f.read())
else:
    print("Learning data not calculated! Update!")

# During every page change in MangaReader causes a new OCR file fetch via interactive_ocr.py.
# Because we decorate it ith word stage data and history, we like to cache the 
# chapter/volume names here to avoid the need to process the 70+MB admin.manga_data.json 
# every page flip
metadata_cache = {'chapter_metadata':{}}


if os.path.exists(metadata_cache_file):
    with open(metadata_cache_file,"r",encoding="utf-8") as f:
        md_cache = json.loads(f.read())
        if md_cache['version'] == CURRENT_METADATA_CACHE_VERSION:
            metadata_cache = md_cache

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
            chapter_metadata[cid]['id'] = id
        metadata_cache['chapter_metadata'] = chapter_metadata

        # just in case we need more info later
        metadata_cache['version'] = CURRENT_METADATA_CACHE_VERSION 

        if source_chapter_id not in metadata_cache['chapter_metadata']:
            # The referred chapter or title was removed. 
            metadata_cache['chapter_metadata'][source_chapter_id] = {
                'name' : 'Removed', 'id' : -1
            }

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
    return comment, cid


def get_word_id_stage_and_history(word_id):
    stage = STAGE_UNKNOWN
    history = []
    last_timestamp = 0
    if word_id in learning_data['words']:
        wd = learning_data['words'][word_id]
        stage = wd['s']
        history = wd['h']
        for h in history:
            h['m']['comment'], h['m']['cid'] = get_chapter_info(h['m'])
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
            metadata['comment'], metadata['cid'] = get_chapter_info(metadata)
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
    pages['word_history'] = []
    stage_history_cache = dict()

    for i, word_id_with_sense in enumerate(pages['parsed_data']['word_id_list']):

        word_id = strip_sense_from_word_id(word_id_with_sense)
        if word_id in stage_history_cache:
            stage, history = stage_history_cache[word_id]
        else:

            stage, history, last_history_from_user = get_word_id_stage_and_history(word_id)

            # set all numerical 'words' known
            seq,word = get_seq_and_word_from_word_id(word_id)
            if is_numerical(word):
                stage = STAGE_KNOWN

            if i in debug_refs:
                pretty_print_word_history(i,word_id,stage,history,last_history_from_user)

            # set words (e.g. 一枚) consisting of a numerical + counter word
            # as KNOWN if the counter word (枚) is also KNOWN
            root_word_id = get_possible_counter_word_id(word_id)

            if word_id != root_word_id:
                root_word_id = strip_sense_from_word_id(root_word_id)

                root_stage, root_history, root_last_history_from_user = get_word_id_stage_and_history(root_word_id)
                if i in debug_refs:
                    pretty_print_word_history(i,root_word_id,root_stage,root_history,root_last_history_from_user)

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
