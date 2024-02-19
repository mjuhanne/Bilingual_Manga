"""
This script is used to parse BilingualManga.org OCR files into Interactive OCR
"""

import os
import json
import sys

STAGE_NONE = 0  # this is reserved for word ignored automatically (such as punctuation)
STAGE_UNKNOWN = 1
STAGE_UNFAMILIAR = 2
STAGE_LEARNING = 3
STAGE_PRE_KNOWN = 4
STAGE_KNOWN = 5
STAGE_FORGOTTEN = 6
STAGE_IGNORED = 7 # this is for words explicitely ignore by the user

SOURCE_USER = 'u'
SOURCE_CHAPTER = 'ch'

base_dir = "./"

manga_data_file = base_dir + "json/admin.manga_data.json"
manga_metadata_file = base_dir + "json/admin.manga_metadata.json"
metadata_cache_file = base_dir + "json/metadata_cache.json"
learning_data_filename = base_dir + 'lang/user/learning_data.json'
user_set_words_file = base_dir + 'json/user_set_words.json'
user_settings_file = base_dir + 'json/user_data.json'

input_dir = base_dir + "ocr/"
target_chapter_dir = base_dir + "lang/chapters/"
target_title_dir = base_dir + "lang/titles/"

learning_data = dict()
user_set_words = dict()

if len(sys.argv)>2:
    input_file_name = sys.argv[1]
    output_file_name = sys.argv[2]
else:
    #raise Exception("Input and output files not given!")
    input_file_name = "../parsed_ocr/bafybeie5tsllsjaequc65c3enuusqili743xwyg4744v4zmcgqqhm5dqvu.json"
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

        title_names = dict()
        chapter_id_to_title_id = dict()
        chapter_id_to_chapter_name = dict()

        # here only the manga names are needed
        with open(manga_metadata_file,"r",encoding="utf-8") as f:
            data = f.read()
            manga_metadata = json.loads(data)
            manga_titles = manga_metadata[0]['manga_titles']
            for t in manga_titles:
                title_id = t['enid']
                title_name = t['entit']
                title_names[title_id] = title_name

        with open(manga_data_file,"r",encoding="utf-8") as f:
            data = f.read()
            manga_data = json.loads(data)
            for m in manga_data:
                title_id = m['_id']['$oid']
                chapter_ids = m['jp_data']['ch_jph']
                chapter_ids = [cid.split('/')[0] for cid in chapter_ids]
                chapter_names = m['jp_data']['ch_najp']
                chapter_number = 1
                for cid in chapter_ids:
                    chapter_id_to_title_id[cid] = title_id
                    chapter_id_to_chapter_name[cid] = chapter_names[chapter_number-1]
                    chapter_number += 1

        chapter_metadata = dict()
        for cid,id in chapter_id_to_title_id.items():
            name = "%s (%s)" % (
                title_names[id],
                chapter_id_to_chapter_name[cid],
            )
            chapter_metadata[cid] = dict()
            chapter_metadata[cid]['name'] = name
        metadata_cache['chapter_metadata'] = chapter_metadata

        metadata_cache['version'] = 1 # just in case we need more info later

        with open(metadata_cache_file,"w",encoding="utf-8") as f:
            f.write(json.dumps(metadata_cache))

    return metadata_cache['chapter_metadata'][chapter_id]


if os.path.exists(learning_data_filename):
    with open(learning_data_filename,"r",encoding="utf-8") as f:
        learning_data = json.loads(f.read())
else:
    print("Learning data not calculated! Update!")

if os.path.exists(user_set_words_file):
    with open(user_set_words_file,"r", encoding="utf-8") as f:
        user_set_words = json.loads(f.read())
else:
    print("No user  (user_data) file!")


if os.path.exists(user_settings_file):
    with open(user_settings_file,"r", encoding="utf-8") as f:
        user_settings = json.loads(f.read())
        learning_settings = user_settings['learning_settings']
else:
    print("No user  (user_data) file!")

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
    #del(pages['word_class_list'])
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
    ignored_pages = ['word_list','word_class_list','word_learning_stages','word_history','settings','version']

    for page_id,blocks in pages.items():

        if page_id in ignored_pages:
            continue

        for block in blocks:

            parsed_lines = block['plines']
            i = 0
            for line in parsed_lines:

                new_line = ''
                for item in line:
                    for word,index in item.items():
                        new_line +=  '<span wid=' + str(index) + '>' + word + '</span>'

                block['lines'][i] = new_line
                i += 1

    f = open(output_file, "w", encoding="utf-8")
    f.write(json.dumps(pages, ensure_ascii=False))
    f.close()
    print("Created " + output_file_name)

create_interactive_ocr(input_file_name, output_file_name)