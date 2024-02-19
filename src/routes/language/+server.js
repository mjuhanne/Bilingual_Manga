import { json } from '@sveltejs/kit';
import db from "$lib/db";
import { AugmentMetadataWithUserData, saveUserData } from "$lib/UserDataTools.js";
import { STAGE } from '$lib/LearningStages.js'
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}

const USER_DIR = 'lang/user';

const LR_JSON_FILE = `${USER_DIR}/language-reactor.json`

function parseLanguageReactorJson(data) {
    let json_data = JSON.parse(data);
    let words = {};

    for (let i in json_data) {
        let item = json_data[i];
        if (item['itemType'] == 'WORD') {
            let stage = STAGE.UNKNOWN;
            let ll_stage = item['learningStage']
            if (ll_stage == 'LEARNING') {
                stage = STAGE.LEARNING;
            } else if (ll_stage == 'KNOWN') {
                stage = STAGE.KNOWN;
            } else if (ll_stage == 'SKIPPED') {
                stage = STAGE.IGNORED;
            }
            let lemma = item['word']['text']
            let timestamp = Math.trunc(item['timeModified_ms']/1000);

            let comment = '';
            try {
                let ref = item.context.phrase.reference
                comment = ref.source + ' / ' + ref.title;
            } catch(err) {
                comment = "Couldn't retrieve word reference";
            }

            let metadata = { 'comment' : comment };
            words[lemma] = { 's':stage, 't':timestamp, 'm' : metadata }
        }
    }
    console.log(`Language Reactor word list with ${Object.keys(words).length} words`);
	fs.writeFile (LR_JSON_FILE, JSON.stringify(words), function(err) {
		if (err) throw err;
	});
}

function parseCustomList(list_type, data, file_name) {
    // NO parsing here. Instead just copy the file and let the python script handle the parsing
    let output_file = `${USER_DIR}/`;
    let f = file_name.split('.')
    let ext = f[f.length-1];
    if (list_type == 'word') {
        output_file += 'user_known_words.';
    } else {
        output_file += 'user_known_kanjis.';
    }
    output_file += ext;
    fs.writeFileSync (output_file, data);
}

async function processFile(key,file) {
    if (!fs.existsSync(USER_DIR)) {
        fs.mkdirSync(USER_DIR, { recursive: true });
    }
    let data = await file.text();
    if (key == 'language-reactor-json') {
        parseLanguageReactorJson(data);
    } else if (key == 'custom-word-list') {
        parseCustomList('word',data, file.name);
    } else if (key == 'custom-kanji-list') {
        parseCustomList('kanji',data, file.name);
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
