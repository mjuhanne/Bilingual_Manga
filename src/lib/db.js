import fetch from 'node-fetch'
import { AugmentMetadataWithUserData, AugmentMetadataWithCustomLanguageSummary, checkUserData } from '$lib/UserDataTools.js'
console.log("Loading data files..")
const response = await fetch('http://localhost:3300/json/BM_data.manga_metadata.json')
if (!response.ok) {
    throw new Error("BM_data.manga_metadata.json not found! Please install the metadata files and restart the server")
}
const a = await response.json()
const response1 = await fetch('http://localhost:3300/json/BM_data.manga_data.json')
const b = await response1.json()
const response_r = await fetch('http://localhost:3300/json/ratings.json')
const ratings = await response_r.json()
const response_l = await fetch('http://localhost:3300/json/lang_summary.json')
if (!response_l.ok) {
    throw new Error("lang_summary.json not found! Please unzip lang_summary.zip and restart the server")
}
const lang_summary = await response_l.json()


const response_emmd = await fetch('http://localhost:3300/json/ext.manga_metadata.json')
if (response_emmd.ok) {
    const ext_mangametadata = await response_emmd.json()
    ext_mangametadata.forEach(element => {
        a[0]['manga_titles'].unshift(element)
    });
}

const response_emd = await fetch('http://localhost:3300/json/ext.manga_data.json')
if (response_emd.ok) {
    const ext_mangadata = await response_emd.json()
    ext_mangadata.forEach(element => {
        //console.log(element)
        b.unshift(element)
    });
}

let ext_ratings = {}
const response_er = await fetch('http://localhost:3300/json/ext_ratings.json')
if (response_er.ok) {
    ext_ratings = await response_er.json()
}

let custom_lang_summary = undefined
const response_cl = await fetch('http://localhost:3300/json/custom_lang_analysis.json')
if (response_cl.ok) {
    custom_lang_summary = await response_cl.json();
} else {
    console.log("Custom language analysis file not yet created")
}

let user_set_words = {}
const response_usw = await fetch('http://localhost:3300/json/user_set_word_ids.json')
if (response_usw.ok) {
    user_set_words = await response_usw.json();
} else {
    console.log("User set word ids file not yet created")
}

let user_data;
const response_ud = await fetch('http://localhost:3300/json/user_data.json')
if (response_ud.ok) {
    user_data = await response_ud.json()
} else {
    console.log("No user_data.json was found. Reverting to default settings");
    user_data = {}
}
checkUserData(user_data);

console.log("Loading data files complete!")

const AugmentMetadataWithRatings = (db) => {
    let manga_titles = db['manga_metadata']['0'].manga_titles;
    let ratings = db['ratings'];
    let ext_ratings = db['ext_ratings'];
    console.log("Augment manga_metadata with " + Object.keys(ratings).length + " ratings");

    manga_titles.forEach(element => {
        let id = element.enid;

        if (id in ratings) {
            element["rating_data"] = ratings[id]
        } else if (id in ext_ratings) {
            if (ext_ratings[id]['series_id'] != -1) {
                element["rating_data"] = ext_ratings[id]
            } else {
                element["rating_data"] = { "url":"http://mangaupdates.com", "rating":-1, "votes": 0, "last_updated":"N/A"}
            }
        } else {
            element["rating_data"] = { "url":"http://mangaupdates.com", "rating":-1, "votes": 0, "last_updated":"N/A"}
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

    if ('average' in ls) {
        db['manga_metadata']['0'].average_manga = ls['average'];
    }
};


const admin={
    "manga_metadata":a,
    "manga_data":b,
    "ratings":ratings,
    "ext_ratings":ext_ratings,
    "lang_summary":lang_summary,
    "user_data":user_data,
    "custom_lang_summary":custom_lang_summary,
    "user_set_words":user_set_words,
}

AugmentMetadataWithUserData(admin);
AugmentMetadataWithRatings(admin);
AugmentMetadataWithLanguageSummary(admin);
if (admin['custom_lang_summary'] !== undefined) {
    AugmentMetadataWithCustomLanguageSummary(admin['manga_metadata'],admin['custom_lang_summary']);
}

export default admin;
