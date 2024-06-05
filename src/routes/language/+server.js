import { STAGE } from '$lib/LearningData.js'
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);

const USER_DIR = 'lang/user';
const LR_JSON_FILE = `${USER_DIR}/language-reactor.json`
const USER_KNOWN_WORDS_FILE = `${USER_DIR}/'user_known_words.json`
const USER_KNOWN_KANJIS_FILE = `${USER_DIR}/'user_known_kanjis.json`
const TEMP_FILE = `${USER_DIR}/import-temp`

async function importFile(input_file,file_type, output_file) {
    let exec_cmd = `python tools/import_lang.py ${input_file} ${file_type} ${output_file}`
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

async function processFile(key,file) {
    if (!fs.existsSync(USER_DIR)) {
        fs.mkdirSync(USER_DIR, { recursive: true });
    }
    let data = await file.text();
    fs.writeFileSync (TEMP_FILE, data);
    if (key == 'language-reactor-json') {
        importFile(TEMP_FILE, key, LR_JSON_FILE);
    } else if (key == 'custom-word-list') {
        importFile(TEMP_FILE, key, USER_KNOWN_WORDS_FILE);
    } else if (key == 'custom-kanji-list') {
        fs.writeFileSync (USER_KNOWN_KANJIS_FILE, data);
    } else {
        console.log("Unknown type!")
    }
}

export async function POST({ request }) {
    const formData = await request.formData();
    formData.forEach((file, key) => {
        console.log(JSON.stringify(file))
        processFile(key,file);
    });
    return new Response(String('Request received'));
  }
