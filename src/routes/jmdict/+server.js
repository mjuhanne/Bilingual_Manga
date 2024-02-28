import { json } from '@sveltejs/kit';
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);

let meanings = {};

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
            let m = JSON.parse(items[6])
            meanings[seq] = m;
        } catch (e) {
            console.log(`Error in line ${line_count} : '${line}' `);
        }
        line_count += 1;
    }
    console.log(`Loaded ${Object.keys(meanings).length} entries`);
}

loadJMDict();

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
        let m_list = [];
        for (let seq of data.seqs) {
            m_list.push(meanings[seq]);
        }
        ret= {
            success : true,
            'meanings' : m_list,
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
