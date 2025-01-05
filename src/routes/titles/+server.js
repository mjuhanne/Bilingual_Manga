import { json } from '@sveltejs/kit';
import { getMetadataForTitles, searchTitleMetadata, getAllValuesForMetadataField } from "$lib/collections.js"
import {exec} from "node:child_process";
import util from "node:util";
const execSync = util.promisify(exec);

async function getTitleMetadata(param) {

    let filter_struct = {
        'skip':param.skip,
        'limit':param.limit,
        'fixed_filter' : param.fixed_filter,
        'filters' : param.variable_filters
    }

    let sort_struct = {
        'field':param.sort_field,
        'reverse':param.reverse,
    }
    
    let result = await getMetadataForTitles(param.user_id, sort_struct, filter_struct)

    console.log(`Returning ${result['title_metadata'].length}/${result['filtered_title_count']}/${result['unfiltered_title_count']} titles`)
    return result;
    //{'title_metadata':result['metadata'],'unfiltered_title_count':title_count,'filtered_title_count':result['filtered_count']}
}


async function searchMetadata(param) {

    let title_metadata = await searchTitleMetadata(param.search_term, param.limit)

    console.log(`Returning ${title_metadata.length} titles`)
    return title_metadata
}


async function setGoogleBooksId(param) {

    let exec_cmd = `python tools/book2bm.py set_google_book_id ${param.title_id} ${param.google_book_id}`
    console.log(exec_cmd);
    try {
        const { stdout, stderr } = await execSync(exec_cmd);
        console.log("Results: " + stdout);
    } catch (error) {
        console.log("Error: ", error);
        return {
            success : false,
            'response' : error
        };
    }
    return {
        success : true,
        'response' : 'ok'
    };
}

export async function POST({ request }) {
    const data = await request.json();
    console.log("POST /titles: " + JSON.stringify(data) );
    let ret = { success : false};
    if (data.func == 'get_title_metadata') {
        ret= {
            success : true,
            'response' : await getTitleMetadata(data.param)
        };
    } else if (data.func == 'get_metadata_field_variations') {
        ret= {
            success : true,
            'response' : await getAllValuesForMetadataField(data.param.field_name)
        };
    } else if (data.func == 'search') {
        ret= {
            success : true,
            'response' : await searchMetadata(data.param)
        };
    } else if (data.func == 'set_google_books_id') {
        let res = 
        ret= await setGoogleBooksId(data.param)
    }
    return json(ret);
}

