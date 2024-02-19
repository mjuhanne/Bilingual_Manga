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

async function createInteractiveOcr(input_file, output_file) {
    let exec_cmd = `python tools/interactive_ocr.py ${input_file} ${output_file}`
    try {
        const { stdout, stderr } = await execSync(exec_cmd);
        } catch (error) {
        console.log(error.stderr);
        return error.stderr;
    }
    return '';
}

async function fetchOcr(chapter_id) {
    let ocr_file = `${OCR_PATH + chapter_id + '.json'}`
    let parsed_ocr_file = `${PARSED_OCR_PATH + chapter_id + '.json'}`
    let ocr;
    if (fs.existsSync(parsed_ocr_file)) {
        let res = await createInteractiveOcr(parsed_ocr_file, INTERACTIVE_OCR_FILE);
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

export async function POST({ request }) {
	const data = await request.json();
	console.log("POST /ocr: " + JSON.stringify(data) );
	let ret = { success : false};
	if (data.func == 'fetch_ocr') {
        ret= {
            success : true,
            'ocr' : await fetchOcr(data.chapter_id)
        };
    }
	return json(ret);
}
