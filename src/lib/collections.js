import { getDB } from '$lib/mongo';
const db = getDB();

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

export async function getUserWordHistory(user_id, word_id)
{
    var search_query = {'user_id':user_id,'wid':word_id}
    console.log("Querying",search_query)
    const data = await db.collection("br_user_word_learning_history").findOne(search_query);
    if (data == null) {
        return [];
    }
    console.log(`getUserWordHistory ${word_id}: ` + JSON.stringify(data['history']))
    return data['history'];
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


const AugmentMetadataWithMangaupdatesCategories = (manga_titles) => {

    let global_avg_votes = 0;
    let valid_entries = 0;

    manga_titles.forEach(element => {
        let id = element.enid;

        if (element['mangaupdates_data'] !== undefined) {
            if (ext_mangaupdates[id]['series_id'] != -1) {
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


export async function getMetadata(user_id, skip, limit)
{
    let m = (await getCollection("br_settings", 0, 0))[0];

    var match_query = {} // TODO

    var title_metadata = await db.collection("br_metadata").aggregate([
        {
            $lookup: { from:"br_mangaupdates", localField:"_id", foreignField:"_id", as:"mangaupdates"}
        },
        {
            $unwind: { path:"$mangaupdates", preserveNullAndEmptyArrays:true }
        },
        {
            $lookup: { from:"br_lang_summary", localField:"_id", foreignField:"_id", as:"series"}
        },
        {
            $unwind: { path:"$series", preserveNullAndEmptyArrays:true }
        },
        {
            $match: match_query
        },
        {
            $sort: {"_id":-1}
        }
    ]).project({_id:0}).skip(skip).limit(limit).toArray();

    m['manga_titles'] = title_metadata
    m['metadata_by_id'] = {}
    for (let d of title_metadata) {
        m['metadata_by_id'][d['enid']] = d
    }

    // average manga/book statistics
    var avg_summary = await db.collection("br_lang_summary").find({'_id':'average_manga'}).project({_id:0}).toArray()
    m['average_manga'] = avg_summary[0]
    m['metadata_by_id']['average_manga'] =  m['average_manga']
    avg_summary = await db.collection("br_lang_summary").find({'_id':'average_book'}).project({_id:0}).toArray()
    m['average_book'] = avg_summary[0]
    m['metadata_by_id']['average_book'] =  m['average_book']

    const custom_lang_search_query = { 'type':'summary', 'user_id':user_id }
    var custom_lang_analyses = await db.collection("br_custom_lang_analysis").find(custom_lang_search_query).project({_id:0,type:0,user_id:0}).toArray()
    for (let an of custom_lang_analyses) {
        let title_id = an['title_id']
        if (title_id in m['metadata_by_id']) {
            iterative_copy(an, m['metadata_by_id'][title_id])
        } else {
            //console.log(title_id + " not found in metadata")
        }
    }

    // Update categories
    m.average_category_vote_count = AugmentMetadataWithMangaupdatesCategories(m['manga_titles'])

    return [m];
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
            $lookup: { from:"br_mangaupdates", localField:"_id", foreignField:"_id", as:"mangaupdates"}
        },
        {
            $unwind: { path:"$mangaupdates", preserveNullAndEmptyArrays:true }
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

    console.log("metadata.series: " + JSON.stringify(title_metadata['series']))

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
