import { getDB } from '$lib/mongo';
import { SOURCE } from '$lib/LearningData';
import { DEFAULT_USER_ID } from './UserDataTools';
const db = getDB();

const SUGGESTED_PREREAD_ANALYSIS_VERSION = 1

export async function getCollection(collection_name, skip, limit)
{
    // get repositories from MongoDB with skip and limit
    const data = await db.collection(collection_name).find({}).project({_id:0}).skip(skip).limit(limit).toArray();

    // return JSON response
    return data;
}

export async function searchCollection(collection_name, field_name, value)
{
    var search_query = {}
    search_query[field_name] = value
    console.log("Querying",search_query)
    // get repositories from MongoDB with search query and regex options
    const data = await db.collection(collection_name).find(search_query).toArray();
    return data;
}

export async function getUserDataValue(user_id, field_name)
{
    var search_query = {'user_id':user_id}
    console.log("Querying",search_query)
    const data = await db.collection("br_userdata").find(search_query).toArray();
    console.log(`getUserDataValue ${field_name}: ` + JSON.stringify(data[0][field_name]))
    return data[0][field_name];
}

export async function updateUserData(userid, field, value)
{
    var new_values = {}
    new_values[field] = value
    var set_newvalues = { $set: new_values};
    var myquery = { user_id: userid };
    var res = await db.collection("br_userdata").updateOne(myquery, set_newvalues, { upsert: true } );
    return res
}

export async function getUserWordLearningHistory(user_id, word_id)
{
    var search_query = {'user_id':user_id,'wid':word_id}
    console.log("Querying",search_query)
    var word_data = await db.collection("br_user_word_learning_history").findOne(search_query);
    if (word_data == null) {
        return [];
    }
    for (let entry of word_data['history']) {
        let e_meta = entry['m']
        var ch_data = await db.collection("br_chapter_lookup_table").findOne({'ch_id':e_meta['cid']});
        let comment = ''
        if (ch_data !== null) {
            var title_metadata = await db.collection("br_metadata").findOne({'_id':ch_data['title_id']});
            var name = title_metadata['entit']
            if (name == 'Placeholder') {
                name = title_metadata['jptit']
            }
            comment += name
            if (ch_data['vol_name'] != '' && (ch_data['vol_name'] != 'No Volume')) {
                comment += ' ' + ch_data['vol_name']
            }
            comment += ' ' + ch_data['ch_name']
            if (e_meta['src'] == SOURCE.USER && e_meta['p' != -1]) {
                comment += ' / page ' + (e_meta['p'])
            }
            if ('comment' in e_meta) {
                comment += e_meta['comment']
            }
            e_meta['comment'] = comment
        }
    }

    console.log(`getUserWordLearningHistory ${word_id}: ` + JSON.stringify(word_data['history']))
    return word_data['history'];
}

export async function updateLearningDataWordStatus(user_id, word_id, history_entry)
{
    var search_query = {'user_id':user_id,'wid':word_id}
    console.log("Querying",search_query)
    var new_word_status = {
        'user_id':user_id,
        'wid':word_id,
        's' : history_entry['s'], // stage
        'lf' : 0
    }
    const previous_word_status = await db.collection("br_user_word_learning_status").findOne(search_query);
    if (previous_word_status != null) {
        new_word_status['lf'] = previous_word_status['lf']
    }
    await db.collection("br_user_word_learning_status").updateOne(search_query, {$set:new_word_status}, { upsert: true } );

    var new_word_history = {
        'user_id':user_id,
        'wid':word_id,
        'ltf' : 0,
        'history' : []
    }
    const previous_word_history_data = await db.collection("br_user_word_learning_history").findOne(search_query);
    if (previous_word_history_data != null) {
        new_word_history['history'] = previous_word_history_data['history']
        new_word_history['ltf'] = previous_word_history_data['ltf']
    }
    history_entry['m']['src'] = SOURCE.USER;
    new_word_history['history'].push(history_entry)
    await db.collection("br_user_word_learning_history").updateOne(search_query, {$set:new_word_history}, { upsert: true } );
    console.log(`updateLearningDataWordStatus ${word_id}: ` + JSON.stringify(new_word_history))
}

export async function getManuallySetWordLearningStateChanges(user_id, word_id)
{
    var search_query = {'user_id':user_id,'wid':word_id}
    console.log("Querying",search_query)
    const data = await db.collection("br_user_set_words").findOne(search_query);
    if (data == null) {
        return [];
    }
    console.log(`getManuallySetWordLearningStateChanges ${word_id}: ` + JSON.stringify(data['history']))
    return data['history'];
}


export async function updateManuallySetWordLearningStateChanges(user_id, word_id, history)
{
    var new_values = {'user_id':user_id,'wid':word_id,'history':history}
    console.log("Updating",new_values)
    var set_newvalues = { $set: new_values };
    var myquery = { 'user_id': user_id, 'wid':word_id };
    var res = await db.collection("br_user_set_words").updateOne(myquery, set_newvalues, { upsert: true } );
    return res
}


export async function getBilingualMangaSettings()
{
    const data = await searchCollection("br_settings","_id","64dcfd8e5e150531818c20cd");
    return data[0]
}

export async function getUserData(user_id)
{
    const data = await searchCollection("br_userdata","user_id",user_id);
    return data[0]
}

export async function getTitleChapters(title_id)
{
    const data = await db.collection("br_chapter_lookup_table").find({'title_id':title_id}).project({ch_id:true}).toArray();
    let cids = [];
    for (let entry of data) {
        cids.push(entry['ch_id'])
    }
    return cids
}

const AugmentMetadataWithMangaupdatesCategories = (manga_titles) => {

    // TODO: calculate these elsewhere
    let global_avg_votes = 0;
    let valid_entries = 0;

    manga_titles.forEach(element => {
        let id = element.enid;

        if (element['mangaupdates_data'] !== undefined) {
            if (element['mangaupdates_data']['series_id'] != -1) {
                let mangaupdates_data = element['mangaupdates_data']
                let avg_votes = 0;
                let category_list = [];
                let category_scores = {};
                let category_votes = {};
                for (let categoryData of mangaupdates_data['categories']) {
                    avg_votes += categoryData.votes;
                    category_votes[categoryData.category] = categoryData.votes;
                    category_list.push(categoryData.category)
                }
                if (mangaupdates_data['categories'].length>0) {
                    avg_votes /= mangaupdates_data['categories'].length;
                }
                for (let categoryData of mangaupdates_data['categories']) {
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
            } else {
                element["mangaupdates_data"] = { "url":"http://mangaupdates.com", "rating":-1, "votes": 0, "last_updated":"N/A", "categories":[],"category_list":[]}
            }

        } else {
            element["mangaupdates_data"] = { "url":"http://mangaupdates.com", "rating":-1, "votes": 0, "last_updated":"N/A", "categories":[],"category_list":[]}
        }
    });

    // return average_category_vote_count
    return global_avg_votes / valid_entries;
};


export async function getTitleCount(count_match_query)
{
    var count = await db.collection("br_metadata").find(count_match_query).count()
    return count;
}

let search_cache = null;
let search_cache_timestamp = 0

export async function searchTitleMetadata(search_term, limit)
{
    /*
    // MongoDB has lousy partial word matching..
    var metadata = await db.collection("br_metadata").find({ $text: { $search: search_term } }).limit(limit).toArray();
    */

    // This is faster but ISN'T really thread-safe!
    if ((search_cache == null) || (Date.now() - search_cache_timestamp > 60*1000)) {
        search_cache = await db.collection("br_metadata").find({},{'entit':true,'jptit':true,'search':true}).toArray();
        search_cache_timestamp = Date.now();
    }
    let results = [];
    for (let m of search_cache) {
        let xv = `${m.entit}${m.jptit}${m.search}`
        xv=xv.toLowerCase()
        if(xv.indexOf(search_term)!=-1) {
            results.push(m);
        }
        if (results.len==limit) {
            console.log("Max search results:",results)
            return results;
        }
    }    
    console.log("Search results:",results)
    return results;
}

export async function getMetadata(user_id)
{
    let m = (await getCollection("br_settings", 0, 0))[0];

    // average manga/book statistics
    var avg_summary = await db.collection("br_lang_summary").find({'_id':'average_manga'}).project({_id:0}).toArray()
    m['average_manga'] = avg_summary[0]
    avg_summary = await db.collection("br_lang_summary").find({'_id':'average_book'}).project({_id:0}).toArray()
    m['average_book'] = avg_summary[0]

    // TODO: seprate custom summary for mangas and books
    const custom_lang_search_query = { 'title_id':'average_title', 'user_id':user_id }
    var average_title_summary = await db.collection("br_custom_lang_analysis_summary").findOne(custom_lang_search_query)
    m['average_manga']['series'] = average_title_summary['series']

    // TODO: pre-process this elsewhere
    // Update categories
    //m.average_category_vote_count = AugmentMetadataWithMangaupdatesCategories(m['manga_titles'])

    return [m];
}


export async function getAllValuesForMetadataField(field_name)
{
    var values = await db.collection("br_metadata").distinct(field_name)
    return values
}

export function ConvertFilterToMatchQuery(match_query, filter, user_data)
{
    if (filter.type == 'boolean') {
        if (filter.field == 'favourite') {
            if (filter.op == '=') {
                match_query['enid'] = { $in: user_data.favourites };
            } else if (filter.op == '!=') {
                match_query['enid'] = { $not: { $in: user_data.favourites } };
            }
        } else {
            if (filter.op == '=') {
                match_query[filter.field] = filter.value;
            } else if (filter.op == '!=') {
                match_query[filter.field] = { $not: { $eq: filter.value } };
            }
        }
    } else if (filter.type == 'val') {
        if (filter.op == '=') {
            match_query[filter.field] = filter.value;;
        } else if (filter.op == '!=') {
            match_query[filter.field] = { $not: { $eq: filter.value } };
        } else if (filter.op == '>') {
            match_query[filter.field] = { $gt: filter.value };
        } else if (filter.op == '>=') {
            match_query[filter.field] = { $gte: filter.value };
        } else if (filter.op == '<') {
            match_query[filter.field] = { $lt: filter.value };
        } else if (filter.op == '<=') {
            match_query[filter.field] = { $lte: filter.value };
        }
    } else if (filter.type == 'list') {
        if (filter.op == '=') {
            // filter.field array contains filter.value
            match_query[filter.field] = { $all: [filter.value] };
        } else if (filter.op == '!=') {
            // filter.field array doesn't contain filter.value
            match_query[filter.field] = { $not: { $all: [filter.value] } };
        }
    }
}

export async function getMetadataForTitles(user_id, sort_struct, filter_struct)
{
    console.log("Filter: " + JSON.stringify(filter_struct))
    console.log("Sort: " + JSON.stringify(sort_struct))
    let sort_field = sort_struct.field
    let reverse = 1 // ascending
    if (sort_struct.reverse) {
        reverse = -1 // descending
    }

    let user_data = await getUserData(user_id)

    var match_query = {}
    if (filter_struct.fixed_filter != {}) {
        ConvertFilterToMatchQuery(match_query, filter_struct.fixed_filter, user_data)
    }
    for (let filter of filter_struct.filters) {
        ConvertFilterToMatchQuery(match_query, filter, user_data)
    }
    console.log("Match query: ",match_query)
    var sort_query = {[sort_field]:reverse}
    console.log(`Sorting: '${JSON.stringify(sort_query)}'`)

    var aggregate = await db.collection("br_metadata").aggregate([
        {
            $lookup: { from:"br_mangaupdates", localField:"_id", foreignField:"_id", as:"mangaupdates_data"}
        },
        {
            $unwind: { path:"$mangaupdates_data", preserveNullAndEmptyArrays:true }
        },
        {
            $lookup: { from:"br_custom_lang_analysis_summary", localField:"_id", foreignField:"title_id", as:"analysis"}
        },
        {
            $unwind: { path:"$analysis", preserveNullAndEmptyArrays:true }
        },
        {
            $match: { "analysis.user_id":user_id }
        },
        {
            $lookup: { from:"br_lang_summary", localField:"_id", foreignField:"_id", as:"analysis.summary"}
        },
        {
            $unwind: { path:"$analysis.summary", preserveNullAndEmptyArrays:true }
        },
        {
            $match: match_query
        },
        {
            $sort: sort_query
        },
        {
            $facet: {
                count: [ { $count: "count" } ],
                results: [
                    {
                        $skip: filter_struct.skip
                    },
                    {
                        $limit: filter_struct.limit,
                    },
                    {
                        $addFields: { "sort_value" : '$' + sort_field }
                    }            
                ]
            }
        }


    ]).toArray();

    var title_metadata = aggregate[0]['results']
    var filtered_count = 0;
    if (aggregate[0]['count'].length>0) {
        filtered_count = aggregate[0]['count'][0]['count']
    }
    console.log("filtered_count",filtered_count)

    var metadata_by_id = {}
    for (let d of title_metadata) {
        metadata_by_id[d['enid']] = d
    }

    for (let meta_data of title_metadata) {
        let id = meta_data['enid']
        if (user_data['favourites'].includes(id)) {
            meta_data["favourite"] = true;
        } else {
            meta_data["favourite"] = false;
        }
    }

    // TODO: preprocess these elsewhere
    // Update categories
    AugmentMetadataWithMangaupdatesCategories(title_metadata)

    let count_match_query = {}
    ConvertFilterToMatchQuery(count_match_query, filter_struct.fixed_filter, user_data )
    let title_count = await getTitleCount(count_match_query)

    return {'title_metadata':title_metadata, 'unfiltered_title_count':title_count, 'filtered_title_count':filtered_count}
}

const iterative_copy = (src,dest) => {
    Object.keys(src).forEach(key => {
        if (typeof src[key] === 'object' && (!Array.isArray(src[key]))) {
            if (src[key] !== null) {
                if (!(key in dest)) {
                    dest[key] = {}
                }
                iterative_copy(src[key],dest[key])
            }
        } else {
            dest[key] = src[key]
        }
    })
}

export async function getMangaMetadataForSingleTitle(user_id, title_id)
{
    var title_metadata = undefined
    title_metadata = await db.collection("br_metadata").aggregate([
        {
            $lookup: { from:"br_mangaupdates", localField:"_id", foreignField:"_id", as:"mangaupdates_data"}
        },
        {
            $unwind: { path:"$mangaupdates_data", preserveNullAndEmptyArrays:true }
        },
        {
            $lookup: { from:"br_lang_summary", localField:"_id", foreignField:"_id", as:"series"}
        },
        {
            $unwind: { path:"$series", preserveNullAndEmptyArrays:true }
        },
        {
            $match: {'_id':title_id}
        }
    ]).project({_id:0}).toArray();

    title_metadata = title_metadata[0];

    if (!('chapter' in title_metadata)) {
        title_metadata['chapter'] = {};
    }
    if (!('unread_idx' in title_metadata['chapter'])) {
        title_metadata['chapter']['unread_idx'] = -1
    }
    if (!('volume' in title_metadata)) {
        title_metadata['volume'] = {};
    }
    if (!('unread_idx' in title_metadata['volume'])) {
        title_metadata['volume']['unread_idx'] = -1
    }
    if (!('translator' in title_metadata)) {
        title_metadata['translator'] = '';
    }

    if (title_metadata['series'] !== undefined) {

        const search_query = {'title_id':title_id, 'user_id':user_id }
        var custom_lang_analyses = await db.collection("br_custom_lang_analysis").find(search_query).toArray()

        for (let an of custom_lang_analyses) {
            if (an['type'] == 'series') {
                iterative_copy(an, title_metadata['series'])
            }
            if (an['type'] == 'next_unread_chapter') {
                iterative_copy(an, title_metadata['chapter'])
            }
            if (an['type'] == 'next_unread_volume') {
                iterative_copy(an, title_metadata['volume'])
            }
            if (an['type'] == 'series_analysis_for_jlpt') {
                title_metadata['jlpt_improvement_pts'] = an['relative_points'];
                title_metadata['jlpt_improvement_words'] = an['num_new_known_words'];
                title_metadata['jlpt_improvement_kanjis'] = an['num_new_known_kanjis'];
            }
        }
    }

    AugmentMetadataWithMangaupdatesCategories([title_metadata])

    return title_metadata;
}


export async function getSuggestedPrereadForTitle(user_id, title_id, target_selection, source_selection)
{
    var suggested_preread = await db.collection("br_metadata").aggregate([
        {
            $lookup: { from:"br_suggested_preread", localField:"_id", foreignField:"source_title_id", as:"suggestion"}
        },
        {
            $unwind: { path:"$suggestion", preserveNullAndEmptyArrays:false }
        },
        {
            $match: {'suggestion.version':SUGGESTED_PREREAD_ANALYSIS_VERSION,'suggestion.user_id':user_id,'suggestion.target_title_id':title_id,'suggestion.target_selection':target_selection,'suggestion.source_selection':source_selection}
        },
        {
            $lookup: { from:"br_mangaupdates", localField:"_id", foreignField:"_id", as:"mangaupdates_data"}
        },
        {
            $unwind: { path:"$mangaupdates_data", preserveNullAndEmptyArrays:true }
        },
    ]).project({_id:0}).toArray();

    return suggested_preread;
}
