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

def parse(line):

    kanji_count = dict()
    lemmas = dict()
    word_count_per_class = [0] * len(unidic_word_classes)

    unique_jmdict_word_list = ['','*','-'] 
    unique_jmdict_word_class_list = [[],[],[]] 
    unique_jmdict_word_seq = [0,0,0]
    unique_jmdict_word_count = [0,0,0]

    kc, ud_words, ud_word_ortho, ud_word_classes = parse_line_with_unidic(line,kanji_count, lemmas)

    print("After unidic scanning:")
    for w,ortho,cl in zip(ud_words, ud_word_ortho, ud_word_classes):
        if ortho == w:
            ortho = ''
        print("%s %s %s %s %s" % ( 
            "".ljust(10), w.ljust(6,'　'), ortho.ljust(6,'　'), 
            unidic_word_classes[cl].ljust(5,'　'), unidic_class_to_string(cl))
        )

    ud_words, ud_word_ortho, ud_word_classes, ud_word_flags = \
        post_process_unidic_particles(ud_words, ud_word_ortho, ud_word_classes)

    print("\nAfter unidic post-processing:")
    for w,ortho,cl,flags in zip(ud_words, ud_word_ortho, ud_word_classes, ud_word_flags):
        if ortho == w:
            ortho = ''
        print("%s %s %s %s %s" % ( 
            flags_to_str(flags).ljust(10), w.ljust(6,'　'), ortho.ljust(6,'　'), 
            unidic_word_classes[cl].ljust(5,'　'), unidic_class_to_string(cl))
        )

    word_ref = parse_with_jmdict(
        ud_words, ud_word_ortho, ud_word_classes, ud_word_flags,
        unique_jmdict_word_list, unique_jmdict_word_count, unique_jmdict_word_seq, unique_jmdict_word_class_list,
        word_count_per_class,
        #unique_jdict_phrases, unique_jdict_phrase_count, unique_jdict_phrase_seq
    )
    jlines = reassemble_block([line], ud_words, word_ref)

    unique_jmdict_word_class_list_txt = []
    for w,cl in zip(unique_jmdict_word_list, unique_jmdict_word_class_list):
        if len(cl)>0:
            unique_jmdict_word_class_list_txt.append((w,jmdict_parts_of_speech_list[cl[0]]))
        else:
            unique_jmdict_word_class_list_txt.append((w,''))

    print("\nAfter jmdict scanning:")
    for i, (entry) in enumerate(jlines[0]):
        w= next(iter(entry))
        cl = ud_word_classes[i]
        cl_str = unidic_word_classes[cl].ljust(5,'　')
        cl_meaning_str = unidic_class_to_string(cl)
        print(" %s %s %s" % ( 
            w.ljust(6,'　'), cl_str, cl_meaning_str
            )
        )

        refs = entry[w]
        if len(refs) == 0:
            print("\t ** NO WORDS FOUND ** ")
        else:
            refs2 = [ (unique_jmdict_word_list[abs(w_idx)], unique_jmdict_word_seq[abs(w_idx)]) for w_idx in refs]
            for (jmdict_w, seq_list) in refs2:
                for seq in seq_list:
                    meanings = jmdict_meanings[seq]
                    print("\t[%d] %s : %s" % (seq, jmdict_w,meanings))
                    cl_list = jmdict_pos[seq]
                    for cl in cl_list:
                        print("\t\t%s" % jmdict_parts_of_speech_list[cl])

    for w,cl in zip(unique_jmdict_word_list, unique_jmdict_word_class_list):
        if len(cl)>0:
            unique_jmdict_word_class_list_txt.append((w,jmdict_parts_of_speech_list[cl[0]]))
        else:
            unique_jmdict_word_class_list_txt.append((w,''))

    jlines_str = str(jlines)
    #print("{'line':'%s','jlines':%s, 'seq':%s, 'word_list':%s}" % (line,str(jlines),str(unique_jmdict_word_seq),str(unique_jmdict_word_list)))
          
    pass

load_jmdict(load_meanings=True)
load_conjugations()

print("test")
print(sys.argv)
if len(sys.argv)<2:
    jslines =  '["どうして","披露するのを","嫌がるの？"]'
    lines = json.loads(jslines)
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

else:
    lines = json.loads(sys.argv[1])
line = ''.join(lines)
print("Line: " + line)

open_log_file("parserlog.txt")
set_verbose_level(2)
parse(line)
close_log_file()
