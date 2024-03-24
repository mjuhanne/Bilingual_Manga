from helper import base_dir
from jmdict import jmdict_class_list


#jmdict_noun_class = jmdict_class_list.index('noun (common) (futsuumeishi)')
jmdict_prefix_class = jmdict_class_list.index('prefix')
jmdict_suffix_class = jmdict_class_list.index('suffix')
jmdict_noun_as_suffix_class = jmdict_class_list.index('noun, used as a suffix')

jmdict_prenominal_class = jmdict_class_list.index('noun or verb acting prenominally')

jmdict_suru_verb_class = jmdict_class_list.index('suru verb - included')
jmdict_godan_ru_i_verb_class = jmdict_class_list.index("Godan verb with 'ru' ending (irregular verb)")

jmdict_adjectival_noun_class = jmdict_class_list.index('adjectival nouns or quasi-adjectives (keiyodoshi)')
jmdict_adj_i_class = jmdict_class_list.index('adjective (keiyoushi)')
jmdict_adj_ii_class = jmdict_class_list.index('adjective (keiyoushi) - yoi/ii class')
jmdict_adj_pn_class = jmdict_class_list.index('pre-noun adjectival (rentaishi)')

jmdict_pronoun_class = jmdict_class_list.index('pronoun')

jmdict_interjection_class = jmdict_class_list.index('interjection (kandoushi)')

jmdict_expression_class = jmdict_class_list.index('expressions (phrases, clauses, etc.)')

jmdict_adverb_class = jmdict_class_list.index('adverb (fukushi)')
jmdict_adverb_to_class = jmdict_class_list.index("adverb taking the 'to' particle")

jmdict_conjunction_class = jmdict_class_list.index('conjunction')
jmdict_particle_class = jmdict_class_list.index('particle')

jmdict_numeric_class = jmdict_class_list.index('numeric')
jmdict_counter_class = jmdict_class_list.index('counter')

jmdict_aux_adj_class = jmdict_class_list.index('auxiliary adjective')
jmdict_auxiliary_class = jmdict_class_list.index('auxiliary')

# DO NOT CHANGE THE ORDER
unidic_class_list = [
    'non_jp_char',
    'alphanum',
    '補助記号',
    #'mid_s_p_m', # mid sentence punctuation mark

    '助動詞',
    '助詞',

    '名詞',
    '動詞',
    '接尾辞',  # suffix
    '副詞', # adverb
    '代名詞', # pronoun
    '形容詞', # adjective #10
    '感動詞', # interjection
    '形状詞', # adjectival noun
    '接頭辞', # prefix
    '接続詞', # conjunction
    '連体詞', ## その、そんな、そんな、あの、どんな。。
    '記号',
    '接頭詞', # different prefix? 超〜, 真〜, 大〜, 小〜, ぶっ〜 ＋ 叩く ＝ ぶっ叩く
    'フィラー',  # failure?
    'counter', # pseudo-class for か月
    'expression', # pseudo-class for expressions
]

unidic_class_name_strings = {
   'non_jp_char' : "",
    '補助記号' : "punctuation_mark",
    'alphanum' : "",
    'mid_s_p_m' : "mid_sentence_punctuation_mark",

    '助動詞' : "aux verb",
    '助詞' : "grammatical particle",

    '名詞' : "noun",
    '動詞' : "verb",
    '接尾辞' : "suffix",
    '副詞' : "adverb",
    '代名詞' : "pronoun",
    '形容詞' : "adjective",
    '感動詞' : "interjection",
    '形状詞' : "adjectival noun",
    '接頭辞' : "prefix",
    '接続詞' : "conjunction",
    '連体詞' : "その、そんな、そんな、あの、どんな。。",
    '記号' : "",
    '接頭詞' : "",
    'フィラー' : "failure?",
    "counter" : "counter",
    "expression" : "expression",
}

def unidic_class_to_string(class_id):
    return unidic_class_name_strings[unidic_class_list[class_id]]

def unidic_classes_to_string(class_ids):
    return '/'.join([unidic_class_name_strings[unidic_class_list[class_id]] for class_id in class_ids])


# words/characters belonging to these classes are lumped
# as one word with other same class members. They aren't saved separately in the unique
# words list but instead will reference a combined word slot, for example
# all sequential alphanumerical characters "１９８０" reference 
# LUMPED_ALPHANUM_CHARACTER_INDEX slot in the word list
alphanum_pseudoclass = unidic_class_list.index('alphanum')
non_jp_char_pseudoclass = unidic_class_list.index('non_jp_char')
punctuation_mark_class = unidic_class_list.index('補助記号')
#mid_sentence_punctuation_mark_class = unidic_class_list.index('mid_s_p_m')
# all classes up to this index are lumped together
#lumped_class = mid_sentence_punctuation_mark_class
lumped_class = punctuation_mark_class


aux_verb_class = unidic_class_list.index('助動詞')
verb_class = unidic_class_list.index('動詞')
interjection_class = unidic_class_list.index('感動詞')
noun_class = unidic_class_list.index('名詞')
prefix_class = unidic_class_list.index('接頭辞')
suffix_class = unidic_class_list.index('接尾辞')
adjective_class = unidic_class_list.index('形容詞')
adjectival_noun_class = unidic_class_list.index('形状詞')
adverb_class = unidic_class_list.index('副詞')
conjunction_class = unidic_class_list.index('接続詞')
pronoun_class = unidic_class_list.index('代名詞')
rentaishi_class = unidic_class_list.index('連体詞') # その、そんな、そんな、あの、どんな。。
grammatical_particle_class = unidic_class_list.index('助詞')
gp_class = grammatical_particle_class # shorthand


# some counter related nouns (か月) are switched into this pseudoclass
counter_pseudoclass = unidic_class_list.index('counter')

expression_class = unidic_class_list.index('expression')

LUMPED_NON_JP_CHARACTER_INDEX = 0
LUMPED_ALPHANUM_CHARACTER_INDEX = 1
LUMPED_AUX_VERB_INDEX = 2
LUMPED_GRAM_PARTICLE_INDEX = 3


allowed_other_class_bindings = {
    jmdict_adjectival_noun_class : [adjectival_noun_class, adjective_class, noun_class],

    jmdict_adverb_class : [adverb_class],
    jmdict_adverb_to_class : [adverb_class],

    jmdict_conjunction_class : [conjunction_class,
            # 癖(名詞)+ に(助詞)
        #noun_class, grammatical_particle_class,
        # それ(代名詞) -> それに(conjunction)
        #pronoun_class,
    ],
    jmdict_adj_i_class : [adjective_class],
    jmdict_adj_ii_class : [adjective_class],
    jmdict_pronoun_class : [
        pronoun_class,
         # か(助詞) -> 誰か
        #grammatical_particle_class,
     ],

    jmdict_interjection_class : [
        interjection_class,
        adverb_class, # some words classified as adverbs work as interjection
        ],
    jmdict_adj_pn_class : [rentaishi_class],
    
    #jmdict_adj_pn_class :  [adverb_class, verb_class] # そういう

    #jmdict_noun_class : [noun_class, prefix_class, suffix_class],

    jmdict_prefix_class : [prefix_class],
    jmdict_suffix_class : [suffix_class],
    jmdict_noun_as_suffix_class : [suffix_class,noun_class],

    jmdict_prenominal_class : [rentaishi_class],
    jmdict_particle_class : [grammatical_particle_class],

    jmdict_numeric_class : [noun_class], # 百，万　are noun in Unidic

    jmdict_counter_class : [
         # ３５歳
        suffix_class, 
        counter_pseudoclass,
    ],

    # this is for volitional ーたい eg (見たい、やりたい)
    jmdict_aux_adj_class : [aux_verb_class], 

    jmdict_auxiliary_class : [aux_verb_class]
}

allowed_noun_bindings = set([noun_class, adjectival_noun_class]) #, prefix_class, suffix_class]
allowed_verb_bindings = set([verb_class, aux_verb_class]) #, adverb_class, ]


# Merge these particles together while forcing the result explicitely 
# to a target class that works well with JMDict
# [ [particle list], [unidic_detected_classes_per_particle], condition, target_unidic_class]
COND_NONE = 0
COND_BLOCK_START = 1
COND_NOT_BEFORE_VERB = 2
COND_NOT_AFTER_NOUN = 4
COND_NOT_AFTER_ADJ = 8

TASK_NONE = 0
TASK_MERGE = 1
TASK_DIVIDE = 2

# word flags
NO_SCANNING = 1
START_OF_SCAN_DISABLED = 2
MERGE_PARTICLE = 4
DIVIDE_PARTICLE = 8
REMOVE_PARTICLE = 16
DISABLE_ORTHO = 32
REPROCESS = 64
ERROR_VERB_CONJUGATION = 128
BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED = 256
SCAN_WITH_LEMMA = 512


explicit_word_changes = [

    #nouns
    [['そこ','ら'],[pronoun_class,suffix_class],COND_NONE,TASK_MERGE,{'class':noun_class}],
    [['タ','オル'],[aux_verb_class,noun_class],COND_NONE,TASK_MERGE,{'class':noun_class,'ortho':'','alt':''}],
    [['Ｔ','シャツ'],[alphanum_pseudoclass,noun_class],COND_NONE,TASK_MERGE,{'class':noun_class}],
    [['文部'],[noun_class],COND_NONE,TASK_DIVIDE,{'parts':['文','部']}],

    # verbs
    [['でしょ'],[aux_verb_class],COND_NONE,TASK_NONE,{'class':verb_class}],
    [['でし','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':verb_class,'root_ortho':'です'}],
    [['だ','も','の'],[aux_verb_class,gp_class,gp_class],COND_NONE,TASK_MERGE,{'class':verb_class}],
    [['し','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_NONE,{'class':verb_class,'ortho':'する'}],
    [['だっ','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':verb_class,'root_ortho':'だ'}],

    # adjectives
    [['らしい'],[aux_verb_class],COND_NONE,TASK_NONE,{'class':adjective_class}],
    [['や','ばい'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adjective_class}],
    [['な','い'],[aux_verb_class,interjection_class],COND_NONE,TASK_MERGE,{'class':adjective_class}],
    [['お','しい'],[prefix_class,verb_class],COND_NONE,TASK_MERGE,{'class':adjective_class}],

    # disable scan start from よく so that it よくある / よくなる won't be detected
    # e.g. いつもよりかっこよくあらへん？
    [['かっこ','よく'],[noun_class,adjective_class],COND_NONE,TASK_NONE,{'add_flags':[0,START_OF_SCAN_DISABLED]}],
    # e.g. 気持ちよくなってきた
    [['気持ち','よく'],[noun_class,adjective_class],COND_NONE,TASK_NONE,{'add_flags':[0,START_OF_SCAN_DISABLED]}],
    # disable scan start from いい so that it いいって言われて won't be detected
    # かっこいいって言われてたね
    [['かっこ','いい'],[noun_class,adjective_class],COND_NONE,TASK_NONE,{'add_flags':[0,START_OF_SCAN_DISABLED]}],
    [['かっこう','いい'],[noun_class,adjective_class],COND_NONE,TASK_NONE,{'add_flags':[0,START_OF_SCAN_DISABLED]}],
    [['気持ち','いい'],[noun_class,adjective_class],COND_NONE,TASK_NONE,{'add_flags':[0,START_OF_SCAN_DISABLED]}],

    # conjunctions
    [['だ','から'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class,'ortho':''}], 
    [['だ','けど'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class,'ortho':''}],



    # それに works as conjunction as long as it's not before verb 
    # (in that case に most likely is a solo particle)
    [['それ','に'],[pronoun_class,gp_class],COND_NOT_BEFORE_VERB,TASK_MERGE,{'class':conjunction_class}],


    [['それ','で'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],
    [['ところ','で'],[noun_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],
    [['だっ','たら'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],
    [['それ','より'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],
    [['そう','し','たら'],[adverb_class,verb_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],
    [['そう','し','て'],[adverb_class,verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],
    [['で','も'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_MERGE,{'class':conjunction_class,'ortho':''}],
    [['こう','やっ','て'],[adverb_class,verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],
    [['だ','って'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_MERGE,{'class':conjunction_class,'ortho':''}],
    [['だ','って'],[aux_verb_class,aux_verb_class],COND_BLOCK_START,TASK_MERGE,{'class':conjunction_class,'ortho':''}],
    [['と','か'],[gp_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class,'ortho':''}],
    [['っつう','か'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],
    [['つう','か'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class}],


    # Forcing these as conjunctions shouldn't affect the verb conjugations
    # because they are done greedily regardless of the unidict class
    [['じゃ'],[gp_class],COND_NONE,TASK_NONE,{'class':conjunction_class}],
    # clear the っつう ortho of って
    [['って'],[aux_verb_class],COND_NONE,TASK_NONE,{'class':conjunction_class,'ortho':''}],

    # で at the start of the sentence is always 'and then/so'
    #[['で'],[aux_verb_class],COND_BLOCK_START,TASK_NONE,{'class':conjunction_class,'ortho':'','word_id':'2028980/3:で'}],

    # pronouns
    [['自分'],[noun_class],COND_NONE,TASK_NONE,{'class':pronoun_class}],

    [['なん','だ','か'],[pronoun_class,aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['な','ん','だ','か'],[aux_verb_class,gp_class,aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['な','ん','だ','けど'],[aux_verb_class,gp_class,aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'parts':['なん','だけど'],'classes':[pronoun_class,conjunction_class],'orthos':['','']}],

    # interjection
    [['ごめん'],[noun_class],COND_NONE,TASK_NONE,{'class':interjection_class}],
    [['さあ'],[gp_class],COND_NONE,TASK_NONE,{'class':interjection_class}],
    [['な','ん','だ'],[aux_verb_class,gp_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':interjection_class,'ortho':''}],
    [['なあん','だ'],[pronoun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':interjection_class,'ortho':''}],
    [['や','だ'],[aux_verb_class,aux_verb_class],COND_BLOCK_START,TASK_MERGE,{'class':interjection_class}],
    [['や','だ'],[adjectival_noun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],
    [['そっ','か'],[pronoun_class,gp_class],COND_BLOCK_START,TASK_MERGE,{'class':interjection_class}],
    [['ん'],[aux_verb_class],COND_BLOCK_START,TASK_NONE,{'class':interjection_class,'ortho':''}],
    [['い','えっ'],[interjection_class,interjection_class],COND_BLOCK_START,TASK_MERGE,{'class':interjection_class}],
    [['おは','よ'],[interjection_class,gp_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],
    [['お','やおや'],[prefix_class,noun_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],

    # force ねえ to interjection only at the beginning of of block (otherwise it could be ない)
    [['ねえ'],[aux_verb_class],COND_BLOCK_START,TASK_NONE,{'class':interjection_class}],


    # adverbs
    #(['もし','も'],[adverb_class,gp_class],adverb_class,COND_NONE,TASK_NONE),
    [['な','ん','で'],[aux_verb_class,gp_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adverb_class,'ortho':''}],
    [['な','ん'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['なん','で'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['なる','ほど'],[verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['なる','ほど'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['ほど'],[gp_class],COND_NONE,TASK_NONE,{'class':adverb_class}],
    [['いつ','で','も'],[pronoun_class,gp_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['いつ','も'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['二人','と','も'],[noun_class,gp_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['ず','っと'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class,'ortho':''}],
    [['この','前'],[rentaishi_class,noun_class],COND_NONE,TASK_MERGE,{'class':adverb_class,'ortho':''}],
    [['断じ','て'],[verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class,'ortho':''}],
    [['まさ','か'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_MERGE,{'class':adverb_class}],
    [['こん','だけ'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['どっ','か'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['どんな','に'],[adjectival_noun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['割','と'],[noun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['たっ','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['いつ','か'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['本気','で'],[noun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['何','やら'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],

    # auxiliary
    # remove だ ortho from なら and で
    [['なら'],[aux_verb_class],COND_NONE,TASK_NONE,{'ortho':''}],
    [['で'],[aux_verb_class],COND_NONE,TASK_NONE,{'ortho':''}],


    # rentaishi_class.  (あなたの)ような..
    [['よう','な'],[adjectival_noun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':rentaishi_class}],
    [['そー','ゆー'],[adverb_class,noun_class],COND_NONE,TASK_MERGE,{'class':rentaishi_class}],
    
    # expressions
    [['そっ','かー'],[adverb_class,gp_class],COND_NONE,TASK_MERGE,{'class':expression_class,'ortho':''}],


]

# alternative unidic classes for certain words to allow for better
# searching from JMDic
alternative_classes = {
    'ねえ' : [interjection_class, grammatical_particle_class],
    'ね' : [interjection_class],
    '一番' : [noun_class],
    'また' : [adverb_class],
    'ほとんど' : [adverb_class],
    '後' : [adverb_class],
    '一見' : [noun_class],
    'で' : [conjunction_class, grammatical_particle_class],
    'まさか' : [interjection_class],
    '大変' : [adverb_class],
    'なんだ' : [interjection_class],
    '確か' : [adjectival_noun_class],
    'と' : [conjunction_class],
    'マシ' : [adjectival_noun_class],
    'じゃあ' : [conjunction_class],
    'もー' : [interjection_class],
    'つい' : [adverb_class],
    '天' : [noun_class],

    # Pre-noun Adjectivals, detected originally as adjectival nouns
    'そんな' : [rentaishi_class],
    'こんな' : [rentaishi_class],

    # originally verbs
    'つれない' : [adjective_class],
    '下らない' : [adjective_class],
    'らしい' : [adjective_class],

    # we put this explicitely here because don't want to allow all nouns to be possible counters
    'か月' : [counter_pseudoclass], 
    'ヶ月' : [counter_pseudoclass], 


    'そっくり' : [adverb_class], # originally adjectival noun

    'や' : [gp_class],
    'って' : [gp_class],

    '議' : [noun_class],
}
alternative_forms = {
    'っちゃん' : ['ちゃん'],
    'いえっ' : ['いえ'],
    'そっかー' : ['そうか'],
    'ねー' : ['ない','ねえ'],
    'いねー' : ['いない'],
}

# some common auxiliary verbs, particles and markings which we ignore for frequency analysis
ignored_classes = [
    '補助記号', # ？
    #'助詞', # Grammatical particles: と, ん, から, の, だけ...
    #'助動詞', # Auxiliary verb: ちゃ, た, ます, てる, ない
    ]

ignored_classes_for_freq = [
    '補助記号', # ？
    '助詞', # Grammatical particles: と, ん, から, の, だけ...
    '助動詞', # Auxiliary verb: ちゃ, た, ます, てる, ない
    'non_jp_char',
    'alphanum',
    ]

SMALL_PARTICLE_THRESHOLD = 2

# this is for clutter prevention. Too many homophones for these common words
hard_coded_seqs = {
    'いる' : (verb_class, 1577980),
    'する' : (verb_class, 1157170),
    'なる' : (verb_class, 1375610),
    '私' : (pronoun_class, 1311110),
    'そう' : (adjectival_noun_class,2137720),
}


manual_additions_to_jmdict_classes = {
    1956330 : [jmdict_suffix_class],  # 師 works also as a suffix
}

# Sometimes Unidict just fails to parse pure Hiragana words..
# For example ばんそうこう (bandage) becomes:
#  ば (grammatical particle)
#  ん (interjection)
#  そうこう (adverb) ..
# To allow matching these kinds of words we disregard the parsed classes
# if the candidate word is a noun and has a length of minimum of 5 characters 
HOMOPHONE_MATCHING_WORD_MINIMUM_LENGTH = 5

# words consisting of these wide characters will be ignored
ignored_full_width_characters = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９％"

def is_all_alpha(word):
    if all(c in ignored_full_width_characters for c in word):
        return True
    if word.isascii() and word.isalnum():
        return True
    return False

