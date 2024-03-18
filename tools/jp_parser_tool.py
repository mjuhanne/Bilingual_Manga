import fugashi
from helper import *
from jp_parser import *
import sys

word_flag_to_str = {
    NO_SCANNING : "NO_SCAN",
    START_OF_SCAN_DISABLED : "DIS_START",
    #MERGE_PARTICLE : ''
    DISABLE_ORTHO : "DIS_ORTHO",
}
def flags_to_str(word_flag):
    return ' '.join([word_flag_to_str[key] for key in word_flag_to_str.keys() if word_flag & key])

def print_scanning_results(jlines, results, ud_items):
    for i, (entry) in enumerate(jlines[0]):
        w= next(iter(entry))
        cl = ud_items[i].cl
        cl_str = unidic_class_list[cl].ljust(5,'　')
        cl_meaning_str = unidic_class_to_string(cl)
        print(" %s %s %s" % ( 
            w.ljust(6,'　'), cl_str, cl_meaning_str
            )
        )

        word_id_refs = entry[w]
        if len(word_id_refs) == 0:
            print("\t ** NO WORDS FOUND ** ")
        else:
            word_ids = [ results['word_id_list'][w_id_idx] for w_id_idx in word_id_refs]
            for (word_id) in word_ids:
                (seq,senses,word) = expand_word_id(word_id)
                if '/' not in word_id:
                    s_ref = '*'
                else:
                    s_ref = str(senses[0])
                print("\t\t[%d/%s] %s\t[F %s/%s]" % (seq,s_ref, word, get_kanji_element_freq(seq), get_reading_freq(seq)))
                for i,(sense) in enumerate(senses):
                    meanings = get_meanings_by_sense(seq,sense)
                    if s_ref == '*':
                        count = str(i + 1)+'#'
                    else:
                        count = ''
                    print("\t\t\t%s %s" % (count,meanings))
                    cl_list = get_class_list_by_seq(seq)[sense]
                    for cl in cl_list:
                        print("\t\t\t\t%s" % jmdict_class_list[cl])

def parse(line):

    kanji_count = dict()
    word_count_per_class = [0] * len(unidic_class_list)

    results = init_scan_results()

    kc, ud_items = parse_line_with_unidic(line,kanji_count)

    print("After unidic scanning:")
    for item in ud_items:
        if item.ortho == item.txt:
            ortho = ''
        else:
            ortho = item.ortho
        print("%s %s %s %s %s" % ( 
            flags_to_str(item.flags).ljust(10), item.txt.ljust(6,'　'), ortho.ljust(6,'　'), 
            unidic_class_list[item.cl].ljust(5,'　'), unidic_class_to_string(item.cl))
        )

    ud_items = post_process_unidic_particles(ud_items)

    print("\nAfter unidic post-processing:")
    for item in ud_items:
        if item.ortho == item.txt:
            ortho = ''
        else:
            ortho = item.ortho
        print("%s %s %s %s %s %s" % ( 
            flags_to_str(item.flags).ljust(10), item.txt.ljust(6,'　'), ortho.ljust(6,'　'), item.alt_txt.ljust(6,'　'),
            unidic_class_list[item.cl].ljust(5,'　'), unidic_class_to_string(item.cl))
        )

    parse_with_jmdict(
        ud_items, results,
    )
    jlines = reassemble_block([line], ud_items, results['item_word_id_refs'])

    print("\nAfter jmdict scanning:")
    print_scanning_results(jlines, results, ud_items)

    jlines_str = str(jlines)
    #print("{'line':'%s','jlines':%s, 'seq':%s, 'word_list':%s}" % (line,str(jlines),str(unique_jmdict_word_seq),str(unique_jmdict_word_list)))
          
    pass

if __name__ == "__main__":
    init_parser(load_meanings=True)
    jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_max_kanji_element_len = get_jmdict_kanji_element_set()
    jmdict_readings, jmdict_reading_seq, jmdict_max_reading_len = get_jmdict_reading_set()

    print("test")
    print(sys.argv)
    if len(sys.argv)<2:
        jslines = '["議師料"]' #'["ねえどうして"]'
        lines = json.loads(jslines)
        """
        lines =  ['を表したとしたら、とても興味深い。',
                'キートン．．．それは面白いですね。警告は' ,
                '能なんかはどうなんでしょう。',
                '太平数の概念はチンバンジーには無理だと',
                '言われていたが、最近ではちゃんと物が数え',
                'られ、数学も理解出来るとわかってる。数と',
                'いうのは本当の抽象擬灸だから、相当な知能',
                'があるということだな。ところでそのラーメ',
                'ン、チャーシューは柔らかかいか？最近、間',
                'いものがイカンようになってな。'
        ]
        """

    else:
        lines = json.loads(sys.argv[1])
    line = ''.join(lines)
    print("Line: " + line)

    open_log_file("parserlog.txt")
    set_verbose_level(2)
    parse(line)
    close_log_file()
