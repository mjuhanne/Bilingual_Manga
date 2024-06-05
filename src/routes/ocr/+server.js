import { json } from '@sveltejs/kit';
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
import {obj} from '$lib/store.js';

const execSync = util.promisify(exec);

let meta;
obj.subscribe(value => { meta=value;});
let x = meta['0'].manga_titles;
let cdncdn=meta['0'].cdn;
let cdncdn1=meta['0'].cdn1;

const OCR_PATH = './ocr/';
const PARSED_OCR_PATH = './parsed_ocr/';
const INTERACTIVE_OCR_FILE = './parsed_ocr/temp.json';

async function createInteractiveOcr(chapter_id, output_file, page_ref, block_id) {
    let exec_cmd = `python tools/interactive_ocr.py ${chapter_id} ${output_file} ${page_ref} ${block_id}`
    try {
        const { stdout, stderr } = await execSync(exec_cmd);
        console.log("* Res: " + stdout);
        } catch (error) {
        console.log("Error: ",error);
        return error.stderr;
    }
    return '';
}

async function fetchOcr(chapter_id,page_ref,block_id) {
    let ocr_file = `${OCR_PATH + chapter_id + '.json'}`
    let parsed_ocr_file = `${PARSED_OCR_PATH + chapter_id + '.json'}`
    let ocr;
    if (fs.existsSync(parsed_ocr_file)) {
        let res = await createInteractiveOcr(chapter_id, INTERACTIVE_OCR_FILE, page_ref, block_id);
        if (res == '') {
            console.log(`Reading Interactive OCR: ${INTERACTIVE_OCR_FILE}`);
            ocr = fs.readFileSync(INTERACTIVE_OCR_FILE, "utf8");
            return JSON.parse(ocr);
        } else {
            console.error(`Error creating Interactive OCR from ${parsed_ocr_file}. Falling back to basic one`);
        }
    } else {
        console.log(`Parsed OCR ${parsed_ocr_file} not found. Falling back to basic one`);
    }

    if (!fs.existsSync(ocr_file)) {
        console.log(`No local OCR found [${url}]- fetching remote`)
        url = `${cdncdn}/ocr/${chapter_id}.json`
        response = await fetch(url);
        try {
            ocr = await response.json();
        } catch (err) {
            console.error(`Error fetching OCR ${url}`)
            return {};
        }
    } else {
        let data = fs.readFileSync(ocr_file,  "utf8");
        ocr = JSON.parse(data);
    }
    return ocr;
}

function update_OCR_block(cid, new_ocr_data) {
    let ocr_changes_file = "json/ocr_corrections.json"
    let corrections = {"block_errata":{},"word_id_errata": {}}
    try {
        let data = fs.readFileSync(ocr_changes_file, "utf8");
        corrections = JSON.parse(data);
    } catch(error) {
    }
    if (!(cid in corrections['block_errata'])) {
        corrections['block_errata'][cid] = []
    }
    // TODO: overwrite previous amendment if it exists
    corrections['block_errata'][cid].push(new_ocr_data)
    fs.writeFile (ocr_changes_file, JSON.stringify(corrections), function(err) {
        if (err) throw err;
    });
    // TODO: parse new ocr block
    return new_ocr_data.new_ocr_block
}

function update_manually_priority_word(cid, new_word_data) {
    let ocr_changes_file = "json/ocr_corrections.json"
    let corrections = {"block_errata":{},"word_id_errata": {}}
    try {
        let data = fs.readFileSync(ocr_changes_file, "utf8");
        corrections = JSON.parse(data);
    } catch(error) {
    }
    if (!(cid in corrections['word_id_errata'])) {
        corrections['word_id_errata'][cid] = []
    } else {
        let new_change_list = []
        for (let change of corrections['word_id_errata'][cid]) {
            if ( (change['pr'] == new_word_data['pr']) && 
                (change['bid']==new_word_data['bid']) && 
                (change['iid']==new_word_data['iid'])
            ) {
                console.log("Removing old entry",JSON.stringify(change));
            } else {
                new_change_list.push(change)
            }
        }
        corrections['word_id_errata'][cid] = new_change_list;
    }
    corrections['word_id_errata'][cid].push(new_word_data)
    fs.writeFile (ocr_changes_file, JSON.stringify(corrections), function(err) {
        if (err) throw err;
    });
}


export async function POST({ request }) {
	const data = await request.json();
	console.log("POST /ocr: " + JSON.stringify(data) );
	let ret = { success : false};
	if (data.func == 'fetch_ocr') {
        ret= {
            success : true,
            'ocr' : await fetchOcr(data.chapter_id,"","")
        };
    } else if (data.func == 'debug_ocr') {
        ret= {
            success : true,
            'ocr' : await fetchOcr(data.chapter_id,data.page_ref,data.block_id)
        };
    } else if (data.func == 'update_ocr_block') {
        ret= {
            success : true, 
            'parsed_ocr_block' : update_OCR_block(data.cid, data.ocr_data)
        };
    } else if (data.func == 'update_manually_priority_word') {
        update_manually_priority_word(data.cid, data.word_data);
        ret = { success : true };
    }
    return json(ret);
}
