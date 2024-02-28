import fugashi
from helper import *
from jp_parser import *

tests = [
{'line':'皆のお父さんやお母さんには前からお知らせしてあったんだけど再来週授業参観があります','jlines':[[{'皆': [3]}, {'の': []}, {'お': [4, 5]}, {'父': [4, 6, 5, 7]}, {'さん': [4, 6]}, {'や': []}, {'お': [8, 9]}, {'母': [8, 10, 9, 11]}, {'さん': [8, 10]}, {'に': []}, {'は': []}, {'前': [12]}, {'から': []}, {'お': [13]}, {'知らせ': [13, 14]}, {'して': [15]}, {'あった': [16]}, {'ん': []}, {'だけど': [17]}, {'再来': [18, 19]}, {'週': [18, 20]}, {'授業': [21, 22]}, {'参観': [21, 23]}, {'が': []}, {'あります': [16]}]], 'seq':[0, 0, 0, [1202150], [1002590], [2709500], [1610490], [1497610], [1002650], [1002370, 2595640], [1609470], [1514990], [1387210, 1392570, 1392580], [1002420], [1420400], [1157170, 1298670, 1567440, 1581900, 1595910], [1296400], [1007370], [1293650], [1293630], [1333450], [2222720], [1330290], [1302180]], 'word_list':['', '*', '-', '皆', 'お父さん', 'お父', '父さん', '父', 'お母さん', 'お母', '母さん', '母', '前', 'お知らせ', '知らせ', 'する', 'ある', 'だけど', '再来週', '再来', '週', '授業参観', '授業', '参観']},
{'line':'嫌なら早めにやっつけなきゃ','jlines':[[{'嫌': [3]}, {'なら': []}, {'早めに': [4]}, {'やっつけなきゃ': [5]}]], 'seq':[0, 0, 0, [1587610], [1400350], [1612950]], 'word_list':['', '*', '-', '嫌', '早めに', 'やっつける']},
{'line':'授業中どうぞよろしくお願いします。!！test思い出す見かける見切るひっ掛けるひっかける','jlines':[[{'授業': [3, 4]}, {'中': [3]}, {'どうぞ': [-5, 6]}, {'よろしく': [-7, -5, -8]}, {'お': [-7, -9, 10]}, {'願い': [-7, -9, 11]}, {'します': [-7, -9, 12]}, {'。!！': []}, {'test': []}, {'思い出す': [13]}, {'見かける': [14]}, {'見切る': [15]}, {'ひっ': []}, {'掛ける': [16]}, {'ひっかける': [17]}]], 'seq':[0, 0, 0, [1885500], [1330290], [1008960], [1189130], [2133750], [1224890, 2835139, 2846370], [1001720], [2036870], [1217950], [1157170, 1298670, 1567440, 1581900, 1595910], [1309260], [1604430], [1846610], [1207610], [1169360]], 'word_list':['', '*', '-', '授業中', '授業', 'どうぞよろしく', 'どうぞ', 'よろしくお願いします', 'よろしく', 'お願いします', 'お願い', '願う', 'する', '思い出す', '見かける', '見切る', '掛ける', 'ひっかける']},
{'line':'まあ隣の人があやしかったよ！！','jlines':[[{'まあ': [3]}, {'隣': [4]}, {'の': []}, {'人': [5]}, {'が': []}, {'あやしかった': [6]}, {'よ': []}, {'！！': []}]], 'seq':[0, 0, 0, [1012050], [1555830], [1580640], [1586700, 2843261]], 'word_list':['', '*', '-', 'まあ', '隣', '人', 'あやしい']},

{'line':'だーからあるいていくんだね～','jlines':[[{'だー': []}, {'から': []}, {'あるいて': [3]}, {'いく': [4]}, {'ん': []}, {'だ': []}, {'ね': []}, {'～': []}]], 'seq':[0, 0, 0, [1514320], [1578850, 2783550, 2856718]], 'word_list':['', '*', '-', 'あるく', 'いく']},
{'line':'人生とは給食みたいなものだもの','jlines':[[{'人生': [3]}, {'と': []}, {'は': []}, {'給食': [4]}, {'みたい': [-5]}, {'な': [-5]}, {'もの': [6]}, {'だもの': [7]}]], 'seq':[0, 0, 0, [1368370], [1230250], [2839776], [1322990, 1502390], [1007470, 1753980]], 'word_list':['', '*', '-', '人生', '給食', 'みたいな', 'もの', 'だもの']},

{'line':'そういえばおばあちゃんの家に行く途中に','jlines':[[{'そう': [-3, 4]}, {'いえば': [-3, 5]}, {'お': [6]}, {'ばあ': [6, 7]}, {'ちゃん': [6, 7]}, {'の': []}, {'家': [8, -8]}, {'に': []}, {'行く': [9]}, {'途中': [10]}, {'に': []}]], 'seq':[0, 0, 0, [1982210], [1176700, 1440810, 2137720], [1254600, 1587040], [2009460], [2009465], [1191730, 1191740, 1457730, 2220300], [1578850], [1582200]], 'word_list':['', '*', '-', 'そういえば', 'そう', 'いう', 'おばあちゃん', 'ばあちゃん', '家', '行く', '途中']},

{'line':'．．．．．別にいいでしょ一人でも誰かと一緒にいる必要はない','jlines':[[{'．．．．．': []}, {'別': [3, 4]}, {'に': [3]}, {'いい': [5]}, {'でしょ': [-6]}, {'一人': [-7, 8]}, {'で': [-7]}, {'も': []}, {'誰': [9, 10]}, {'か': [9]}, {'と': []}, {'一緒': [11, 12]}, {'に': [11]}, {'いる': [13]}, {'必要': [14]}, {'は': []}, {'ない': [15]}]], 'seq':[0, 0, 0, [1509480], [1509430, 2259830], [2820690], [1008420], [1163700], [1576150], [1416840], [1416830], [1163420], [1163400], [1322180, 1391500, 1465580, 1546640, 1577980, 1587780, 2209310, 2729170, 2851105, 2851106], [1487660], [1518450, 1529520]], 'word_list':['', '*', '-', '別に', '別', 'いい', 'でしょ', '一人で', '一人', '誰か', '誰', '一緒に', '一緒', 'いる', '必要', 'ない']},

{'line':'ばんそうこう持ってるから','jlines':[[{'ば': [3]}, {'ん': []}, {'そうこう': [4]}, {'持ってる': [5]}, {'から': []}]], 'seq':[0, 0, 0, [1525750], [1831960], [1315720]], 'word_list':['', '*', '-', 'ばん', 'そうこう', '持つ']},
{'line':'頭おかしくなっちゃったの？','jlines':[[{'頭': [3]}, {'おかしく': [4]}, {'なっちゃった': [5]}, {'の': []}, {'？': []}]], 'seq':[0, 0, 0, [1582310, 2252700, 2791490, 2791510, 2843246, 2856438, 2856439, 2856440], [1190860], [1375610, 1532910, 1611000]], 'word_list':['', '*', '-', '頭', 'おかしい', 'なる']},
{'line':'一人なの？','jlines':[[{'一人': [3]}, {'な': [-4]}, {'の': [-4]}, {'？': []}]], 'seq':[0, 0, 0, [1576150], [2425930]], 'word_list':['', '*', '-', '一人', 'なの']},
{'line':'ねえどうして腕を切っていたの？','jlines':[[{'ねえ': []}, {'どう': [3, 4]}, {'して': [3, 5]}, {'腕': [6]}, {'を': []}, {'切って': [7]}, {'いた': [8]}, {'の': []}, {'？': []}]], 'seq':[0, 0, 0, [1466940], [1008910], [1157170, 1298670, 1567440, 1581900, 1595910], [1562850, 2139850], [1384830], [1322180, 1391500, 1465580, 1546640, 1577980, 1587780, 2209310, 2729170, 2851105, 2851106]], 'word_list':['', '*', '-', 'どうして', 'どう', 'する', '腕', '切る', 'いる']},
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

        print("Testing:",line)
        kc, ud_words, ud_word_ortho, ud_word_classes = \
            parse_line_with_unidic(line,kanji_count, lemmas)
        
        ud_words, ud_word_ortho, ud_word_class, ud_word_flags = \
            post_process_unidic_particles(ud_words, ud_word_ortho, ud_word_class)

        word_ref = parse_with_jmdict(
            ud_words, ud_word_ortho, ud_word_classes, ud_word_flags,
            word_list, word_count, word_seq, word_class_list,
            word_count_per_class, 
        )
        jlines = reassemble_block([line], ud_words, word_ref)

        ud_word_class_txt = [(w,unidic_word_classes[cl]) for w,cl in zip(ud_words, ud_word_classes)]
        unique_jmdict_word_class_list_txt = []
        for w,cl in zip(word_list, word_class_list):
            if len(cl)>0:
                unique_jmdict_word_class_list_txt.append((w,jmdict_parts_of_speech_list[cl[0]]))
            else:
                unique_jmdict_word_class_list_txt.append((w,''))


        if jlines != test['jlines']:
            for i, (a,b) in enumerate(zip(jlines[0], test['jlines'][0])):
                if a != b:
                    print("%d : %s != %s" % (i,a,b))
            raise Exception("Error in references!")
        if word_seq != test['seq']:
            for i, (a,b) in enumerate(zip(word_seq, test['seq'])):
                if a != b:
                    print("%d : %s != %s" % (i,a,b))
            raise Exception("Error in sequences!")
        if word_list != test['word_list']:
            raise Exception("Error in word list!")
    print("Tests ok")


def test_jmdict():
    #line = "皆のお父さんやお母さんには前からお知らせしてあったんだけど再来週授業参観があります"
    #line = '嫌なら早めにやっつけなきゃ'
    #line = '授業中どうぞよろしくお願いします。!！test思い出す見かける見切るひっ掛けるひっかける'
    #line = 'まあ隣の人があやしかったよ！！'
    #line = 'だーからあるいていくんだね～'

    #line = 'お茶がほしいです。'
    #line = "様子を見てもらうとても大事な日だから今から回すプリントをきちんとお父さんお母さんに渡してね"
    #line = '人生とは給食みたいなものだもの'

    #line = 'じゃあ私にはきっと無理痛いのは嫌いだもの'
    #line = '食べ物が貰えないから悲しいのかしら'
    #line = 'そういえばおばあちゃんの家に行く途中に'
    #line = 'お茶を濁す'
    #line = 'ばんそうこう持ってるから'
    #line = '頭おかしくなっちゃったの？'
    #line = '一人なの？'
    #line ='．．．．．別にいいでしょ一人でも誰かと一緒にいる必要はない'
    #line =   '．．．．．．あんた嫌われてんでしょ？'
    #line = 'ねえどうして腕を切っていたの？'

    line = '子どもの癖に偉そうな喋り方'
    line = '確かにそれには私も同じ考えを持っているわ'
    line = 'まあでもそこらの子ども達よりは偉いかも'
    line = '．．．．．．なんでんなことを会ったばっかりのあんたに話さなくちゃいけないの？'
    line = '私が本当にやばい奴だったらどうすんだおごネるよ'

    line = 'それにしても腕を切って落ち着く人がいるなんて世界はまだまだ分からないことだらけ'
    line = 'どうしたんだ突然'

    line = "しかし、これらの文明の源はすべてギリシアにあるのです"

    line =  'を表したとしたら、とても興味深い。' \
            'キートン．．．それは面白いですね。警告は' \
            '能なんかはどうなんでしょう。'\
            '太平数の概念はチンバンジーには無理だと'\
            '言われていたが、最近ではちゃんと物が数え'\
            'られ、数学も理解出来るとわかってる。数と'\
            'いうのは本当の抽象擬灸だから、相当な知能'\
            'があるということだな。ところでそのラーメ'\
            'ン、チャーシューは柔らかかいか？最近、間'\
            'いものがイカンようになってな。'

    kanji_count = dict()
    lemmas = dict()
    word_count_per_class = [0] * len(unidic_word_classes)

    unique_jmdict_word_list = ['','*','-'] 
    unique_jmdict_word_class_list = [[],[],[]] 
    unique_jmdict_word_seq = [0,0,0]
    unique_jmdict_word_count = [0,0,0]

    kc, ud_words, ud_word_ortho, ud_word_class = parse_line_with_unidic(line,kanji_count, lemmas)

    ud_words, ud_word_ortho, ud_word_class, ud_word_flags = \
        post_process_unidic_particles(ud_words, ud_word_ortho, ud_word_class)

    word_ref = parse_with_jmdict(
        ud_words, ud_word_ortho, ud_word_class, ud_word_flags,
        unique_jmdict_word_list, unique_jmdict_word_count, unique_jmdict_word_seq, unique_jmdict_word_class_list,
        word_count_per_class, 
        #unique_jdict_phrases, unique_jdict_phrase_count, unique_jdict_phrase_seq
    )
    jlines = reassemble_block([line], ud_words, word_ref)


    ud_word_class_txt = [(w,unidic_word_classes[cl]) for w,cl in zip(ud_words, ud_word_class)]
    unique_jmdict_word_class_list_txt = []
    for w,cl in zip(unique_jmdict_word_list, unique_jmdict_word_class_list):
        if len(cl)>0:
            unique_jmdict_word_class_list_txt.append((w,jmdict_parts_of_speech_list[cl[0]]))
        else:
            unique_jmdict_word_class_list_txt.append((w,''))

    """
    kanji_count = dict()
    lemmas = dict()
    word_count_per_class = [0] * len(unidic_word_classes)

    unique_jmdict_word_list = ['','*','-'] 
    unique_jmdict_word_class_list = [[],[],[]] 
    unique_jmdict_word_seq = [0,0,0]
    unique_jmdict_word_count = [0,0,0]


    parsed_lines = []
    parsed_lines_ortho = []
    parsed_lines_classes = []
    parsed_lines_flags = []


    line = ''.join(lines)
    kc, ud_words2, ud_word_ortho2, ud_word_class2, ud_word_flags2, = \
        parse_line_with_unidic(line, kanji_count, lemmas)

    jlines = parse_with_jmdict(
        ud_words2, ud_word_ortho2, ud_word_class2, ud_word_flags2,
        unique_jmdict_word_list, unique_jmdict_word_count, unique_jmdict_word_seq, unique_jmdict_word_class_list,
        word_count_per_class, 
        #unique_jdict_phrases, unique_jdict_phrase_count, unique_jdict_phrase_seq
    )

    block = reassemble_block(lines, ud_words2, jlines)
    """

    jlines_str = str(jlines)
    print("{'line':'%s','jlines':%s, 'seq':%s, 'word_list':%s}" % (line,str(jlines),str(unique_jmdict_word_seq),str(unique_jmdict_word_list)))
          
    pass

load_jmdict()
load_conjugations()

test_jmdict()
do_tests()
