import fugashi
from helper import *
from jp_parser import *
from jp_parser_tool import print_scanning_results

# TODO:  どんあに gets fused with つまらなくても
#ですがどんなにつまらなくても毎日行くことになっています

# できたら
#朝から南さんとお話できたらどんなに素敵なことか

tests = [
{'c':'honorific in front of adjective (medetai)','line':'おめでとう','jlines':[[{'お': [0, 1, 2]}, {'めでとう': [0, 3]}]], 'slist':['2077340', '2268350', '2826528', '1608630'], 'word_list':['', '*', '-', 'おめでとう', 'お', 'めでたい']},
{'c':'honorific + suffix','line':'お父さん','jlines':[[{'お': [0, 1, 2, 3, 4]}, {'父': [0, 1, 5, 2, 6]}, {'さん': [0, 1, 5, 7, 8, 9]}]], 'slist':['1002590/0', '1002590/1', '2709500', '2268350', '2826528', '1610490', '1497610', '1005340', '2085690', '2106250/2'], 'word_list':['', '*', '-', 'お父さん', 'お父', 'お', '父さん', '父', 'さん']},
{'c':'prefix/suffix must be detected even when not found in the dictionary together with the stem word','line':'議師料','jlines':[[{'議': [0]}, {'師': [1, 2]}, {'料': [3]}]], 'slist':['2273760', '1956330/1', '1956330/2', '1554270'], 'word_list':['', '*', '-', '議', '師', '料']},
{'c':'iya nara / hayame+ni / tsukenakya','line':'嫌なら早めにやっつけなきゃ','jlines':[[{'嫌': [0, 1]}, {'なら': [2, 3]}, {'早め': [4, 5]}, {'に': [4]}, {'やっつけなきゃ': [6]}]], 'slist':['1587610/0', '1587610/1', '1009470/0', '1009470/1', '1400350', '2078850', '1612950'], 'word_list':['', '*', '-', '嫌', 'なら', '早めに', '早め', 'やっつける']},
{'c':'long phrase','line':'よろしくお願いします','jlines':[[{'よろしく': [0, 1, 2, 3]}, {'お': [0, 4, 5, 6, 7]}, {'願い': [0, 4, 5, 8]}, {'します': [0, 4, 9]}]], 'slist':['2133750', '1224890', '2835139', '2846370', '1001720', '2036870/0', '2268350', '2826528', '1217950', '1157170'],'swi':[3, 4, 4, 4, 5, 6, 7, 7, 8, 9],'word_list':['', '*', '-', 'よろしくお願いします', 'よろしく', 'お願いします', 'お願い', 'お', '願う', 'する']},
{'c':'past tense','line':'あやしかった','jlines':[[{'あやしかっ': [0, 1]}, {'た': [2]}]], 'slist':['1586700', '2843261', '2654250'],'swi':[3, 3, 4],'word_list':['', '*', '-', 'あやしい', 'た']},
{'c':'streched sentence','line':'だーからあるいていくんだね～','jlines':[[{'だー': [0]}, {'から': [1]}, {'あるいて': [2]}, {'いく': [3, 4, 5, 6]}, {'ん': [7, 8, 9]}, {'だ': [7, 0]}, {'ね': [10, 11, 12, 13, 14, 15]}, {'～': []}]], 'slist':['2089020', '1002980', '1514320', '1157500', '1578850', '2783550', '2856718', '2849387', '2139720/3', '2139720/4', '2029080/0', '2029080/2', '2029080/3', '2029080/4', '2029080/5', '2841117/0'],'swi':[3, 4, 5, 6, 6, 6, 6, 7, 8, 8, 9, 9, 9, 9, 9, 9],'word_list':['', '*', '-', 'だ', 'から', 'あるく', 'いく', 'んだ', 'ん', 'ね']},
{'c':'mitai+na / mono + da mono','line':'給食みたいなものだもの','jlines':[[{'給食': [0]}, {'みたい': [1, 2]}, {'な': [1]}, {'もの': [3, 4, 5, 6, 7, 8, 9, 10, 11]}, {'だもの': [12, 13]}]], 'slist':['1230250', '2839776', '2016410', '1322990', '1502390/0', '1502390/1', '1502390/2', '1502390/3', '1502390/4', '1502390/5', '1502390/8', '1502390/9', '1007470', '2089020'],'swi':[3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 8],'word_list':['', '*', '-', '給食', 'みたいな', 'みたい', 'もの', 'だもの', 'だ']},
{'c':'conditional','line':'そういえば','jlines':[[{'そう': [0, 1]}, {'いえば': [0, 2, 3]}]], 'slist':['1982210', '2137720/0', '1254600', '1587040'],'swi':[3, 4, 5, 5],'word_list':['', '*', '-', 'そういえば', 'そう', 'いう']},
{'c':'betsu+ni / desho','line':'別にいいでしょ','jlines':[[{'別': [0, 1, 2, 3, 4]}, {'に': [0]}, {'いい': [5]}, {'でしょ': [6, 7]}]], 'slist':['1509480', '1509430/0', '1509430/1', '1509430/2', '2259830', '2820690', '1008420', '1628500'],'swi':[3, 4, 4, 4, 4, 5, 6, 7],'word_list':['', '*', '-', '別に', '別', 'いい', 'でしょ', 'です']},

{'c':'hitori demo/ dare+ka / isshou+ni','line':'一人でも誰かと一緒にいる必要はない','jlines':[[{'一人': [0, 1, 2, 3]}, {'で': [0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]}, {'も': [4, 5, 6, 7, 14, 15, 16, 17]}, {'誰': [18, 19]}, {'か': [18, 20, 21, 22, 23]}, {'と': [24, 25, 26, 27, 28]}, {'一緒': [29, 30]}, {'に': [29, 31]}, {'いる': [32]}, {'必要': [33]}, {'は': [34]}, {'ない': [35, 36, 37]}]], 'slist':['1163700', '1576150/0', '1576150/1', '1576150/2', '1008460/1', '1008460/2', '1008460/3', '1008460/4', '2028980/0', '2028980/1', '2028980/2', '2028980/3', '2028980/5', '2844355', '2028940/0', '2028940/1', '2028940/2', '2028940/3', '1416840', '1416830', '2028970/0', '2028970/1', '2028970/2', '2028970/3', '1008490/0', '1008490/1', '1008490/2', '1008490/3', '1008490/5', '1163420', '1163400', '2028990', '1577980', '1487660', '2028920', '1518450', '1529520', '2257550/1'],'swi':[3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 8, 9, 10, 10, 10, 10, 11, 11, 11, 11, 11, 12, 13, 14, 15, 16, 17, 18, 18, 18],'word_list':['', '*', '-', '一人で', '一人', 'でも', 'で', 'も', '誰か', '誰', 'か', 'と', '一緒に', '一緒', 'に', 'いる', '必要', 'は', 'ない']},
{'c':'long hard-to-parse hiragana word','line':'ばんそうこう持ってるから','jlines':[[{'ば': [0, 1]}, {'ん': [0, 2, 3]}, {'そうこう': [0, 4, 5]}, {'持ってる': [6]}, {'から': [7]}]], 'slist':['1570430', '2029040', '2139720/0', '2139720/1', '1399160', '1831960', '1315720', '1002980'],'swi':[3, 4, 5, 5, 6, 6, 7, 8],'word_list':['', '*', '-', 'ばんそうこう', 'ば', 'ん', 'そうこう', '持つ', 'から']},
{'c':'i-adjective + ku / nacchatta','line':'頭おかしくなっちゃったの？','jlines':[[{'頭': [0, 1, 2, 3, 4, 5, 6, 7]}, {'おかしく': [8]}, {'なっちゃった': [9, 10, 11]}, {'の': [12, 13]}, {'？': []}]], 'slist':['1582310', '2252700', '2791490', '2791510', '2843246', '2856438', '2856439', '2856440', '1190860', '1375610', '1532910', '1611000', '1469800', '2270030'],'swi':[3, 3, 3, 3, 3, 3, 3, 3, 4, 5, 5, 5, 6, 6],'word_list':['', '*', '-', '頭', 'おかしい', 'なる', 'の']},
{'c':'na no?','line':'一人なの？','jlines':[[{'一人': [0, 1, 2]}, {'な': [3]}, {'の': [3, 4, 5]}, {'？': []}]], 'slist':['1576150/0', '1576150/1', '1576150/2', '2425930', '1469800', '2270030'],'swi':[3, 3, 3, 4, 5, 5],'word_list':['', '*', '-', '一人', 'なの', 'の']},
{'c':'nee.. doushite','line':'ねえどうして','jlines':[[{'ねえ': [0, 1, 2, 3]}, {'どう': [4, 5, 6, 7]}, {'して': [4, 5, 6, 8]}]], 'slist':['1529520/4', '1529520/5', '2029080', '2841117', '1466940/0', '1466940/1', '1466940/2', '1008910', '1157170'],'swi':[3, 3, 4, 4, 5, 5, 5, 6, 7],'word_list':['', '*', '-', 'ない', 'ねえ', 'どうして', 'どう', 'する']},
{'c':'counter','line':'せいぜい一回','jlines':[[{'せいぜい': [0]}, {'一': [1, 2, 3, 4, 5, 6]}, {'回': [1, 7, 8, 9, 10, 11]}]], 'slist':['1596050', '1161310', '1160790', '1160820', '2747940', '2821500', '2843147', '1199330/1', '1199330/2', '1199330/3', '1199330/4', '1199330/5'],'swi':[3, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6],'word_list':['', '*', '-', 'せいぜい', '一回', '一', '回']},
{'c':'general long sentence','line':'皆のお父さんやお母さんには前からお知らせしてあったんだけど再来週授業参観があります','jlines':[[{'皆': [0]}, {'の': [1, 2]}, {'お': [3, 4, 5, 6, 7]}, {'父': [3, 4, 8, 5, 9]}, {'さん': [3, 4, 8, 10, 11, 12]}, {'や': [13, 14, 15]}, {'お': [16, 17, 18, 19, 6, 7]}, {'母': [16, 17, 20, 18, 19, 21]}, {'さん': [16, 17, 20, 10, 11, 12]}, {'に': [22, 23]}, {'は': [22, 24]}, {'前': [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37]}, {'から': [38]}, {'お': [39, 6, 7]}, {'知らせ': [39, 40]}, {'して': [41]}, {'あった': [42]}, {'ん': [43, 44, 45]}, {'だけど': [46, 43]}, {'再来': [47]}, {'週': [47, 48]}, {'授業': [49, 50]}, {'参観': [49, 51]}, {'が': [52, 53]}, {'あります': [42]}]], 'slist':['1202150', '1469800', '2270030', '1002590/0', '1002590/1', '2709500', '2268350', '2826528', '1610490', '1497610', '1005340', '2085690', '2106250/2', '2028960/0', '2028960/1', '2028960/7', '1002650/0', '1002650/1', '1002370', '2595640', '1609470', '1514990', '2215430', '2028990', '2028920', '1387210', '1392570/0', '1392570/1', '1392570/3', '1392580/0', '1392580/1', '1392580/2', '1392580/3', '1392580/4', '1392580/5', '1392580/7', '1392580/8', '1392580/9', '1002980', '1002420', '1420400', '1157170', '1296400', '2849387', '2139720/3', '2139720/4', '1007370', '1293650', '1333450', '2222720', '1330290', '1302180', '2028930/0', '2028930/1'],'swi':[3, 4, 4, 5, 5, 6, 7, 7, 8, 9, 10, 10, 10, 11, 11, 11, 12, 12, 13, 13, 14, 15, 16, 17, 18, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 20, 21, 22, 23, 24, 25, 26, 26, 27, 28, 29, 30, 31, 32, 33, 33],'word_list':['', '*', '-', '皆', 'の', 'お父さん', 'お父', 'お', '父さん', '父', 'さん', 'や', 'お母さん', 'お母', '母さん', '母', 'には', 'に', 'は', '前', 'から', 'お知らせ', '知らせ', 'する', 'ある', 'んだ', 'ん', 'だけど', '再来週', '週', '授業参観', '授業', '参観', 'が']},

]

def do_tests():
    
    for test in tests:
        c = test['c']
        line = test['line']
        if 'slist' in test:
            slist = test['slist']
        else:
            slist = []
        kanji_count = dict()
        lemmas = dict()
        word_list = ['','*','-'] 
        word_seq = [0,0,0]
        word_count = [0,0,0]
        word_count_per_class = [0 for x in range(len(unidic_item_classes))] 
        sense_list = []
        sense_word_index = []
        sense_class_list = []

        print("Testing:",line)
        kc, ud_words, ud_word_ortho, ud_word_class = \
            parse_line_with_unidic(line,kanji_count, lemmas)
        
        ud_words, ud_word_ortho, ud_word_class, ud_word_flags = \
            post_process_unidic_particles(ud_words, ud_word_ortho, ud_word_class)

        sense_ref = parse_with_jmdict(
            ud_words, ud_word_ortho, ud_word_class, ud_word_flags,
            sense_list, sense_word_index, word_list, word_count, word_seq,
            word_count_per_class, sense_class_list,
        )
        jlines = reassemble_block([line], ud_words, sense_ref)

        ud_word_class_txt = [(w,unidic_item_classes[cl]) for w,cl in zip(ud_words, ud_word_class)]
        unique_jmdict_word_class_list_txt = []
        """
        for w,cl in zip(word_list, word_class_list):
            if len(cl)>0:
                unique_jmdict_word_class_list_txt.append((w,jmdict_parts_of_speech_list[cl[0]]))
            else:
                unique_jmdict_word_class_list_txt.append((w,''))
        """

        print("\nAfter jmdict scanning:")
        print_scanning_results(jlines, sense_list, sense_word_index, word_list, ud_word_class)


        jlines_str = str(jlines)
        print("{'c':'%s','line':'%s','jlines':%s, 'slist':%s,'swi':%s,'word_list':%s}" % (c,line,str(jlines),str(sense_list),str(sense_word_index),str(word_list)))



        if jlines != test['jlines']:
            for i, (a,b) in enumerate(zip(jlines[0], test['jlines'][0])):
                (w1, refs1) =list(a.items())[0]
                (w2,refs2) = list(b.items())[0]
                #seqs1 = [sense_list[idx] for idx in refs1]
                w_idx1 = [sense_word_index[idx] for idx in refs1]
                words1 = [word_list[idx] for idx in w_idx1]

                words2 = []

                try:
                    swi = test['swi']
                    wl = test['word_list']
                    w_idx2 = [swi[idx] for idx in refs2]
                    words2 = [wl[idx] for idx in w_idx2]
                except:
                    pass

                if words1 != words2:
                    print("%d : %s [%s] != %s [%s]" % (i,w1,words1,w2,words2))
            #raise Exception("Error in references!")
        if word_list != test['word_list']:
            raise Exception("Error in word list!")
        if 'slist' not in test or sense_list != test['slist']:

            a_ref_set = set(sense_list)
            b_ref_set = set(slist)
            extra_in_a = a_ref_set - b_ref_set
            missing_in_a = b_ref_set - a_ref_set

            if len(extra_in_a)>0:
                print("Extra:")
                for seq_sense in extra_in_a:
                    s = seq_sense.split('/')
                    seq = int(s[0])
                    if len(s)>1:
                        sense = int(s[1])
                        meanings = jmdict_meaning_per_sense[seq][sense]
                    else:
                        sense = '*'
                        meanings = jmdict_meaning_per_sense[seq][0] # print just the first
                    print("\t[%d] %s : %s" % (seq, sense, meanings))
                    #cl_list = jmdict_pos[seq]
                    #for cl in cl_list:
                    #    print("\t\t%s" % jmdict_parts_of_speech_list[cl])

            if len(missing_in_a)>0:
                print("Missing:")
                for seq in missing_in_a:
                    s = seq_sense.split('/')
                    seq = s[0]
                    if len(s)>1:
                        sense = s[1]
                        meanings = jmdict_meaning_per_sense[seq][sense]
                    else:
                        sense = '*'
                        meanings = jmdict_meaning_per_sense[seq][0] # print just the first
                    print("\t[%d] %s : %s" % (seq, meanings))

                print("%d : %s != %s" % (i,a,b))
            raise Exception("Error in sense list!")
    print("Tests ok")


def test_jmdict():
    #line = "皆のお父さんやお母さんには前からお知らせしてあったんだけど再来週授業参観があります"
    #line = '嫌なら早めにやっつけなきゃ'
    #line = '授業中どうぞよろしくお願いします。!！test思い出す見かける見切るひっ掛けるひっかける'
    line = 'まあ隣の人があやしかったよ！！'
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
    line ='．．．．．別にいいでしょ一人でも誰かと一緒にいる必要はない'
    #line =   '．．．．．．あんた嫌われてんでしょ？'
    #line = 'ねえどうして腕を切っていたの？'
    """
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
    """
    
    #line = "人生とは給食みたいなものだもの"

    #line = '３５歳の公務員じゃ団地に入れただけでも幸せってものでしょう'
    line = '子どもの癖に偉そうな喋り方'

    line = 'ねえどうして'
    #line = 'どうぞよろしくお願いします'
    line = '古代エジフトの全にはアンチモンが含まれていて、もっと赤っぽかったんです'
    line = '判定できなかった田'
    line = 'ＩＲＡの犯行の可能性は低いですね'
    line = 'オックスフォードの全男子学生憧れの日本のマドンナを射止めたって'


    c = 'honorific + suffix'
    line = '議師料'
    line = 'お父さん'
    line = '喰えるな'
    line = '自分よりスリムなやしの木や"'

    #line = 'まあ隣の人があやしかったよ！！'

    line = 'でもやっぱり'
    line = 'もったいないわよ'
    line = 'どうだい元気にしてた'

    kanji_count = dict()
    lemmas = dict()
    word_count_per_class = [0 for x in range(len(unidic_item_classes))] 

    jmdict_word_list = ['','*','-'] 
    jmdict_word_senses = [None,None,None]
    jmdict_word_count = [0,0,0]
    jmdict_sense_list = []
    jmdict_sense_word_index = []
    jmdict_sense_class_list = []

    kc, ud_words, ud_word_ortho, ud_word_class = parse_line_with_unidic(line,kanji_count, lemmas)

    ud_words, ud_word_ortho, ud_word_class, ud_word_flags = \
        post_process_unidic_particles(ud_words, ud_word_ortho, ud_word_class)

    sense_ref = parse_with_jmdict(
        ud_words, ud_word_ortho, ud_word_class, ud_word_flags,
        jmdict_sense_list, jmdict_sense_word_index,
        jmdict_word_list, jmdict_word_count, jmdict_word_senses,
        word_count_per_class, jmdict_sense_class_list,
    )
    jlines = reassemble_block([line], ud_words, sense_ref)

    ud_word_class_txt = [(w,unidic_item_classes[cl]) for w,cl in zip(ud_words, ud_word_class)]
    unique_jmdict_word_class_list_txt = []

    jlines_str = str(jlines)
    print("{'c':'%s','line':'%s','jlines':%s, 'slist':%s, 'word_list':%s}" % (c, line,str(jlines),str(jmdict_sense_list),str(jmdict_word_list)))
          
    pass

load_jmdict(True)
load_conjugations()
set_verbose_level(2)

test_jmdict()
do_tests()

