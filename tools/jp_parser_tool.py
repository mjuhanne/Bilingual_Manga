import fugashi
from helper import *
from jp_parser import *
from jp_parser_print import *
import sys
import argparse

parser = argparse.ArgumentParser(
    prog="jp_parser tool. Parses text for lexical elements",
    description="",
)

parser.add_argument('text', nargs='?', type=str, default=None, help='Text to be parsed')
parser.add_argument('--verbose-level', '-v', type=int, default=3, help='Verbose level')

args = vars(parser.parse_args())



def parse(lines):

    #line = ''.join(lines)
    print("Lines: " + str(lines))

    kanji_count = dict()
    word_count_per_class = [0] * len(unidic_class_list)

    results = init_scan_results()

    kc, ud_items, mismatch = parse_block_with_unidic(lines,kanji_count)

    print("After unidic scanning:")
    for item in ud_items:
        if item.ortho == item.txt:
            ortho = '。'
        else:
            ortho = item.ortho
        cll = item.classes
        cl_str = '/'.join([unidic_class_list[cl] for cl in cll]).ljust(5,'　')
        cl_meaning_str = '/'.join([unidic_class_to_string(cl) for cl in cll])
        unidic_verb_conj = ''
        if verb_class in cll:
            if item.details is not None:
                unidic_verb_conj = item.details[5]
            else:
                unidic_verb_conj = ''
        masu = ''
        if item.is_masu:
            masu = '-masu'
        print("%s %s %s %s %s %s %s" % ( 
            flags_to_str(item.flags).ljust(10), item.txt.ljust(6,'　'), ortho.ljust(6,'　'), 
            cl_str, cl_meaning_str, unidic_verb_conj, masu)
        )

    ud_items = post_process_unidic_particles(ud_items)

    print("\nAfter unidic post-processing:")
    for item in ud_items:
        pretty_print_lexical_item(item)

    parse_with_jmdict(
        ud_items, results,
    )
    jlines = reassemble_block(lines, ud_items, results['item_word_id_refs'])
    scores = reassemble_block_scores(lines, ud_items, results['item_word_id_scores'])

    print("Lines: " + str(lines))

    print("\nAfter jmdict scanning:")
    print_scanning_results(jlines, scores, results, ud_items)

    print("Score: %d" % results['score'])
    jlines_str = str(jlines)
    #print("{'line':'%s','jlines':%s, 'seq':%s, 'word_list':%s}" % (line,str(jlines),str(unique_jmdict_word_seq),str(unique_jmdict_word_list)))
          
    pass

if __name__ == "__main__":
    init_parser(load_meanings=True)
    jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_max_kanji_element_len = get_jmdict_kanji_element_set()
    jmdict_readings, jmdict_reading_seq, jmdict_max_reading_len = get_jmdict_reading_set()
    load_manga_specific_adjustments("ALL")
    print(sys.argv)
    if args['text'] is None:
        #jslines = '["ようこそおきな"]' #'["ねえどうして"]'
        #lines = json.loads(jslines)
        lines = ["ボール", "とってー！！"]

    else:
        lines = json.loads(args['text'])

    open_log_file("parserlog.txt")
    set_verbose_level(args['verbose_level'])
    parse(lines)
    close_log_file()
