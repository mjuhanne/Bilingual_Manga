# Bilingual Manga Language analysis summary tool
#
# This script calculates aggregate kanji and word count data as well as word distribution
# for each 5 JLPT levels. The resulting data is saved into lang_summary.json file.
import json
import argparse
INVALID_VALUE = -1
from helper import *
import time
from bm_learning_engine_helper import get_analysis_data_for_title

jlpt_kanjis = get_jlpt_kanjis()
jlpt_word_levels = get_jlpt_word_levels()
jlpt_word_reading_levels= get_jlpt_word_reading_levels()

volume_count_corrections = {
    'Bakemonogatari' : 13,
    'Yokohama Kaidashi Kikou' : 14,
    'Azumanga Daioh' : 3,
    'City Hunter' : 37,
}

def calculate_volume_count_per_title(title_id):

    if is_book(title_id):
        volumes = get_volumes_by_title_id(title_id, lang='jp')
        return len(volumes)
    
    m = get_data_by_title_id(title_id)

    title_id = m['_id']
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

    return volume_count


# This calculates word and kanji distribution for each JLPT levels (1-5)
# 0 = non-Katakana non-JLPT word, 6=Katakana non-JLPT word
def fetch_jlpt_levels(data, calc, total):

    ## WORDS
    jlpt_word_count_per_level = [ 0 for i in range(7) ]

    total_w = 0
    for wid,c in zip(data['word_id_list'], data['word_frequency']):
        seq,w = get_seq_and_word_from_word_id(wid)
        if w in jlpt_word_levels:
            level = jlpt_word_levels[w]
        else:
            if w in jlpt_word_reading_levels:
                level = jlpt_word_reading_levels[w]
            else:
                # non-jlpt word
                if is_katakana_word(w):
                    level = 6
                else:
                    level = 0
        if total:
            jlpt_word_count_per_level[level] += c
            total_w += c
        else:
            jlpt_word_count_per_level[level] += 1
            total_w += 1

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

    if title_data['num_sentences'] != 0:
        calc['w_per_s'] = int(calc['num_words'] / title_data['num_sentences'])
    else:
        calc['w_per_s'] = INVALID_VALUE

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


def calculate_summary_for_title(title_id):
    # recalculate the title summary
    title_data = get_analysis_data_for_title(title_id)

    if title_data is None:
        print("analysis data file for %s doesn't exist!" % (title_id))
        return

    if title_data['version'] != get_version(OCR_SUMMARY_VERSION):
        raise Exception("Old version of title [%s] summary file! Please rerun bm_ocr_prosessor.py" % (title_id))

    title_data['num_volumes'] = calculate_volume_count_per_title(title_id)

    # Average tankobon volume page count is 180, but it might vary considerable by
    # manga, so to make those statistics more comparable we calculate virtual volume
    # count and use that for those variables that rely on # of volumes.
    title_data['num_virtual_volumes'] = round(title_data['num_pages'] / AVERAGE_PAGES_PER_VOLUME,2)

    total_calc = dict()
    unique_calc = dict()

    total_calc['num_words'] = title_data['num_words']
    total_calc['num_kanjis'] = title_data['num_kanjis']
    total_calc['num_characters'] = title_data['num_characters']
    
    unique_calc['num_words'] = title_data['num_unique_words']
    unique_calc['num_kanjis'] = title_data['num_unique_kanjis']
    unique_calc['num_characters'] = -1

    fetch_jlpt_levels(title_data, total_calc, total=True)
    fetch_jlpt_levels(title_data, unique_calc, total=False)

    calculate_stats(title_data, total_calc, total=True)
    calculate_stats(title_data, unique_calc, total=False)

    # drop the detailed frequency data for the summary
    del(title_data['word_frequency'])
    del(title_data['kanji_frequency'])
    del(title_data['word_id_list'])
    if 'word_class_list' in title_data:
        del(title_data['word_class_list'])
    del(title_data['sentence_list'])
    if 'lemmas' in title_data:
        del(title_data['lemmas']) # redundant

    title_data['total_statistics'] = total_calc
    title_data['unique_statistics'] = unique_calc

    title_data['version'] = get_version(OCR_SUMMARY_VERSION)
    title_data['parser_version'] == get_version(LANUGAGE_PARSER_VERSION)
    title_data['_id'] = title_id
    title_data['is_book'] = is_book(title_id)
    title_data['updated_timestamp'] = int(time.time())
    database[BR_LANG_SUMMARY].update_one({'_id':title_id},{'$set':title_data},upsert=True)
    return title_data


def calculate_averages():

    total_manga_pages = 0
    total_manga_volumes = 0
    valid_manga_titles = 0
    total_book_pages = 0
    valid_books = 0
    for category in ['average_manga','average_book']:

        if category == 'average_manga':
            summary = database[BR_LANG_SUMMARY].find({'is_book':False}).to_list()
            for title_data in summary:
                if title_data['num_pages']>0:
                    valid_manga_titles += 1
                    total_manga_pages += title_data['num_pages']
                    total_manga_volumes += title_data['num_virtual_volumes']
        else:
            summary = database[BR_LANG_SUMMARY].find({'is_book':True}).to_list()
            for title_data in summary:
                if title_data['num_pages']>0:
                    total_book_pages += title_data['num_pages']
                    valid_books += 1

        num_valid_titles = len(summary)

        single_value_fields = list(summary[-1]['total_statistics'].keys())
        single_value_fields.remove('jlpt_word_level_pct')
        single_value_fields.remove('jlpt_word_level_per_v')
        single_value_fields.remove('jlpt_kanji_level_pct')
        single_value_fields.remove('jlpt_kanji_level_per_v')
        
        avg_calc = dict()
        for calc_f in ['total_statistics','unique_statistics']:
            avg_calc[calc_f] = dict()

            # averages for single value vields
            for f in single_value_fields:
                val = 0
                for title_data in summary:
                    val += title_data[calc_f][f]

                val /= num_valid_titles
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
            for title_data in summary:
                for i in range(7):
                    jlpt_w_level_pct[i] += title_data[calc_f]['jlpt_word_level_pct'][i]
                    jlpt_w_level_per_v[i] += title_data[calc_f]['jlpt_word_level_per_v'][i]
                for i in range(6):
                    jlpt_k_level_pct[i] += title_data[calc_f]['jlpt_kanji_level_pct'][i]
                    jlpt_k_level_per_v[i] += title_data[calc_f]['jlpt_kanji_level_per_v'][i]
            for i in range(7):
                jlpt_w_level_pct[i] = round(jlpt_w_level_pct[i]/num_valid_titles,1)
                jlpt_w_level_per_v[i] = round(jlpt_w_level_per_v[i]/num_valid_titles,1)
            for i in range(6):
                jlpt_k_level_pct[i] = round(jlpt_k_level_pct[i]/num_valid_titles,1)
                jlpt_k_level_per_v[i] = round(jlpt_k_level_per_v[i]/num_valid_titles,1)

            avg_calc[calc_f]['jlpt_word_level_pct'] = jlpt_w_level_pct
            avg_calc[calc_f]['jlpt_word_level_per_v'] = jlpt_w_level_per_v
            avg_calc[calc_f]['jlpt_kanji_level_pct'] = jlpt_k_level_pct
            avg_calc[calc_f]['jlpt_kanji_level_per_v'] = jlpt_k_level_per_v

        avg_calc['_id'] = category
        database[BR_LANG_SUMMARY].update_one({'_id':category},{'$set':avg_calc},upsert=True)

        if category == 'average_manga':
            avg_page_count = total_manga_pages/total_manga_volumes
            print("Valid %d manga titles (from total %d titles) with average page count %d / volume" 
                % (valid_manga_titles, len(get_title_names().keys()), avg_page_count))
        else:
            avg_page_count = total_book_pages/valid_books
            print("Valid %d books (from total %d titles) with average page count %d / volume" 
                % (valid_books, len(get_title_names().keys()), avg_page_count))


def save_summary():

    title_names = get_title_names()

    for title_idx, (title_id, title_name) in enumerate(title_names.items()):

        # check if summary needs recalculation
        update = True
        if not args['force']:
            old_data = database[BR_LANG_SUMMARY].find_one({'_id':title_id})

            if old_data is not None and 'parser_version' in old_data and 'version' in old_data:
                if old_data['parser_version'] == get_version(LANUGAGE_PARSER_VERSION) and \
                    old_data['version'] == get_version(OCR_SUMMARY_VERSION):
                        update = False

        if update:
            print("%d/%d [%s]" % (title_idx, len(title_names), title_name))
            calculate_summary_for_title(title_id)
    calculate_averages()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="bm_lang_summary",
        description="Bilingual Manga Language data summary generator",
    )
    parser.add_argument('--force', '-f', action='store_true', help='Force update')
    parser.add_argument('--update', '-u', action='store_true', help='Update summary (normally only add missing titles)')
    args = vars(parser.parse_args())

    save_summary()