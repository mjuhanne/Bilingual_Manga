import { showcase_sort_options } from '$lib/MangaSorter.js';

export let available_filters = {
    ...{
        'Genre': { s:'', field: 'genres',   type:'list'},
        'Category': { s:'mangaupdates_data', field: 'category_list',   type:'list'},
        'Author': { s:'', field: 'Author',   type:'list'},
        'Artist': { s:'', field: 'Artist',   type:'list'},
        'Book': { s:'', field: 'is_book',   type:'boolean'},
    },
    ...showcase_sort_options,
}

const getFilterValue = (data, filter_params) => {
    let filter_value = undefined;

    if (filter_params.s != '') {
        // sort value is in sub-dictionary
        if (filter_params.s in data) {
            if (filter_params.field in data[filter_params.s]) {
                filter_value = data[filter_params.s][ filter_params.field ];
            }
        }
    } else {
        if (filter_params.field in data) {
            filter_value = data[ filter_params.field ];
        }
    }
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

    for (let key in x) {
        let m = x[key];
        let match = true;
        for (let filter of filters) {
            if (filter['en']) {
                let filter_params = available_filters[filter['f']]
                let v = getFilterValue(m, filter_params);
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
        }
        if (match) {
            filtered_manga_list.push(m);
        }
    }
    return filtered_manga_list;
};
