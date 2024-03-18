import { json } from '@sveltejs/kit';
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);

let meanings = {};
let readings = {};
let classes = {};
let kanji_elements = {};
let common_pri_tags = {};
let k_pri_tags = {};
let r_pri_tags = {};

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
            readings[seq] = items[2].split(',');
            common_pri_tags[seq] = items[6].split(',');
            k_pri_tags[seq] = items[7].split(',');
            r_pri_tags[seq] = items[8].split(',');
            meanings[seq] = JSON.parse(items[9]);
        } catch (e) {
            console.log(`Error in line ${line_count} : '${line}' `);
        }
        line_count += 1;
    }
    console.log(`Loaded ${Object.keys(meanings).length} entries`);
}

loadJMDict();

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
        selected_info[seq] = {}
        selected_info[seq]['meanings'] = meanings[seq];
        selected_info[seq]['readings'] = readings[seq];
        selected_info[seq]['kanji_elements'] = kanji_elements[seq];
        selected_info[seq]['common_priority_tags'] = common_pri_tags[seq];
        selected_info[seq]['kanji_element_only_priority_tags'] = k_pri_tags[seq];
        selected_info[seq]['reading_only_priority_tags'] = r_pri_tags[seq];
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
