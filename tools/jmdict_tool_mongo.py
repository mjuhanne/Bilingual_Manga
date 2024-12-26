from helper import *
from jp_parser_helper import *
from jp_parser import *
import sys
import argparse
from mongo import *
database =client['jmdict']


results = []
result_seq_set = set()

force_exact = False

parser = argparse.ArgumentParser(
    prog="jmdict_tool",
    description="JMDict search tool",
)

parser.add_argument('--exact', '-e', action='store_true', help='Require exact match')
parser.add_argument('--tsv-file', '-tsv', nargs='?', default=None, help='Output to .tsv file')
parser.add_argument('--part-of-speech', '-pos', nargs='?', type=str, default=None, help='Filter entries with this part of speech code')
parser.add_argument('keyword', nargs='?', type=str, default='', help='search term')

args = vars(parser.parse_args())

#args = {'keyword':'いらっし','exact':False,'part_of_speech':None}

term = args['keyword']
force_exact = args['exact']


if args['part_of_speech'] is not None:
    if args['part_of_speech'] in jmdict_parts_of_speech_codes:
        target_class = jmdict_class_list.index(jmdict_parts_of_speech_codes[args['part_of_speech']])
    else:
        print("POS %s not found! Select from this list:" % args['part_of_speech'])
        for pos,expl in jmdict_parts_of_speech_codes.items():
            print("%s\t%s" % (pos,expl))
        exit(1)
else:
    target_class = None

if force_exact:
    re_results = database["re_lookup"].find({'_id':term})
    ke_results = database["ke_lookup"].find({'_id':term})
else:
    re_results = database["re_lookup"].find({'_id':{ "$regex": term }})
    ke_results = database["ke_lookup"].find({'_id':{ "$regex": term }})
    pass
pass

seqs = set()
for res in ke_results:
    seqs.update(res['seqs'])
for res in re_results:
    seqs.update(res['seqs'])
seqs = list(seqs)

results = database["entries"].find({"_id": {"$in": seqs}})

for res in results:
    k_elem_freq = ["%s(%d)" % (elem['t'],elem['f']) for elem in res['kl']]
    r_elem_freq = ["%s(%d)" % (elem['t'],elem['f']) for elem in res['rl']]
    k_elems = ' '.join(k_elem_freq)
    r_elems = ' '.join(r_elem_freq)
    seq = res['_id']
    if k_elems != '':
        r_elems = '(' + r_elems + ')'
    
    print("%s %s %s" % (seq, k_elems.ljust(8), r_elems.ljust(8)))
    for i, s in enumerate(res['sl']):
        cl_list = s['pl']
        meanings = s['gl']
        print("\t\t%d# %s" % (i,meanings))
        for cl in cl_list:
            cl_name = jmdict_class_list[cl]
            pos_code = get_jmdict_pos_code(cl)
            print("\t\t\t%s (%s)" % (cl_name,pos_code))

print("Total %d matches" % results.retrieved)

if args['tsv_file'] is not None:
    print("Saving to %s" % args['tsv_file'])
    f = open(args['tsv_file'],'w',encoding="utf-8")

    for res in results:

        if len(res['kl'])>0:
            word = res['kl'][0]['t']
            k_elem = word
        else:
            word = res['rl'][0]['t']
            k_elem = ''
        r_elem = res['rl'][0]['t']

        for i, s in enumerate(res['sl']):
            cl_list = s['pl']
            meanings = s['gl']

            pos_list = []
            for cl in cl_list:
                if target_class is None or target_class == cl:
                    pos_code = get_jmdict_pos_code(cl)
                    pos_list.append(pos_code)

            if len(pos_list)>0:
                word_id = '%s/%d:%s' % (seq,i,word)
                line = [word_id,k_elem,r_elem,','.join(pos_list),meanings[0]]
                f.write('\t'.join(line) + '\n')

    f.close()

