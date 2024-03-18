import json
from helper import user_set_words_file__old, user_set_word_ids_file, ocr_dir, get_seq_and_word_from_word_id


def load_parsed_ocr_file(chapter_id):
    try:
        parsed_ocr_path = "parsed_ocr/" + chapter_id + ".json"
        f = open(parsed_ocr_path, "r", encoding="utf-8")
        f_data = f.read()
        f.close()    
        pages = json.loads(f_data)
        return pages
    except:
        return None


last_cid = None
last_pages = None

user_set_word_ids = dict()

def strip_sense_from_word_id(word_id):
    sw = word_id.split(':')
    word = sw[1]
    seq = sw[0].split('/')[0]
    word_id0 = str(seq) + ':' + word
    return word_id0


with open(user_set_words_file__old,"r",encoding="utf-8") as f:
    data = f.read()
    user_set_words = json.loads(data)

    ## load manually set words and their learning stages
    for user_word, history in user_set_words.items():
            for entry in history:
                cid = entry['m']['cid']

                if cid != last_cid:
                    pages = load_parsed_ocr_file(cid)

                if pages is not None:

                    seqs = []
                    word_id_list = pages['parsed_data']['word_id_list']
                    for word_id in word_id_list:
                        seq, word = get_seq_and_word_from_word_id(word_id)
                        word_id0 = str(seq) + ':' + word
                        if user_word == word:
                            seqs.append(word_id0)

                    if len(seqs)==0:
                        print("Warning! %s not found in %s" % (user_word, cid))
                    elif len(seqs)==1:
                        user_set_word_ids[seqs[0]] = history
                    else:
                        page = pages[ entry['m']['pr']]
                        block = page[ entry['m']['b']]
                        jlines = block['jlines']
                        filtered_seqs = set()
                        for line in jlines:
                            for item_ref in line:
                                for item,refs in item_ref.items():
                                    for ref in refs:
                                        word_id = word_id_list[ref]
                                        seq, word = get_seq_and_word_from_word_id(word_id)
                                        word_id0 = str(seq) + ':' + word
                                        if word_id0 in seqs:
                                            filtered_seqs.update([word_id0])
                        for seq in filtered_seqs:
                            user_set_word_ids[seq] = history

                    last_pages = pages
                    last_cid = cid


with open(user_set_word_ids_file,"w",encoding="utf-8") as f:
    f.write(json.dumps(user_set_word_ids, ensure_ascii=False))



