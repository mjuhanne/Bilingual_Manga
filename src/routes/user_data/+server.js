import { json } from '@sveltejs/kit';
import db from "$lib/db";
import { saveUserSetWords, EVENT_TYPE } from "$lib/UserDataTools.js";
import fs from "fs";
import {exec} from "node:child_process";
import child_process from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);
import { EventEmitter } from 'node:events';
import { getUserDataValue, updateUserData, updateManuallySetWordLearningStateChanges, getManuallySetWordLearningStateChanges, getUserWordHistory } from '$lib/collections.js' 
import { DEFAULT_USER_ID } from '../../lib/UserDataTools.js';

// Overwrite the last history event if the change happened less than hour ago.
// This prevents logging unnecessary events when user accidently flips between stages
const LEARNING_STAGE_CHANGE_REMORSE_PERIOD = 60*60; // 1 hour

const LEARNING_ENGINE_TOOL = `bm_learning_engine.py`
const ANALYZER_TOOL = `bm_analyze.py`

let clients = [];
let update_process_lock = false;
let redo_process = false;

let suggest_preread_lock = new Set();

let analysis_status_msg = '';

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}


async function toggleFavourite(manga_id) {
    let favourite = false;
    let favourites = await getUserDataValue(DEFAULT_USER_ID, "favourites")
    if (favourites.includes(manga_id)) {
        favourites = favourites.filter((id) => id != manga_id);
    } else {
        favourites.push(manga_id);
        favourite = true;
    }
	await updateUserData(DEFAULT_USER_ID, "favourites", favourites);
	return favourite;
}

async function updateLearningSettings(settings) {
	await updateUserData(DEFAULT_USER_ID, "learning_settings", settings);
	await updateUserData(DEFAULT_USER_ID, "timestamp", Date.now());
    updateCustomLanguageAnalysis()
}

async function updateAnkiSettings(settings) {
	await updateUserData(DEFAULT_USER_ID, "anki_settings", settings);
}

async function massSetChapterReadingStatus(status_list) {
    console.log("massSetChapterReadingStatus")
    let rs = await getUserDataValue(DEFAULT_USER_ID, "chapter_reading_status")
    console.log("rs: " + JSON.stringify(rs))
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
	await updateUserData(DEFAULT_USER_ID, "chapter_reading_status", rs);
	await updateUserData(DEFAULT_USER_ID, "timestamp", Date.now());
    updateCustomLanguageAnalysis();
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

    LaunchLanguageTool_Spawn(LEARNING_ENGINE_TOOL,["update"],
        (exit_code) => {
            if (exit_code == 0) {

                broadcastEvent(EVENT_TYPE.UPDATING_ANALYSIS);
                LaunchLanguageTool_Spawn(ANALYZER_TOOL,['analyze','--progress-output'],
                    (exit_code) => {
                        update_process_lock = false;
                        if (exit_code == 0) {
                            if (redo_process) {
                                redo_process = false;
                                console.log("updateCustomLanguageAnalysis - redo process");
                                updateCustomLanguageAnalysis();
                            } else {
                                console.log("updateCustomLanguageAnalysis - analysis done")
                                broadcastEvent(EVENT_TYPE.UPDATED_ANALYSIS);
                            }
                            broadcastEvent(EVENT_TYPE.UPDATED_SUGGESTED_PREREAD,"")
                        } else {
                            broadcastEvent(EVENT_TYPE.ANALYSIS_ERROR, `Learning engine tool exited with exit code ${exit_code}`);
                        }
                    },
                    (progress_msg) => {
                        console.log("progress:",progress_msg);
                        broadcastEvent(EVENT_TYPE.ANALYSIS_PROGRESS,progress_msg)
                    },
                    (error_msg) => {
                        console.log("err:",error_msg);
                        broadcastEvent(EVENT_TYPE.ANALYSIS_WARNING,error_msg)
                    }
                );    
        
            } else {
                broadcastEvent(EVENT_TYPE.ANALYSIS_ERROR, `Learning engine tool exited with exit code ${exit_code}`);
                update_process_lock = false;
            }
        },
        (progress_msg) => {
            console.log("progress:",progress_msg);
            //broadcastEvent(EVENT_TYPE.SUGGESTED_PREREAD_PROGRESS,progress_msg)
        },
        (error_msg) => {
            console.log("err:",error_msg);
            broadcastEvent(EVENT_TYPE.ANALYSIS_WARNING,error_msg)
        }
    );
}


function LaunchLanguageTool_Spawn(cmd, args, exit_cb, progress_cb, error_cb) {
    console.log("Starting Process.");
    var spawn_args = [`tools/${cmd}`].concat(args);
    console.log(spawn_args);
    var child = child_process.spawn("python", spawn_args);

    child.on('error', (err) => {
        console.error('Failed to start subprocess.',JSON.stringify(err));
      });    

    child.stdout.setEncoding('utf8');
    child.stdout.on('data', function(data) {
        //console.log('stdout: ' + data);
        progress_cb(data.toString());
    });

    child.stderr.setEncoding('utf8');
    child.stderr.on('data', function(data) {
        console.log('stderr: ' + data);
        error_cb(data.toString());
    });

    child.on('close', function(code) {
        exit_cb(code);
    });
}


async function getSuggestedPreread(title_id) {
    console.log(`getSuggestedPreread ${title_id}`);
    let preread_dir = 'lang/suggested_preread/';
    let filename = preread_dir + title_id + '.json';
    if (fs.existsSync(filename)) {
        let data = fs.readFileSync(filename, "utf8");
        let json_data = JSON.parse(data);
        return {
            success : true,
            'suggested_preread' : json_data,
        }
    }
    return {
        success : false,
        error_message : "Analysis not yet done",
    }
}


async function calculateSuggestedPreread(title_id,target_selection,source_selection,source_filter) {
    console.log(`getSuggestedPreread ${title_id}`);
    let preread_dir = 'lang/suggested_preread/';
    if (!fs.existsSync(preread_dir)) {
        fs.mkdirSync(preread_dir, { recursive: true });
    }
    
    if (suggest_preread_lock.has(title_id)) {
        return {
            success : false,
            error_message : "Already analyzing..",
        }    
    }
    suggest_preread_lock.add(title_id);

    console.log("Recalculating suggested preread")

    let tool_args = ["suggest_preread",title_id,'--progress-output','--filter',source_filter]
    tool_args.push('--target_scope')
    tool_args.push(target_selection)
    tool_args.push('--source_scope')
    tool_args.push(source_selection)
    LaunchLanguageTool_Spawn(ANALYZER_TOOL,tool_args,
        (exit_code) => {
            console.log("exit code:",exit_code);
            suggest_preread_lock.delete(title_id);
            if (exit_code == 0) {
                broadcastEvent(EVENT_TYPE.UPDATED_SUGGESTED_PREREAD,"")
            }
        },
        (progress_msg) => {
            console.log("progress:",progress_msg);
            broadcastEvent(EVENT_TYPE.SUGGESTED_PREREAD_PROGRESS,progress_msg)
        },
        (error_msg) => {
            console.log("err:",error_msg);
            broadcastEvent(EVENT_TYPE.ANALYSIS_ERROR,error_msg)
        }
    );
    return {
        success : true,
        error_message : "Starting to recalculate..",
    }
}

async function updateManuallySetWordLearningStage(data) {
    let word_id = data.word_id;
    let stage = data.stage;
    let word_metadata = data.metadata;
    let timestamp = Math.trunc(Date.now()/1000);
    let history_entry = { 't' : timestamp, 's':stage, 'm':word_metadata};
    let replaced_last_entry = false;
    let word_history = await getManuallySetWordLearningStateChanges(data.user_id, word_id)
    if (word_history !== null) {
        let last_timestamp = word_history[word_history.length-1].t;
        if (timestamp - last_timestamp < LEARNING_STAGE_CHANGE_REMORSE_PERIOD) {
            word_history[word_history.length-1] = history_entry
            replaced_last_entry = true;
        } else {
            word_history.push(history_entry);
        }
    } else {
        word_history = [history_entry];
    }
    console.log(`Updated ${word_id} history to ${JSON.stringify(word_history)}`)
    await updateManuallySetWordLearningStateChanges(data.user_id, word_id, word_history)
    return replaced_last_entry;
}

async function getWordHistory(data) {
    let word_history = await getUserWordHistory(data.user_id, data.word_id)
    if (word_history == null) {
        word_history = [];
    }
    return word_history;
}

function broadcastEvent(event_type, msg) {
    console.log(`broadcastEvent ${event_type}: ${msg}`);
    for (const client of clients) {
        client.emit('event',{'event_type':event_type,'msg':msg});
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
			client.on('event', (event) => {
                let data;
                //console.log(`sending updated event '${event.event_type}' to ${client.clientId}`)
                data = JSON.stringify(event);
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
            'favourite' : await toggleFavourite(data.manga_id)
        };
	} else if (data.func == 'mass_set_chapter_reading_status') {
        await massSetChapterReadingStatus(data.status_list),
        ret= {success : true};
    } else if (data.func == 'get_suggested_preread') {
        ret= await getSuggestedPreread(data.title_id);
        return json(ret);
    } else if (data.func == 'calculate_suggested_preread') {
        ret= await calculateSuggestedPreread(data.title_id,data.target_selection,data.source_selection,data.source_filter);
        return json(ret);
    } else if (data.func == 'update_learning_settings') {
        await updateLearningSettings(data.settings);
        ret= {success : true};
    } else if (data.func == 'update_manually_set_word_learning_stage') {
        ret= {
            success : true, 
            'replaced_last_entry' : await updateManuallySetWordLearningStage(data.param)
        };
    } else if (data.func == 'get_word_history') {
        ret= {
            success : true, 
            'history' : await getWordHistory(data.param)
        };
    } else if (data.func == 'update_anki_settings') {
        await updateAnkiSettings(data.settings);
        ret= {success : true};
    }
    console.log("POST /user_data return: " + JSON.stringify(ret));
	return json(ret);
}