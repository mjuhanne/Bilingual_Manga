from helper import base_dir

jmdict_file = base_dir + "lang/JMdict_e_s.tsv"
jmdict_with_meanings_file = base_dir + "lang/JMdict_e_m.tsv"

# DO NOT CHANGE THE ORDER
jmdict_parts_of_speech_list = [
    # these are our modifications.
    'non_jp_char',
    'alphanum',
    'punctuation marks 補助記号',
    # These are from JMdict. Sorted by frequency in descending order
    'noun (common) (futsuumeishi)', 
    'expressions (phrases, clauses, etc.)', 
    'adjectival nouns or quasi-adjectives (keiyodoshi)', 
    'Ichidan verb', 
    'adverb (fukushi)', 
    "nouns which may take the genitive case particle 'no'", 
    "Godan verb with 'ru' ending", "Godan verb with 'su' ending", 
    'adjective (keiyoushi)', "Godan verb with 'ku' ending", 
    'interjection (kandoushi)', "Godan verb with 'mu' ending", 
    'noun or verb acting prenominally', "Godan verb with 'u' ending", 
    'suffix', "adverb taking the 'to' particle", "'taru' adjective", 
    'suru verb - special class', 'pronoun', 'noun, used as a suffix', 
    'prefix', 'particle', 'conjunction', "Godan verb with 'tsu' ending", 
    'noun or participle which takes the aux. verb suru', 'counter', 
    'pre-noun adjectival (rentaishi)', "Godan verb with 'gu' ending", 
    'Ichidan verb - zuru verb (alternative form of -jiru verbs)', 
    'auxiliary verb', 'numeric', 'noun, used as a prefix', 
    "Godan verb with 'bu' ending", 'suru verb - included', 'auxiliary', 
    'Godan verb - Iku/Yuku special class', 
    "Nidan verb (lower class) with 'mu' ending (archaic)", 
    "'ku' adjective (archaic)", 'su verb - precursor to the modern suru', 
    'unclassified', "Yodan verb with 'ru' ending (archaic)", 
    "Nidan verb (lower class) with 'ru' ending (archaic)", 
    "Nidan verb (lower class) with 'dzu' ending (archaic)", 
    "Yodan verb with 'ku' ending (archaic)", 'archaic/formal form of na-adjective', 
    'adjective (keiyoushi) - yoi/ii class', "Yodan verb with 'su' ending (archaic)", 
    "Godan verb with 'nu' ending", "Yodan verb with 'hu/fu' ending (archaic)", 
    "Godan verb with 'u' ending (special class)", 'Kuru verb - special class', 
    'Godan verb - -aru special class', 'copula', "'shiku' adjective (archaic)", 
    'irregular ru verb, plain form ends with -ri', 
    "Godan verb with 'ru' ending (irregular verb)", 
    "Yodan verb with 'tsu' ending (archaic)", 
    "Nidan verb (lower class) with 'hu/fu' ending (archaic)", 
    "Nidan verb (lower class) with 'ku' ending (archaic)", 
    "Nidan verb (lower class) with 'tsu' ending (archaic)", 
    'intransitive verb', "Nidan verb (lower class) with 'gu' ending (archaic)", 
    "Nidan verb (lower class) with 'yu' ending (archaic)", 
    "Nidan verb (upper class) with 'yu' ending (archaic)", 
    'auxiliary adjective', 'irregular nu verb', 
    "Nidan verb (upper class) with 'gu' ending (archaic)", 
    "Nidan verb (lower class) with 'su' ending (archaic)", 
    "Yodan verb with 'mu' ending (archaic)", 
    "Nidan verb with 'u' ending (archaic)", 
    "Nidan verb (upper class) with 'bu' ending (archaic)", 
    "Nidan verb (lower class) with 'nu' ending (archaic)", 
    'Ichidan verb - kureru special class', 
    "Nidan verb (upper class) with 'hu/fu' ending (archaic)", 
    'verb unspecified', "Nidan verb (upper class) with 'ru' ending (archaic)", 
    "Yodan verb with 'gu' ending (archaic)", "Yodan verb with 'bu' ending (archaic)", 
    "Nidan verb (upper class) with 'ku' ending (archaic)", 
    "Nidan verb (upper class) with 'tsu' ending (archaic)", 
    "Nidan verb (lower class) with 'zu' ending (archaic)", 
    "Nidan verb (lower class) with 'u' ending and 'we' conjugation (archaic)", 
    'transitive verb'
]

jmdict_parts_of_speech_codes = {
'adj-f': "noun or verb acting prenominally",
'adj-i': "adjective (keiyoushi)",
'adj-ix': "adjective (keiyoushi) - yoi/ii class",
'adj-kari': "'kari' adjective (archaic)",
'adj-ku': "'ku' adjective (archaic)",
'adj-na': "adjectival nouns or quasi-adjectives (keiyodoshi)",
'adj-nari': "archaic/formal form of na-adjective",
'adj-no': "nouns which may take the genitive case particle 'no'",
'adj-pn': "pre-noun adjectival (rentaishi)",
'adj-shiku': "'shiku' adjective (archaic)",
'adj-t': "'taru' adjective",
'adv': "adverb (fukushi)",
'adv-to': "adverb taking the 'to' particle",
'aux': "auxiliary",
'aux-adj': "auxiliary adjective",
'aux-v': "auxiliary verb",
'conj': "conjunction",
'cop': "copula",
'ctr': "counter",
'exp': "expressions (phrases, clauses, etc.)",
'int': "interjection (kandoushi)",
'n': "noun (common) (futsuumeishi)",
'n-adv': "adverbial noun (fukushitekimeishi)",
'n-pr': "proper noun",
'n-pref': "noun, used as a prefix",
'n-suf': "noun, used as a suffix",
'n-t': "noun (temporal) (jisoumeishi)",
'num': "numeric",
'pn': "pronoun",
'pref': "prefix",
'prt': "particle",
'suf': "suffix",
'unc': "unclassified",
'v-unspec': "verb unspecified",
'v1': "Ichidan verb",
'v1-s': "Ichidan verb - kureru special class",
'v2a-s': "Nidan verb with 'u' ending (archaic)",
'v2b-k': "Nidan verb (upper class) with 'bu' ending (archaic)",
'v2b-s': "Nidan verb (lower class) with 'bu' ending (archaic)",
'v2d-k': "Nidan verb (upper class) with 'dzu' ending (archaic)",
'v2d-s': "Nidan verb (lower class) with 'dzu' ending (archaic)",
'v2g-k': "Nidan verb (upper class) with 'gu' ending (archaic)",
'v2g-s': "Nidan verb (lower class) with 'gu' ending (archaic)",
'v2h-k': "Nidan verb (upper class) with 'hu/fu' ending (archaic)",
'v2h-s': "Nidan verb (lower class) with 'hu/fu' ending (archaic)",
'v2k-k': "Nidan verb (upper class) with 'ku' ending (archaic)",
'v2k-s': "Nidan verb (lower class) with 'ku' ending (archaic)",
'v2m-k': "Nidan verb (upper class) with 'mu' ending (archaic)",
'v2m-s': "Nidan verb (lower class) with 'mu' ending (archaic)",
'v2n-s': "Nidan verb (lower class) with 'nu' ending (archaic)",
'v2r-k': "Nidan verb (upper class) with 'ru' ending (archaic)",
'v2r-s': "Nidan verb (lower class) with 'ru' ending (archaic)",
'v2s-s': "Nidan verb (lower class) with 'su' ending (archaic)",
'v2t-k': "Nidan verb (upper class) with 'tsu' ending (archaic)",
'v2t-s': "Nidan verb (lower class) with 'tsu' ending (archaic)",
'v2w-s': "Nidan verb (lower class) with 'u' ending and 'we' conjugation (archaic)",
'v2y-k': "Nidan verb (upper class) with 'yu' ending (archaic)",
'v2y-s': "Nidan verb (lower class) with 'yu' ending (archaic)",
'v2z-s': "Nidan verb (lower class) with 'zu' ending (archaic)",
'v4b': "Yodan verb with 'bu' ending (archaic)",
'v4g': "Yodan verb with 'gu' ending (archaic)",
'v4h': "Yodan verb with 'hu/fu' ending (archaic)",
'v4k': "Yodan verb with 'ku' ending (archaic)",
'v4m': "Yodan verb with 'mu' ending (archaic)",
'v4n': "Yodan verb with 'nu' ending (archaic)",
'v4r': "Yodan verb with 'ru' ending (archaic)",
'v4s': "Yodan verb with 'su' ending (archaic)",
'v4t': "Yodan verb with 'tsu' ending (archaic)",
'v5aru': "Godan verb - -aru special class",
'v5b': "Godan verb with 'bu' ending",
'v5g': "Godan verb with 'gu' ending",
'v5k': "Godan verb with 'ku' ending",
'v5k-s': "Godan verb - Iku/Yuku special class",
'v5m': "Godan verb with 'mu' ending",
'v5n': "Godan verb with 'nu' ending",
'v5r': "Godan verb with 'ru' ending",
'v5r-i': "Godan verb with 'ru' ending (irregular verb)",
'v5s': "Godan verb with 'su' ending",
'v5t': "Godan verb with 'tsu' ending",
'v5u': "Godan verb with 'u' ending",
'v5u-s': "Godan verb with 'u' ending (special class)",
#'v5uru': "Godan verb - Uru old class verb (old form of Eru)",
'vi': "intransitive verb",
'vk': "Kuru verb - special class",
'vn': "irregular nu verb",
'vr': "irregular ru verb, plain form ends with -ri",
'vs': "noun or participle which takes the aux. verb suru",
'vs-c': "su verb - precursor to the modern suru",
'vs-i': "suru verb - included",
'vs-s': "suru verb - special class",
'vt': "transitive verb",
'vz': "Ichidan verb - zuru verb (alternative form of -jiru verbs)",
'gikun': "gikun (meaning as reading) or jukujikun (special kanji reading)",
'ik': "word containing irregular kana usage",
'ok': "out-dated or obsolete kana usage",
'rk': "rarely used kana form",
'sk': "search-only kana form",
}

jmdict_noun_classes = []
jmdict_verb_classes = []

#jmdict_noun_class = jmdict_parts_of_speech_list.index('noun (common) (futsuumeishi)')
jmdict_prefix_class = jmdict_parts_of_speech_list.index('prefix')
jmdict_suffix_class = jmdict_parts_of_speech_list.index('suffix')
jmdict_noun_as_suffix_class = jmdict_parts_of_speech_list.index('noun, used as a suffix')

jmdict_prenominal_class = jmdict_parts_of_speech_list.index('noun or verb acting prenominally')

jmdict_suru_verb_class = jmdict_parts_of_speech_list.index('suru verb - included')
jmdict_godan_ru_i_verb_class = jmdict_parts_of_speech_list.index("Godan verb with 'ru' ending (irregular verb)")

jmdict_adjectival_noun_class = jmdict_parts_of_speech_list.index('adjectival nouns or quasi-adjectives (keiyodoshi)')
jmdict_adj_i_class = jmdict_parts_of_speech_list.index('adjective (keiyoushi)')
jmdict_adj_ii_class = jmdict_parts_of_speech_list.index('adjective (keiyoushi) - yoi/ii class')
jmdict_adj_pn_class = jmdict_parts_of_speech_list.index('pre-noun adjectival (rentaishi)')

jmdict_pronoun_class = jmdict_parts_of_speech_list.index('pronoun')

jmdict_interjection_class = jmdict_parts_of_speech_list.index('interjection (kandoushi)')

jmdict_expression_class = jmdict_parts_of_speech_list.index('expressions (phrases, clauses, etc.)')

jmdict_adverb_class = jmdict_parts_of_speech_list.index('adverb (fukushi)')
jmdict_adverb_to_class = jmdict_parts_of_speech_list.index("adverb taking the 'to' particle")

jmdict_conjunction_class = jmdict_parts_of_speech_list.index('conjunction')
jmdict_particle_class = jmdict_parts_of_speech_list.index('particle')

jmdict_numeric_class = jmdict_parts_of_speech_list.index('numeric')
jmdict_counter_class = jmdict_parts_of_speech_list.index('counter')

jmdict_aux_adj_class = jmdict_parts_of_speech_list.index('auxiliary adjective')
jmdict_auxiliary_class = jmdict_parts_of_speech_list.index('auxiliary')

# DO NOT CHANGE THE ORDER
unidic_item_classes = [
    'non_jp_char',
    'alphanum',
    '補助記号',

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
]

unidic_class_name_strings = {
   'non_jp_char' : "",
    'alphanum' : "",
    '補助記号' : "punctuation_mark",

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
    'フィラー' : "failure?"
}

def unidic_class_to_string(class_id):
    return unidic_class_name_strings[unidic_item_classes[class_id]]

def unidic_classes_to_string(class_ids):
    return '/'.join([unidic_class_name_strings[unidic_item_classes[class_id]] for class_id in class_ids])


# words/characters belonging to these classes are lumped
# as one word with other class members. They aren't saved separately in the unique
# words list but instead are lumped into combined word slot, for examlple
# all sequential alphanumerical characters are saved into LUMPED_ALPHANUM_CHARACTER_INDEX
aux_verb_class = unidic_item_classes.index('助動詞')
alphanum_class = unidic_item_classes.index('alphanum')
non_jp_char_class = unidic_item_classes.index('non_jp_char')
punctuation_mark_class = unidic_item_classes.index('補助記号')
# all classes up to this index are lumped together
lumped_class = punctuation_mark_class

verb_class = unidic_item_classes.index('動詞')

interjection_class = unidic_item_classes.index('感動詞')
noun_class = unidic_item_classes.index('名詞')
prefix_class = unidic_item_classes.index('接頭辞')
suffix_class = unidic_item_classes.index('接尾辞')
adjective_class = unidic_item_classes.index('形容詞')
adjectival_noun_class = unidic_item_classes.index('形状詞')
adverb_class = unidic_item_classes.index('副詞')
conjunction_class = unidic_item_classes.index('接続詞')
pronoun_class = unidic_item_classes.index('代名詞')

rentaishi_class = unidic_item_classes.index('連体詞') # その、そんな、そんな、あの、どんな。。

grammatical_particle_class = unidic_item_classes.index('助詞')
gp_class = grammatical_particle_class # shorthand

counter_pseudoclass = unidic_item_classes.index('counter')

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

    jmdict_interjection_class : [interjection_class],
    jmdict_adj_pn_class : [rentaishi_class],
    
    #jmdict_adj_pn_class :  [adverb_class, verb_class] # そういう

    #jmdict_noun_class : [noun_class, prefix_class, suffix_class],

    jmdict_prefix_class : [prefix_class],
    jmdict_suffix_class : [suffix_class],
    jmdict_noun_as_suffix_class : [suffix_class],

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
# to a proper class that works well with JMDict
# ( [particle list], [unidic_detected_classes_per_particle], proper_unidic_class)
COND_NONE = 0
COND_BLOCK_START = 1
TASK_NONE = 0
TASK_CLEAR_ORTHO = 1
explicit_words = [
    #nouns
    (['そこ','ら'],[pronoun_class,suffix_class], noun_class,COND_NONE,TASK_NONE),

    # verbs
    (['でしょ'],[aux_verb_class],verb_class,COND_NONE,TASK_NONE),
    (['だ','も','の'],[aux_verb_class,gp_class,gp_class],verb_class,COND_NONE,TASK_NONE),

    # adjectives
    (['らしい'],[aux_verb_class],adjective_class,COND_NONE,TASK_NONE),
    (['や','ばい'],[aux_verb_class,gp_class],adjective_class,COND_NONE,TASK_NONE),

    # conjunctions
    (['だ','から'],[aux_verb_class,gp_class],conjunction_class,COND_NONE,TASK_NONE), 
    (['だ','けど'],[aux_verb_class,gp_class],conjunction_class,COND_NONE,TASK_NONE),
    (['それ','に'],[pronoun_class,gp_class],conjunction_class,COND_NONE,TASK_NONE),
    (['ところ','で'],[noun_class,gp_class],conjunction_class,COND_NONE,TASK_NONE),
    (['だっ','たら'],[aux_verb_class,aux_verb_class],conjunction_class,COND_NONE,TASK_NONE),
    (['それ','より'],[pronoun_class,gp_class],conjunction_class,COND_NONE,TASK_NONE), 
    (['そう','し','たら'],[adverb_class,verb_class,aux_verb_class],conjunction_class,COND_NONE,TASK_NONE), 
    (['そう','し','て'],[adverb_class,verb_class,gp_class],conjunction_class,COND_NONE,TASK_NONE), 
    (['で','も'],[aux_verb_class,gp_class],conjunction_class,COND_BLOCK_START,TASK_CLEAR_ORTHO),
    (['こう','やっ','て'],[adverb_class,verb_class,gp_class],conjunction_class,COND_NONE,TASK_NONE),


    # Forcing these as conjunctions shouldn't affect the verb conjugations
    # because they are done greedily regardless of the unidict class
    (['って'],[aux_verb_class],conjunction_class,COND_NONE,TASK_NONE),
    (['じゃ'],[gp_class],conjunction_class,COND_NONE,TASK_NONE),

    # pronouns
    #(['だれ','か'],[pronoun_class,gp_class],pronoun_class),
    #(['誰','か'],[pronoun_class,gp_class],pronoun_class),
    (['自分'],[noun_class],pronoun_class,COND_NONE,TASK_NONE),

    # interjection
    (['ごめん'],[noun_class],interjection_class,COND_NONE,TASK_NONE),
    (['さあ'],[gp_class],interjection_class,COND_NONE,TASK_NONE),
    (['な','ん','だ'],[aux_verb_class,gp_class,aux_verb_class],interjection_class,COND_NONE,TASK_NONE),
    (['や','だ'],[aux_verb_class,aux_verb_class],interjection_class,COND_BLOCK_START,TASK_NONE),

    # adverbs
    #(['もし','も'],[adverb_class,gp_class],adverb_class,COND_NONE,TASK_NONE),
    (['な','ん'],[aux_verb_class,gp_class],adverb_class,COND_NONE,TASK_NONE),
    (['なん','で'],[pronoun_class,gp_class],adverb_class,COND_NONE,TASK_NONE),
    (['なる','ほど'],[verb_class,gp_class],adverb_class,COND_NONE,TASK_NONE),
    (['なる','ほど'],[aux_verb_class,gp_class],adverb_class,COND_NONE,TASK_NONE),
    (['ほど'],[gp_class],adverb_class,COND_NONE,TASK_NONE),
    (['いつ','で','も'],[pronoun_class,gp_class,gp_class],adverb_class,COND_NONE,TASK_NONE),
    (['いつ','も'],[pronoun_class,gp_class],adverb_class,COND_NONE,TASK_NONE),

    # rentaishi_class.  (あなたの)ような..
    (['よう','な'],[adjectival_noun_class,aux_verb_class],rentaishi_class,COND_NONE,TASK_NONE),
    
]

# alternative unidic classes for certain words to allow for bettering
# searching from JMDic
alternative_classes = {
    'ねえ' : [interjection_class, grammatical_particle_class],
    '一番' : [noun_class],
    'また' : [adverb_class],
    'ほとんど' : [adverb_class],
    '後' : [adverb_class],
    '一見' : [noun_class],
    'で' : [conjunction_class],
    'まさか' : [interjection_class],
    '大変' : [adverb_class],
    'なんだ' : [interjection_class],
    '確か' : [adjectival_noun_class],
    'と' : [conjunction_class],

    # Pre-noun Adjectivals, detected originally as adjectival nouns
    'そんな' : [rentaishi_class],
    'こんな' : [rentaishi_class],


    # we put this explicitely here because don't want to allow all nouns to be possible counters
    'か月' : [counter_pseudoclass], 

    'そっくり' : [adverb_class], # originally adjectival noun

    'なかっ' : [suffix_class], # TODO: leave it here or try to improve verb conjugation?
    'や' : [gp_class],


    '議' : [noun_class],
}
alternative_forms = {
    'っちゃん' : 'ちゃん'
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
    '私' : (pronoun_class, 1311110),
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


# word flags
NO_SCANNING = 1
START_OF_SCAN_DISABLED = 2
MERGE_PARTICLE = 4
DISABLE_ORTHO = 8
PROCESS_AFTER_MERGING = 16
ERROR_VERB_CONJUGATION = 32
BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED = 64
