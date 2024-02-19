import fs from "fs"

export const EVENT_TYPE = {
    CONNECTED           : "OK",
    UPDATING_STATS      : "Updating statistics",
    UPDATING_ANALYSIS   : "Updating analysis",
    UPDATED_STATS       : "Statistics updated",
    UPDATED_ANALYSIS    : "Analysis updated",
    CALCULATION_ERROR   : "Error calculating comprehension data",
}

const empty_reading_status = {
    'status':'Unread',
    'comprehension' : 0,
};

export const saveUserData = (db) => {
    console.log("saveUserData"); // + JSON.stringify(db['user_data']));
	fs.writeFile ("json/user_data.json", JSON.stringify(db['user_data']), function(err) {
		if (err) throw err;
    });
};

export const saveUserSetWords = (db) => {
    console.log("saveUserSetWords");
	fs.writeFile ("json/user_set_words.json", JSON.stringify(db['user_set_words']), function(err) {
		if (err) throw err;
    });
};

export const checkUserData = (user_data) => {
    if (!("favourites" in user_data)) {
        user_data["favourites"] = [];
    }
    if (!("chapter_reading_status" in user_data)) {
        user_data["chapter_reading_status"] = {};
    }
}

export const AugmentMetadataWithCustomLanguageSummary = (manga_metadata, custom_lang_summary) => {
    let manga_titles = manga_metadata['0'].manga_titles;
    let ls = custom_lang_summary['analysis']['series_analysis'];
    console.log("Augment manga_metadata with custom language summary for " + Object.keys(ls).length + " titles");
    
    manga_metadata['0'].custom_lang_summary_timestamp = custom_lang_summary['timestamp']
    manga_titles.forEach(element => {
        let id = element.enid;

        if (id in ls) {
            let l = ls[id];
            element['total_statistics']['pct_known_words'] = l['total_statistics']['words']['pct_known_pre_known'];
            element['unique_statistics']['pct_known_words'] = l['unique_statistics']['words']['pct_known_pre_known'];

            element['total_statistics']['pct_known_kanjis'] = l['total_statistics']['kanjis']['pct_known_pre_known'];
            element['unique_statistics']['pct_known_kanjis'] = l['unique_statistics']['kanjis']['pct_known_pre_known'];

            element['total_statistics']['num_unknown_words'] = l['total_statistics']['words']['num_unknown'];
            element['unique_statistics']['num_unknown_words'] = l['unique_statistics']['words']['num_unknown'];

            element['total_statistics']['num_unknown_kanjis'] = l['total_statistics']['kanjis']['num_unknown'];
            element['unique_statistics']['num_unknown_kanjis'] = l['unique_statistics']['kanjis']['num_unknown'];

            element['total_statistics']['jlpt_known_k_level_pct'] = l['total_statistics']['kanjis']['jlpt_level_pct'];
            element['unique_statistics']['jlpt_known_k_level_pct'] = l['unique_statistics']['kanjis']['jlpt_level_pct'];
            element['total_statistics']['jlpt_known_w_level_pct'] = l['total_statistics']['words']['jlpt_level_pct'];
            element['unique_statistics']['jlpt_known_w_level_pct'] = l['unique_statistics']['words']['jlpt_level_pct'];
            element['total_statistics']['jlpt_known_k_level_per_v'] = l['total_statistics']['kanjis']['jlpt_level_per_v'];
            element['unique_statistics']['jlpt_known_k_level_per_v'] = l['unique_statistics']['kanjis']['jlpt_level_per_v'];
            element['total_statistics']['jlpt_known_w_level_per_v'] = l['total_statistics']['words']['jlpt_level_per_v'];
            element['unique_statistics']['jlpt_known_w_level_per_v'] = l['unique_statistics']['words']['jlpt_level_per_v'];
        }
    });

    ls = custom_lang_summary['analysis']['next_unread_chapter_analysis'];
    console.log("Augment manga_metadata with custom language summary for " + Object.keys(ls).length + " next unread chapters");
    
    manga_titles.forEach(element => {
        let id = element.enid;

        if (id in ls) {
            let l = ls[id];
            element['total_statistics']['pct_known_words_next_ch'] = l['total_statistics']['words']['pct_known_pre_known'];
            element['unique_statistics']['pct_known_words_next_ch'] = l['unique_statistics']['words']['pct_known_pre_known'];

            element['total_statistics']['pct_known_kanjis_next_ch'] = l['total_statistics']['kanjis']['pct_known_pre_known'];
            element['unique_statistics']['pct_known_kanjis_next_ch'] = l['unique_statistics']['kanjis']['pct_known_pre_known'];

            element['total_statistics']['num_unknown_words_next_ch'] = l['total_statistics']['words']['num_unknown'];
            element['unique_statistics']['num_unknown_words_next_ch'] = l['unique_statistics']['words']['num_unknown'];

            element['total_statistics']['num_unknown_kanjis_next_ch'] = l['total_statistics']['kanjis']['num_unknown'];
            element['unique_statistics']['num_unknown_kanjis_next_ch'] = l['unique_statistics']['kanjis']['num_unknown'];

        }
    });

    ls = custom_lang_summary['analysis']['series_analysis_for_jlpt'];
    console.log("Augment manga_metadata with custom language summary for " + Object.keys(ls).length + " JLPT series analysis");
    
    manga_titles.forEach(element => {
        let id = element.enid;

        if (id in ls) {
            let l = ls[id];
            element['jlpt_improvement_pts'] = l['relative_points'];
            element['jlpt_improvement_words'] = l['num_new_known_words'];
            element['jlpt_improvement_kanjis'] = l['num_new_known_kanjis'];
        }
    });

};

export const AugmentMetadataWithUserData = (db) => {

    let user_data = db['user_data'];
    let read_chapters = 'chapter_reading_status' in user_data ? Object.keys(user_data['chapter_reading_status']) : [];
    let read_chapter_pct_by_manga = {};
    let chapter_names_by_manga = {};

    console.log("Augment manga_metadata with " +read_chapters.length + " read chapters");

    // Augment manga_data with chapter/volume reading status 
    // and count number of read chapters
    db['manga_data'].forEach(element => {

        let manga_id = element['_id']['$oid'];

        let chapter_ids = [];
        element.jp_data.chapter_reading_status = {};
        element.jp_data.chapter_names = {};
        let number_of_chapters_read = 0;

        let i = 0;
        for (let ch of element.jp_data.ch_jph) {
            let chapter_id = ch.split('/')[0];
            chapter_ids.push(chapter_id);
            if (read_chapters.includes(chapter_id)) {
                let reading_data = user_data['chapter_reading_status'][chapter_id];
                element.jp_data.chapter_reading_status[chapter_id] = reading_data;
                if (reading_data.status == 'Read') {
                    number_of_chapters_read += 1;
                } else if (reading_data.status == 'Reading') {
                    number_of_chapters_read += 0.5;
                }
            } else {
                element.jp_data.chapter_reading_status[chapter_id] = empty_reading_status;
            }
            element.jp_data.chapter_names[chapter_id] = element.jp_data.ch_najp[i];
            i += 1;
        }
        element.jp_data.chapter_ids = chapter_ids;
        read_chapter_pct_by_manga[manga_id] = Math.trunc(100*number_of_chapters_read/element.jp_data.ch_jph.length);
        chapter_names_by_manga[manga_id] = element.jp_data.chapter_names;

        for (let vol in element.jp_data.vol_jp) {
            let vol_chapters = [];
            let start_c = element.jp_data.vol_jp[vol].s;
            let end_c = element.jp_data.vol_jp[vol].e
            for (let idx = start_c; idx <= end_c; idx ++ ) {
                vol_chapters.push(chapter_ids[idx]);
            }
            element.jp_data.vol_jp[vol].chapter_ids = vol_chapters;
        };
    });

    // Augment manga_metadata with favourites and percentage of read chapters
    let manga_titles = db['manga_metadata']['0'].manga_titles;
    console.log("Augment manga_metadata with " + user_data['favourites'].length + " favourites");

    manga_titles.forEach(element => {
        let id = element.enid;

        if (user_data['favourites'].includes(id)) {
            console.log(" - Favourite: " + element.entit);
            element["favourite"] = true;
        } else {
            element["favourite"] = false;
        }

        element["read_chapter_pct"] = read_chapter_pct_by_manga[id];
        element["chapter_names"] = chapter_names_by_manga[id];
    });

};
