import { json } from '@sveltejs/kit';
import fs from "fs";
import util from "node:util";
import { EventEmitter } from 'node:events';
import fetch from "node-fetch"
import { STAGE } from '$lib/LearningData.js'

const files = {'kanji':'lang/user/anki_kanjis.json'}

const ANKI_KNOWN_INTERVAL = 21  // 21 days

let clients = [];
let fetch_process_lock = false;

function anki_server_invoke(address, action, version, params={}) {
    return new Promise((resolve, reject) => {

        const body = JSON.stringify({action, version, params});

        //console.log("Body",body);

        fetch(address, {
            method: 'post',
            body: body,
            headers: {'Content-Type': 'application/json'}
        }).then(
            (res)=>{
               res.json().then((response) => {
                    //console.log("response: ",response);
                    try {
                        if (Object.getOwnPropertyNames(response).length != 2) {
                            throw 'response has an unexpected number of fields';
                        }
                        if (!response.hasOwnProperty('error')) {
                            throw 'response is missing required error field';
                        }
                        if (!response.hasOwnProperty('result')) {
                            throw 'response is missing required result field';
                        }
                        if (response.error) {
                            throw response.error;
                        }
                        resolve(response.result);
                    } catch (e) {
                        reject(e);
                    }
                })
            },
            (err)=>{
                reject(`failed to issue request: ${err}`)
            }
        );
    });
}


// This is the event handler for user data consumers
export async function GET({ request }) {

	console.log("GET /anki: " + JSON.stringify(request) );

    const client = new EventEmitter();
    client.clientId = Date.now();;
	clients.push(client);

    const stream = new ReadableStream({
		start(controller) {
            console.log(`${client.clientId} New user_data connection`);
            let data = JSON.stringify({'event_type':"stream connected"});
            controller.enqueue(`event: message\ndata:${data}\n\n`);
			client.on('event', (event_type) => {
                let data;
                console.log(`sending updated event '${event_type}' to ${client.clientId}`)
                data = JSON.stringify({'event_type':event_type,'msg':'test'});
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

function broadcastEvent(event_type) {
    console.log("broadcastEvent " + event_type);
    for (const client of clients) {
        client.emit('event',event_type);
    }
}

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}

async function fetchValues(anki_settings, collection) {
    if (fetch_process_lock) {
        console.log("Already fetching!")
        return;
    }
    broadcastEvent("Processing..");
    fetch_process_lock = true;
    let values = [];
    let card_intervals = [];
    try {
        let card_ids = await anki_server_invoke(anki_settings['address'],'findCards', 6, {"query":"deck:"+anki_settings[collection]['deck']});
        if (card_ids.length>0) {

            await delay(100);
            broadcastEvent("Loading intervals..");
            card_intervals = await anki_server_invoke(anki_settings['address'],'getIntervals', 6, {"cards":card_ids});
            await delay(100);

            broadcastEvent("Fetching card data..");
            // Convert cards to notes because notesInfo is MUCH faster than cardsInfo
            let note_ids = await anki_server_invoke(anki_settings['address'],'cardsToNotes', 6, {'cards':card_ids});

            let chunk_size = 100;
            let note_chunk_array = [];
            for (let i = 0; i < note_ids.length; i += chunk_size) {
                note_chunk_array.push(note_ids.slice(i, i + chunk_size));
            }
            for (let note_chunk of note_chunk_array) {
                //console.log("Fetching",note_chunk);
                await delay(100);

                const card_info = await anki_server_invoke(anki_settings['address'],'notesInfo', 6, {"notes":note_chunk});
                let chunk = [];
                for (let ci of card_info) {
                    chunk.push(ci['fields'][anki_settings[collection]['field']]['value'])
                }
                console.log("Chunk: ",chunk);
                values = values.concat(chunk);
                broadcastEvent(`Loaded ${values.length} / ${note_ids.length} cards`);
            }
            broadcastEvent(`Completed loading ${values.length} / ${note_ids.length} cards`);
        }
    } catch (err) {
        broadcastEvent(`error: ${err}`);
        values = [];
    }
    fetch_process_lock = false;
    if (values.length>0) {
        let stages = {}
        for (let i in values) {
            let stage = STAGE.UNKNOWN;
            if (card_intervals[i] >= ANKI_KNOWN_INTERVAL) {
                stage = STAGE.KNOWN; // mature card
            } else if (card_intervals[i] > 0) {
                stage = STAGE.PRE_KNOWN; // immature card but let's not classify this as learning anymore
            }
            stages[values[i]] = stage;
        }
        console.log("Saving to ",files[collection]);
        let data = {
            'timestamp': Math.round(Date.now()/1000),
            'item_learning_stages':stages
        }
        fs.writeFile (files[collection], JSON.stringify(data), function(err) {
            if (err) throw err;
        });
    }
}


export async function POST({ request }) {
	const data = await request.json();
	console.log("POST /anki: " + JSON.stringify(data) );
	let ret = { success : false};
	if (data.func == 'fetch_values') {
        fetchValues(data.settings,data.collection);
        ret = {
            success : true // unsuccessful operation for this async function will be signaled via broadcastEvent
        };
    } 
    return json(ret);
}
