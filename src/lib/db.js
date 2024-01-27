import fetch from 'node-fetch'
import { AugmentMetadataWithUserData, checkUserData } from '$lib/UserDataTools.js'
const response = await fetch('http://localhost:3300/json/admin.manga_metadata.json')
const a = await response.json()
const response1 = await fetch('http://localhost:3300/json/admin.manga_data.json')
const b = await response1.json()
const response_r = await fetch('http://localhost:3300/json/ratings.json')
const ratings = await response_r.json()
const response_l = await fetch('http://localhost:3300/json/lang_summary.json')
const lang_summary = await response_l.json()

let user_data;

try {
    const response_ud = await fetch('http://localhost:3300/json/user_data.json')
    user_data = await response_ud.json()
    console.log("User_data: " + JSON.stringify(user_data));
} catch (error) {
    console.log("No user_data.json was found. Reverting to default settings");
    user_data = {}
}
checkUserData(user_data);

const AugmentMetadataWithRatings = (db) => {
    let manga_titles = db['manga_metadata']['0'].manga_titles;
    let ratings = db['ratings'];
    console.log("Augment manga_metadata with " + Object.keys(ratings).length + " ratings");

    manga_titles.forEach(element => {
        let id = element.enid;

        if (id in ratings) {
            element["rating_data"] = ratings[id]
        } else {
            element["rating_data"] = { "url":"http://mangaupdates.com", "rating":"N/A", "votes": 0, "last_updated":"N/A"}
        }
    });
};

const AugmentMetadataWithLanguageSummary = (db) => {
    let manga_titles = db['manga_metadata']['0'].manga_titles;
    let ls = db['lang_summary'];
    console.log("Augment manga_metadata with language summary for " + Object.keys(ls).length + " titles");

    manga_titles.forEach(element => {
        let id = element.enid;

        if (id in ls) {
            let l = ls[id];
            for (let k of Object.keys(l)) {
                element[k] = l[k];
            }
        }
    });
};

const admin={"manga_metadata":a,"manga_data":b,"ratings":ratings,"lang_summary":lang_summary,"user_data":user_data}

AugmentMetadataWithUserData(admin);
AugmentMetadataWithRatings(admin);
AugmentMetadataWithLanguageSummary(admin);

export default admin;
