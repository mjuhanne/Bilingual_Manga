from mongo import *
jmdict_db = mongo_client['jmdict']

JMDICT_ENTRIES = "entries"

def get_readings_by_all_seqs():
    res = jmdict_db[JMDICT_ENTRIES].find({},['rl'])
    r_by_seq = { entry['_id']:[ r['t'] for r in entry['rl'] ] for entry in res }
    return r_by_seq

def get_kanji_elements_by_all_seqs():
    res = jmdict_db[JMDICT_ENTRIES].find({},['kl'])
    ke_by_seq = { entry['_id']:[ ke['t'] for ke in entry['kl'] ] for entry in res }
    return ke_by_seq
