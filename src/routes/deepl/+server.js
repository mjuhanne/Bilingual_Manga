import { json } from '@sveltejs/kit';
import { updateUserData, getUserData } from '$lib/collections.js'
import { DEFAULT_USER_ID } from '$lib/UserDataTools.js'

async function fetchTranslation(text,deepl_key) {
    try {
        const response = await fetch( "https://api-free.deepl.com/v2/translate", {
            headers: {
                "Content-Type" : "application/json",
                "Authorization" : `DeepL-Auth-Key ${deepl_key}`
            },
            method: 'POST',
            body: JSON.stringify({
                'text' : [text],
                "target_lang":"en",
            })
        });
        let res;
        if (response.ok) {
            let res_json = await response.json()
            console.log("ok",JSON.stringify(res_json))
            res = {'success':true,'translation':res_json['translations'][0]["text"]}
        } else {
            console.log("failed",response)
            res = {'success':false,'error':response.status}
        }
        return res;
    } catch (error) {
        console.error(error.message);
        return {'success':false, 'error':error.message}
    }
}

async function saveKey(deepl_key) {
    let test_text = "どうぞよろしくお願いします"
    let res = await fetchTranslation(test_text,deepl_key)
    console.log("res",JSON.stringify(res))
    if (res.success) {
        await updateUserData(DEFAULT_USER_ID, 'deepl_key', deepl_key)
        console.log("Saved DeepL key")
        return {'success':true}
    } else {
        console.log("DeepL test translation failed!")
    }
    return res
}


export async function POST({ request }) {
	const data = await request.json();
	console.log("POST /deepl: " + JSON.stringify(data) );
	let ret = { success : false, 'error':'Undefined function'};
	if (data.func == 'save_key') {
        ret = await saveKey(data.deepl_key);
    } else if (data.func == 'translate') {
        var user_data = await getUserData(DEFAULT_USER_ID);
        if ('deepl_key' in user_data) {
            if (user_data['deepl_key'] != '') {
                ret = await fetchTranslation(data.text,user_data['deepl_key']);
            } else {
                ret = {'success':false,'error':'DeepL key not yet set!'}
            }
        } else {
            ret = {'success':false,'error':'DeepL key not yet set!'}
        }
    } 
    return json(ret);
}
