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

    print(sys.argv)
    if args['text'] is None:
        jslines = '["ようこそおきな"]' #'["ねえどうして"]'
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
        lines = ['聞いたん', 'じゃなくて、', 'オレが新一', 'だって！！', '・へんな薬', '飲まされて', '小さくされ', 'ちまったん', 'だよ！！']
        lines = ['くだらないね', 'しゃべってて', 'やだな。']
        lines = ['花火デートできたら']
        lines = ['壊れててない']
        lines = ['別にのぞいたりもんだり見せたりするつもりは．']
        lines = ['あ～～あ', 'なんてこった']
        lines = ['さまざみやげ', 'ヒミの王子は相を', 'お持ち下さいっとで、', '姫様は言い', 'ました。', '．．．ギョクシュバコ', '２何や？こうま', 'んか？']
        lines = ['そういうワケで', 'とりあえず', '二浪してます']
        lines = ['つきあって','みたらって']
        lines = ["追い出そーと", "しとるんやろ"]
        lines = ["見張ってんのよ"]
        lines = ['つきあって','みたらって']
        lines = ['知らない']
        lines = ["尊敬しちゃいます"]
        lines = ["バッチつけてんだぜ"]
        lines = ["食えなくなった"]
        lines = ['駄目だといっ', 'たら駄目なの']
        lines = ["特定したくなかった", "からだ！！"]
        lines = ["迷っちゃ", "おっか？"]
        lines = ["主人のお友達で", "らした．．．"]
        lines =  ["エッちゃん！","何してんの","先生が起きて","いいっておっ","しゃったの"]
        lines = ["．．．パッとした"]
        lines = ["まだまだ", "帰れそうに", "ない。"]
        lines = ["頼りないって", "思われてる", "ワケじゃ", "ないのか"]
        lines = ["そうじゃないのは"]
        lines = ["妹を", "可哀相", "あつかい", "しないって", "決めたんだ。"]
        lines = ["ちょっと", "ほっといてみ。"]
        lines = ["ほら", "手を出す"]
        lines = ["白丸先輩の", "ゲームセンターの人が", "エアコンを直しに", "きてくれましたが、", "丸ごと交換が必要とかで", "直りませんでした"]
        lines = ["あいつー", "【秘密を知ってる", "クラスメイトーくんを", "無視しやがってー"]
        lines = ["お願いしまーす"]
        lines = ["耳にしたろう．．．"]
        lines = ["あたしもトトロの", "最初から最後まで", "セリフ言える特技", "披露したかった。"]
        lines = ["なんで", "こんなに", "ヒマ", "なのよ。"]
        lines = ["きくのまずかったかな"]
        lines = ["はるかさん", "こいつどーにか", "してくださいよ"]
        lines = ["テルテル", "坊主．．．．．．"]
        lines = ["詳しい話は", "そㇱときしな．．．"]
        lines = ['まったく', '．．．', '軽率', 'な', 'ヤツラ', 'にゃ', '頭', 'が', '下', 'が', 'る', 'ぜ']
        lines = ["なにそれ", "知ってるしー。"]
        lines = ["言いづらくてさ。"]
        lines = ["おい", "しいー"]
        lines = ['負傷者は', 'チェックして', 'へリへ運べ']
        lines = ["そんな事を", "言っとんじゃない"]
        lines = ['あれがなくっちゃ', 'パーティも盛り', '上がんねェもㇱな']
        lines = ["特定したくなかった", "からだ！！"]
        lines = [ "メールはしといた。"]
        lines = ["聞こえませー", "ーん！！"]
        lines = ["おい", "しいー"]
        lines = ["つめた～い", "かき氷は", "至福だぞ。"]
        lines = ["今しとる"]
        lines = ["こーんなに", "かれんな", "ヨーコさんが"]
        lines = ['そんな事', '言ってる場合は', 'じゃねェぜ']
        lines = ["ココラー", "出てこ〜い"]
        lines = ["水路に", "おっこっちゃっ", "てそれっきり"]
        lines = ["底なし池に", "沈んで", "いったんだけど"]
        lines = ['捜す手間が', 'はぶけたぜ']
        lines = ['お母さんも', 'そう言って', 'たわ。']
        lines = ['お願いします、', 'そしたら次回も', '出席に', 'しときます']
        lines = ['私は由緒正しき家柄']
        lines = ['あ～～あ', 'なんてこった']
        lines = ['部下達は、', '近くの村をくまなく', '回っている']
        lines = ['やめろ！！', 'ここに', '置いていけ']
        lines = ['何よりも疑いのかかっている者からの案を採る']
        lines = ["そんなの", "ほっとき", "なさい！！"]
        lines = ['わ．．．わかったよ、', 'あんたが嫌なら', 'ヤクもやらないよ。']
        lines = ["上マエをはねていた。"]
        lines = ["こいつは二百万倍は", "ある。"]
        lines = ["私に、新しい女性ができたって悪かないだろ。"]
        lines = ['昨〜楽しんでくださ', 'かなわぬ夢は']
        lines = ["そうよ新ちゃん、"]
        lines = ["意味不", "だけど"]
        lines = ['くそー', 'カンカラは', 'どこだ．．．']
        lines = ["私に、", "新しい女性が", "できたって", "悪かないだろ。"]
        lines = ['◆高所注意', '転落の恐れあり', '特に旅館の', '屋根など注意', '鳥夫の責な', 'にも注意すべ']
    else:
        lines = json.loads(args['text'])

    open_log_file("parserlog.txt")
    set_verbose_level(args['verbose_level'])
    parse(lines)
    close_log_file()
