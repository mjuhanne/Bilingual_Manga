import { json } from '@sveltejs/kit';
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);

let meanings = {};
let readings = {};
let classes = {};
let kanji_elements = {};
let k_elem_freq = {};
let r_elem_freq = {};
let pri_tags = {};
let seq_frequency = {};

function loadJMDict() {
    console.log("Loading JMDict");
    let data = fs.readFileSync("lang/JMdict_e_m.tsv", "utf8");
    console.log("Parsing JMDict");
    var lines = data.split('\n');
    let line_count = 1;
    for (let line of lines) {
        try {
            let items = line.split('\t');
            let seq = parseInt(items[0]);
            kanji_elements[seq] = items[1].split(',');
            k_elem_freq[seq] = items[4].split(',');
            readings[seq] = items[2].split(',');
            r_elem_freq[seq] = items[5].split(',');
            pri_tags[seq] = JSON.parse(items[6]);
            meanings[seq] = JSON.parse(items[7]);
        } catch (e) {
            console.log(`Error in line ${line_count} : '${line}' `);
        }
        line_count += 1;
    }
    console.log(`Loaded ${Object.keys(meanings).length} entries`);


    console.log("Loading JMnedict");
    data = fs.readFileSync("lang/JMnedict_e.tsv", "utf8");
    console.log("Parsing JMnedict");
    var lines = data.split('\n');
    line_count = 1;
    for (let line of lines) {
        try {
            let items = line.split('\t');
            let seq = parseInt(items[0]);
            kanji_elements[seq] = items[1].split(',');
            readings[seq] = items[2].split(',');
            k_elem_freq[seq] = parseInt(items[3]);
            r_elem_freq[seq] = k_elem_freq[seq]
            pri_tags[seq] = []
            meanings[seq] = [[items[4]]];
        } catch (e) {
            console.log(`Error in line ${line_count} : '${line}' `);
        }
        line_count += 1;
    }
    console.log(`Loaded ${Object.keys(meanings).length} entries`);

}


function load_seq_freq() {
    console.log("Loading seq freq");
    let data = fs.readFileSync("lang/seq_count.json", "utf8");
    seq_frequency = JSON.parse(data);
    console.log(`Loaded ${seq_frequency['sorted_freq_list'].length} entries`);
}

loadJMDict();
load_seq_freq();

function get_meanings(seq_list) {
    let selected_meanings = {};
    console.log("seq_list: "+seq_list);
    for (let seq of seq_list) {
        selected_meanings[seq] = meanings[seq];
    }
    return selected_meanings;
}

function get_word_info(seq_list) {
    let selected_info = {};
    console.log("seq_list: "+seq_list);
    for (let seq of seq_list) {
        let seq_int = parseInt(seq);
        selected_info[seq] = {}
        selected_info[seq]['meanings'] = meanings[seq];
        selected_info[seq]['readings'] = readings[seq];
        selected_info[seq]['kanji_elements'] = kanji_elements[seq];
        selected_info[seq]['priority_tags'] = pri_tags[seq];

        selected_info[seq]['k_elem_freq'] = k_elem_freq[seq]
        selected_info[seq]['r_elem_freq'] = k_elem_freq[seq]

        selected_info[seq]['seq_order'] = seq_frequency['sorted_freq_list'].indexOf(seq_int);
        selected_info[seq]['seq_count'] = seq_frequency['seq_count'][seq];
        selected_info[seq]['priority_seq_order'] = seq_frequency['sorted_priority_freq_list'].indexOf(seq_int);
        selected_info[seq]['priority_seq_count'] = seq_frequency['priority_seq_count'][seq];
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
	if (data.func == 'get_meanings') {
        ret= {
            success : true,
            'meanings' : get_meanings(data.seq_list),
        };
    }
	if (data.func == 'get_word_info') {
        ret= {
            success : true,
            'word_info' : get_word_info(data.seq_list),
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
