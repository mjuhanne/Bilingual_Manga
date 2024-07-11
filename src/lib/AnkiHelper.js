import {obj} from '$lib/store.js';

export const DEFAULT_ANKI_SETTINGS = {
    'address':'http://127.0.0.1:8765',
    'kanji' : {
        'deck':'',
        'field':''
        }, 
    'output' : {
        'deck':'',
        'model':'',
        'fields' : {}
    } 
};

export const ANKI_FIELD_TYPES = {
    NONE        : "None",
    EXPRESSION     : "Expression",
    READING     : "Reading",
    SENTENCE  : "Sentence",
    GLOSSARY    : "Glossary",
    JAP_PIC   : "Japanese image",
    ENG_PIC   : "English image",
};


let anki_settings = DEFAULT_ANKI_SETTINGS;

let meta;
obj.subscribe(value => { 
        if (value != "") {
            meta=value;
            let user_data=meta['0'].user_data
            if ('anki_settings' in user_data) {
                for (let k of Object.keys(user_data['anki_settings'])) {
                    anki_settings[k] = user_data['anki_settings'][k];
                }
            }
        }
    });

    
export function checkAnkiSettings() {
    if (anki_settings['output']['deck'] == '' ||
        anki_settings['output']['model'] == '' || getWordField() == '') {
            return false;
        }
    return true;
}

function getWordField() {
    for (let field of Object.keys(anki_settings['output']['fields'])) {
        if (anki_settings['output']['fields'][field] == ANKI_FIELD_TYPES.EXPRESSION) {
            return field;
        }
    }
    return '';
}

export async function checkIfCardExists(term) {
    let params = {
        "notes": [ {
                "deckName" : anki_settings['output']['deck'],
                "modelName" : anki_settings['output']['model'],
                "fields" : { }
        } ]
    }
    params["notes"][0]["fields"][ getWordField() ] = term
    let res = await anki_invoke(anki_settings['address'], 'canAddNotes', 6, params);
    return !res[0];
}

export async function getNoteIds(term) {
    let params = {
            "query" : "deck:" + anki_settings['output']['deck'] + " " +
            getWordField() + ":" + term
    }
    return await anki_invoke(anki_settings['address'], 'findNotes', 6, params);
}

const blobToBase64 = async blob => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result
        const [_, base64] = dataUrl.split(','); 
        resolve(base64)
      }
      reader.onerror = err => reject(err)
      reader.readAsDataURL(blob)
    })
  }

export async function augmentNote(noteId, word, sentence, images, include_images ) {
    let params = {
            "note" : {
                "id" : noteId,
                "fields" : {  },
                "picture" : [
                ]
            }
        }

    for (let field of Object.keys(anki_settings['output']['fields'])) {
        let field_type = anki_settings['output']['fields'][field];
        if (field_type == ANKI_FIELD_TYPES.SENTENCE) {
            params["note"]["fields"][ field ] = sentence;
        } else if (field_type == ANKI_FIELD_TYPES.JAP_PIC) {
            // clear the previous image field
            params["note"]["fields"][ field] = ""
            params["note"]["picture"].push(
                {
                    "data": await blobToBase64(images["jap"]),
                    "filename":word+'_jap_pic.jpeg',
                    "fields":[field]
                },
            );
        } else if (field_type == ANKI_FIELD_TYPES.ENG_PIC) {
            // clear the previous image field
            params["note"]["fields"][ field] = ""
            params["note"]["picture"].push(
                {
                    "data": await blobToBase64(images["eng"]),
                    "filename":word+'_eng_pic.jpeg',
                    "fields":[field]
                },
            );
        }
    }
    //console.log(JSON.stringify(params));
    return await anki_invoke(anki_settings['address'], 'updateNoteFields', 6, params);
}

function glossaryList2Html(glossary_list) {
    let html = '<div><ol>';
    for (let glossary of glossary_list) {
        html += '<li>' + glossary + '</li>'
    }
    html += '</ol></div>'
    return html;
}

export async function createNote(word,readings,sentence,glossary,images,include_images) {
    let params = {
            "note" : {
                "deckName" : anki_settings['output']['deck'],
                "modelName" : anki_settings['output']['model'],
                "fields" : {  },
                "picture" : [
                ]
            }
        }

    for (let field of Object.keys(anki_settings['output']['fields'])) {
        let field_type = anki_settings['output']['fields'][field];
        if (field_type == ANKI_FIELD_TYPES.SENTENCE) {
            params["note"]["fields"][ field ] = sentence;
        } else if (field_type == ANKI_FIELD_TYPES.JAP_PIC && include_images['jap']) {
            // clear the previous image field
            params["note"]["fields"][ field] = ""
            params["note"]["picture"].push(
                {
                    "data": await blobToBase64(images["jap"]),
                    "filename":word+'_jap_pic.jpeg',
                    "fields":[field]
                },
            );
        } else if (field_type == ANKI_FIELD_TYPES.ENG_PIC && include_images['eng']) {
            // clear the previous image field
            params["note"]["fields"][ field] = ""
            params["note"]["picture"].push(
                {
                    "data": await blobToBase64(images["eng"]),
                    "filename":word+'_eng_pic.jpeg',
                    "fields":[field]
                },
            );
        } else if (field_type == ANKI_FIELD_TYPES.GLOSSARY) {
            params["note"]["fields"][field] = glossaryList2Html(glossary); 
        } else if (field_type == ANKI_FIELD_TYPES.READING) {
            params["note"]["fields"][field] = readings.join(', '); 
        } else if (field_type == ANKI_FIELD_TYPES.EXPRESSION) {
            params["note"]["fields"][field] = word; 
        }
    }
    return await anki_invoke(anki_settings['address'], 'addNote', 6, params);
}

export function anki_invoke(address, action, version, params={}) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.addEventListener('error', (err) => {
            reject(`failed to issue request: ${err}`)
        });
        xhr.addEventListener('load', () => {
            try {
                const response = JSON.parse(xhr.responseText);
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
        });

        xhr.open('POST', address);
        xhr.send(JSON.stringify({action, version, params}));
    });
}

