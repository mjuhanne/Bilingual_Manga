# Bilingual Manga Language analysis summary tool
#
# This script calculates aggregate kanji and word count data as well as word distribution
# for each 5 JLPT levels. The resulting data is saved into lang_summary.json file.
import json
import argparse
INVALID_VALUE = -1
from helper import *

volume_count_per_title = dict()

jlpt_kanjis = get_jlpt_kanjis()
jlpt_word_levels = get_jlpt_word_levels()
jlpt_word_reading_levels= get_jlpt_word_reading_levels()

volume_count_corrections = {
    'Bakemonogatari' : 13,
    'Yokohama Kaidashi Kikou' : 14,
    'Azumanga Daioh' : 3,
    'City Hunter' : 37,
}

parser = argparse.ArgumentParser(
    prog="bm_lang_summary",
    description="Bilingual Manga Language data summary generator",
)
parser.add_argument('--force', '-f', action='store_true', help='Force update')
args = vars(parser.parse_args())


read_manga_metadata()

with open(manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_data = json.loads(data)

ext_manga_data = []
ext_manga_oids = []
with open(ext_manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    ext_manga_data = json.loads(data)
    manga_data += ext_manga_data
    for m in ext_manga_data:
        ext_manga_oids.append(m['_id']['$oid'])

old_summary = dict()
if os.path.exists(summary_file):
    with open(summary_file,"r") as f:
        old_summary_data = json.loads(f.read())
        if 'version' in old_summary_data and old_summary_data['version'] == get_version(OCR_SUMMARY_VERSION):
            old_summary = old_summary_data

old_ext_summary = dict()
if os.path.exists(ext_summary_file):
    with open(ext_summary_file,"r") as f:
        old_ext_summary_data = json.loads(f.read())
        if 'version' in old_ext_summary_data and old_ext_summary_data['version'] == get_version(OCR_SUMMARY_VERSION):
            old_ext_summary = old_ext_summary_data

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


def save_summary():

    summary = dict()
    ext_summary = dict()

    title_names = get_title_names()
    num_titles = len(title_names)

    total_pages = 0
    num_valid_titles = 0
    num_valid_ext_titles = 0
    total_volumes = 0

    single_value_field_keys = None
    for title_id, title_name in title_names.items():

        # check if summary needs recalculation
        title_data = None
        if not args['force']:
            old_data = None
            if title_id in old_summary:
                old_data = old_summary[title_id]
            elif title_id in old_ext_summary:
                old_data = old_ext_summary[title_id]
            if old_data is not None and 'parser_version' in old_data and 'version' in old_data:
                if old_data['parser_version'] == get_version(LANUGAGE_PARSER_VERSION) and \
                    old_data['version'] == get_version(OCR_SUMMARY_VERSION):
                        title_data = old_data

        if title_data is None:

            # recalculate the title summary
            print(title_name)
            title_filename = title_analysis_dir + title_id + ".json"

            if not os.path.exists(title_filename):
                print("%s data file %s doesn't exist!" % (title_name,title_filename))
                continue

            o_f = open(title_filename,"r",encoding="utf-8")
            title_data = json.loads(o_f.read())
            o_f.close()

            if title_data['version'] != get_version(OCR_SUMMARY_VERSION):
                raise Exception("Old version of title [%s] summary file %s! Please rerun bm_ocr_prosessor.py" % (title_name,title_filename))

            title_data['num_volumes'] = volume_count_per_title[title_id]

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
            del(title_data['word_class_list'])
            del(title_data['sentence_list'])
            if 'lemmas' in title_data:
                del(title_data['lemmas']) # redundant

            title_data['total_statistics'] = total_calc
            title_data['unique_statistics'] = unique_calc

            single_value_field_keys = total_calc.keys()

        if title_id in ext_manga_oids:
            ext_summary[title_id] = title_data
        else:
            summary[title_id] = title_data

        if title_data['num_pages']>0:
            if title_id in ext_manga_oids:
                num_valid_ext_titles += 1
            else:
                num_valid_titles += 1
            total_pages += title_data['num_pages']
            total_volumes += title_data['num_virtual_volumes']

    if single_value_field_keys is not None:
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
            for title_id, title_data in summary.items():
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

        summary['average'] = avg_calc

        avg_page_count = total_pages/total_volumes
        print("Valid titles %d(+%d ext) / %d with average page count %d / volume" 
            % (num_valid_titles, num_valid_ext_titles, len(title_names.keys()), avg_page_count))

        with open(summary_file,"w") as f:
            summary['version'] = get_version(OCR_SUMMARY_VERSION)
            f.write(json.dumps(summary, ensure_ascii=False))
        if len(ext_summary.keys())>0:
            with open(ext_summary_file,"w") as f:
                ext_summary['version'] = get_version(OCR_SUMMARY_VERSION)
                f.write(json.dumps(ext_summary, ensure_ascii=False))
    else:
        # nothing changed 
        print("No changes")


save_summary()