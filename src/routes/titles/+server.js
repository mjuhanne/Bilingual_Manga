import { json } from '@sveltejs/kit';
import { getMetadataForTitles, searchTitleMetadata, getAllValuesForMetadataField } from "$lib/collections.js"

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
    }
    return json(ret);
}

