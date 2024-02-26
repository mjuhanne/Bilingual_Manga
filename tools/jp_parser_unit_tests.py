import fugashi
from helper import *
from jp_parser import *

tests = [
{'line':'皆のお父さんやお母さんには前からお知らせしてあったんだけど再来週授業参観があります','jlines':[[{'皆': [3]}, {'の': []}, {'お': [5, 4]}, {'父': [7, 5, 6, 4]}, {'さん': [5, 7]}, {'や': []}, {'お': [9, 8]}, {'母': [11, 9, 10, 8]}, {'さん': [9, 11]}, {'に': []}, {'は': []}, {'前': [12]}, {'から': []}, {'お': [13]}, {'知らせ': [13, 14]}, {'して': [15, 16]}, {'あった': [17]}, {'ん': []}, {'だ': [18]}, {'けど': [18]}, {'再来': [20, 19]}, {'週': [20, 21]}, {'授業': [23, 22]}, {'参観': [23, 24]}, {'が': []}, {'あります': [17]}]], 'seq':[0, 0, 0, 1202150, 2709500, 1002590, 1497610, 1610490, 2595640, 1002650, 1514990, 1609470, 1392580, 1002420, 1420400, 1595910, 2424740, 1586840, 1007370, 1293630, 1293650, 1333450, 1330290, 2222720, 1302180], 'word_list':['', '*', '-', '皆', 'お父', 'お父さん', '父', '父さん', 'お母', 'お母さん', '母', '母さん', '前', 'お知らせ', '知らせ', 'する', 'して', 'ある', 'だけど', '再来', '再来週', '週', '授業', '授業参観', '参観']},
{'line':'嫌なら早めにやっつけなきゃ','jlines':[[{'嫌': [3]}, {'なら': []}, {'早め': [6, 5]}, {'に': [6]}, {'やっつけなきゃ': [7]}]], 'seq':[0, 0, 0, 1587610, 2827768, 2078850, 1400350, 1612950], 'word_list':['', '*', '-', '嫌', 'なら', '早め', '早めに', 'やっつける']},
{'line':'授業中どうぞよろしくお願いします。!！test思い出す見かける見切るひっ掛けるひっかける','jlines':[[{'授業': [4, 3]}, {'中': [4]}, {'どうぞ': [-6, 5]}, {'よろしく': [-8, -7, -6]}, {'お': [-8, -10, 9]}, {'願い': [-8, -10, 9, 11, 12]}, {'します': [-8, -10, 13]}, {'。!！': []}, {'test': []}, {'思い出す': [14]}, {'見かける': [15]}, {'見切る': [16]}, {'ひっ': [17]}, {'掛ける': [18]}, {'ひっかける': [19]}]], 'seq':[0, 0, 0, 1330290, 1885500, 1189130, 1008960, 2846370, 2133750, 2036870, 1001720, 1217950, 1217900, 1595910, 1309260, 1604430, 1846610, 2564800, 1207610, 1169360], 'word_list':['', '*', '-', '授業', '授業中', 'どうぞ', 'どうぞよろしく', 'よろしく', 'よろしくお願いします', 'お願い', 'お願いします', '願う', '願い', 'する', '思い出す', '見かける', '見切る', 'ひっ', '掛ける', 'ひっかける']},
{'line':'まあ隣の人があやしかったよ！！','jlines':[[{'まあ': [3]}, {'隣': [4]}, {'の': []}, {'人': [5]}, {'が': []}, {'あやしかっ': [6]}, {'た': [6]}, {'よ': []}, {'！！': []}]], 'seq':[0, 0, 0, 1012050, 1555830, 2149890, 2843261], 'word_list':['', '*', '-', 'まあ', '隣', '人', 'あやしい']},
]

def do_tests():
    
    for test in tests:
        line = test['line']
        kanji_count = dict()
        lemmas = dict()
        word_list = ['','*','-'] 
        word_class_list = [[],[],[]] 
        word_seq = [0,0,0]
        word_count = [0,0,0]
        word_count_per_class = [0] * len(unidic_word_classes)

        kc, ud_words, ud_word_ortho, ud_word_classes = parse_line_with_unidic(line,kanji_count, lemmas)
        jlines = parse_block_with_jmdict(
            [ud_words], [ud_word_ortho], [ud_word_classes], 
            word_list, word_count, word_seq, word_class_list,
            word_count_per_class, 
        )

        if jlines != test['jlines']:
            raise Exception("Error in references!")
        if word_seq != test['seq']:
            raise Exception("Error in sequences!")
        if word_list != test['word_list']:
            raise Exception("Error in word list!")
    print("Tests ok")


def test_jmdict():
    #line = "皆のお父さんやお母さんには前からお知らせしてあったんだけど再来週授業参観があります"
    #line = '嫌なら早めにやっつけなきゃ'
    #line = '授業中どうぞよろしくお願いします。!！test思い出す見かける見切るひっ掛けるひっかける'
    #line = 'まあ隣の人があやしかったよ！！'

    #line = 'お茶がほしいです。'
    #line = 'お茶を濁す'
    line = "様子を見てもらうとても大事な日だから今から回すプリントをきちんとお父さんお母さんに渡してね"

    kanji_count = dict()
    lemmas = dict()
    word_count_per_class = [0] * len(unidic_word_classes)

    unique_jmdict_word_list = ['','*','-'] 
    unique_jmdict_word_class_list = [[],[],[]] 
    unique_jmdict_word_seq = [0,0,0]
    unique_jmdict_word_count = [0,0,0]

    kc, ud_words, ud_word_ortho, ud_word_classes = parse_line_with_unidic(line,kanji_count, lemmas)

    #parsed_lines.append(unidic_words)
    jlines = parse_block_with_jmdict(
        [ud_words], [ud_word_ortho], [ud_word_classes], 
        unique_jmdict_word_list, unique_jmdict_word_count, unique_jmdict_word_seq, unique_jmdict_word_class_list,
        word_count_per_class, 
        #unique_jdict_phrases, unique_jdict_phrase_count, unique_jdict_phrase_seq
    )
    jlines_str = str(jlines)
    print("{'line':'%s','jlines':%s, 'seq':%s, 'word_list':%s}" % (line,str(jlines),str(unique_jmdict_word_seq),str(unique_jmdict_word_list)))
          
    pass

load_jmdict()
test_jmdict()
do_tests()
