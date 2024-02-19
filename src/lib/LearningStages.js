export const STAGE = {
    NONE        : 0,
    UNKNOWN     : 1,
    UNFAMILIAR  : 2,
    LEARNING    : 3,
    PRE_KNOWN   : 4,
    KNOWN       : 5,
    FORGOTTEN   : 6,
    IGNORED     : 7,
};

export const learning_stage_explanation = {
    [STAGE.UNKNOWN] : "A word never seen before",
    [STAGE.UNFAMILIAR] : "A word seen only once or twice. Maybe a bit too rare word to learn at this point?",
    [STAGE.LEARNING] :  "A word that has been encountered enough times so we know this word could be useful",
    [STAGE.PRE_KNOWN] : "A word that has been in learning stage and encountered already so many times that the user should know it already. If automatic graduation to 'known' is not enabled the word will stay in this category until confirmed by the user",
    [STAGE.KNOWN] : "A word that has been graduated into 'known status' automatically by the system or manually by the user",
    [STAGE.FORGOTTEN] : "User hasn't seen this word for a long time so it is marked as forgotten. Needs a manual intervention in order to be restored to 'known'",
    [STAGE.IGNORED] : "A word marked as irrelevant by the user. It will be omitted for any statistics",
};

export const learning_stages = {
    [STAGE.UNKNOWN] : "Unknown",
    [STAGE.UNFAMILIAR] : "Unfamiliar",
    [STAGE.LEARNING] : "Learning",
    [STAGE.PRE_KNOWN] : "Pre-known",
    [STAGE.KNOWN] : "Known",
    [STAGE.FORGOTTEN] : "Forgotten",
    [STAGE.IGNORED] : "Ignored",
}

export const learning_stage_colors = {
    [STAGE.NONE] : '#fff',
    [STAGE.UNKNOWN] : '#dbd',
    [STAGE.UNFAMILIAR] : '#bbf',
    [STAGE.LEARNING] :  '#F8C471',
    [STAGE.PRE_KNOWN] : '#7f7',
    [STAGE.KNOWN] : "#fff",
    [STAGE.FORGOTTEN] : "#F977CB",
    [STAGE.IGNORED] : '#ccc',
}

export const SOURCE = {
    JLPT    : 'jlpt',
    CUSTOM  : 'cu',
    LANGUAGE_REACTOR : 'lr',
    CHAPTER : 'ch',
    ENGINE  : 'en',
    USER    : 'u',
    KNOWN_AUX : 'ka',
}

export const source_to_name = {
    [SOURCE.JLPT]    : 'JLPT',
    [SOURCE.CUSTOM]  : 'Custom list',
    [SOURCE.LANGUAGE_REACTOR] : 'Language Reactor',
    [SOURCE.CHAPTER] : 'Bilingual Manga',
    [SOURCE.ENGINE]  : 'Engine',
    [SOURCE.USER]    : 'User',
    [SOURCE.KNOWN_AUX]: 'Known aux verb/particle',
}

export const word_classes = [
    '名詞',
    '助詞',
    '補助記号',
    '動詞',
    '助動詞',
    '接尾辞',
    '副詞',
    '代名詞',
    '形容詞',
    '感動詞',
    '形状詞',
    '接頭辞',
    '接続詞',
    '連体詞',
    '記号',
    '接頭詞',
    'フィラー',  // failure?
]
