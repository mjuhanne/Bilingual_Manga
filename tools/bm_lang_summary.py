# Bilingual Manga Language analysis summary tool
#
# This script calculates aggregate kanji and word count data as well as word distribution
# for each 5 JLPT levels. Resulting data is saved into lang_summary.json file.
import os
import json

manga_metadata_file = "../json/admin.manga_metadata.json"
manga_data_file = "../json/admin.manga_data.json"
volume_dir = "freq/volumes/"
title_dir = "freq/titles/"
jlpt_kanjis_file = "freq/jlpt/jlpt_kanjis.json"
jlpt_vocab_file =  "freq/jlpt/jlpt_vocab.json"

summary_file = "../json/lang_summary.json"

volume_id_to_title_id = dict()
volume_id_to_volume_number = dict()
volume_number_to_volume_id = dict()
title_volumes = dict()
title_names = dict()
title_name_to_id = dict()

individual_jlpt_words = dict()

jlpt_kanjis = dict()
jlpt_words = dict()

with open(jlpt_kanjis_file,"r",encoding="utf-8") as f:
    data = f.read()
    jlpt_kanjis = json.loads(data)

with open(jlpt_vocab_file,"r",encoding="utf-8") as f:
    d = f.read()
    v = json.loads(d)
    jlpt_words = v['words']
    jlpt_word_reading_reverse = v['word_reading_reverse']

with open(manga_metadata_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_metadata = json.loads(data)
    manga_titles = manga_metadata[0]['manga_titles']
    for t in manga_titles:
        title_id = t['enid']
        title_name = t['entit']
        title_names[title_id] = title_name
        title_name_to_id[title_name] = title_id

with open(manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_data = json.loads(data)
    for m in manga_data:
        title_id = m['_id']['$oid']
        volume_ids = m['jp_data']['ch_jph']
        volume_ids = [vid.split('/')[0] for vid in volume_ids]
        pages = m['jp_data']['ch_jp']
        title_volumes[title_id] = volume_ids
        for vid in volume_ids:
            volume_id_to_title_id[vid] = title_id
            volume_number = volume_ids.index(vid) + 1
            volume_id_to_volume_number[vid] = volume_number
            volume_number_to_volume_id[(title_id,volume_number)] = vid
 

def fetch_jlpt_levels(title_id, title_data):
    jlpt_level_count = [ 0 for i in range(6) ]
    for w,c in title_data['word_frequency'].items():
        if w in jlpt_words:
            level = jlpt_words[w]
            jlpt_level_count[level] += c
        else:
            if w in jlpt_word_reading_reverse:
                rw = jlpt_word_reading_reverse[w]

                if len(rw)==1:
                    w = rw[0]
                    level = jlpt_words[w]
                    jlpt_level_count[level] += c
                else:
                    # ambigous (too many homonymous readings). Assume non-jlpt word
                    jlpt_level_count[0] += c

            else:
                # non-jlpt word
                jlpt_level_count[0] += c

    total_w = title_data['num_words']
    if total_w > 0:
        jlpt_level_pct = [ round(100*jlpt_level_count[i]/total_w,1) for i in range(6) ]
    else:
        jlpt_level_pct = [ 0 for i in range(6) ]
    title_data['jlpt_level_pct'] = jlpt_level_pct
    title_data['jlpt_content_pct'] = round(sum(jlpt_level_pct) - jlpt_level_pct[0],1)
    title_data['advanced_jlpt_content_pct'] = round(jlpt_level_pct[1],1)
    title_data['intermediate_jlpt_content_pct'] = round(jlpt_level_pct[2] + jlpt_level_pct[3],1)

# Analyze whole titles
def save_summary():

    summary = dict()

    for title_id, title_name in title_names.items():

        print(title_name)
        title_filename = title_dir + title_id + ".json"
        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()

        fetch_jlpt_levels(title_id, title_data)

        if title_data['num_pages'] != 0:
            title_data['w_per_p'] = int(title_data['num_words'] / title_data['num_pages']);
        else:
            title_data['w_per_p'] = -1;
        if title_data['num_words'] != 0:
            title_data['k_per_w_perc'] = int(100*title_data['num_kanjis'] / title_data['num_words']);
        else:
            title_data['k_per_w_perc'] = -1;
        # drop detailed frequency data for the summary
        del(title_data['word_frequency'])
        del(title_data['kanji_frequency'])
        del(title_data['title_id']) # redundant

        summary[title_id] = title_data
    
    with open(summary_file,"w") as f:
        f.write(json.dumps(summary))

save_summary();