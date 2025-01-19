import { getDB } from '$lib/mongo';
import { SOURCE } from '$lib/LearningData';
import { DEFAULT_USER_ID } from './UserDataTools';
const db = getDB();

const COLLECTION_SETTINGS = "settings"
const COLLECTION_TITLEDATA = "titledata"
const COLLECTION_VOLUMEDATA = "volumedata"
const COLLECTION_CHAPTERDATA = "chapterdata"
const COLLECTION_IMAGE_CORRESPONDENCE_DATA = "imgcorrdata"
const COLLECTION_MANGAUPDATES = "mangaupdates"
const COLLECTION_LANG_SUMMARY = "lang_summary"
const COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY = "custom_lang_analysis_summary"
const COLLECTION_CUSTOM_LANG_ANALYSIS = "custom_lang_analysis"
const COLLECTION_USERDATA = "userdata"
const COLLECTION_USER_WORD_LEARNING_HISTORY = "user_word_learning_history"
const COLLECTION_USER_WORD_LEARNING_STATUS = "user_word_learning_status"
const COLLECTION_USER_SET_WORDS = "user_set_words"
const COLLECTION_GOOGLE_BOOKS = "google_books_volumedata"
const COLLECTION_SUGGESTED_PREREAD = "suggested_preread"
const COLLECTION_VOL_IMPORT_METADATA = "vol_import_metadata"

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
    const data = await db.collection(COLLECTION_USERDATA).find(search_query).toArray();
    console.log(`getUserDataValue ${field_name}: ` + JSON.stringify(data[0][field_name]))
    return data[0][field_name];
}

export async function updateUserData(userid, field, value)
{
    var new_values = {}
    new_values[field] = value
    var set_newvalues = { $set: new_values};
    var myquery = { user_id: userid };
    var res = await db.collection(COLLECTION_USERDATA).updateOne(myquery, set_newvalues, { upsert: true } );
    return res
}

function getTitle(titledata) {
    if (Object.keys(titledata.lang).includes('en') && titledata.lang.en.title != '') {
        return titledata.lang.en.title;
    } else {
        return titledata.lang.jp.title;
    }
}

export async function getUserWordLearningHistory(user_id, word_id)
{
    var search_query = {'user_id':user_id,'wid':word_id}
    console.log("Querying",search_query)
    var word_data = await db.collection(COLLECTION_USER_WORD_LEARNING_HISTORY).findOne(search_query);
    if (word_data == null) {
        return [];
    }
    for (let entry of word_data['history']) {
        let e_meta = entry['m']
        var ch_data = await db.collection(COLLECTION_CHAPTERDATA).findOne({'ch_id':e_meta['cid']});
        let comment = ''
        if (ch_data !== null) {
            var title_metadata = await db.collection(COLLECTION_TITLEDATA).findOne({'_id':ch_data['title_id']});
            var vol_data = await db.collection(COLLECTION_VOLUMEDATA).findOne({'_id':ch_data['vol_id']});
            var name = getTitle(title_metadata)
            comment += name
            if (vol_data['vol_name'] != '' && (vol_data['vol_name'] != 'No Volume')) {
                comment += ' ' + vol_data['vol_name']
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
    const previous_word_status = await db.collection(COLLECTION_USER_WORD_LEARNING_STATUS).findOne(search_query);
    if (previous_word_status != null) {
        new_word_status['lf'] = previous_word_status['lf']
    }
    await db.collection(COLLECTION_USER_WORD_LEARNING_STATUS).updateOne(search_query, {$set:new_word_status}, { upsert: true } );

    var new_word_history = {
        'user_id':user_id,
        'wid':word_id,
        'ltf' : 0,
        'history' : []
    }
    const previous_word_history_data = await db.collection(COLLECTION_USER_WORD_LEARNING_HISTORY).findOne(search_query);
    if (previous_word_history_data != null) {
        new_word_history['history'] = previous_word_history_data['history']
        new_word_history['ltf'] = previous_word_history_data['ltf']
    }
    history_entry['m']['src'] = SOURCE.USER;
    new_word_history['history'].push(history_entry)
    await db.collection(COLLECTION_USER_WORD_LEARNING_HISTORY).updateOne(search_query, {$set:new_word_history}, { upsert: true } );
    console.log(`updateLearningDataWordStatus ${word_id}: ` + JSON.stringify(new_word_history))
}

export async function getManuallySetWordLearningStateChanges(user_id, word_id)
{
    var search_query = {'user_id':user_id,'wid':word_id}
    console.log("Querying",search_query)
    const data = await db.collection(COLLECTION_USER_SET_WORDS).findOne(search_query);
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
    var res = await db.collection(COLLECTION_USER_SET_WORDS).updateOne(myquery, set_newvalues, { upsert: true } );
    return res
}


export async function getBilingualMangaSettings()
{
    const data = await searchCollection(COLLECTION_SETTINGS,"_id","64dcfd8e5e150531818c20cd");
    return data[0]
}

export async function getUserData(user_id)
{
    const data = await searchCollection(COLLECTION_USERDATA,"user_id",user_id);
    return data[0]
}

export async function getTitleChapters(title_id)
{
    const data = await db.collection(COLLECTION_CHAPTERDATA).find({'title_id':title_id}).project({ch_id:true}).toArray();
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
    var count = await db.collection(COLLECTION_TITLEDATA).find(count_match_query).count()
    return count;
}

let search_cache = null;
let search_cache_timestamp = 0

async function ConvertToOldFormat(title_data) {
    title_data.languages = [];
    for (let lang of ['jp','en']) {
        if (Object.keys(title_data.lang).includes(lang)) {
            let lang_info = title_data.lang[lang]

            if (lang == 'jp') {
                title_data.jptit = lang_info.title
            } else if ( lang == 'en') {
                title_data.entit = lang_info.title
            }
            if ('volumes' in title_data.lang[lang]) {
                if (title_data.lang[lang].volumes.length>0) {
                    title_data.languages.push(lang)
                }
            }
        }
    }
    if (Object.keys(title_data).includes('first_jp_vol')) {
        title_data.syn_jp = title_data.first_jp_vol.syn
        title_data.coverjp = title_data.first_jp_vol.cover
    }
    if (Object.keys(title_data).includes('first_en_vol')) {
        title_data.syn_en = title_data.first_en_vol.syn
        title_data.coveren = title_data.first_en_vol.cover
    }
    title_data.enid = title_data['_id']
}

export async function searchTitleMetadata(search_term, limit)
{
    /*
    // MongoDB has lousy partial word matching..
    var metadata = await db.collection("br_metadata").find({ $text: { $search: search_term } }).limit(limit).toArray();
    */

    // This is faster but ISN'T really thread-safe!
    let t1 = Date.now()
    if ((search_cache == null) || (Date.now() - search_cache_timestamp > 60*1000)) {
        search_cache = await db.collection(COLLECTION_TITLEDATA).find({},{'lang':true,'search':true}).toArray();
        search_cache_timestamp = Date.now();
    }
    let t2 = Date.now()
    console.log(`Fetch after ${t2-t1} ms:`)
    let results = [];
    for (let m of search_cache) {
        let xv = `${m.search}`
        for (let lang of Object.keys(m.lang)) {
            xv += m.lang[lang].title
        }
        xv=xv.toLowerCase()
        if(xv.indexOf(search_term)!=-1) {
            ConvertToOldFormat(m)
            results.push(m);
        }
        if (results.length==limit) {
            let t3 = Date.now()
            console.log(`Max search results after ${t3-t2} ms:`,results)
            return results;
        }
    }    
    let t3 = Date.now()
    console.log(`Search results after ${t3-t2} ms:`,results)
    return results;
}

export async function getMetadata(user_id)
{
    let m = (await getCollection(COLLECTION_SETTINGS, 0, 0))[0];

    // TODO: seprate custom summary for mangas and books
    const custom_lang_search_query = { 'title_id':'average_title', 'user_id':user_id }

    // average manga/book statistics
    var avg_summary = await db.collection(COLLECTION_LANG_SUMMARY).findOne({'_id':'average_manga'})
    if (avg_summary != undefined) {
        console.log("avg summary",avg_summary)
        m['average_manga'] = avg_summary
        var average_title_summary = await db.collection(COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY).findOne(custom_lang_search_query)
        m['average_manga']['series'] = average_title_summary['series']
    } else {
        console.log("Warning! Language analysis summary for average manga not found!")
    }

    avg_summary = await db.collection(COLLECTION_LANG_SUMMARY).findOne({'_id':'average_book'})
    if (avg_summary != null) {
        m['average_book'] = avg_summary
        var average_title_summary = await db.collection(COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY).findOne(custom_lang_search_query)
        m['average_book']['series'] = average_title_summary['series']
    } else {
        console.log("Warning! Language analysis summary for average book not found!")
    }

    // TODO: pre-process this elsewhere
    // Update categories
    //m.average_category_vote_count = AugmentMetadataWithMangaupdatesCategories(m['manga_titles'])

    return [m];
}


export async function getAllValuesForMetadataField(field_name)
{
    var values = await db.collection(COLLECTION_TITLEDATA).distinct(field_name)
    return values
}


function getCollectionByFieldName(field_name) {
    var collection = COLLECTION_TITLEDATA // default
    if (field_name.indexOf('lang_summary.')==0) {
        collection = COLLECTION_LANG_SUMMARY
    } else if (field_name.indexOf('analysis.')==0) {
        collection = COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY
    } else if (field_name.indexOf('mangaupdates_data.')==0) {
        collection = COLLECTION_MANGAUPDATES
    } else if (field_name=='Release') {
        collection = '__FIRST_JP_VOL__'
    }
    return collection;
}

export function ConvertFilterToMatchQuery(match_query_per_collection, filter, user_data)
{
    var collection = getCollectionByFieldName(filter.field)
    console.log("Filter : ",filter, "Collection: ",collection)
    var match_query = match_query_per_collection[collection];
    if (filter.type == 'boolean') {
        if (filter.field == 'favourite') {
            if (filter.op == '=') {
                match_query['_id'] = { $in: user_data.favourites };
            } else if (filter.op == '!=') {
                match_query['_id'] = { $not: { $in: user_data.favourites } };
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

    // convert each filter to query and divide them among the collections
    var match_query_per_collection = {
        [COLLECTION_TITLEDATA]:{}, 
        [COLLECTION_MANGAUPDATES]:{}, 
        [COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY]:{}, 
        [COLLECTION_LANG_SUMMARY]:{},
        '__FIRST_JP_VOL__':{},
        '__FIRST_EN_VOL__':{}
    }
    if (Object.keys(filter_struct.fixed_filter).length > 0) {
        ConvertFilterToMatchQuery(match_query_per_collection, filter_struct.fixed_filter, user_data)
    }
    for (let filter of filter_struct.filters) {
        ConvertFilterToMatchQuery(match_query_per_collection, filter, user_data)
    }

    console.log("Match query per collection: ",match_query_per_collection)
    var sort_query = {[sort_field]:reverse}
    var sort_collection = getCollectionByFieldName(sort_field)
    console.log(`Sort query: '${JSON.stringify(sort_query)}'`)

    /// The following is MongoDB optimization magic

    const collection_order = [COLLECTION_TITLEDATA,COLLECTION_MANGAUPDATES,COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY,COLLECTION_LANG_SUMMARY,'__FIRST_JP_VOL__','__FIRST_EN_VOL__']
    const collection_join_stages = {
        [COLLECTION_TITLEDATA] : [] ,
        [COLLECTION_MANGAUPDATES] : [
            {
                $lookup: { from: COLLECTION_MANGAUPDATES, localField:"_id", foreignField:"_id", as:"mangaupdates_data"}
            },
            {
                $unwind: { path:"$mangaupdates_data", preserveNullAndEmptyArrays:true }
            }
        ],
        [COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY] : [
            {
                $lookup: { from:COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY, localField:"_id", foreignField:"title_id", as:"analysis"}
            },
            {
                $unwind: { path:"$analysis", preserveNullAndEmptyArrays:true }
            },
            {
                // fill out the missing analysis to prevent failed match
                $fill: {
                    output: {'analysis': {value:{'user_id':user_id}}}
                },
            },
            {
                $match: { "analysis.user_id":user_id }
            }
        ],
        [COLLECTION_LANG_SUMMARY] : [
            {
                $lookup: { from:COLLECTION_LANG_SUMMARY, localField:"_id", foreignField:"_id", as:"lang_summary"}
            },
            {
                $unwind: { path:"$lang_summary", preserveNullAndEmptyArrays:true }
            }
        ],
        '__FIRST_JP_VOL__' : [
            {
                $set: { "first_jp_vol_id": { "$arrayElemAt": [ "$lang.jp.volumes", 0 ] } }
            },
            {
                $lookup: { from:COLLECTION_VOLUMEDATA, localField:"first_jp_vol_id", foreignField:"vol_id", as:"first_jp_vol"}
            },
            {
                $unwind: { path:"$first_jp_vol", preserveNullAndEmptyArrays:true }
            },
            {
                $set: { "release": "$first_jp_vol.release" }
            }
        ],
        '__FIRST_EN_VOL__' : [
            {
                $set: { "first_en_vol_id": { "$arrayElemAt": [ "$lang.en.volumes", 0 ] } }
            },
            {
                $lookup: { from:COLLECTION_VOLUMEDATA, localField:"first_en_vol_id", foreignField:"vol_id", as:"first_en_vol"}
            },
            {
                $unwind: { path:"$first_en_vol", preserveNullAndEmptyArrays:true }
            },
        ]
    }

    var aggregate_stages = []
    var joined_collections = [];

    // First do filtering as early as possible and join collections only when needed
    for (let collection of collection_order) {
        if (Object.keys(match_query_per_collection[collection]).length>0) {
            aggregate_stages = aggregate_stages.concat(collection_join_stages[collection])
            aggregate_stages.push( {
                $match: match_query_per_collection[collection]
            })
            joined_collections.push(collection)
        }
    }

    // then sort, adding the needed collection if needed
    if (!joined_collections.includes(sort_collection)) {
        aggregate_stages = aggregate_stages.concat(collection_join_stages[sort_collection])
        joined_collections.push(sort_collection)
    }
    aggregate_stages.push( {
        $sort: sort_query
    })

    // Bifurcate the pipeline:
    // Pipeline 1. count the titles at this pipeline (before limiting in order to get the filtered title count)
    // Pipeline 2.
    // - do skip and limit (for page windowing)
    // - add sorted value already at the database level
    var second_pipeline_stages = [
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
    // - finally join the rest of the collections if needed
    for (let coll of collection_order) {
        if (!joined_collections.includes(coll)) {
            second_pipeline_stages = second_pipeline_stages.concat(collection_join_stages[coll])
        }
    }

    aggregate_stages.push({
        $facet: {
            count: [ { $count: "count" } ],
            results: second_pipeline_stages
        }
    })

    console.log("Aggregate query: ",aggregate_stages)
    console.log("2nd phase aggregate query: ",second_pipeline_stages)

    // Do the actual query
    var aggregate = await db.collection(COLLECTION_TITLEDATA).aggregate(aggregate_stages).toArray();

    var title_metadata = aggregate[0]['results']
    var filtered_count = 0;
    if (aggregate[0]['count'].length>0) {
        filtered_count = aggregate[0]['count'][0]['count']
    }
    console.log("filtered_count",filtered_count)

    var metadata_by_id = {}
    for (let d of title_metadata) {
        ConvertToOldFormat(d)
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

    // Fetch the total title count after fixed filter (e.g. Author / Genre)
    let count_match_query = {[COLLECTION_TITLEDATA]:{}}
    if (Object.keys(filter_struct.fixed_filter).length>0) {
        ConvertFilterToMatchQuery(count_match_query, filter_struct.fixed_filter, user_data )
    }
    let title_count = await getTitleCount(count_match_query[COLLECTION_TITLEDATA])

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
    title_metadata = await db.collection(COLLECTION_TITLEDATA).aggregate([
        {
            $match: {'_id':title_id}
        },
        {
            $lookup: { from:COLLECTION_MANGAUPDATES, localField:"_id", foreignField:"_id", as:"mangaupdates_data"}
        },
        {
            $unwind: { path:"$mangaupdates_data", preserveNullAndEmptyArrays:true }
        },
        {
            $lookup: { from:COLLECTION_LANG_SUMMARY, localField:"_id", foreignField:"_id", as:"lang_summary"}
        },
        {
            $unwind: { path:"$lang_summary", preserveNullAndEmptyArrays:true }
        },
        {
            $set: { "first_jp_vol_id": { "$arrayElemAt": [ "$lang.jp.volumes", 0 ] } }
        },
        {
            $lookup: { from:COLLECTION_GOOGLE_BOOKS, localField:"first_jp_vol_id", foreignField:"_id", as:"google_books"}
        },
        {
            $unwind: { path:"$google_books", preserveNullAndEmptyArrays:true }
        },
        {
            $lookup: { from:COLLECTION_VOLUMEDATA, localField:"first_jp_vol_id", foreignField:"vol_id", as:"first_jp_vol"}
        },
        {
            $unwind: { path:"$first_jp_vol", preserveNullAndEmptyArrays:true }
        },
        {
            $set: { "release": "$first_jp_vol.release" }
        },
        {
            $set: { "first_en_vol_id": { "$arrayElemAt": [ "$lang.en.volumes", 0 ] } }
        },
        {
            $lookup: { from:COLLECTION_VOLUMEDATA, localField:"first_en_vol_id", foreignField:"vol_id", as:"first_en_vol"}
        },
        {
            $unwind: { path:"$first_en_vol", preserveNullAndEmptyArrays:true }
        }
    ]).toArray();

    title_metadata = title_metadata[0];

    if (!('translator' in title_metadata)) {
        title_metadata['translator'] = '';
    }

    title_metadata['languages'] = [];
    if ('first_en_vol' in title_metadata) {
        title_metadata.languages.push('en')
    }
    if ('first_jp_vol' in title_metadata) {
        title_metadata.languages.push('jp')
        title_metadata['first_jp_vol_collection'] = title_metadata.first_jp_vol.collection
    }
    title_metadata['analysis'] = {}

    const search_query = {'title_id':title_id, 'user_id':user_id }
    var custom_lang_analyses = await db.collection(COLLECTION_CUSTOM_LANG_ANALYSIS).find(search_query).toArray()

    for (let an of custom_lang_analyses) {
        if (an['type'] == 'series_analysis_for_jlpt') {
            title_metadata['analysis']['jlpt_improvement_pts'] = an['relative_points'];
            title_metadata['analysis']['jlpt_improvement_words'] = an['num_new_known_words'];
            title_metadata['analysis']['jlpt_improvement_kanjis'] = an['num_new_known_kanjis'];
        } else {
            title_metadata['analysis'][ an['type'] ] = an
        }
    }

    title_metadata.analysis.status = 'stale';
    if ('series' in title_metadata.analysis) {
        let analysis_metadata = title_metadata.analysis.series.custom_lang_analysis_metadata
        if (analysis_metadata.timestamp < analysis_metadata.update_due) {
            title_metadata.analysis.status = 'up_to_date'
        }
    }

    AugmentMetadataWithMangaupdatesCategories([title_metadata])
    title_metadata['enid'] = title_id

    return title_metadata;
}


export async function getSuggestedPrereadForTitle(user_id, title_id, target_selection, source_selection)
{
    var suggested_preread = await db.collection(COLLECTION_TITLEDATA).aggregate([
        {
            $lookup: { from:COLLECTION_SUGGESTED_PREREAD, localField:"_id", foreignField:"source_title_id", as:"suggestion"}
        },
        {
            $unwind: { path:"$suggestion", preserveNullAndEmptyArrays:false }
        },
        {
            $match: {'suggestion.version':SUGGESTED_PREREAD_ANALYSIS_VERSION,'suggestion.user_id':user_id,'suggestion.target_title_id':title_id,'suggestion.target_selection':target_selection,'suggestion.source_selection':source_selection}
        },
        {
            $lookup: { from:COLLECTION_MANGAUPDATES, localField:"_id", foreignField:"_id", as:"mangaupdates_data"}
        },
        {
            $unwind: { path:"$mangaupdates_data", preserveNullAndEmptyArrays:true }
        },
    ]).toArray();

    return suggested_preread;
}

export async function getMangaDataForSingleTitle(title_id) {

    var title_metadata = await db.collection(COLLECTION_TITLEDATA).findOne({'_id':title_id})
    if (title_metadata == null) {
        return undefined;
    }

    let volume_data = await db.collection(COLLECTION_VOLUMEDATA).aggregate([
        {
            $match: {'title_id':title_id}
        },
        {
            $lookup: { from:COLLECTION_VOL_IMPORT_METADATA, localField:"vol_id", foreignField:"_id", as:"import_metadata"}
        },
        {
            $unwind: { path:"$import_metadata", preserveNullAndEmptyArrays:true }
        }
    ]).toArray();

    let vol_by_id = {}
    for (let vol_info of volume_data) {
        vol_by_id[vol_info.vol_id] = vol_info
    }

    var chapter_data = await db.collection(COLLECTION_CHAPTERDATA).find({'title_id':title_id}).toArray()
    var chapter_by_id = {}
    for (let chapter_info of chapter_data) {
        chapter_by_id[chapter_info.ch_id] = chapter_info
    }

    var img_corr_data = await db.collection(COLLECTION_IMAGE_CORRESPONDENCE_DATA).findOne({'title_id':title_id})

    var title_data = {
        'en_data' : { 'ch_en':{}, 'ch_enh':[], 'vol_en':{}, 'ch_naen':[], 'num_pages':[]},
        'jp_data' : { 'ch_jp':{}, 'ch_jph':[], 'vol_jp':{}, 'ch_najp':[], 'num_pages':[]},
    }
    if (img_corr_data !== null) {
        title_data.imgdata = img_corr_data
    }

    for (let lang of ['en','jp']) {
        if (Object.keys(title_metadata.lang).includes(lang)) {
            let start_ch_idx = 0
            let ch_idx = 0
            if ('volumes' in title_metadata.lang[lang]) {
                let volumes = title_metadata.lang[lang].volumes
                let lang_data = title_data[lang+'_data']
                let ch_lang = lang_data['ch_'+lang] // file list by chapter idx
                let ch_lang_h = lang_data['ch_'+lang+'h']   // chapter 'url' list
                let ch_na_lang = lang_data['ch_na'+lang]    // chapter name list
                let vol_lang = lang_data['vol_'+lang]   // volume structure
                let ch_num_pages = lang_data.num_pages
                let vol_num = 0
                for (let vol_id of volumes) {
                    let vol = vol_by_id[vol_id];
                    let vol_content_ready = false;
                    for (let ch_id of vol.chapters) {
                        let ch = chapter_by_id[ch_id]
                        ch_lang[ch_idx+1] = ch.files
                        ch_lang_h.push(ch.ch_url)
                        ch_na_lang.push(ch.ch_name)
                        ch_num_pages.push(ch.num_pages)
                        ch_idx += 1
                        if (ch.files.length>0) {
                            vol_content_ready = true;
                        }
                    }
                    vol_lang[vol.vol_name] = {'id':vol.vol_id, 's':start_ch_idx, 'e':ch_idx-1, 'vol_num': vol_num, 'num_pages':vol.num_pages ,'content_ready':vol_content_ready}
                    start_ch_idx += ch_idx
                    vol_num += 1
                }
            }
        }
    }

    title_data['vol_info'] = vol_by_id
    title_data['_id'] = {'$oid':title_id}

    return title_data
}
