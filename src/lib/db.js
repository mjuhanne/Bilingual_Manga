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
const response_r = await fetch('http://localhost:3300/json/mangaupdates.json')
const mangaupdates = await response_r.json()
const response_l = await fetch('http://localhost:3300/json/lang_summary.json')
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

let ext_mangaupdates = {}
const response_er = await fetch('http://localhost:3300/json/ext_mangaupdates.json')
if (response_er.ok) {
    ext_mangaupdates = await response_er.json()
}

const response_el = await fetch('http://localhost:3300/json/ext_lang_summary.json')
let ext_lang_summary = {}
if (response_el.ok) {
    ext_lang_summary = await response_el.json();
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

const AugmentMetadataWithmangaupdates = (db) => {
    let manga_titles = db['manga_metadata']['0'].manga_titles;
    let mangaupdates = db['mangaupdates'];
    let ext_mangaupdates = db['ext_mangaupdates'];
    console.log("Augment manga_metadata with " + Object.keys(mangaupdates).length + " mangaupdates.com entries");

    let global_avg_votes = 0;
    let valid_entries = 0;

    function process_categories(element,id,mangaupdates_data) {
        let avg_votes = 0;
        let category_list = [];
        let category_scores = {};
        let category_votes = {};
        for (let categoryData of mangaupdates_data[id]['categories']) {
            avg_votes += categoryData.votes;
            category_votes[categoryData.category] = categoryData.votes;
            category_list.push(categoryData.category)
        }
        if (mangaupdates_data[id]['categories'].length>0) {
            avg_votes /= mangaupdates_data[id]['categories'].length;
        }
        for (let categoryData of mangaupdates_data[id]['categories']) {
            if (categoryData.votes < avg_votes*2/3) {
                category_scores[categoryData.category] = 1;
            } else if (categoryData.votes > avg_votes*4/3) {
                category_scores[categoryData.category] = 3;
            } else {
                category_scores[categoryData.category] = 2;
            }
        }
        element["mangaupdates_data"]['avg_category_votes'] = avg_votes;
        element["mangaupdates_data"]['category_list'] = category_list;
        element["mangaupdates_data"]['category_votes'] = category_votes;
        element["mangaupdates_data"]['category_scores'] = category_scores;
        global_avg_votes += avg_votes;
        valid_entries += 1;
    }
    manga_titles.forEach(element => {
        let id = element.enid;

        if (id in mangaupdates) {
            element["mangaupdates_data"] = mangaupdates[id]
            process_categories(element,id,mangaupdates);
        } else if (id in ext_mangaupdates) {
            if (ext_mangaupdates[id]['series_id'] != -1) {
                element["mangaupdates_data"] = ext_mangaupdates[id]
                process_categories(element,id,ext_mangaupdates);
            } else {
                element["mangaupdates_data"] = { "url":"http://mangaupdates.com", "rating":-1, "votes": 0, "last_updated":"N/A", "categories":[],"category_list":[]}
            }
        } else {
            element["mangaupdates_data"] = { "url":"http://mangaupdates.com", "rating":-1, "votes": 0, "last_updated":"N/A", "categories":[],"category_list":[]}
        }
    });
    db['manga_metadata']['0'].average_category_vote_count = global_avg_votes / valid_entries;
};

const AugmentMetadataWithLanguageSummary = (db) => {
    let manga_titles = db['manga_metadata']['0'].manga_titles;
    let ls = db['lang_summary'];
    let els = db['ext_lang_summary'];
    console.log("Augment manga_metadata with language summary for " + Object.keys(ls).length + " titles and " + Object.keys(els).length + " external titles");

    manga_titles.forEach(element => {
        let id = element.enid;

        if (id in ls) {
            let l = ls[id];
            for (let k of Object.keys(l)) {
                element[k] = l[k];
            }
        } else if (id in els) {
            let l = els[id];
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
    "mangaupdates":mangaupdates,
    "ext_mangaupdates":ext_mangaupdates,
    "lang_summary":lang_summary,
    "ext_lang_summary":ext_lang_summary,
    "user_data":user_data,
    "custom_lang_summary":custom_lang_summary,
    "user_set_words":user_set_words,
}

AugmentMetadataWithUserData(admin);
AugmentMetadataWithmangaupdates(admin);
AugmentMetadataWithLanguageSummary(admin);
if (admin['custom_lang_summary'] !== undefined) {
    AugmentMetadataWithCustomLanguageSummary(admin['manga_metadata'],admin['custom_lang_summary']);
}

export default admin;
