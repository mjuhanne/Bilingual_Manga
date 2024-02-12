import { json } from '@sveltejs/kit';
import db from "$lib/db";
import { AugmentMetadataWithUserData, AugmentMetadataWithCustomLanguageSummary, saveUserData, EVENT_TYPE } from "$lib/UserDataTools.js";
import fs from "fs";
import {exec} from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);
import { EventEmitter } from 'node:events';

let clients = [];
let update_process_lock = false;
let redo_process = false;

let analysis_error_msg = '';

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

const updateComprehensionSettings = (settings) => {
    for (let k of Object.keys(settings)) {
        db['user_data'][k] = settings[k];
    }
	saveUserData(db);
    updateCustomLanguageAnalysis();
	AugmentMetadataWithUserData(db);
}

const setReadingStatus = (chapter_ids,reading_data) => {
    console.log("setReadingStatus")
    let rs = db['user_data']['chapter_reading_status'];
    for (let c_id of chapter_ids) {
        console.log("Processing " + c_id);
        if (c_id in rs) {
            if (reading_data.status == 'Unread') {
                delete rs[c_id];
            } else {
                rs[c_id] = reading_data;
            }
        } else {
            if (reading_data.status != 'Unread') {
                rs[c_id] = reading_data;
            }
        }
    }
    db['user_data']['chapter_reading_status'] = rs;
    updateCustomLanguageAnalysis();
	AugmentMetadataWithUserData(db);
	return reading_data;
}

const updateComprehension = (chapter_ids, comprehension) => {
    console.log("updateComprehension")
    let rs = db['user_data']['chapter_reading_status'];
    for (let c_id of chapter_ids) {
        if (c_id in rs) {
            rs[c_id].comprehension = comprehension;
        } else {
            throw ("Chapter " + c_id + " reading status not yet set!");
        }
    }
    db['user_data']['chapter_reading_status'] = rs;
    updateCustomLanguageAnalysis();
	AugmentMetadataWithUserData(db);
	return comprehension;
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

        let res = await doCustomLangAnalysis('update','');
        if (res == '') {
            analysis_error_msg = '';
        } else {
            console.log("updateCustomLanguageAnalysis - error")
            analysis_error_msg = res;
            broadcastEvent(EVENT_TYPE.ANALYSIS_ERROR);
            update_process_lock = false;
            return;
        }
        broadcastEvent(EVENT_TYPE.UPDATED_STATS);

        broadcastEvent(EVENT_TYPE.UPDATING_ANALYSIS);
        res = await doCustomLangAnalysis('analyze','');
        if (res == '') {
            analysis_error_msg = '';
        } else {
            console.log("updateCustomLanguageAnalysis - error")
            analysis_error_msg = res;
            broadcastEvent(EVENT_TYPE.ANALYSIS_ERROR);
            update_process_lock = false;
            return;
        }
    } while(redo_process);
    console.log("updateCustomLanguageAnalysis - analysis done")
    db['user_data']['timestamp'] = Math.trunc(Date.now()/1000); // use seconds instead of msec
    saveUserData(db); // save timestamp
    updateMetadata();
    broadcastEvent(EVENT_TYPE.UPDATED_ANALYSIS);
    update_process_lock = false;
}

async function doCustomLangAnalysis(cmd, manga_id) {
    let exec_cmd = `python tools/bm_custom_lang_analysis.py ${cmd} ${manga_id}`
    try {
        const { stdout, stderr } = await execSync(exec_cmd);
        } catch (error) {
        console.log(error.stderr);
        return error.stderr;
    }
    return '';
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
        let res = await doCustomLangAnalysis('suggest_preread',manga_id)
        if (res != '') {
            return {
                success : false,
                error_message : res,
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
                if (event_type == EVENT_TYPE.ANALYSIS_ERROR) {
                    console.log(`sending error event '${event_type}' to ${client.clientId}`)
                    data = JSON.stringify({'event_type':event_type,'msg':analysis_error_msg});
                } else {
                    console.log(`sending updated event '${event_type}' to ${client.clientId}`)
                    data = JSON.stringify({'event_type':event_type});    
                }
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
	} else if (data.func == 'set_reading_status') {
        ret= {
            success : true,
            'reading_status' : setReadingStatus(data.chapters, data.reading_data),
        };
	} else if (data.func == 'update_comprehension') {
        ret= {
            success : true,
            'comprehension' : updateComprehension(data.chapters, data.comprehension),
        };
    } else if (data.func == 'get_suggested_preread') {
        ret= await getSuggestedPreread(data.manga_id);
        return json(ret);
    } else if (data.func == 'update_comprehension_settings') {
        updateComprehensionSettings(data.settings);
    }
    console.log("POST /user_data return: " + JSON.stringify(ret));
	return json(ret);
}