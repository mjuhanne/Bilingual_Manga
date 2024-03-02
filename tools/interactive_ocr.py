"""
This script is used to parse BilingualManga.org OCR files into Interactive OCR
"""

import os
import json
import sys
from helper import *

metadata_cache_file = base_dir + "json/metadata_cache.json"
learning_data_filename = base_dir + 'lang/user/learning_data.json'
learning_data = dict()

if len(sys.argv)>2:
    input_file_name = sys.argv[1]
    output_file_name = sys.argv[2]
else:
    #raise Exception("Input and output files not given!")
    #input_file_name = "parsed_ocr/bafybeie5tsllsjaequc65c3enuusqili743xwyg4744v4zmcgqqhm5dqvu.json"
    input_file_name = "parsed_ocr/bafybeigcep3esjli46hp5gbt54aw5i5e4hf53rcfomlf4sgkedhjmwejii.json"
    output_file_name = "test.json"


# During every page change in MangaReader causes a new OCR file fetch via interactive_ocr.py.
# Because we decorate it ith word stage data and history, we like to cache the 
# chapter/volume names here to avoid the need to process the 70+MB admin.manga_data.json 
# every page flip
metadata_cache = {'chapter_metadata':{}}

if os.path.exists(metadata_cache_file):
    with open(metadata_cache_file,"r",encoding="utf-8") as f:
        metadata_cache = json.loads(f.read())

def get_metadata(chapter_id):
    if chapter_id not in metadata_cache['chapter_metadata']:

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

    return metadata_cache['chapter_metadata'][chapter_id]
    
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


def create_interactive_ocr(input_file, output_file):

    f = open(input_file, "r", encoding="utf-8")
    f_data = f.read()
    f.close()
    
    pages = json.loads(f_data)

    # insert learning settings, word learning stages and history
    pages['settings'] = learning_settings
    pages['word_learning_stages'] = []
    pages['word_history'] = []
    index = 0
    for word in pages['word_list']:
        stage = STAGE_UNKNOWN
        history = []
        last_timestamp = 0

        if word == '':
            # non jp word/string
            stage = STAGE_NONE
        else:
            if word in learning_data['words']:
                wd = learning_data['words'][word]
                stage = wd['s']
                history = wd['h']
                for h in history:
                    h['m']['comment'] = get_chapter_info(h['m'])
                last_timestamp = history[-1]['t']

        if word in user_set_words:
            user_set_history = user_set_words[word]
            user_timestamp = user_set_history[-1]['t']
            if user_timestamp > last_timestamp:
                # the learning stage was changed by the user after the
                # last learning_data update so propagate the change
                stage = user_set_words[word][-1]['s']
                metadata = user_set_history[-1]['m']
                metadata['src'] = SOURCE_USER
                metadata['comment'] = get_chapter_info(metadata)
                history.append(user_set_history[-1])
        pages['word_learning_stages'].append(stage)
        pages['word_history'].append(history)
        index += 1

    # the lists and settings are kept as separate 'pages'. Ugly, but works.
    ignored_pages = ['word_list',
                     'word_senses','sense_word_idx','sense_list','sense_class_list',
                     'lemmas',
                     'word_learning_stages','word_history','settings',
                     'phrase_list','phrase_seq','version','parser_version']

    for page_id,blocks in pages.items():

        if page_id in ignored_pages:
            continue

        for block in blocks:

            block['og_lines'] = block['lines'].copy()
            
            parsed_lines = block['jlines']
            i = 0
            for line in parsed_lines:

                new_line = ''
                for item in line:
                    for word,ref_list in item.items():
                        # TODO: handle many word/phrase references for each unidict 
                        # recognized word/particle. Now just use the largest phrase
                        # and if not found, then first word
                        idx = 0
                        if len(ref_list) > 0:
                            s_idx = ref_list[0]
                            idx = pages['sense_word_idx'][s_idx]

                        new_line +=  '<span wid=' + str(idx) + '>' + word + '</span>'

                block['lines'][i] = new_line
                i += 1

    f = open(output_file, "w", encoding="utf-8")
    f.write(json.dumps(pages, ensure_ascii=False))
    f.close()
    print("Created " + output_file_name)


if os.path.exists(learning_data_filename):
    with open(learning_data_filename,"r",encoding="utf-8") as f:
        learning_data = json.loads(f.read())
else:
    print("Learning data not calculated! Update!")

user_set_words = get_user_set_words()
user_settings = read_user_settings()
learning_settings = get_learning_settings()

create_interactive_ocr(input_file_name, output_file_name)