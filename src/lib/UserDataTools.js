export const DEFAULT_USER_ID = 0

export const EVENT_TYPE = {
    CONNECTED           : "OK",
    UPDATING_STATS      : "Updating statistics",
    UPDATING_ANALYSIS   : "Updating analysis",
    UPDATED_STATS       : "Statistics updated",
    UPDATED_ANALYSIS    : "Analysis updated",
    UPDATED_SUGGESTED_PREREAD : "Suggested pre-read updated",
    ANALYSIS_WARNING    : "Warning during language engine processing",
    ANALYSIS_ERROR      : "Error during language engine processing",
    SUGGESTED_PREREAD_PROGRESS : "Suggested Preread Progress",
    ANALYSIS_PROGRESS   : "Analysis progress"
}

const empty_reading_status = {
    'status':'Unread',
    'comprehension' : 0,
};


export const AugmentTitleMetadataWithUserData = (metadata, titledata, user_data) => {

    let read_chapters = 'chapter_reading_status' in user_data ? Object.keys(user_data['chapter_reading_status']) : [];
    metadata.user_data_timestamp = user_data['timestamp'];

    // Augment title data with chapter/volume reading status 
    // and count number of read chapters
    let chapter_ids = [];
    titledata.jp_data.chapter_reading_status = {};
    let number_of_chapters_read = 0;

    let i = 0;
    for (let ch of titledata.jp_data.ch_jph) {
        let chapter_id = ch.split('/')[0];
        chapter_ids.push(chapter_id);
        if (read_chapters.includes(chapter_id)) {
            let reading_data = user_data['chapter_reading_status'][chapter_id];
            titledata.jp_data.chapter_reading_status[chapter_id] = reading_data;
            if (reading_data.status == 'Read') {
                number_of_chapters_read += 1;
            } else if (reading_data.status == 'Reading') {
                number_of_chapters_read += 0.5;
            }
        } else {
            titledata.jp_data.chapter_reading_status[chapter_id] = empty_reading_status;
        }
        i += 1;
    }

    // Augment manga_metadata with favourites and percentage of read chapters
    metadata["read_chapter_pct"] = Math.trunc(100*number_of_chapters_read/titledata.jp_data.ch_jph.length);
    let id = metadata.enid;
    if (user_data['favourites'].includes(id)) {
        metadata["favourite"] = true;
    } else {
        metadata["favourite"] = false;
    }

};
