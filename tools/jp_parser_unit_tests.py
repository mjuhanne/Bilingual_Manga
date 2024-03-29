import fugashi
from helper import *
from jp_parser import *
from jp_parser_tool import print_scanning_results
from parser_logging import *

#その子を寂しがらせることもない
# 誇り高い人
# きっとなっちゃんがいつかその子達に
# ゴール。２人ではじめた旅の  de-hajimeru (ei dehajimeru)
# お風呂はいってこよ！
# なんであれほどの人が  nandeare != are hodo

# ありがとー
# 噂されてる   sarete + (i)ru
# 上靴捨ててんの   sama
# トイレのゴミ箱に捨ててあんじゃん  arun jan

# おっしえなーい
# はっずかしい

# 本に興味がないかって   hon ni

# もうよさないか。姉さん！おやじが死んだ夜に金の話なんか．   yosanai -> yosu
# 短いスカートはおなかが冷えるからよしなさいっていったでしょ？ yoshinasai -> yosu
# 服かわかさなきゃ   かわかす / 乾かす
# うふふなるさんとっても素敵ですよ   なるさん
# 絶対！！こわさせないわよ   こわす
# 穴をよさげ。
# よしなさいよヨシツネ
# まぁまぁ

# ありゃ？珍しくさっぱりキレーに片付いとるやん  きれー　-> kirei

# たとえ荒らせたとしてもサイフを探すなんて不可能だ！！   tatoe
# 犯人が逃げる時に拭きとったって事も   hikitotta + tte

# ６名ってあるけど    名って (?)

# いま寝つけたら、"  - tara
# 混ざれなくってさ
# 家中を動きまわれた人物  ugokimaware-ta
# 使いこなせる  tsukai-konaseru

# 俺なんかが首つっ込んでいい方向にいくのかなって  tsukkonde
# 死亡推定時刻がわりだせず   waridase-zu
# 探偵さんはうまくだませたかもしれないけど、写真は、だませないよ   damase-ta, damase-nai
# そのペンが書けないの知ってたんだ！  shitte-ta-n
# よーし出発点はここだ！！   y--shi!
# めんどくさー
# Ａ８０３号室に入院しています   goushitsu
# 口裏合わせて 
# また？
# ストーカーなん？   (nan->nano)
# 鐵穴にガムをおし込み自動ロックを不能にした  o-shikomu
# 怨念ここに晴らせり    harase-ri
# 運悪くテープが切れてもはがせます　 hagase-masu
# いい逃れできねーよな？  deki-nee
# しかし犯人が逃げる時に拭きとったって事も  nukitot-tatte
# 悲しんでる
# ヤレヤレ仲のいいこと
# こらホントにカケオチかーあの二人？ kakeochi
# 何もしゃべれなかったもんな  shaberenakatta
# 明日から楽しめそーやで   sou - ya de
# 女だからとて客赦せぬぞ  yuruse-nu
# だから用ないんなら  nara != da
# でも浦島君ゴメンナサイ．  gomen nasai != nasaru
# こんな武器でウチは倒せまへんで  taosema-hen-de / masen
# 何かどーしても言いだせなくて
# あうーもー喰えん  mou  / kue-nai
# どこか
# カケオチっていう病気で死んだのか？ kake-ochi
# ちょっとだけ世の中に知らしめてやれりゃよかったんだ  shirashime-te
# そう簡単に償えるもんじゃないか  mon
# オシメしてくればあ！？  oshime = diaper
# 歌舞伎町なんて行ったら、生きて帰れんぞ普通。  ikitekaere-n  (n=nai)
# とり逃がしましたじゃすまねえぞ！！  suma-nee
# おかげで死にたくても死ねねえや。 shine-nee
# 帰れなかったら．
# なんかウチに用スか？  you yksinään
# そんなわけのわがんねえクスリ打たれたら、どうにかなっちまうぜ！！  dou-ni-ka (kanau)
# ただこの中華街は  tada
# それでもやっぱりイジメられてるような   soredemo / ijimerareteru
# そろそろ歩けそうだ  aruke-sou
# この小泉が売りこんだげる！！  urikomu - ageru
# 投査本部の情報を得られた   投げる ei saisi olla yksi permutaatio
# そんな大声出しちゃん  
# ところでキツネちゃんなるちゃんはどこだい？   doko dai
# ねーちゃん
# てことはイモ喰い放題の上イタズラし放題おかしもらい放題でもー笑いが止まんねーゾ   kui-houdai / okashi / morai-houdai
# 立ち入り禁止区域になってたのにまったく．  natte-ta

# だって面白くて目が離せなかったもん！  me ga hanasenai

# 大声だすときもちいいよ！ ookoedasu
# 毎日夜空を見つづけた．  mitsutsuketa (見続ける)
# ココラー出てこ〜い   koraaa.. dete-koi
# 殺人犯になりたくないんだ   naritakunai
# あっいたいた！ ita + ita
# ぜひ行きたいと思ってたのだ  omotte-ta
# おしりいたい～  oshiri / itai
# ー頭がいたくない。   atama ga itai
# 落ち着けとくから   - ochitsukete - oku
# なんかしなよー  nanika shi-na yo
# 母親なめんな  nameru + na

#  待っていよう   -te verbi + iyou -> force only ortho scan
# 目一杯カッコよくきめた  kakko yoku -> kakkoo ii
# 曲は言いづらそうにしてたけど   tsura + sou-ni
# 美術部じゃそんなアダ名がついてたんだな．   adana
# 犯人にされちゃたまんないわよ   tamannai (tama-ra-nai)
# 娘が来てたとしたら   to-shitara
# 忙しそーにしてたもの  isogashi-sou
# 本当はんなトコ行きたかねーけど  iki-taka-nee (ikitakunai)
# あの時のワシはどうかしてたんじゃ  doukashite
# バカも休み休みいいたまえ！！  ii-tamae
# もうみんな帰り仕たくすんどるでー  kaeri-shitaku-sunderu (going home preparations are ready)
# ゃゃやややっぱり私達落ちてたんーっっだわー ochite-itan
# ン違いしてたのー！ kanchigau
# ビビって声も出ないとはな  bibiru
# ごめんなさぁい  nasaai
# あこの子かいちょっとワケありでねーははは  wakeari
# このへコミは！？   hekomi
# 一言も言ってませんよね  ittemasen
#  しやがって。へラへラ  herahera
# でなきゃ、おめーみてーな  denakya
#  彼女ナシ   (nashi, if after noun)
# あれ？もう帰っちゃうんスカ？  desu-ka
# 世界を破滅させようとしている連中だ   you to shite-iru (pin down to-shite to 2136890 (to suru) instead of to-shite )
# 遊園地に連れてってくれるって！！  tsurete -tte
# こんなガキにつけられやがって． tsukerareyagatte
# でなきゃ、おめーみてーな  mitaina
# この写真が何だというんだね？  nandato vs nanda to iu
# そ、そうかもね．  souka / sou kamone
# 二度と日外せんという約束  
# せんせいおげんきですか
#  どっかでドブにでもはまってんでしょ dokoka de
# どうかしたのかい？なるちゃん
# あれ彼氏！？こっり合ってねーよなもったいなーーっメガネー！ mottainai
# 呼んでへん呼んでへん  yonde-hen/nai
# カナちゃん．．．本気でみんなとケンカしたかった訳じゃないんでしょ  honki de != honki da
# それを断ち切らねば本当の生は得られん  kiraneba / eraren
# どう書いたのか見てなかったのか？  nakatta
# 合宿行けることになりそうで  nari-sou
# 自分の心の中に留めておいてくれそうだと思った   prioritize oku after te-verb
# 最近心が軽い気がする  saikin
# 彼女は何かあったのにそれをひた隠しにしていた   block ni-shite
# あんなに必要とされてるって知らなかったから   sareteru
# このままだと私達遊びでキスくらいしちゃうんじゃないかしらってドキドキしてる  block kurai-suru
# ほら、なかなか通じなかったとか．．  tooji-nakatta
# いっつも思うけど  itsumo
# はい今日は抜きうちテストですよー   nukiuchi-testo (pop quiz), not in JMDict?
# それにたとえ通れたとしても、１０秒ぐらいしかがわんねーよ wannee(wakaranai
# しまった見つかった！  shimatta
# オレ達ウソついてねーぞ！！  uso wo tsuku
#  バーロテメーを数えてねーんだよ！ baaro / temee   (match if katakana word?)
# だってガンダんち金持ちじゃないの  ganda nchi (no uchi)
# ガンタのせいって、こと？  ganta-no-sei     (block tano)  prioritize せい after の?
# バイバイ  prioritize kana-match (バイバイ instead of ばいばい) even though the latter is more common
# オジちゃん、バイバーイ！  baibai
# なーんてね！！何ムシのいいこと考えてんのかしら私  sama
# 待ってますよーー  matte-masu
# 金とオモチャや、花が届き始めたのは二年前からだから、  omocha + ya != omocha-ya.  Do not mix hiragana/katakana?
# ゴメンなさいまちがえましたーーーッ  machigaemashita
# そーゆー言い方やめてよ。 sou yuu

# こいつといっしょじゃねーと抜けたくねえってな  -takunee
# あんたの勝手なカン違いじゃない  kanchigai . Try converting to hiragana
# きょーときょーと  kyoto kyoto
# バっカみたい  baka mitai
# スマン４人分の旅費で消えた  4-nin  (to numeric and noun
# サラちゃんのいやがらせぐらいでやめてたまるか   WTF..!
# お前のイタズラに毎日付き合わされるから大変なんだろー！？ itasura != itasura-ni   tsukiawasareru
# むつみさん疲れて寝ちゃったねーしょうがないな．  block naishou somehow
# うふふ何だかゴキゲンですねなるさん  nandaka
#  そうですねパーーっと遊びますか！  paaatto. Only 1 ー !
# 私がチェックインしとくからね  chekku in suru vs. in suru
# はーいいってらっしゃーい
# 茶あるからとりにきて。   toru != tori (toru is detected though)
# ま、まてカニ  (matsu is right but now it's referring to noun, not verb)

# 今日は屋根から落ちそうになりました。私って、おっちゃん
# 何度やっても吐きそうになったって．
# 武器も持たずいかにもリラックスしていそうな場所というと．shite-i-sou-na
# しばらく帰れそうにねーな．  sou-ni-nai
# すぐにでも自決しそうな感じだな  shi-sou-na
# もうちょっとで完成しそうなんです．shi-sou-da
# お年玉あげるから帰りな。kaeri-na
# あったまきちゃう！ maki-chau
# 楽しみましょっか♡  -shou

# 夏江さんに近づき、旗本家に入り込み、 do not use noun if , is after verb
# 邪魔だ、どいてろ！！  doite (v5k)
# どこふいてんのよ！！  fuku (wipe/blow) vs fuku (cloth)
# 反陽子はどん世界はほろんといてー   horobu (to be ruined)
# 以前から足を洗いたがっていました．．  tagatte

# カゼひいたそやなーけーたろ kaze hiita so-ya-naa.
#  あれっきり連絡もしてこんし  shite-konai shi
# 何やってんのスウちゃん！！はなしなさ  hanashi-nasa(i)
# あっちでふきましょ！  -masho
# うみんな帰り仕たくすんどるでー
# わっ俺を置いてかないでよー！？  oite-ikanaide yo
# でなきゃ、おめーみてーな
# なかなかうまくいかへんかー  ika-hen-ka
# チビのくせに渡さへんで watasa-hen-

# そのことごとくを あの女は ふりおった！！  onna ha furiotta vs onna hafuri-otta (re-unidic if needed )
# ["うーん","どうかな？"]   sama

# 可愛く思えてませんよ oboete-imasen
# 見た目で判断しちゃったね mita-me
# なんだかねー
# 時間がねー
# うへー高っけーなー．
# 本当だったみてーだな！
# あたりめーだ！
# 許してやろーと思ったが  yarou
# うーさむっ！ひえるしコタツでやろーかな  samui / yarou
# 遊んじゃってるよね〜〜
# 横でおとなしくしとるからえーやろーー？ ii darou
# 何そこうっとりしてんのよっ！！  shite-irun
# まいったな　　　verb->interjection?
# あんたは食料でも探してきなさーーい！！  sagashite-iki-nasai
# 何か高そ〜な店
# しらない(verb/adjective) not allowed for しらない(interjection (kandoushi))
# でも、起こさんかったら起こさんかったで、怒るんやろなあいつ  okosan-kattara
# 話したがらなかったから． tagara-nakattara
# 行かなくちゃって必死に  ikanakuchatte
# そこ置いといてー 
# 当の 町田くんは  tou-no
# ほっとけば良かった   hotte(horu)-okeba
# 欲さ禁じられています   欲 (adjective) as noun

#  誰か入ってなかってこなかった？   is this even possible grammar? (nakatte-)

# お金貯めてんの  tameten = tamete-irun
# おめーら気合い入ってんのか。 sama

# 持ってっとく  motte itte oku?

tests = [
{'c':'honorific in front of adjective (medetai)','line':'おめでとう','jlines':[[{'お': [4, 2, 5, 1, 0]}, {'めでとう': [4, 2, 5, 3]}]], 'wilist':['2268350:お', '2826528:お', '1647360:おめでたい', '1608630:めでたい', '1270700:おめでとう', '2077340:おめでとう']},

{'c':'honorific + suffix','line':'お父さん','jlines':[[{'お': [1, 2, 0, 5, 6]}, {'父': [1, 2, 4, 0, 3]}, {'さん': [1, 2, 4, 7, 8, 9]}]], 'slist':['2709500', '1002590/0', '1002590/1', '1497610', '1610490', '2268350', '2826528', '1005340', '2085690', '2106250/2'], 'swi':[3, 4, 4, 5, 6, 7, 7, 8, 8, 8], 'word_list':['', '*', '-', 'お父', 'お父さん', '父', '父さん', 'お', 'さん']},

{'c':'prefix/suffix must be detected even when not found in the dictionary together with the stem word','line':'議師料','jlines':[[{'議': [0]}, {'師': [1, 2]}, {'料': [3]}]], 'slist':['2273760', '1956330/1', '1956330/2', '1554270'], 'swi':[3, 4, 4, 5], 'word_list':['', '*', '-', '議', '師', '料']},

{'c':'long phrase','line':'よろしくお願いします','jlines':[[{'よろしく': [0, 1, 2, 3]}, {'お': [0, 4, 5, 6, 7]}, {'願い': [0, 4, 5, 8]}, {'します': [0, 4, 9]}]], 'slist':['2133750', '1224890', '2835139', '2846370', '1001720', '2036870/0', '2268350', '2826528', '1217950', '1157170'],'swi':[3, 4, 4, 4, 5, 6, 7, 7, 8, 9],'word_list':['', '*', '-', 'よろしくお願いします', 'よろしく', 'お願いします', 'お願い', 'お', '願う', 'する']},
{'c':'past tense','line':'あやしかった','jlines':[[{'あやしかった': [0, 1]}]], 'wilist':['1586700:あやしい', '2843261:あやしい']},
{'c':'streched sentence','line':'だーからあるいていくんだね～','jlines':[[{'だー': [0]}, {'から': [1]}, {'あるいて': [2]}, {'いく': [4, 3, 5, 6]}, {'ん': [9, 7, 8]}, {'だ': [9, 0]}, {'ね': [10, 11]}, {'～': []}]], 'wilist':['2089020:だ', '1002980:から', '1514320:あるく', '1157500:いく', '1578850:いく', '2783550:いく', '2856718:いく', '2139720/3:ん', '2139720/4:ん', '2849387:んだ', '2029080:ね', '2841117/0:ね']},
{'c':'mitai+na / mono + da mono','line':'給食みたいなものだもの','jlines':[[{'給食': [0]}, {'みたい': [2, 1]}, {'な': [2]}, {'もの': [4, 3]}, {'だもの': [6, 5]}]], 'wilist':['1230250:給食', '2016410:みたい', '2839776:みたいな', '1322990:もの', '1502390:もの', '2089020:だ', '1007470:だもの']},
{'c':'conditional','line':'そういえば','jlines':[[{'そう': [0, 1]}, {'いえば': [0, 2, 3]}]], 'slist':['1982210', '2137720/0', '1254600', '1587040'],'swi':[3, 4, 5, 5],'word_list':['', '*', '-', 'そういえば', 'そう', 'いう']},
{'c':'betsu+ni / desho','line':'別にいいでしょ','jlines':[[{'別': [2, 0, 1]}, {'に': [2]}, {'いい': [3]}, {'でしょ': [5, 4]}]], 'wilist':['1509430:別', '2259830:別', '1509480:別に', '2820690:いい', '1628500:です', '1008420:でしょ']},

{'c':'hitori demo/ dare+ka / isshou+ni','line':'一人でも誰かと一緒にいる必要はない','jlines':[[{'一人': [0, 1, 2, 3]}, {'で': [0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]}, {'も': [4, 5, 6, 7, 14, 15, 16, 17]}, {'誰': [18, 19]}, {'か': [18, 20, 21, 22, 23]}, {'と': [24, 25, 26, 27, 28]}, {'一緒': [29, 30]}, {'に': [29, 31]}, {'いる': [32]}, {'必要': [33]}, {'は': [34]}, {'ない': [35, 36, 37]}]], 'slist':['1163700', '1576150/0', '1576150/1', '1576150/2', '1008460/1', '1008460/2', '1008460/3', '1008460/4', '2028980/0', '2028980/1', '2028980/2', '2028980/3', '2028980/5', '2844355', '2028940/0', '2028940/1', '2028940/2', '2028940/3', '1416840', '1416830', '2028970/0', '2028970/1', '2028970/2', '2028970/3', '1008490/0', '1008490/1', '1008490/2', '1008490/3', '1008490/5', '1163420', '1163400', '2028990', '1577980', '1487660', '2028920', '1518450', '1529520', '2257550/1'],'swi':[3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 8, 9, 10, 10, 10, 10, 11, 11, 11, 11, 11, 12, 13, 14, 15, 16, 17, 18, 18, 18],'word_list':['', '*', '-', '一人で', '一人', 'でも', 'で', 'も', '誰か', '誰', 'か', 'と', '一緒に', '一緒', 'に', 'いる', '必要', 'は', 'ない']},
{'c':'long hard-to-parse hiragana word','line':'ばんそうこう持ってるから','jlines':[[{'ば': [0, 1]}, {'ん': [0, 2, 3]}, {'そうこう': [0, 4, 5]}, {'持ってる': [6]}, {'から': [7]}]], 'slist':['1570430', '2029040', '2139720/0', '2139720/1', '1399160', '1831960', '1315720', '1002980'],'swi':[3, 4, 5, 5, 6, 6, 7, 8],'word_list':['', '*', '-', 'ばんそうこう', 'ば', 'ん', 'そうこう', '持つ', 'から']},
{'c':'i-adjective + ku / nacchatta','line':'頭おかしくなっちゃったの？','jlines':[[{'頭': [0, 1, 2, 3, 4, 5, 6, 7]}, {'おかしく': [8]}, {'なっちゃった': [9]}, {'の': [10, 11]}, {'？': []}]], 'wilist':['1582310:頭', '2252700:頭', '2791490:頭', '2791510:頭', '2843246:頭', '2856438:頭', '2856439:頭', '2856440:頭', '1190860:おかしい', '1375610:なる', '1469800:の', '2270030:の']},
{'c':'na no?','line':'一人なの？','jlines':[[{'一人': [0, 1, 2]}, {'な': [3]}, {'の': [3, 4, 5]}, {'？': []}]], 'slist':['1576150/0', '1576150/1', '1576150/2', '2425930', '1469800', '2270030'],'swi':[3, 3, 3, 4, 5, 5],'word_list':['', '*', '-', '一人', 'なの', 'の']},
{'c':'nee.. doushite','line':'ねえどうして','jlines':[[{'ねえ': [2, 0, 1, 3]}, {'どう': [6, 7, 8, 4]}, {'して': [6, 7, 8, 5]}]], 'slist':['1529520/4', '1529520/5', '2029080', '2841117', '1008910', '1157170', '1466940/0', '1466940/1', '1466940/2'], 'swi':[0, 0, 1, 1, 2, 3, 4, 4, 4], 'word_list':['ない', 'ねえ', 'どう', 'する', 'どうして']},
{'c':'counter','line':'せいぜい一回','jlines':[[{'せいぜい': [0]}, {'一': [1, 2, 3, 4, 5, 6]}, {'回': [1, 7, 8, 9, 10, 11]}]], 'slist':['1596050', '1161310', '1160790', '1160820', '2747940', '2821500', '2843147', '1199330/1', '1199330/2', '1199330/3', '1199330/4', '1199330/5'],'swi':[3, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6],'word_list':['', '*', '-', 'せいぜい', '一回', '一', '回']},

{'c':'iya nara / hayame+ni / tsukenakya','line':'嫌なら早めにやっつけなきゃ','jlines':[[{'嫌': [0, 1]}, {'なら': [4, 5]}, {'早め': [3, 2]}, {'に': [3]}, {'やっつけなきゃ': [6]}]], 'slist':['1587610/0', '1587610/1', '2078850', '1400350', '1009470/0', '1009470/1', '1612950'], 'swi':[3, 3, 4, 5, 6, 6, 7], 'word_list':['', '*', '-', '嫌', '早め', '早めに', 'なら', 'やっつける']},

{'c':'general long sentence','line':'皆のお父さんやお母さんには前からお知らせしてあったんだけど再来週授業参観があります','jlines':[[{'皆': [0]}, {'の': [25, 26]}, {'お': [2, 3, 1, 28, 27]}, {'父': [2, 3, 5, 1, 4]}, {'さん': [2, 3, 5, 29, 30, 31]}, {'や': [32, 33, 34]}, {'お': [8, 9, 6, 7, 28, 27]}, {'母': [8, 9, 11, 6, 7, 10]}, {'さん': [8, 9, 11, 29, 30, 31]}, {'に': [36, 35]}, {'は': [36, 37]}, {'前': [12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 13]}, {'から': [38]}, {'お': [23, 28, 27]}, {'知らせ': [23, 24]}, {'して': [39]}, {'あった': [40]}, {'ん': [43, 41, 42]}, {'だけど': [49, 43]}, {'再来': [44]}, {'週': [44, 45]}, {'授業': [47, 46]}, {'参観': [47, 48]}, {'が': [50, 51]}, {'あります': [40]}]], 'wilist':['1202150:皆', '2709500:お父', '1002590/0:お父さん', '1002590/1:お父さん', '1497610:父', '1610490:父さん', '1002370:お母', '2595640:お母', '1002650/0:お母さん', '1002650/1:お母さん', '1514990:母', '1609470:母さん', '1387210:前', '1392570:前', '1392580/0:前', '1392580/1:前', '1392580/2:前', '1392580/3:前', '1392580/4:前', '1392580/5:前', '1392580/7:前', '1392580/8:前', '1392580/9:前', '1002420:お知らせ', '1420400:知らせ', '1469800:の', '2270030:の', '2268350:お', '2826528:お', '1005340:さん', '2085690:さん', '2106250/2:さん', '2028960/0:や', '2028960/1:や', '2028960/7:や', '2028990:に', '2215430:には', '2028920:は', '1002980:から', '1157170:する', '1296400:ある', '2139720/3:ん', '2139720/4:ん', '2849387:んだ', '1293650:再来週', '1333450:週', '1330290:授業', '2222720:授業参観', '1302180:参観', '1007370:だけど', '2028930/0:が', '2028930/1:が']},

]

def do_tests():
    
    for test in tests:
        c = test['c']
        line = test['line']
        kanji_count = dict()

        results = init_scan_results()

        print("Testing:",line)
        kc, unidic_items = parse_line_with_unidic(line,kanji_count)
        
        unidic_items = post_process_unidic_particles(unidic_items)

        sense_ref = parse_with_jmdict(
            unidic_items, results
        )
        jlines = reassemble_block([line], unidic_items, results['item_word_id_refs'])

        print("\nAfter jmdict scanning:")
        print_scanning_results(jlines, results, unidic_items)

        print("{'c':'%s','line':'%s','jlines':%s, 'wilist':%s}" % (c, line,str(jlines),str(results['word_id_list'])))

        for i, (a,b) in enumerate(zip(jlines[0], test['jlines'][0])):
            (w1, refs1) =list(a.items())[0]
            (w2,refs2) = list(b.items())[0]
            w_ids_1 = [results['word_id_list'][idx] for idx in refs1]
            words1 = [w_id.split(':')[1] for w_id in w_ids_1]

            words2 = []

            if 'swi' in test:
                swi = test['swi']
                wl = test['word_list']

                w_idx2 = [swi[idx] for idx in refs2]
                words2 = [wl[idx] for idx in w_idx2]
            elif 'wilist' in test:
                w_ids_2 = [test['wilist'][idx] for idx in refs2]
                words2 = [w_id.split(':')[1] for w_id in w_ids_2]
            else:
                raise Exception("Wrong test set!!")


            if words1 != words2:
                print("%d : %s [%s] != %s [%s]" % (i,w1,words1,w2,words2))
                raise Exception("Error in references!")

        a_ref_set = set([wid.split(':')[0] for wid in results['word_id_list']])
        if 'slist' in test:
            b_ref_set = set(test['slist'])
        else:
            b_ref_set = set([wid.split(':')[0] for wid in test['wilist']])
        extra_in_a = a_ref_set - b_ref_set
        missing_in_a = b_ref_set - a_ref_set

        if len(extra_in_a)>0:
            print("Extra:")
            for seq_sense in extra_in_a:
                s = seq_sense.split('/')
                seq = int(s[0])
                if len(s)>1:
                    sense = int(s[1])
                    meanings = get_meanings_by_sense(seq,sense)
                else:
                    sense = '*'
                    meanings = get_meanings_by_sense(seq,0)  # print just the first
                print("\t[%d] %s : %s" % (seq, sense, meanings))
            raise Exception("Error in sense list!")

        if len(missing_in_a)>0:
            print("Missing:")
            for seq_sense in missing_in_a:
                s = seq_sense.split('/')
                seq = int(s[0])
                if len(s)>1:
                    sense = int(s[1])
                    meanings = get_meanings_by_sense(seq,sense)
                else:
                    sense = '*'
                    meanings = get_meanings_by_sense(seq,0)  # print just the first
                print("\t[%d] %s : %s" % (seq, sense, meanings))
            raise Exception("Error in sense list!")

        """
        if set(results['word_list']) != set(test['word_list']):
            if set(results['word_list']) != set(test['word_list'][3:]):
                raise Exception("Error in word list!")
        """

        print("%s ok" % line)
    print("Tests ok")


def test_jmdict():
    line = 'こんだけ降ってたら'
    line = '踏み切り通ってく'
    line = 'サンドイッチは作ってある'
    line = '行ったり来たりしてるぞ'
    line = '人相がけわしくなっていって'
    line = '行きたがらないの'
    line = 'ここの扉鍵が壊れてて、完全に閉めると'
    line = '本読んだり参考書みたり。'
    line = 'カサ持ってっとけ'
    line = 'ございましたら'
    line = 'でもデータだけうつしちゃおう'
    line = '戻らないとかいっといて'
    line = 'シカトされ","てただけ'
    line = 'すごー'
    kanji_count = dict()

    scan_results = init_scan_results()

    kc, ud_items = parse_line_with_unidic(line,kanji_count)

    ud_items = \
        post_process_unidic_particles(ud_items)

    parse_with_jmdict(
        ud_items, scan_results
    )
    jlines = reassemble_block([line], ud_items, scan_results['item_word_id_refs'])
    jlines_str = str(jlines)
    #print("{'c':'%s','line':'%s','jlines':%s, 'wilist':%s}" % (c, line,str(jlines),str(scan_results['word_id_list'])))
          
    pass

init_parser(load_meanings=True)

set_verbose_level(2)

test_jmdict()
do_tests()

