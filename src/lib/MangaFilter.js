import { showcase_sort_options, getValue } from '$lib/MangaSorter.js';

export let available_filters = {
    ...{
        'Genre': { sc:false, field: 'genres',   type:'list'},
        'Category': { sc:false, field: 'mangaupdates_data.category_list',   type:'list'},
        'Author': { sc:false, field: 'authors',   type:'list'},
        'Artist': { sc:false, field: 'artists',   type:'list'},
        'Status': { sc:false, field: 'status',   type:'list'},
        'Type': { sc:false, field: 'type',   type:'list'},
        'Favourite': { sc:false, field: 'favourite',   type:'boolean'},
    },
    ...showcase_sort_options,
}

export function getFixedFilter(filter_name, filter_value) {
    if (filter_name in available_filters) {
        return {'field':available_filters[filter_name].field,'op':'=','value':filter_value,'type':available_filters[filter_name].type}
    }
    return {}
}


const getFilterValue = (elem, filter_params, scope) => {
    let filter_value = getValue(elem, filter_params, scope)

    if (filter_value === undefined) {
        if ( filter_params.type == 'val') {
            filter_value = -1;
        } else {
            filter_value = '-';
        }
    }
    return filter_value;
}

export const filterManga = (x, filters) => {
    let filtered_manga_list = [];

    let active_filters = [];
    for (let filter of filters) {
        if (filter['en']) {
            let idx = Object.keys(available_filters).indexOf(filter['f']);
            if (idx != -1) {
                active_filters.push(filter)
            }
        }
    }

    for (let key in x) {
        let m = x[key];
        let match = true;
        for (let filter of active_filters) {
            let filter_params = available_filters[filter['f']]

            let v;
            if (filter_params.sc) {
                v = getFilterValue(m, filter_params, filter['sc']);
            } else {
                v = getFilterValue(m, filter_params, '');
            }
            switch(filter['op']) {
                case '<':
                    if (v >= filter['v']) {
                        match = false;
                    }
                    break;
                case '<=':
                    if (v > filter['v']) {
                        match = false;
                    }
                    break;
                case '>':
                    if (v <= filter['v']) {
                        match = false;
                    }
                    break;
                case '>=':
                    if (v < filter['v']) {
                        match = false;
                    }
                    break;
                case '=':
                    if (filter_params.type == 'list') {
                        if (v.indexOf(filter['v']) == -1) {
                            match = false;
                        }
                    } else {
                        if (v != filter['v']) {
                            match = false;
                        }
                    }
                    break;
                case '!=':
                    if (filter_params.type == 'list') {
                        if (v.indexOf(filter['v']) != -1) {
                            match = false;
                        }
                    } else {
                        if (v == filter['v']) {
                            match = false;
                        }
                    }
                    break;
                default:
                    console.log("Unknown op",filter['op']);
                    match = false;
                }
            //console.log(m['title'],v);
        }
        if (match) {
            filtered_manga_list.push(m);
        }
    }
    return filtered_manga_list;
};
