import { json } from '@sveltejs/kit';
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";

const execSync = util.promisify(exec);

const INTERACTIVE_CHAPTER_FILE = './parsed_ocr/temp_book_chapter.html';

async function createInteractiveBookChapter(chapter_id, output_file) {
    let exec_cmd = `python tools/interactive_book.py ${chapter_id} ${output_file}`
    try {
        const { stdout, stderr } = await execSync(exec_cmd);
        console.log("* Res: " + stdout);
        if (stderr != '') {
            console.log("* Err: " + stderr);
        }
        } catch (error) {
        console.log("Error: ",error);
        return error.stderr;
    }
    return '';
}

async function fetchBookChapter(chapter_id) {
    let res = await createInteractiveBookChapter(chapter_id, INTERACTIVE_CHAPTER_FILE);
    if (res == '') {
        console.log(`Reading Interactive chapter file: ${INTERACTIVE_CHAPTER_FILE}`);
        let chapter_data = fs.readFileSync(INTERACTIVE_CHAPTER_FILE, "utf8");
        return JSON.parse(chapter_data)
    } else {
        console.error(`Error creating Interactive Chapter file`);
    }
}


export async function POST({ request }) {
	const data = await request.json();
	console.log("POST /ocr: " + JSON.stringify(data) );
	let ret = { success : false};
	if (data.func == 'fetch_book_chapter') {
        ret= {
            success : true,
            'chapter_data' : await fetchBookChapter(data.chapter_id)
        };
    } 
    return json(ret);
}
