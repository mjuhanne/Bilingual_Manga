import { json } from '@sveltejs/kit';
import db from "$lib/db";
import { AugmentMetadataWithUserData, saveUserData } from "$lib/UserDataTools.js";

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

const setReadingStatus = (chapter_ids,reading_data) => {
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

	saveUserData(db);
	AugmentMetadataWithUserData(db);
	return reading_data;
}

const updateComprehension = (chapter_ids, comprehension) => {
    let rs = db['user_data']['chapter_reading_status'];
    for (let c_id of chapter_ids) {
        if (c_id in rs) {
            rs[c_id].comprehension = comprehension;
        } else {
            throw ("Chapter " + c_id + " reading status not yet set!");
        }
    }
    db['user_data']['chapter_reading_status'] = rs;
	saveUserData(db);
	AugmentMetadataWithUserData(db);
	return comprehension;
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
	}
	console.log("POST /user_data return: " + JSON.stringify(ret));
	return json(ret);
}