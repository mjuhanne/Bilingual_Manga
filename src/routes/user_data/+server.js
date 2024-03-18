import { json } from '@sveltejs/kit';
import db from "$lib/db";
import { AugmentMetadataWithUserData, AugmentMetadataWithCustomLanguageSummary, saveUserData, saveUserSetWords, EVENT_TYPE } from "$lib/UserDataTools.js";
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);
import { EventEmitter } from 'node:events';

// Overwrite the last history event if the change happened less than hour ago.
// This prevents logging unnecessary events when user accidently flips between stages
const LEARNING_STAGE_CHANGE_REMORSE_PERIOD = 60*60; // 1 hour

const LEARNING_ENGINE_TOOL = `bm_learning_engine.py`
const ANALYZER_TOOL = `bm_analyze.py`

let clients = [];
let update_process_lock = false;
let redo_process = false;

let analysis_status_msg = '';

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}

function updateMetadata() {
    let filename = 'json/custom_lang_analysis.json';
    if (fs.existsSync(filename)) {
        let data = fs.readFileSync(filename, "utf8");
        let json_data = JSON.parse(data);
        db['custom_lang_summary'] = json_data;
        AugmentMetadataWithCustomLanguageSummary(db['manga_metadata'],db['custom_lang_summary']);
    } else {
        console.error(`Custom lang summary file ${filename} not found!`)
    }
}

const toggleFavourite = (manga_id) => {
    let favourite = false;
    if (db['user_data'].favourites.includes(manga_id)) {
        console.log(db['user_data'].favourites);
        db['user_data'].favourites = db['user_data'].favourites.filter((id) => {id != manga_id});
    } else {
        db['user_data'].favourites.push(manga_id);
        favourite = true;
    }
	saveUserData(db);
	AugmentMetadataWithUserData(db);
	return favourite;
}

const updateLearningSettings = (settings) => {
    db['user_data']['learning_settings'] = settings
	saveUserData(db);
    updateCustomLanguageAnalysis();
	AugmentMetadataWithUserData(db);
}


const massSetChapterReadingStatus = (status_list) => {
    console.log("massSetChapterReadingStatus")
    let rs = db['user_data']['chapter_reading_status'];
    for (const [c_id, reading_data] of Object.entries(status_list)) {
        if (c_id in rs) {
            if (reading_data.status == 'Unread') {
                console.log(" * Unread " + c_id);
                delete rs[c_id];
            } else {
                console.log(" * Modified " + c_id + ": " + JSON.stringify(reading_data));
                rs[c_id] = reading_data;
            }
        } else {
            if (reading_data.status != 'Unread') {
                console.log(" * New " + c_id + ": " + JSON.stringify(reading_data));
                rs[c_id] = reading_data;
            }
        }
    }
    db['user_data']['chapter_reading_status'] = rs;
    updateCustomLanguageAnalysis();
	AugmentMetadataWithUserData(db);
}


async function updateCustomLanguageAnalysis() {
    console.log("updateCustomLanguageAnalysis");
    if (update_process_lock) {
        redo_process = true;
        console.log("Signal to redo process");
        return;
    }
    update_process_lock = true;
    broadcastEvent(EVENT_TYPE.UPDATING_STATS);
    saveUserData(db); // save reading status & comprehension
    do {
        if (redo_process) {
            console.log("updateCustomLanguageAnalysis - redo process");
            redo_process=false; 
        }

        let res = await LaunchLanguageTool(LEARNING_ENGINE_TOOL,'update');
        analysis_status_msg = res.msg;
        if (res.status == 'warning') {
            console.log("updateCustomLanguageAnalysis - warning")
            broadcastEvent(EVENT_TYPE.ANALYSIS_WARNING);
        } else if (res.status == 'error'){
            console.log("updateCustomLanguageAnalysis - error")
            broadcastEvent(EVENT_TYPE.ANALYSIS_ERROR);
            update_process_lock = false;
            return;
        }
        broadcastEvent(EVENT_TYPE.UPDATED_STATS);

        broadcastEvent(EVENT_TYPE.UPDATING_ANALYSIS);
        res = await LaunchLanguageTool(ANALYZER_TOOL,'analyze');
        analysis_status_msg = res.msg;
        if (res.status == 'warning') {
            console.log("updateCustomLanguageAnalysis - warning")
            broadcastEvent(EVENT_TYPE.ANALYSIS_WARNING);
        } else if (res.status == 'error'){
            console.log("updateCustomLanguageAnalysis - error")
            broadcastEvent(EVENT_TYPE.ANALYSIS_ERROR);
            update_process_lock = false;
            return;
        }
    } while(redo_process);
    console.log("updateCustomLanguageAnalysis - analysis done")
    db['user_data']['timestamp'] = Date.now();
    saveUserData(db); // save timestamp
    updateMetadata();
    broadcastEvent(EVENT_TYPE.UPDATED_ANALYSIS);
    update_process_lock = false;
}

async function LaunchLanguageTool(cmd, argument) {
    let exec_cmd = `python tools/${cmd} ${argument}`
    let warning_msg = ''
    try {
        const { stdout, stderr } = await execSync(exec_cmd);
        warning_msg = stderr;
    } catch (error) {
        console.log("LaunchLanguageTool ERROR: " + error.stderr);
        return {'status':'error','msg':error.stderr};
    }
    if (warning_msg != '') {
        console.log("LaunchLanguageTool WARNING: " + warning_msg)
        return {'status':'warning','msg':warning_msg}
    }
    return {'status':'ok'}
}

async function getSuggestedPreread(manga_id) {
    if (!('timestamp' in db['user_data'])) {
        return {
            success : false,
            error_message : "Language analysis settings not yet configured!",
        }    
    }
    console.log(`getSuggestedPreread ${manga_id} timestamp ${db['user_data']['timestamp']}`);
    let preread_dir = 'lang/suggested_preread/';
    if (!fs.existsSync(preread_dir)) {
        fs.mkdirSync(preread_dir, { recursive: true });
    }

    while (update_process_lock) {
        await delay(1000);
    }
    
    let filename = preread_dir + manga_id + '.json';
    let json_data;
    let stale = true;
    if (fs.existsSync(filename)) {
        let data = fs.readFileSync(filename, "utf8");
        json_data = JSON.parse(data);
        console.log(`existing timestamp ${json_data.timestamp}`);
        if (json_data.timestamp < db['user_data']['timestamp']) {
            console.log("Recalculating suggested preread")
        } else {
            stale = false;
        }
    }

    if (stale) {
        let res = await LaunchLanguageTool(ANALYZER_TOOL,`suggest_preread ${manga_id}`)
        if (res.status != 'ok') {
            return {
                success : false,
                error_message : res.msg,
            }    
        }
        let data = fs.readFileSync(filename, "utf8");
        json_data = JSON.parse(data);
    }
    return {
        success : true,
        'suggested_preread' : json_data.analysis,
    }
}

const updateManuallySetWordLearningStage = (data) => {
    let word_id = data.word_id;
    let stage = data.stage;
    let word_metadata = data.metadata;
    let timestamp = Math.trunc(Date.now()/1000);
    let history_entry = { 't' : timestamp, 's':stage, 'm':word_metadata};
    let replaced_last_entry = false;
    if (word_id in db['user_set_words']) {
        let word_history = db['user_set_words'][word_id];
        let last_timestamp = word_history[word_history.length-1].t;
        if (timestamp - last_timestamp < LEARNING_STAGE_CHANGE_REMORSE_PERIOD) {
            word_history[word_history.length-1] = history_entry
            replaced_last_entry = true;
        } else {
            word_history.push(history_entry);
        }
    } else {
        db['user_set_words'][word_id] = [history_entry];
    }
	saveUserSetWords(db);
    // TODO: We don't want to do this every time a single word status changes
    //updateCustomLanguageAnalysis();
    return replaced_last_entry;
}

function broadcastEvent(event_type) {
    console.log("broadcastEvent " + event_type);
    for (const client of clients) {
        client.emit('event',event_type);
    }
}

// This is the event handler for user data consumers
export async function GET({ request }) {

	console.log("GET /user_data: " + JSON.stringify(request) );

    const client = new EventEmitter();
    client.clientId = Date.now();;
	clients.push(client);

    const stream = new ReadableStream({
		start(controller) {
            console.log(`${client.clientId} New user_data connection`);
            let data = JSON.stringify({'event_type':EVENT_TYPE.CONNECTED});
            controller.enqueue(`event: message\ndata:${data}\n\n`);
			client.on('event', (event_type) => {
                let data;
                console.log(`sending updated event '${event_type}' to ${client.clientId}`)
                data = JSON.stringify({'event_type':event_type,'msg':analysis_status_msg});
				controller.enqueue(`event: message\ndata:${data}\n\n`);
			});
		},
		cancel() {
            console.log(`${client.clientId} User_data connection closed`);
            clients = clients.filter(cl => client.clientId !== cl.clientId);
		}
	});

    return new Response(stream, {
		headers: {
			'Content-Type': 'text/event-stream',
			'Cache-Control': 'no-cache',
			Connection: 'keep-alive'
		}
	});
}


export async function POST({ request }) {
	const data = await request.json();
	console.log("POST /user_data: " + JSON.stringify(data) );
	let ret = { success : false};
	if (data.func == 'toggle_favourite') {
        ret= {
            success : true,
            'favourite' : toggleFavourite(data.manga_id)
        };
	} else if (data.func == 'mass_set_chapter_reading_status') {
        massSetChapterReadingStatus(data.status_list),
        ret= {success : true};
    } else if (data.func == 'get_suggested_preread') {
        ret= await getSuggestedPreread(data.manga_id);
        return json(ret);
    } else if (data.func == 'update_learning_settings') {
        updateLearningSettings(data.settings);
        ret= {success : true};
    } else if (data.func == 'update_manually_set_word_learning_stage') {        
        ret= {
            success : true, 
            'replaced_last_entry' : updateManuallySetWordLearningStage(data.stage_data)
        };
    }
    console.log("POST /user_data return: " + JSON.stringify(ret));
	return json(ret);
}