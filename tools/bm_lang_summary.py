# Bilingual Manga Language analysis summary tool
#
# This script calculates aggregate kanji and word count data as well as word distribution
# for each 5 JLPT levels. The resulting data is saved into lang_summary.json file.
import json

INVALID_VALUE = -1
from helper import *

summary_file = base_dir + "json/lang_summary.json"

volume_count_per_title = dict()

jlpt_kanjis = get_jlpt_kanjis()
read_jlpt_word_file()
jlpt_words = get_jlpt_words()
jlpt_word_reading_reverse = get_jlpt_word_reverse_readings()

read_manga_metadata()

volume_count_corrections = {
    'Bakemonogatari' : 13,
    'Yokohama Kaidashi Kikou' : 14,
    'Azumanga Daioh' : 3,
    'City Hunter' : 37,
}

with open(manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_data = json.loads(data)
    for m in manga_data:
        title_id = m['_id']['$oid']
        volume_ids = m['jp_data']['ch_jph']
        volume_ids = [vid.split('/')[0] for vid in volume_ids]
        pages = m['jp_data']['ch_jp']

        name = get_title_by_id(title_id)
        # it's very complex to count how many volumes the manga has because
        # sometimes the listed chapters are actually volumes. Then there are extras 
        # and few times it's a mixed bag. 
        if name in volume_count_corrections:
            volume_count = volume_count_corrections[name]
        else:
            small_chapter_cutoff = 70

            page_count_per_chapter = [len(pages[ch]) for ch in pages]
            vol_structures = m['jp_data']['vol_jp']
            volume_count = 0
            chapter_count = len(page_count_per_chapter)
            large_chapters = sum(page_count > small_chapter_cutoff for page_count in page_count_per_chapter)
            if large_chapters ==  chapter_count:
                # chapters are actually volumes
                volume_count = chapter_count
            elif large_chapters == 0:
                # each volume is actually a volume
                volume_count = len(vol_structures)
                print(name, volume_count, " volumes divided into ",chapter_count, "chapters")
            elif len(vol_structures) == 1:
                # few smaller chapters (extras?). Count only larger chapters as volumes
                volume_count = large_chapters
                print(name, volume_count, " volumes with ",large_chapters,"full volumes and ",chapter_count-large_chapters, "smaller")
            elif len(vol_structures) == large_chapters - 1:
                volume_count = large_chapters +1 
                print(name, volume_count, " volumes with ",large_chapters,"full volumes and 1 incomplete with " , chapter_count-large_chapters , " chapters")
            else:
                print("*** ",name)
                for vol_name, vol_struct in vol_structures.items():
                    start = vol_struct['s']
                    end = vol_struct['e']
                    chapters_in_vol = end + 1 - start
                    large_chapters_in_vol = sum(page_count_per_chapter[i] > small_chapter_cutoff for i in range(start,end+1))
                    if large_chapters_in_vol > 0:
                        # assume each chapter in this 'volume folder' is actually a volume and the smaller chapters are extras
                        print("   ", vol_name, " has volumes with ",large_chapters_in_vol,"full volumes and " , chapters_in_vol-large_chapters_in_vol , " smaller extras")
                        volume_count += large_chapters_in_vol
                    else:
                        # all chapters are part of bigger volume
                        print("   ", vol_name, " is 1 volume with ",chapters_in_vol," chapters")
                        volume_count += 1
                print("  ",name," has total ",volume_count," volumes")

        volume_count_per_title[title_id] = volume_count


# This calculates word and kanji distribution for each JLPT levels (1-5)
# 0 = non-Katakana non-JLPT word, 6=Katakana non-JLPT word
def fetch_jlpt_levels(data, calc, total):

    ## WORDS
    jlpt_word_count_per_level = [ 0 for i in range(7) ]
    for w,c in data['word_frequency'].items():
        if w in jlpt_words:
            level = jlpt_words[w]
        else:
            if w in jlpt_word_reading_reverse:
                rw = jlpt_word_reading_reverse[w]

                if len(rw)==1:
                    w = rw[0]
                    level = jlpt_words[w]
                else:
                    # ambigous (too many homonymous readings). Assume non-jlpt word
                    if is_katakana_word(w):
                        level = 6
                    else:
                        level = 0
            else:
                # non-jlpt word
                if is_katakana_word(w):
                    level = 6
                else:
                    level = 0
        if total:
            jlpt_word_count_per_level[level] += c
        else:
            jlpt_word_count_per_level[level] += 1

    total_w = calc['num_words']
    if total_w > 0:
        jlpt_w_level_pct = [ round(100*jlpt_word_count_per_level[i]/total_w,1) for i in range(7) ]
        jlpt_w_level_per_v = [ round(jlpt_word_count_per_level[i]/data['num_virtual_volumes'],1) for i in range(7) ]
    else:
        jlpt_w_level_pct = [ 0 for i in range(7) ]
        jlpt_w_level_per_v = [ 0 for i in range(7) ]

    calc['jlpt_word_level_pct'] = jlpt_w_level_pct
    calc['jlpt_word_level_per_v'] = jlpt_w_level_per_v

    calc['jlpt_word_content_pct'] = round(sum(jlpt_w_level_pct) - jlpt_w_level_pct[0] - jlpt_w_level_pct[6],1)
    calc['advanced_jlpt_word_content_pct'] = round(jlpt_w_level_pct[1],1)
    calc['intermediate_jlpt_word_content_pct'] = round(jlpt_w_level_pct[2] + jlpt_w_level_pct[3],1)
    calc['weighted_intermediate_jlpt_word_content_pts'] = \
        round( 50 + 
            jlpt_w_level_pct[0]*(-1.5) + 
            jlpt_w_level_pct[1]*(-0.7) + 
            jlpt_w_level_pct[2]*2 + 
            jlpt_w_level_pct[3]*2 + 
            jlpt_w_level_pct[4]*1 + 
            jlpt_w_level_pct[5]*0, 1)
    calc['num_non_jlpt_words'] = jlpt_word_count_per_level[0]

    ### KANJIS
    jlpt_kanji_count_per_level = [ 0 for i in range(6) ]
    for k,c in data['kanji_frequency'].items():
        if k in jlpt_kanjis:
            level = jlpt_kanjis[k]
        else:
            level = 0
        if total:
            jlpt_kanji_count_per_level[level] += c
        else:
            jlpt_kanji_count_per_level[level] += 1

    total_k = calc['num_kanjis']
    if total_k > 0:
        jlpt_k_level_pct = [ round(100*jlpt_kanji_count_per_level[i]/total_k,1) for i in range(6) ]
        jlpt_k_level_per_v = [ round(jlpt_kanji_count_per_level[i]/data['num_virtual_volumes'],1) for i in range(6) ]
    else:
        jlpt_k_level_pct = [ 0 for i in range(6) ]
        jlpt_k_level_per_v = [ 0 for i in range(6) ]
    calc['jlpt_kanji_level_pct'] = jlpt_k_level_pct
    calc['jlpt_kanji_level_per_v'] = jlpt_k_level_per_v
    calc['jlpt_kanji_content_pct'] = round(sum(jlpt_k_level_pct) - jlpt_k_level_pct[0],1)
    calc['advanced_jlpt_kanji_content_pct'] = round(jlpt_k_level_pct[1],1)
    calc['intermediate_jlpt_kanji_content_pct'] = round(jlpt_k_level_pct[2] + jlpt_k_level_pct[3],1)
    calc['num_non_jlpt_kanjis'] = jlpt_kanji_count_per_level[0]


def calculate_stats(title_data, calc, total=True):

    if title_data['num_pages'] != 0:
        calc['w_per_p'] = int(calc['num_words'] / title_data['num_pages'])
        calc['k_per_p'] = int(calc['num_kanjis'] / title_data['num_pages'])
    else:
        calc['w_per_p'] = INVALID_VALUE
        calc['k_per_p'] = INVALID_VALUE

    if calc['num_words'] != 0:
        calc['k_per_w_pct'] = int(100*calc['num_kanjis'] / calc['num_words'])
    else:
        calc['k_per_w_pct'] = INVALID_VALUE
    
    if title_data['num_virtual_volumes'] > 0:
        calc['w_per_v'] = int(calc['num_words'] / title_data['num_virtual_volumes'])
        calc['k_per_v'] = int(calc['num_kanjis'] / title_data['num_virtual_volumes'])
        calc['num_non_jlpt_words_per_v'] = int(calc['num_non_jlpt_words']/ title_data['num_virtual_volumes'])
        calc['num_non_jlpt_kanjis_per_v'] = int(calc['num_non_jlpt_kanjis']/ title_data['num_virtual_volumes'])
    else:
        calc['k_per_v'] = INVALID_VALUE
        calc['w_per_v'] = INVALID_VALUE
        calc['num_non_jlpt_words_per_v'] = INVALID_VALUE
        calc['num_non_jlpt_kanjis_per_v'] = INVALID_VALUE


def save_summary():

    summary = dict()

    title_names = get_title_names()
    num_titles = len(title_names)

    total_pages = 0
    num_valid_titles = 0
    total_volumes = 0

    for title_id, title_name in title_names.items():

        print(title_name)
        title_filename = title_analysis_dir + title_id + ".json"
        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()

        title_data['num_volumes'] = volume_count_per_title[title_id]

        # Average tankobon volume page count is 180, but it might vary considerable by
        # manga, so to make those statistics more comparable we calculate virtual volume
        # count and use that for those variables that rely on # of volumes.
        title_data['num_virtual_volumes'] = round(title_data['num_pages'] / AVERAGE_PAGES_PER_VOLUME,2)

        if title_data['num_pages']>0:
            num_valid_titles += 1
            total_pages += title_data['num_pages']
            total_volumes += title_data['num_virtual_volumes']

        total_calc = dict()
        unique_calc = dict()

        total_calc['num_words'] = title_data['num_words']
        total_calc['num_kanjis'] = title_data['num_kanjis']

        unique_calc['num_words'] = title_data['num_unique_words']
        unique_calc['num_kanjis'] = title_data['num_unique_kanjis']

        fetch_jlpt_levels(title_data, total_calc, total=True)
        fetch_jlpt_levels(title_data, unique_calc, total=False)

        calculate_stats(title_data, total_calc, total=True)
        calculate_stats(title_data, unique_calc, total=False)

        # drop the detailed frequency data for the summary
        del(title_data['word_frequency'])
        del(title_data['kanji_frequency'])
        del(title_data['title_id']) # redundant

        title_data['total_statistics'] = total_calc
        title_data['unique_statistics'] = unique_calc

        summary[title_id] = title_data
    
    single_value_fields = list(total_calc.keys())
    single_value_fields.remove('jlpt_word_level_pct')
    single_value_fields.remove('jlpt_word_level_per_v')
    single_value_fields.remove('jlpt_kanji_level_pct')
    single_value_fields.remove('jlpt_kanji_level_per_v')

    # calculate averages
    avg_calc = dict()
    for calc_f in ['total_statistics','unique_statistics']:
        avg_calc[calc_f] = dict()

        # averages for single value vields
        for f in single_value_fields:
            val = 0
            for title_id, title_data in summary.items():
                val += title_data[calc_f][f]
            val /= num_titles
            if 'pct' in f or 'pts' in f:
                val = round(val,1)
            else:
                val = int(val)
            avg_calc[calc_f][f] = val

        # averages for JLPT word/kanji level bins
        jlpt_w_level_pct = [ 0 for i in range(7) ]
        jlpt_w_level_per_v = [ 0 for i in range(7) ]
        jlpt_k_level_pct = [ 0 for i in range(6) ]
        jlpt_k_level_per_v = [ 0 for i in range(6) ]
        for title_id, title_data in summary.items():
            for i in range(7):
                jlpt_w_level_pct[i] += title_data[calc_f]['jlpt_word_level_pct'][i]
                jlpt_w_level_per_v[i] += title_data[calc_f]['jlpt_word_level_per_v'][i]
            for i in range(6):
                jlpt_k_level_pct[i] += title_data[calc_f]['jlpt_kanji_level_pct'][i]
                jlpt_k_level_per_v[i] += title_data[calc_f]['jlpt_kanji_level_per_v'][i]
        for i in range(7):
            jlpt_w_level_pct[i] = round(jlpt_w_level_pct[i]/num_titles,1)
            jlpt_w_level_per_v[i] = round(jlpt_w_level_per_v[i]/num_titles,1)
        for i in range(6):
            jlpt_k_level_pct[i] = round(jlpt_k_level_pct[i]/num_titles,1)
            jlpt_k_level_per_v[i] = round(jlpt_k_level_per_v[i]/num_titles,1)

        avg_calc[calc_f]['jlpt_word_level_pct'] = jlpt_w_level_pct
        avg_calc[calc_f]['jlpt_word_level_per_v'] = jlpt_w_level_per_v
        avg_calc[calc_f]['jlpt_kanji_level_pct'] = jlpt_k_level_pct
        avg_calc[calc_f]['jlpt_kanji_level_per_v'] = jlpt_k_level_per_v

    summary['average'] = avg_calc

    avg_page_count = total_pages/total_volumes
    print("Valid titles %d/%d with average page count %d / volume" 
          % (num_valid_titles, len(title_names.keys()), avg_page_count))

    with open(summary_file,"w") as f:
        f.write(json.dumps(summary, ensure_ascii=False))

save_summary()