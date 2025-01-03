import { error } from '@sveltejs/kit';
import {AugmentTitleMetadataWithUserData, DEFAULT_USER_ID} from '$lib/UserDataTools.js'
import { searchCollection, getBilingualMangaSettings, getUserData, getMangaMetadataForSingleTitle} from "$lib/collections.js";

// Replace uncommon characters in local file names with '_'  
function cleanFileNames(manga_data) {
    let chapter_files = {'en':manga_data.en_data["ch_en"], 'jp':manga_data.jp_data["ch_jp"]};
    let chapter_names = {'en':manga_data.en_data["ch_naen"], 'jp':manga_data.jp_data["ch_najp"]};
    for (let lang in chapter_files) {
        let chapter_set = chapter_files[lang];
        let ch_i = 0;
        for (let ch in chapter_set) {
            let files = chapter_set[ch]
            for (let f_i in files) {
                let filename = files[f_i];
                let new_filename = filename.replace(/[^A-Za-z0-9 ,+'!_&\%@#\-\[\].\/()]+/g, '_');
                if (filename != new_filename) {
                    console.log(` * Warning: ${lang} chapter ${chapter_names[lang][ch_i]}:'${filename}' -> '${new_filename}'`)
                    chapter_files[lang][ch][f_i] = new_filename;
                }
            }
            ch_i += 1;
        }
    }
}

/** @type {import('./$types').PageServerLoad} */
export async function load({params,url}) {   
    let id=params["slug"]

    const meta_data_by_id = await searchCollection("br_metadata", "_id", id);

    var meta_data = undefined;
    if (meta_data_by_id.length>0) {
        meta_data = meta_data_by_id[0]
    } else {
        const meta_data_by_enslug = await searchCollection("br_metadata", "enslug", id);
        if (meta_data_by_enslug.length>0) {
            meta_data = meta_data_by_enslug[0]
            id = meta_data['_id']
            url.searchParams.set('lang',"en");
        } else {
            const meta_data_by_jpslug = await searchCollection("br_metadata", "jpslug", id);
            if (meta_data_by_jpslug.length>0) {
                meta_data = meta_data_by_jpslug[0]
                id = meta_data['_id']
                url.searchParams.set('lang',"jp");
            }
        }   
    }

    meta_data = await getMangaMetadataForSingleTitle(DEFAULT_USER_ID, id)

    if (meta_data !== undefined) {

        const data = await searchCollection("br_data", "_id", id);

        if (data.length>0) {
            const title_data = data[0];

            const settings = await getBilingualMangaSettings();
            const user_data = await getUserData(DEFAULT_USER_ID);

            let jsonc;
            const ref = url.searchParams.get('lang');
            const chen = url.searchParams.get('chen');
            const chjp = url.searchParams.get('chjp');
            const enp = url.searchParams.get('enp');
            const jpp = url.searchParams.get('jpp');
    
            let ipfsss=""
            let aa1=await fetch(`${settings.cdn1}/json/dw.json`)
            let aa2 = await aa1.json()
            let pm = aa2["pm"]
    
            if(pm.includes(id) || !title_data.from_bilingualmanga_org)
            {
                ipfsss=settings.ipfsgate1
                cleanFileNames(title_data);
            }
            else
            {
                ipfsss=settings.ipfsgate
            }
            title_data.is_book = meta_data.is_book
    
            // create list of jp chapter ids and jp chapter id -> chapter name lookup table
            let chapter_ids = [];
            title_data.jp_data.chapter_names = {};
            let i = 0;
            for (let ch of title_data.jp_data.ch_jph) {
                let chapter_id = ch.split('/')[0];
                chapter_ids.push(chapter_id);
                title_data.jp_data.chapter_names[chapter_id] = title_data.jp_data.ch_najp[i];
                i += 1;
            }
            title_data.jp_data.chapter_ids = chapter_ids;

            // create a list of chapters per volume
            for (let vol in title_data.jp_data.vol_jp) {
                let vol_chapters = [];
                let start_c = title_data.jp_data.vol_jp[vol].s;
                let end_c = title_data.jp_data.vol_jp[vol].e
                for (let idx = start_c; idx <= end_c; idx ++ ) {
                    vol_chapters.push(chapter_ids[idx]);
                }
                title_data.jp_data.vol_jp[vol].chapter_ids = vol_chapters;
            };

            // Add en chapter id lookup table
            chapter_ids = [];
            for (let ch of title_data.en_data.ch_enh) {
                let chapter_id = ch.split('/')[0];
                chapter_ids.push(chapter_id);
            }
            title_data.en_data.chapter_ids = chapter_ids;

            AugmentTitleMetadataWithUserData(meta_data, title_data, user_data)

            let jsona={"p":id,"l":ref,"chen":chen,"chjp":chjp,"enp":enp,"jpp":jpp,"manga_data":title_data,"meta_data":meta_data,"ipfs":ipfsss};
            jsonc = JSON.stringify(jsona);
            jsonc=JSON.parse(jsonc)
            return jsonc;
        }
        throw error(404, 'Data not found');
    }
    throw error(404, 'Not found');
}
