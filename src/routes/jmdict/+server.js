import { json } from '@sveltejs/kit';
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
import { getJmdictClientDB } from '$lib/mongo_jmdict';
const db = getJmdictClientDB();

const COLLECTION_ENTRIES = "entries"

const execSync = util.promisify(exec);

function freq2str(freq) {
    return Math.ceil(parseInt(freq)*0.5).toString() + 'K';
}

/*
function load_seq_freq() {
    console.log("Loading seq freq");
    let data = fs.readFileSync("lang/seq_count.json", "utf8");
    seq_frequency = JSON.parse(data);
    console.log(`Loaded ${seq_frequency['sorted_freq_list'].length} entries`);
}
*/

async function get_word_info(seq_list) {
    let selected_info = {};
    console.log("seq_list: "+seq_list);
    for (let seq of seq_list) {
        let seq_int = parseInt(seq);
        let res = await db.collection(COLLECTION_ENTRIES).findOne({'_id':seq_int})
        if (res !== null) {
            console.log(res)
            selected_info[seq] = {
                'kanji_elements' : [],
                'readings' : [],
                'k_elem_freq' : [],
                'r_elem_freq' : [],
                'priority_tags' : {},
                'meanings' : []
            }
            for (let re of res.rl) {
                selected_info[seq]['readings'].push(re.t);
                selected_info[seq]['r_elem_freq'].push(freq2str(re.f));
                selected_info[seq]['priority_tags'][re.t] = re.p
                console.log(re.p)
            }
            for (let ke of res.kl) {
                selected_info[seq]['kanji_elements'].push(ke.t);
                selected_info[seq]['k_elem_freq'].push(freq2str(ke.f));
                selected_info[seq]['priority_tags'][ke.t] = ke.p
            }
            for (let sense of res.sl) {
                selected_info[seq]['meanings'].push(sense.gl);
                // TODO: sense classes
            }

            selected_info[seq]['seq_order'] = 'NA'; //seq_frequency['sorted_freq_list'].indexOf(seq_int);
            selected_info[seq]['seq_count'] = 'NA'; //seq_frequency['seq_count'][seq];
            selected_info[seq]['priority_seq_title_count'] = 'NA'; //seq_frequency['priority_seq_title_count'][seq];
            selected_info[seq]['priority_seq_order'] = 'NA'; //seq_frequency['sorted_priority_freq_list'].indexOf(seq_int);
            selected_info[seq]['priority_seq_count'] = 'NA'; //seq_frequency['priority_seq_count'][seq];

        }
        console.log(seq + ": "+JSON.stringify(selected_info[seq]));
    }
    return selected_info;
}

async function parse(text) {
    let exec_cmd = `python tools/jp_parser_tool.py '${JSON.stringify(text)}'`
    console.log(exec_cmd);
    try {
        const { stdout, stderr } = await execSync(exec_cmd);
        console.log("parse Results: " + stdout);
        } catch (error) {
        console.log(error.stderr);
        return error.stderr;
    }
    return '';
}

export async function POST({ request }) {
	const data = await request.json();
	console.log("POST /jmdict: " + JSON.stringify(data) );
	let ret = { success : false};
	if (data.func == 'get_word_info') {
        ret= {
            success : true,
            'word_info' : await get_word_info(data.seq_list),
        };
    }
	if (data.func == 'parse') {
        parse(data.text)
        ret= {
            success : true,
        };
    }
	return json(ret);
}
