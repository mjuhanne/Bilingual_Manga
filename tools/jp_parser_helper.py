
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

jmdict_suru_verb_class = jmdict_parts_of_speech_list.index('suru verb - included')
jmdict_godan_ru_i_verb_class = jmdict_parts_of_speech_list.index("Godan verb with 'ru' ending (irregular verb)")

jmdict_adj_pn_class = jmdict_parts_of_speech_list.index('pre-noun adjectival (rentaishi)')

jmdict_pronoun_class = jmdict_parts_of_speech_list.index('pronoun')

jmdict_interjection_class = jmdict_parts_of_speech_list.index('interjection (kandoushi)')

jmdict_adjectival_noun_class = jmdict_parts_of_speech_list.index('adjectival nouns or quasi-adjectives (keiyodoshi)')
jmdict_adj_i_class = jmdict_parts_of_speech_list.index('adjective (keiyoushi)')
#jmdict_noun_class = jmdict_parts_of_speech_list.index('noun (common) (futsuumeishi)')
jmdict_expression_class = jmdict_parts_of_speech_list.index('expressions (phrases, clauses, etc.)')
jmdict_adverb_class = jmdict_parts_of_speech_list.index('adverb (fukushi)')

jmdict_conjunction_class = jmdict_parts_of_speech_list.index('conjunction')

jmdict_adj_ii_class = jmdict_parts_of_speech_list.index('adjective (keiyoushi) - yoi/ii class')

jmdict_suffix_class = jmdict_parts_of_speech_list.index('suffix')

jmdict_prenominal_class = jmdict_parts_of_speech_list.index('noun or verb acting prenominally')

jmdict_particle_class = jmdict_parts_of_speech_list.index('particle')
jmdict_numeric_class = jmdict_parts_of_speech_list.index('numeric')



# DO NOT CHANGE THE ORDER
unidic_word_classes = [
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
    '接頭詞',
    'フィラー',  # failure?
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
    return unidic_class_name_strings[unidic_word_classes[class_id]]

# words/characters belonging to these classes are lumped
# as one word with other class members. They aren't saved separately in the unique
# words list but instead are lumped into combined word slot, for examlple
# all sequential alphanumerical characters are saved into LUMPED_ALPHANUM_CHARACTER_INDEX
aux_verb_class = unidic_word_classes.index('助動詞')
alphanum_class = unidic_word_classes.index('alphanum')
non_jp_char_class = unidic_word_classes.index('non_jp_char')
punctuation_mark_class = unidic_word_classes.index('補助記号')
# all classes up to this index are lumped together
lumped_class = punctuation_mark_class

verb_class = unidic_word_classes.index('動詞')
grammatical_particle_class = unidic_word_classes.index('助詞')
interjection_class = unidic_word_classes.index('感動詞')
noun_class = unidic_word_classes.index('名詞')
prefix_class = unidic_word_classes.index('接頭辞')
suffix_class = unidic_word_classes.index('接尾辞')
adjective_class = unidic_word_classes.index('形容詞')
adjectival_noun_class = unidic_word_classes.index('形状詞')
adverb_class = unidic_word_classes.index('副詞')
conjunction_class = unidic_word_classes.index('接続詞')
pronoun_class = unidic_word_classes.index('代名詞')

rentaishi_class = unidic_word_classes.index('連体詞') # その、そんな、そんな、あの、どんな。。

LUMPED_NON_JP_CHARACTER_INDEX = 0
LUMPED_ALPHANUM_CHARACTER_INDEX = 1
LUMPED_AUX_VERB_INDEX = 2
LUMPED_GRAM_PARTICLE_INDEX = 3


allowed_other_class_bindings = {
    jmdict_adjectival_noun_class : [adjectival_noun_class, adjective_class, noun_class],

    jmdict_adverb_class : [adverb_class,
        # 一緒(名詞), に(助詞) /  別(名詞) に(助動詞)　/
        noun_class,grammatical_particle_class, aux_verb_class,
        #  して(動詞) -> どうして
        verb_class,
        # なん(代名詞)
        #pronoun_class,
    ],
    jmdict_conjunction_class : [conjunction_class,
            # 癖(名詞)+ に(助詞)
        noun_class, grammatical_particle_class,
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

    jmdict_suffix_class : [noun_class, suffix_class],

    jmdict_prenominal_class : [rentaishi_class],
    jmdict_particle_class : [grammatical_particle_class],

    jmdict_numeric_class : [noun_class], # 百，万　are noun in Unidic

}

allowed_noun_bindings = [noun_class, prefix_class, suffix_class]
allowed_verb_bindings = [verb_class, adverb_class, aux_verb_class]

explicit_words = [
    (['だ','も','の'],noun_class),
    (['そこ','ら'],noun_class),
    (['だ','けど'],conjunction_class),
    (['でしょ'],verb_class),
    (['それ','に'],conjunction_class),
    (['だれ','か'],pronoun_class),
    (['自分'],pronoun_class),
]

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

# words consisting of these wide characters will be ignored
ignored_full_width_characters = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９％"

# word flags
NO_SCANNING = 1
START_OF_SCAN_DISABLED = 2
MERGE_PARTICLE = 4
DISABLE_ORTHO = 8
PROCESS_AFTER_MERGING = 16
ERROR_VERB_CONJUGATION = 32
