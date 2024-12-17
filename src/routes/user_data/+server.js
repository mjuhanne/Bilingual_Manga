import { json } from '@sveltejs/kit';
import db from "$lib/db";
import { AugmentMetadataWithUserData, AugmentMetadataWithCustomLanguageSummary, saveUserData, saveUserSetWords, EVENT_TYPE } from "$lib/UserDataTools.js";
import fs from "fs";
import {exec} from "node:child_process";
import child_process from "node:child_process";
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

let suggest_preread_lock = new Set();

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
        db['user_data'].favourites = db['user_data'].favourites.filter((id) => id != manga_id);
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
    db['user_data']['timestamp'] = Date.now();
	saveUserData(db);
    updateCustomLanguageAnalysis();
}

const updateAnkiSettings = (settings) => {
    db['user_data']['anki_settings'] = settings
	saveUserData(db);
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
    db['user_data']['timestamp'] = Date.now();
    saveUserData(db);
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
                                updateMetadata();
                                AugmentMetadataWithUserData(db);
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
    if (!('timestamp' in db['user_data'])) {
        return {
            success : false,
            error_message : "Language analysis settings not yet configured!",
        }    
    }
    console.log(`getSuggestedPreread ${title_id} user data timestamp ${db['user_data']['timestamp']}`);
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
    if (!('timestamp' in db['user_data'])) {
        return {
            success : false,
            error_message : "Language analysis settings not yet configured!",
        }    
    }
    console.log(`getSuggestedPreread ${title_id} user data timestamp ${db['user_data']['timestamp']}`);
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
            'favourite' : toggleFavourite(data.manga_id)
        };
	} else if (data.func == 'mass_set_chapter_reading_status') {
        massSetChapterReadingStatus(data.status_list),
        ret= {success : true};
    } else if (data.func == 'get_suggested_preread') {
        ret= await getSuggestedPreread(data.title_id);
        return json(ret);
    } else if (data.func == 'calculate_suggested_preread') {
        ret= await calculateSuggestedPreread(data.title_id,data.target_selection,data.source_selection,data.source_filter);
        return json(ret);
    } else if (data.func == 'update_learning_settings') {
        updateLearningSettings(data.settings);
        ret= {success : true};
    } else if (data.func == 'update_manually_set_word_learning_stage') {        
        ret= {
            success : true, 
            'replaced_last_entry' : updateManuallySetWordLearningStage(data.stage_data)
        };
    } else if (data.func == 'update_anki_settings') {
        updateAnkiSettings(data.settings);
        ret= {success : true};
    }
    console.log("POST /user_data return: " + JSON.stringify(ret));
	return json(ret);
}