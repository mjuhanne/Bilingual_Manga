from jmdict import * #jmdict_class_list
from dataclasses import dataclass, field

@dataclass
class LexicalItem:
    txt: str
    ortho: str
    classes:list
    flags: int = 0
    replaced_particles:list = field(default_factory=lambda: [])
    conjugation_root:str = ''
    details:list = None
    is_masu = False
    alt_forms: list = field(default_factory=lambda: [])
    # alt forms constructed of non-ortho/basic forms which can accept subsequent items
    appendable_alt_forms: list = field(default_factory=lambda: [])
    end_type_alt_forms: list = field(default_factory=lambda: [])
    non_ending_alt_forms: list = field(default_factory=lambda: [])
    lemma: str = ''
    conj_details:list = field(default_factory=lambda: [])
    word_id: str = ''
    is_conjugated = False
    is_base_form = True
    pron_base: str = ''
    color = None
    any_class = False
    base_score: int = 0
    alt_scores:dict = field(default_factory=lambda: dict())
    alt_form_flags:dict = field(default_factory=lambda: dict())
    end_of_clause = False
    # if this alt form is used then the following item is also scored differently
    neighbour_alt_score_modifier:dict = field(default_factory=lambda: dict())
    inhibit_seq_list: list = field(default_factory=lambda: [])
    alt_orthos: list = field(default_factory=lambda: [])
    is_katakana = False
    is_hiragana = False
    explicitly_allow_conjugation = False
    lemma_hiragana:str = ''

mid_sentence_punctuation_marks = [
    '・',
    'っ',
]
elongation_marks = [
    'ー',
    '～', # full-width tilde
    '〜', # wave dash (YES THEY ARE DIFFERENT!)
]

# DO NOT CHANGE THE ORDER
unidic_class_list = [
    'non_jp_char',
    '補助記号',
    'mid_s_p_m', # mid sentence punctuation mark
    'em', # elongation mark
    'alphabet',
    'numeric',

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
    'stutter',
]

unidic_class_name_strings = {
   'non_jp_char' : "",
    '補助記号' : "punctuation_mark",
    'alphabet' : "",
    'numeric' : "",
    'mid_s_p_m' : "mid_sentence_punctuation_mark",
    'em' : "elongation mark",

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
    "stutter" : "stutter"
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
numeric_pseudoclass = unidic_class_list.index('numeric')
alphabet_pseudoclass = unidic_class_list.index('alphabet')
non_jp_char_pseudoclass = unidic_class_list.index('non_jp_char')
punctuation_mark_class = unidic_class_list.index('補助記号')
mid_sentence_punctuation_mark_class = unidic_class_list.index('mid_s_p_m')
elongation_mark_class = unidic_class_list.index('em')
# all classes up to this index are lumped together
#lumped_class = mid_sentence_punctuation_mark_class
lumped_class = numeric_pseudoclass


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
stutter_class = unidic_class_list.index('stutter')
any_class = -1

# some counter related nouns (か月) are switched into this pseudoclass
counter_pseudoclass = unidic_class_list.index('counter')

expression_class = unidic_class_list.index('expression')

LUMPED_NON_JP_CHARACTER_INDEX = 0
LUMPED_ALPHANUM_CHARACTER_INDEX = 1
LUMPED_AUX_VERB_INDEX = 2
LUMPED_GRAM_PARTICLE_INDEX = 3

class_base_scores = {
    noun_class : 10,
    verb_class : 10,
    adjective_class : 10,
    adjectival_noun_class : 10,
    adverb_class : 10,
    pronoun_class : 10,
    expression_class : 10,

    alphabet_pseudoclass : 1,
    numeric_pseudoclass : 2,
    gp_class : 4,
    aux_verb_class : 3,
    'default' : 8,
}

def get_class_base_score(cl):
    if cl in class_base_scores:
        return class_base_scores[cl]
    return class_base_scores['default']

allowed_other_class_bindings = {
    jmdict_adjectival_noun_class : {adjectival_noun_class:1.0, adjective_class:1.0, noun_class:1.0},

    jmdict_adverb_class : {adverb_class:1.0
                           #adjectival_noun_class
    },
    jmdict_adverb_to_class : {adverb_class:1.0},

    jmdict_conjunction_class : {conjunction_class:1.0},
    jmdict_adj_i_class : {adjective_class:1.0},
    jmdict_adj_ii_class : {adjective_class:1.0},
    jmdict_pronoun_class : {
        pronoun_class:1.0,
         # か(助詞) -> 誰か
        #grammatical_particle_class,
    },

    jmdict_interjection_class : {
        interjection_class:1.0,
        adverb_class:0.9, # some words classified as adverbs work as interjection
    },
    jmdict_adj_pn_class : {rentaishi_class:1.0},
    
    #jmdict_adj_pn_class :  [adverb_class, verb_class] # そういう

    #jmdict_noun_class : [noun_class, prefix_class, suffix_class],

    jmdict_prefix_class : {prefix_class:1.0},
    jmdict_suffix_class : {suffix_class:1.0},
    jmdict_noun_as_suffix_class : {suffix_class:1.0,noun_class:1.0},

    jmdict_prenominal_class : {rentaishi_class:1.0},
    jmdict_particle_class : {grammatical_particle_class:1.0},

    jmdict_numeric_class : {noun_class:1.0, numeric_pseudoclass:1.0}, # 百，万　are noun in Unidic

    jmdict_counter_class : {
         # ３５歳
        suffix_class:1.0, 
        counter_pseudoclass:1.0,
    },

    # this is for volitional ーたい eg (見たい、やりたい)
    jmdict_aux_adj_class : {aux_verb_class:1.0}, 

    jmdict_auxiliary_class : {aux_verb_class:1.0}
}

allowed_noun_bindings = {noun_class:1.0, adjectival_noun_class:1.0} #, prefix_class, suffix_class]
allowed_verb_bindings = {verb_class:1.0, aux_verb_class:1.0} #, adverb_class, ]


# Merge these particles together while forcing the result explicitely 
# to a target class that works well with JMDict
# [ [particle list], [unidic_detected_classes_per_particle], condition, target_unidic_class]
COND_NONE = 0
COND_NOT = 1
COND_BLOCK_START = 2
COND_AFTER_MASU = 4
COND_BEFORE_TE = 8
COND_AFTER_TE = 16
COND_BEFORE_ITEM = 32
COND_AFTER_ITEM = 64
COND_BEFORE_CLASS = 128
COND_AFTER_CLASS = 256
COND_END_OF_CLAUSE = 512
COND_NON_BASE_FORM = 1024
COND_NON_ORIGINAL_FORM = 2048
COND_FLEXIBLE = 4096

condition_text = {
    COND_NON_BASE_FORM : 'non-base-form',
    COND_NON_ORIGINAL_FORM : '!= original form',
    COND_BEFORE_CLASS : 'before class',
    COND_END_OF_CLAUSE : 'end of clause',
}

TASK_MODIFY = 0
TASK_MERGE = 1
TASK_DIVIDE = 2
TASK_REPLACE = 3

# word flags
NO_SCANNING = 1
START_OF_SCAN_DISABLED = 2
MERGE_ITEM = 4
REPLACE_ITEM = 8
REMOVE_ITEM = 16
DISABLE_ORTHO = 32
REPROCESS = 64
ERROR_VERB_CONJUGATION = 128
BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED = 256
SCAN_WITH_LEMMA = 512
ANY_CLASS = 1024

# separate these so conjugations can be detected more easily
pre_conjugation_modifications = [

    # divide the colloquial form to separate particles
    # e.g. 行っ + てく -> 寄っ + て + いく
    [['てく'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['て','く'],'classes':[aux_verb_class,verb_class],'orthos':['','行く'],'alt_forms':['','いく'],'conjugation_roots':['','いく']}],
    [['でく'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['で','く'],'classes':[aux_verb_class,verb_class],'orthos':['','行く'],'conjugation_roots':['','いく']}],
    # e.g. 行 + ってく -> 行 + って + いく
    [['ってく'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['って','く'],'classes':[aux_verb_class,verb_class],'orthos':['','行く'],'conjugation_roots':['','いく']}],
    [['てか'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['て','か'],'classes':[aux_verb_class,verb_class],'orthos':['','行く'],'alt_forms':['',['いか','いく_']],'conjugation_roots':['','いか']}],
    [['ってか'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['って','か'],'classes':[aux_verb_class,verb_class],'orthos':['','行く'],'alt_forms':['',['いか','いく_']],'conjugation_roots':['','いか']}],
    [['てこ'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['て','こ'],'classes':[aux_verb_class,verb_class],'orthos':['','行く'],'alt_forms':['','いく'],'conjugation_roots':['','いく']}],
    [['てこう'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['て','こう'],'classes':[aux_verb_class,verb_class],'orthos':['','行く'],'alt_forms':['',['いこう','いく']],'conjugation_roots':['','いく']}],

    [['て','った'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['て','','った'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','行く',''],'alt_forms':['','',''],'conjugation_roots':['','いく','']}],

    # 置いてっちゃう -> 置い + て + 行っちゃう
    [['て','っちゃう'],[aux_verb_class, aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['て','','っちゃう'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','行く',''],'alt_forms':['て',['い','いく'],'']}],

    # colloquial for (te-ru)
    [['てる'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['て','る'],'classes':[aux_verb_class,verb_class],'orthos':['','いる'],'alt_forms':['','いる'],'conjugation_roots':['','いる']}],
    [['ってる'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['って','る'],'classes':[aux_verb_class,verb_class],'orthos':['','いる'],'alt_forms':['','いる'],'conjugation_roots':['','いる']}],
    # て + いれば
    [['てりゃ'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['て','りゃ'],'classes':[aux_verb_class,verb_class],'orthos':['','いる'],'alt_forms':['','いれば'],'conjugation_roots':['','いる']}],
    [['ってりゃ'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['って','りゃ'],'classes':[aux_verb_class,verb_class],'orthos':['','いる'],'alt_forms':['','いれば'],'conjugation_roots':['','いる']}],

    # wakattoru = wakatte-iru
    [['っとる'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['っと','る'],'classes':[aux_verb_class,verb_class],'orthos':['','いる'],'alt_forms':['って','いる'],'conjugation_roots':['','いる']}],
    # しとる -> している
    [['し','とる'],[aux_verb_class, verb_class],COND_NONE,TASK_DIVIDE,{'parts':['し','と','る'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['する','','いる'],'alt_forms':['','て','いる'],'word_id':['1157170:する','','']}],
    [['し','とる'],[verb_class, aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['し','と','る'],'classes':[verb_class,verb_class,aux_verb_class],'orthos':['する','','いる'],'alt_forms':['','て','いる'],'word_id':['1157170:する','','']}],
    [['って','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'orthos':['','いる'],'alt_forms':['','いた'],'conjugation_roots':['','いる']}],

    # 言っとった -> 言 + って + お + った
    [['っと','った'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['っと','','った'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','おる',''],'alt_forms':['って','お',''],'conjugation_roots':['','おる','']}],


    # っつって　= と言って
    [['っつ','って'],[aux_verb_class,gp_class],COND_NONE,TASK_REPLACE,{'parts':['っ','つ','って'],'classes':[aux_verb_class,verb_class,gp_class],'orthos':['','言う',''],'alt_forms':['と','言','って'],'conjugation_roots':['','言う','']}],
    # つった　= と言った
    [['つ','った'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['つ','','った'],'classes':[gp_class,verb_class,aux_verb_class],'orthos':['','言う',''],'alt_forms':['と','言','った'],'conjugation_roots':['','言う','']}],


    # -tte oranai
    [['っとら','ん'],[aux_verb_class, any_class],COND_NONE,TASK_REPLACE,{'parts':['っと','ら','ん'],'classes':[aux_verb_class,aux_verb_class,aux_verb_class],'orthos':['','おる','ない'],'alt_forms':['って','おら','ない']}],
    [['っと','らん'],[gp_class, any_class],COND_NONE,TASK_REPLACE,{'parts':['っと','ら','ん'],'classes':[aux_verb_class,aux_verb_class,aux_verb_class],'orthos':['','おる','ない'],'alt_forms':['って','おら','ない']}],
    [['ってろ'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['って','ろ'],'classes':[aux_verb_class,aux_verb_class]}],    

    # 言っとん -> 言っているん
    [['っと','ん'],[aux_verb_class, gp_class],COND_NONE,TASK_REPLACE,{'parts':['っと','','ん'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','いる',''],'alt_forms':['って','いる','']}],
    # 思っとん -> 思っているん
    [['っとん'],[aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['っと','','ん'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','いる',''],'alt_forms':['って','いる','']}],

    # 頼まれとったん -> 頼まれ + て + おったん
    # ?? needed
    #[['と','った'],[verb_class, aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['と','','った'],'classes':[verb_class,verb_class,aux_verb_class],'orthos':['とる','おる',''],'alt_forms':['て','お','']}],

    
    [['ってらっしゃる'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['って','らっしゃる'],'classes':[aux_verb_class,verb_class],'orthos':['','おらっしゃる'],'alt_forms':['って','']}],
    
    # wakatte-n
    [['てん'],[aux_verb_class],COND_AFTER_MASU,TASK_DIVIDE,{'parts':['て','','ん'],'classes':[aux_verb_class,aux_verb_class,aux_verb_class],'orthos':['','いる',''],'alt_forms':['','いる','']}],
    # やってん
    [['ってん'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['って','','ん'],'classes':[aux_verb_class,aux_verb_class,aux_verb_class],'orthos':['','いる',''],'alt_forms':['','いる','']}],

    # -tte oku (do something ahead)
    # # e.g. いっとく -> い　+　って + おく
    [['っとく'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['っと','く'],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['って',''],'conjugation_roots':['','おく']}],
    # しとく -> し　+　て + おく
    [['とく'],[aux_verb_class],COND_AFTER_MASU,TASK_DIVIDE,{'parts':['と','く'],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['て',''],'conjugation_roots':['','おく']}],
    # # e.g. いっといて -> い　+　って + おいて
    [['っとい','て'],[aux_verb_class,gp_class],COND_NONE,TASK_REPLACE,{'parts':['っと','い','て'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','おく',''],'alt_forms':['って','お','いて'],'conjugation_roots':['','おく','']}],
    # 頼ん + ど + い + て + くれ -> 頼んで + おいて + くれ
    [['ど','い','て'],[gp_class,verb_class,gp_class],COND_NONE,TASK_MODIFY,{'orthos':['','おく',''],'alt_forms':['で','おい','て'],'conjugation_roots':['','おく','']}],
    # 置い + ときます -> 置い + て　+ き + ます 
    [['とき'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['とき',''],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['て','おき'],'conjugation_roots':['','おく']}],
    # ほっときなさい -> ほ + って　+ き + なさい 
    [['っとき'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['っとき',''],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['って','おき'],'conjugation_roots':['','おく']}],
    # し + とか + ない  -> し + て + おか + ない
    [['とか'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['と','か'],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['て','おか'],'conjugation_roots':['','おく']}],
    [['っとか'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['っと','か'],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['って','おか'],'conjugation_roots':['','おく']}],
    # チェックしとけよ -> て + おけ + よ
    [['とけ'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['と','け'],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['て','おけ'],'conjugation_roots':['','おけ']}],
    # 言っとけよ -> て + おけ + よ
    [['っとけ'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['っと','け'],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['って','おけ'],'conjugation_roots':['','おけ']}],
    [['っとけよ'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['っと','け','よ'],'classes':[aux_verb_class,verb_class,gp_class],'orthos':['','おく',''],'alt_forms':['って','おけ',''],'conjugation_roots':['','おけ','']}],
    # # e.g. つけといた -> + つけ + て　+ おい + た
    [['とい','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['と','','いた'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','おく',''],'alt_forms':['て','お','いた'],'conjugation_roots':['','おく','']}],
    [['っとい','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['っと','','いた'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','おく',''],'alt_forms':['って','お','いた'],'conjugation_roots':['','おく','']}],
    [['とい','て'],[aux_verb_class,gp_class],COND_NONE,TASK_REPLACE,{'parts':['と','','いて'],'classes':[aux_verb_class,verb_class,aux_verb_class],'orthos':['','おく',''],'alt_forms':['て','お','いて'],'conjugation_roots':['','おく','']}],
    # 買 + っとこう -> 買 + って + おこう
    [['っとこう'],[aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['っと','こう'],'classes':[aux_verb_class,verb_class],'orthos':['','おく'],'alt_forms':['って','おこう'],'conjugation_roots':['','おく']}],

    [['ど','った'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'classes':[aux_verb_class,verb_class],'orthos':['','いる'],'alt_forms':['で','いた'],'conjugation_roots':['','いる']}],
    [['て','れ','ば'],[gp_class,aux_verb_class,gp_class],COND_NONE,TASK_MODIFY,{'classes':[gp_class,verb_class,verb_class],'orthos':['','いる',''],'alt_forms':['て','いれ','ば'],'conjugation_roots':['','いる','']}],
    [['たがら'],[aux_verb_class],COND_AFTER_MASU,TASK_DIVIDE,{'parts':['たが','ら'],'classes':[aux_verb_class,aux_verb_class],'orthos':['たがる','']}],

    [['ったって'],[gp_class],COND_NONE,TASK_DIVIDE,{'parts':['った','って'],'classes':[gp_class,gp_class],'orthos':['','']}],
    [['たって'],[gp_class],COND_NONE,TASK_DIVIDE,{'parts':['た','って'],'classes':[gp_class,gp_class],'orthos':['','']}],

    # 生き + てけ + ない -> 生きて + いけ　+ ない
    [['てけ'],[aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['て','け'],'classes':[aux_verb_class,verb_class],'orthos':['','いく'],'alt_forms':['','いけ'],'conjugation_roots':['','いく']}],

    # でてる
    [['で','てる'],[gp_class,any_class],COND_NONE,TASK_REPLACE,{'parts':['で','て','る'],'classes':[verb_class,aux_verb_class,aux_verb_class],'orthos':['でる','',''],'alt_forms':['','','いる'],'conjugation_roots':['でる','',''],'word_id':['1338240:でる','','']}],


    # still needed?
    #[['たか'],[aux_verb_class],COND_AFTER_MASU,TASK_DIVIDE,{'parts':['た','か'],'classes':[aux_verb_class,aux_verb_class],'orthos':['','']}],
    #[['たら'],[aux_verb_class],COND_AFTER_MASU,TASK_DIVIDE,{'parts':['た','ら'],'classes':[aux_verb_class,aux_verb_class],'orthos':['','']}],
    #[['ったら'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['った','ら'],'classes':[aux_verb_class,aux_verb_class],'orthos':['','']}],
    #[['たり'],[gp_class],COND_AFTER_MASU,TASK_DIVIDE,{'parts':['た','り'],'classes':[aux_verb_class,aux_verb_class],'orthos':['','']}],
    #[['ったり'],[gp_class],COND_NONE,TASK_DIVIDE,{'parts':['った','り'],'classes':[aux_verb_class,aux_verb_class],'orthos':['','']}],
    #[['だり'],[gp_class],COND_NONE,TASK_DIVIDE,{'parts':['だ','り'],'classes':[gp_class,gp_class],'orthos':['','']}],
    #[['せよう'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['せ','よう'],'classes':[aux_verb_class,aux_verb_class],'orthos':['','']}],

    [['っちゃおっ'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['っちゃ','おっ'],'classes':[aux_verb_class,aux_verb_class],'orthos':['ちゃう','']}],
    [['ちゃおう'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['ちゃ','おう'],'classes':[aux_verb_class,aux_verb_class],'orthos':['ちゃう','']}],
    [['なか'],[aux_verb_class],COND_AFTER_TE,TASK_DIVIDE,{'parts':['な','か'],'classes':[verb_class,aux_verb_class],'alt_forms':['いな','か'],'orthos':['いる','']}],
    [['たく'],[aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['た','く'],'classes':[aux_verb_class,aux_verb_class],'orthos':['たい','']}],

    [['そう'],[noun_class],COND_AFTER_CLASS,TASK_MODIFY,{'cond_class':aux_verb_class,'class':gp_class,'ortho':''}],


    # special short verb cases
    # もむ
    [['もん','だり'],[noun_class,gp_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,gp_class],'orthos':['もむ','']}],
    [['やん','だり'],[verb_class,gp_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,gp_class],'orthos':['やむ','']}],
    # いむ / 忌む
    [['い','ん','だ'],[verb_class,gp_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,gp_class,aux_verb_class],'orthos':['いむ','','']}],
    [['洗い'],[verb_class],COND_NONE,TASK_MODIFY,{'ortho':'洗う'}],
    [['追い出'],[verb_class],COND_NONE,TASK_MODIFY,{'ortho':'追い出す'}],
    [['しな'],[suffix_class],COND_END_OF_CLAUSE,TASK_MODIFY,{'classes':[verb_class],'orthos':['する']}],
    [['なれ'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class],'orthos':['なる']}],
    [['ま','てェ'],[aux_verb_class,gp_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,gp_class],'orthos':['待つ',''],'alt_forms':['','って']}],
    [['どかん'],[adverb_class],COND_NONE,TASK_DIVIDE,{'parts':['どか','ん'],'classes':[verb_class,aux_verb_class],'orthos':['どく','ない']}],
    [['出','てこ'],[verb_class, aux_verb_class],COND_NONE,TASK_DIVIDE,{'parts':['出','て','こ'],'classes':[verb_class,aux_verb_class,verb_class],'orthos':['出る','','来る']}],
    [['じゃ'],[aux_verb_class],COND_AFTER_CLASS,TASK_MODIFY,{'cond_class':noun_class,'classes':[verb_class]}],
    [['で','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,aux_verb_class],'orthos':['でる','']}],
    [['や','れる'],[gp_class, aux_verb_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,aux_verb_class],'orthos':['やる','']}],
 

    # まって! at the start of a block is not correctly identified
    [['ま','って'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_MODIFY,{'classes':[verb_class,aux_verb_class],'orthos':['まつ','']}],
    [['ま','て'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_MODIFY,{'classes':[verb_class,aux_verb_class],'orthos':['まつ',''],'alt_forms':['','って']}],
    [['でしょう'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'add_class':verb_class,'ortho':'だ'}],
    [['でしょ'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'add_class':verb_class,'ortho':'だ'}],
    [['でし','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':verb_class,'root_ortho':'だ'}],
    [['し','た'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,aux_verb_class],'orthos':['する','']}],
    [['だ','った'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,aux_verb_class],'orthos':['だ','']}],
    [['でき'],[aux_verb_class,aux_verb_class],COND_BLOCK_START,TASK_MODIFY,{'class':verb_class,'ortho':'できる'}],

    [['お','いでよ'],[prefix_class, any_class],COND_NONE,TASK_REPLACE,{'parts':['おいで','よ'],'classes':[verb_class,gp_class],'orthos':['','おいで']}],
    [['つん','でき'],[adverb_class, verb_class],COND_NONE,TASK_REPLACE,{'parts':['つんで','き'],'classes':[verb_class,verb_class],'orthos':['つむ','くる'],'word_id':['','1547720:くる']}],


    # 信じらん -> 信じられない
    [['ら','ン'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'alt_forms':['','れ']}],
    [['ら','ん'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'alt_forms':['','れ']}],

    # とられちゃう (add verb class)
    [['とら','れ'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MODIFY,{'classes':[verb_class,aux_verb_class]}],

    [['やろー'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'orthos':['やる']}],
    [['やろう'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'orthos':['やる']}],

    [['放','ったら','か'],[verb_class, aux_verb_class, gp_class],COND_NONE,TASK_MODIFY,{'orthos':['放ったらかす','','']}],
]


explicit_word_changes = [

    #nouns
    [['そこ','ら'],[pronoun_class,suffix_class],COND_NONE,TASK_MERGE,{'class':noun_class}],
    [['タ','オル'],[aux_verb_class,noun_class],COND_NONE,TASK_MERGE,{'class':noun_class,'ortho':'','alt':''}],
    [['Ｔ','シャツ'],[alphabet_pseudoclass,noun_class],COND_NONE,TASK_MERGE,{'class':noun_class}],
    [['ま','っか','な'],[aux_verb_class,gp_class,gp_class],COND_NONE,TASK_REPLACE,{'parts':['まっか','な'],'classes':[adjectival_noun_class,gp_class]}],
    # heli(copter) with hiragana he
    [['へ','リ'],[gp_class,noun_class],COND_NONE,TASK_MERGE,{'alt':'ヘリ','alt_score':12,'class':noun_class}],

    # verbs
    [['だ','も','の'],[aux_verb_class,gp_class,gp_class],COND_NONE,TASK_MERGE,{'class':verb_class}],

    # adjectives
    [['らしい'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'add_class':adjective_class}],
    [['や','ばい'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adjective_class}],
    [['な','い'],[aux_verb_class,interjection_class],COND_NONE,TASK_MERGE,{'class':adjective_class}],
    [['お','しい'],[prefix_class,verb_class],COND_NONE,TASK_MERGE,{'class':adjective_class}],
    [['くだら','ん'],[verb_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adjective_class}],
    [['や','べ'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_MERGE,{'class':adjective_class}],
    [['へー','き'],[interjection_class,any_class],COND_NONE,TASK_MERGE,{'class':adjective_class,'alt_forms':['へい','']}],

    # disable scan start from よく so that it よくある / よくなる won't be detected
    # e.g. いつもよりかっこよくあらへん？
    [['かっこ','よく'],[noun_class,adjective_class],COND_NONE,TASK_MODIFY,{'add_flags':[0,START_OF_SCAN_DISABLED]}],
    # e.g. 気持ちよくなってきた
    [['気持ち','よく'],[noun_class,adjective_class],COND_NONE,TASK_MODIFY,{'add_flags':[0,START_OF_SCAN_DISABLED]}],
    # disable scan start from いい so that it いいって言われて won't be detected
    # かっこいいって言われてたね
    [['かっこ','いい'],[noun_class,adjective_class],COND_NONE,TASK_MODIFY,{'add_flags':[0,START_OF_SCAN_DISABLED]}],
    [['かっこう','いい'],[noun_class,adjective_class],COND_NONE,TASK_MODIFY,{'add_flags':[0,START_OF_SCAN_DISABLED]}],
    [['気持ち','いい'],[noun_class,adjective_class],COND_NONE,TASK_MODIFY,{'add_flags':[0,START_OF_SCAN_DISABLED]}],

    # conjunctions
    [['だ','から'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class,'ortho':''}], 
    [['だ','けど'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class,'ortho':''}],
    [['しか','も'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':conjunction_class,'ortho':''}],

    # それに works as conjunction as long as it's not before verb 
    # (in that case に most likely is a solo particle)
    [['それ','に'],[pronoun_class,gp_class],COND_NOT|COND_BEFORE_CLASS,TASK_MERGE,{'cond_class':verb_class,'class':conjunction_class}],


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
    [['じゃ'],[gp_class],COND_NONE,TASK_MODIFY,{'add_class':conjunction_class}],
    # clear the っつう ortho of って
    [['って'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'add_class':conjunction_class,'ortho':''}],

    # で at the start of the sentence is always 'and then/so'
    #[['で'],[aux_verb_class],COND_BLOCK_START,TASK_MODIFY,{'class':conjunction_class,'ortho':'','word_id':'2028980/3:で'}],

    # pronouns
    [['自分'],[noun_class],COND_NONE,TASK_MODIFY,{'add_class':pronoun_class}],
    [['あん','たら'],[verb_class,aux_verb_class],COND_NONE,TASK_REPLACE,{'parts':['あんた','ら'],'classes':[pronoun_class,suffix_class]}],

    [['な','ん','だ','か'],[aux_verb_class,gp_class,aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['な','ん','だ','けど'],[aux_verb_class,gp_class,aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'parts':['なん','だけど'],'classes':[pronoun_class,conjunction_class],'orthos':['','']}],
    [['なん','だ','か'],[pronoun_class,aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['な','に'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_REPLACE,{'parts':['なに'],'classes':[pronoun_class]}],

    # interjection
    [['ごめん'],[noun_class],COND_NONE,TASK_MODIFY,{'add_class':interjection_class}],
    [['さあ'],[gp_class],COND_NONE,TASK_MODIFY,{'add_class':interjection_class}],
    [['な','ん','だ'],[aux_verb_class,gp_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':interjection_class,'ortho':''}],
    [['なあん','だ'],[pronoun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':interjection_class,'ortho':''}],
    [['や','だ'],[aux_verb_class,aux_verb_class],COND_BLOCK_START,TASK_MERGE,{'class':interjection_class}],
    [['や','だ'],[adjectival_noun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],
    [['そっ','か'],[pronoun_class,gp_class],COND_BLOCK_START,TASK_MERGE,{'class':interjection_class}],
    [['ん'],[aux_verb_class],COND_BLOCK_START,TASK_MODIFY,{'add_class':interjection_class,'ortho':''}],
    [['い','えっ'],[interjection_class,interjection_class],COND_BLOCK_START,TASK_MERGE,{'class':interjection_class}],
    [['おは','よ'],[interjection_class,gp_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],
    [['お','やおや'],[prefix_class,noun_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],
    [['よう','こそ'],[adjective_class,gp_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],
    [['おほ','ん'],[interjection_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],
    [['うっ','せー'],[interjection_class,verb_class],COND_NONE,TASK_MERGE,{'class':interjection_class}],
    [['さ'],[suffix_class],COND_END_OF_CLAUSE,TASK_MODIFY,{'add_class':interjection_class}],

    # force ねえ to interjection only at the beginning of of block (otherwise it could be ない)
    [['ねえ'],[aux_verb_class],COND_BLOCK_START,TASK_MODIFY,{'add_class':interjection_class}],

    # adverbs
    #(['もし','も'],[adverb_class,gp_class],adverb_class,COND_NONE,TASK_MODIFY),
    [['な','ん','で'],[aux_verb_class,gp_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adverb_class,'ortho':''}],
    [['な','ん'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['なん','で'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['なる','ほど'],[verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['なる','ほど'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['ほど'],[gp_class],COND_NONE,TASK_MODIFY,{'add_class':adverb_class}],
    [['いつ','で','も'],[pronoun_class,gp_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['いつ','も'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['二人','と','も'],[noun_class,gp_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['ず','っと'],[aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class,'ortho':''}],
    [['この','前'],[rentaishi_class,noun_class],COND_NONE,TASK_MERGE,{'class':adverb_class,'ortho':''}],
    [['断じ','て'],[verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class,'ortho':''}],
    [['まさ','か'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_MERGE,{'class':adverb_class}],
    [['こん','だけ'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['どこ','か'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['どっ','か'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['どんな','に'],[adjectival_noun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['割','と'],[noun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['た','った'],[aux_verb_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['いつ','か'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['本気','で'],[noun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['何','やら'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['どう','に','か'],[adverb_class,gp_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['なん','か'],[pronoun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['何','ン','か'],[pronoun_class,gp_class,gp_class],COND_NONE,TASK_MERGE,{'class_list':[adverb_class,pronoun_class,interjection_class],'ortho':''}],
    [['な','ん','て'],[aux_verb_class,aux_verb_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['いく','つ'],[noun_class,suffix_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['要','は'],[noun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['今','や'],[noun_class,gp_class],COND_NONE,TASK_MERGE,{'class':adverb_class}],
    [['ま'],[aux_verb_class],COND_BLOCK_START|COND_END_OF_CLAUSE,TASK_MODIFY,{'class':adverb_class}],
    [['な','ぜ'],[aux_verb_class,gp_class],COND_BLOCK_START,TASK_MERGE,{'class':adverb_class}],

    # auxiliary
    # remove だ ortho from なら and で
    [['なら'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'ortho':''}],
    [['で'],[aux_verb_class],COND_NONE,TASK_MODIFY,{'ortho':''}],


    # rentaishi_class.  (あなたの)ような..
    [['よう','な'],[adjectival_noun_class,aux_verb_class],COND_NONE,TASK_MERGE,{'class':rentaishi_class}],
    [['そー','ゆー'],[adverb_class,noun_class],COND_NONE,TASK_MERGE,{'class':rentaishi_class}],
    [['そー','ゆー'],[adverb_class,interjection_class],COND_NONE,TASK_MERGE,{'class':rentaishi_class}],
    [['どう','いう'],[adverb_class,interjection_class],COND_NONE,TASK_MERGE,{'class':rentaishi_class}],
    
    # expressions
    #[['そっ','かー'],[adverb_class,gp_class],COND_NONE,TASK_MERGE,{'class':expression_class,'ortho':''}],
    # stupid unidic thinks this is 気に行ってる. Force it to 入る
    [['気','に','い','って','る'],[noun_class,gp_class,verb_class,aux_verb_class,verb_class],COND_NONE,TASK_MODIFY,{'orthos':['','','入る','','']}],
    [['往'],[verb_class],COND_NONE,TASK_MODIFY,{'orthos':['往く']}],
    [['思い巡ら'],[verb_class],COND_NONE,TASK_MODIFY,{'orthos':['思い巡らす']}],


    # suffix
    [['ど','も'],[noun_class,gp_class],COND_AFTER_CLASS,TASK_MERGE,{'cond_class':noun_class,'class':suffix_class}],

    # particles
    [['ぞ','い'],[gp_class,interjection_class],COND_END_OF_CLAUSE,TASK_MERGE,{'class':gp_class}],
    # TODO
    #[['な'],[aux_verb_class],COND_BLOCK_START,TASK_MODIFY,{'class':gp_class}],

    # separate incorrectly merged items
    [['文部'],[noun_class],COND_NONE,TASK_DIVIDE,{'parts':['文','部']}],
    [['内また'],[noun_class],COND_NONE,TASK_DIVIDE,{'parts':['内','また'],'classes':[noun_class,conjunction_class]}],
    [['やっとな'],[interjection_class],COND_NONE,TASK_DIVIDE,{'parts':['やっと','な'],'classes':[adverb_class,gp_class]}],
    [['ま','たもと'],[interjection_class,noun_class],COND_NONE,TASK_REPLACE,{'parts':['また','もと'],'classes':[adverb_class,noun_class]}],
    [['ま','じと'],[interjection_class,adverb_class],COND_NONE,TASK_REPLACE,{'parts':['まじ','と'],'classes':[noun_class,gp_class]}],

    # colloquial terms
    [['ど','っから'],[aux_verb_class,gp_class],COND_NONE,TASK_MODIFY,{'alt_forms':['どこ','から'],'classes':[pronoun_class,gp_class]}],


    # series specific bindings
    [['けー','たろ'],[interjection_class,aux_verb_class],COND_NONE,TASK_MERGE,{'alt':'景太郎','class':noun_class}],
    [['けー','くん'],[interjection_class,adverb_class],COND_NONE,TASK_MERGE,{'alt':'景太郎','class':noun_class}],

    [['ンな'],[rentaishi_class],COND_NONE,TASK_DIVIDE,{'parts':['ン','な'],'alt_forms':['ん',''],'classes':[noun_class,interjection_class]}],
    
    [['と','はい','わん'],[gp_class,interjection_class,adverb_class],COND_NONE,TASK_REPLACE,{'parts':['と','は','いわん'],'classes':[gp_class,gp_class,verb_class],'orthos':['','','言う'],'alt_forms':['','','言わない'],'conjugation_roots':['','','言う']}],

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
    'っつ' : [conjunction_class],
    'なんて' : [interjection_class],
    'よし' : [interjection_class],
    'ずつ' : [suffix_class],
    'あら' : [interjection_class],
    'べ' : [aux_verb_class],

    # Pre-noun Adjectivals, detected originally as adjectival nouns
    'そんな' : [rentaishi_class],
    'こんな' : [rentaishi_class],

    'こんなに' : [adverb_class],

    # originally verbs
    'つれない' : [adjective_class],
    '下らない' : [adjective_class],
    'らしい' : [adjective_class],

    'なん' : [pronoun_class],

    # we put this explicitely here because don't want to allow all nouns to be possible counters
    'か月' : [counter_pseudoclass], 
    'ヶ月' : [counter_pseudoclass], 


    'そっくり' : [adverb_class], # originally adjectival noun

    'や' : [gp_class],
    'って' : [gp_class],

    '議' : [noun_class],
    'ブス' : [noun_class],
    'に' : [gp_class],
    'めったに' : [adverb_class],
    'いー' : [adjective_class],
    
}
alternative_forms = {
    'っちゃん' : ['ちゃん'],
    #'いえっ' : ['いえ'],
    #'そっかー' : ['そうか'],
    'ねー' : ['ない','ねえ'],
    'いねー' : ['いない'],
    'でしょ' : ['でしょう'],
    '何ンか' : ['何か'],
    '建て物' : ['建物'],
    'とォ' : ['と'],
    'ゆー' : ['いう'],
    'かァ' : ['か'],
    'せー' : ['さい'],
    'ちぇー' : ['ちゃい'],
    'やべ' : ['やばい'],
    'ヤダ':['いや'],
    'カ' : ['力'] # katakana ka -> chikara
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

word_id_score_adjustment = {
    '1313580:こと' : 100,
    '1343100:とこ' : 30,
    '2607690:よし' : 20,
    '2091550:しとく' : 20,
    '1610040:せい' : 10,
    '1578150:この' : -20,
    '2607690:よーし' : 200,
    '1382450:石' : -20,
    '1582710:日本': 100,
    '1605840:よう' : 10,
    '1538330:わけ' : 10,
    '1499730:ふう' : 5,
    '1247310:君達' : 60,
    '1315130:字' : 5,
    '1578850:いく' : 130,
    '1327770:手首' : 10,
    '1440260:天文' : 50,
    '1415610:卓球' : 50,
    '1316300:時代' : 100,
    '2153760/0:者' : 80,
    '1256490:兼' : 80,
    '1006870:その実' : 200,
    '2840247:みたく' : 250,
    '2396190:それと' : 550,
    '1404730:足らず' : 150,
    '2141560:何よりも' : 50,
    '1375610:なる' : 20,
    '1430230:ちょうだい' : 50,
    '2600500:そのへん' : 300,
    '1288950:今にも' : 350,
    '2662220:そうとも' : 650,


    # lower priority for these hiragana words that get mixed up 
    '1309910:してい' : -100,
    '1312070/0:してい' : -100,
    '1433050:つうか' : -70,
    '1433070:つうか' : -20,
    '1559280:連れて' : -100,
    #'1402900:そうなん' : -200,
    '2833849:おった' : -50,
    '1609500:かかる' : -30,
    '2849135:本に' : -400, # hard to distinguish from 本 + に
    '2843516:し' : -150,
    '2453440:いいかも' : -1000,
    '1208240:かっこ' : -50,
    '5123359:ひとつだけ' : -800,
    '1398200:そうに' : -200,
    '1328650:ことに' : -500,
    '1314700:にかよう' : -200,

    '1459400:ないよう' : -300,
    '1459440:ないよう' : -300,
    #'2005400:だったん' : -50,
    #'1596400:そうじゃ' : -200,
    #'2851654:もんじゃ' : -150,
    #'1461020:なんだい' : -400,
    #'1301230:さんなん' : -200,
    '1280630:こうなん' : -100,
    '1012500:若し' : -10,
    '1466930:若し' : -10,
    '1368800:人中' : -50,
    '1916880:郎君' : -700,

    # confusing jmnedict entries
    '5360828:でした' : -100,
    '5003643:その実' : -100,
    '5683386:ありません' : -200,
    '5617979:ふっつ' : -50,
    '5003641:その子' : -100,
    '5575123:なんだろう' : -300,
    '5505827:になるだけ' : -1000,
    '5580634:日後' : -100,
    '5345109:じゃあな' : -800,
    '5585267:年春' : -100,
    '5585264:年秋' : -100,
    '5430895:これた' : -200,
    '5663916:明日雪' : -200,
    '5167190:家の前' : -700,
    '5002512:ことな' : -200,
    '5003637:その絵' : -100,
    '5661634:なにし' : -500,
    '5160456:したもん' : -300,
    '2850132:したもの' : -550,
    '5571883:ないもん' : -100,
    '2774840:いたい' : -150,
    '1493770:ふたつ' : -10,
    '5132791:はしません' : -1000,
    '5682011:あります' : -1000,

    # emphasize these jmndict entries
    '5555810:東大' : 50,
    '5322427:山手線' : 50,
    '5407287:新宿': 50,

    # gets confused with 外 + に
    '1203280:外に': -400,
}

word_score_adjustment = {
    'きすぎ' : -300,
    'にいこ' : -300,
    'にいこう': -300,
    'そのこ' : -300,
    'いたがき' : -300,
    'きたみ' :-300,
}

word_id_score_adjustment_with_conditions = {
    '1529560:なし' : [[100,COND_AFTER_CLASS,{'cond_class':noun_class}]],
    '1632520:ふん' : [[100,COND_BLOCK_START]],
    '1011710:ほれ' : [[200,COND_BLOCK_START]],
    '1547720:くる' : [[300,COND_AFTER_TE]],
    '1421850:おく' : [[200,COND_AFTER_TE]],
    '1587040:いう' : [[400,COND_AFTER_ITEM,{'item_txt':'って','item_class':gp_class}]],
    '2016410:みたい' : [
        [100,COND_BEFORE_ITEM|COND_FLEXIBLE,{'item_txt':'に','item_class':any_class}],
        [100,COND_BEFORE_ITEM|COND_FLEXIBLE,{'item_txt':'な','item_class':any_class}]
    ],
    '2084840:年' : [[50,COND_AFTER_CLASS,{'cond_class':numeric_pseudoclass}]],
    '2029110/3:な' : [[10,COND_BLOCK_START]],
    '2029120/2:さ' : [[50,COND_END_OF_CLAUSE]],
    '2262080:たまる' : [[100,COND_AFTER_TE]],
    '2027910:つつある' : [[500,COND_AFTER_MASU]],
}

inhibit_seq_pattern_list = [
    ['いったん',verb_class,['だ','で'],[1164650,1164660,1587500,2842983]]
]

word_id_whitelist = [
    '1005600:しまった',
    '1002800:かしら',
    '1577915:かたき',
    '1000590:あんな',
    '1981450:あんなに',

    # allow these kanji+particle combos (which are usually blocked)
    '1448940:当の',
    '1611020:何で',
    '1853530:真の',
    '1524990:又は',
    '1587590:今迄',
]

seq_whitelist = [
    int(wid.split(':')[0]) for wid in word_id_whitelist
]

word_id_blacklist_with_conditions = {
    '1394680:そう言う' : [[COND_NON_BASE_FORM]],
    '1004320:こう言う' : [[COND_NON_BASE_FORM]],
    '2136910:にして' : [[COND_NON_ORIGINAL_FORM]],
    '1009550:に置いて' : [[COND_BEFORE_CLASS,{'cond_class':verb_class}]],
    '1643550:おいて' : [[COND_BEFORE_CLASS,{'cond_class':verb_class}]],
    '1009780:について' : [[COND_BEFORE_CLASS,{'cond_class':verb_class}]],
    '2630530:に従って' : [[COND_BEFORE_CLASS,{'cond_class':verb_class}]],
    '1215400:まじか' : [[COND_END_OF_CLAUSE]],
    '2028970:か' : [[COND_BLOCK_START]],
    '2029040:ば' : [[COND_BLOCK_START]],
    '2160680:方がいい' : [[COND_AFTER_MASU]], # ほうがいい gets mixed up with e.g. 考え方がいい
    '1155020:もって' : [[COND_BEFORE_TE]],
    '2083340:やろう' : [[COND_AFTER_TE]],
    '2222870:へん' : [[COND_BLOCK_START]],
    '1512070:へん' : [[COND_BLOCK_START]],
    '1880760:したのかい' : [[COND_END_OF_CLAUSE]],

    '1598780:とって' : [[COND_BLOCK_START]],
    '2248980:いた' : [[COND_BEFORE_ITEM,{'item_txt':'こと','item_class':any_class}]],
    '1007660:ちゃん' : [[COND_BLOCK_START]],
    '2008640:そう言った' : [[COND_END_OF_CLAUSE]],
}
seq_blacklist_with_conditions = {
    int(wid.split(':')[0]):cond for wid,cond in word_id_blacklist_with_conditions.items()
}

word_id_whitelist_with_conditions = {
    '1632520/0:ふん' : [[COND_BLOCK_START]],
}


high_frequency_word_id_blacklist = [
    '1007720:ちゃんと', # todo
    '1401490:そうかい',
    '1299940:さんかい',
    '1402900:そうなん',
    '1188650:なんかい',
    '1461020:なんだい',
    '1534050:もうしょ',
    '1279820:こうない',
    '1596400:そうじゃ',
]

high_frequency_seq_blacklist = [
    int(wid.split(':')[0]) for wid in high_frequency_word_id_blacklist
]

low_frequency_word_id_whitelist = [
    '1982310:どうにも',
    '1454270:どうりで',
    '2833978:みたいだ',
    '1984790:うそつけ',
    '1219990:いくらか',
    '1205770:たしかに',
    '1006990:それだけ',
    '2663180:いまから',
    '2143050:たりない',
    '2847848:あれきり',
    '1288920:いまでも',
    '1188870:いつまで',
    '2206500:どっちか',
    '1189040:どこまで',
    '1009080:どこでも',
    '1984400:じゃーん',
    '2084310:おそろい',
    '2272480:どうした',
    '2008160:これだけ',
    '2763130:なぜだか',
    '2009220:どころか',
    '2158990:いいとこ',
    '2007850:くすくす',
    '2186610:じゃーね',
    '1383760:きっての',
    '2206500:どちらか',
    '2840820:でしたら',
    '1255480:つきかげ',
    '1188810:いつしか',
    '2838041:おかたい',
    '1868140:がきども',
    '2136210:あるべき',
    '2007630:かくして',
    '2170880:どこへも',
    '2244400:なんなら',
    '1007030:それなり',
    '1577160:どれほど',
    '2855265:そやけど',
    '2852555:やめとき',
    '2097300:そのくせ',
    '2024710:あかずの',
    '1589270:おとひめ',
    '2835691:くせして',
    '1288800:これほど',
    '2846266:おたずね',
    '2719260:ふんふん',
    '1478030:ばっとう',
    '2839522:あんだけ',
    '2132060:いいとも',
    '2016850:おいとま',
    '1012270:まんまと',
    '2744410:どうでも',
    '2749120:いくらも',
    '1982200:それこそ',
    '1835720:いいきみ',
    '1188600:いずれも',
    '1310890:しにがみ',
    '2264440:なくして',
    '2083770:あんさん',
    '2839522:あんだけ',
]

low_frequency_seq_whitelist = [
    int(wid.split(':')[0]) for wid in low_frequency_word_id_whitelist
]

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

