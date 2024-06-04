
let common_sort_options = {
    'Newly added': { s:'', field: '',         is_value:false, subheading_template:'', rev:false },
    'A-Z'        : { s:'', field: 'entit',    is_value:false, subheading_template:'', rev:false },
    'Release'    : { s:'', field: 'Release',  is_value:true, subheading_template:'Release _', rev:true },
    'Rating'     : { s:'rating_data', field: 'rating', is_value:true, subheading_template:'Rating: _', rev:true },
    'Status'     : { s:'', field: 'Status',   is_value:false, subheading_template:'_', rev:false },
    'Read status': { s:'', field: 'read_chapter_pct',   is_value:true, subheading_template:'Read _ %', rev:true },
    'JLPT content': { s:'total_statistics', field: 'jlpt_word_content_pct',  is_value:true, subheading_template:'JLPT _ %', rev:true },
    'Advanced JLPT': { s:'total_statistics', field: 'advanced_jlpt_word_content_pct',   is_value:true, subheading_template:'JLPT1 _ %', rev:true },
    'Intermediate JLPT (w)': { s:'total_statistics', field: 'weighted_intermediate_jlpt_word_content_pts',   is_value:true, subheading_template:'JLPT2-3 _', rev:true },
    'non-JLPT words/vol': { s:'unique_statistics', field: 'num_non_jlpt_words_per_v',   is_value:true, subheading_template:'non-JLPT w/v _', rev:false },
    'Volumes':    { s:'', field: 'num_volumes',is_value:true, subheading_template:'_ volumes', rev:true },
    'Pages':      { s:'', field: 'num_pages',     is_value:true, subheading_template:'_ pages', rev:true },
    'Total words': { s:'total_statistics', field: 'num_words',     is_value:true, subheading_template:'_ words', rev:true },
    'Words/page': { s:'total_statistics', field: 'w_per_p',       is_value:true, subheading_template:'_ words/page', rev:true },
    'Kanji/word': { s:'total_statistics', field: 'k_per_w_pct',  is_value:true, subheading_template:'Kanjis/word _ %', rev:true },
    'Comp input pct': { s:'', field: 'comprehensible_input_pct',  is_value:true, subheading_template:'CI _ %', rev:true },
    'Comp input next ch pct': { s:'', field: 'comprehensible_input_pct_next_ch',  is_value:true, subheading_template:'CI _ %', rev:true },
    'Known w %': { s:'total_statistics', field: 'pct_known_words',  is_value:true, subheading_template:'Known w _ %', rev:true },
    'Next chp comp': { s:'total_statistics', field: 'pct_known_words_next_ch',  is_value:true, subheading_template:'Next chapter comp _ %', rev:true },
    'Next chp unkn words': { s:'unique_statistics', field: 'num_unknown_words_next_ch',  is_value:true, subheading_template:'_ unk w in next chp', rev:true },
    'JLPT improvement': { s:'', field: 'jlpt_improvement_pts',  is_value:true, subheading_template:'_ pts', rev:true },
};


export let download_view_sort_options = {
    ...{
        'Repository status': { s:'', field: 'repo_status',   is_value:false, subheading_template:'_', rev:false },
    },
    ...common_sort_options,
}

export let suggested_preread_sort_options = {
    ...{
        'Common unknown words': { s:'', field: 'ncuuw',   is_value:true, subheading_template:'_', rev:true },
        'Common unknown words/vol': { s:'', field: 'ncuuw_per_vol',   is_value:true, subheading_template:'_', rev:true },
        'Comprehension % improvement': { s:'', field: 'improvement_pct',   is_value:true, subheading_template:'_', rev:true },
        'Relative improvement': { s:'', field: 'relative_improvement',   is_value:true, subheading_template:'_', rev:true },
    },
    ...common_sort_options,
}

export let showcase_sort_options = common_sort_options;

let sort_options = {
    ...download_view_sort_options,
    ...suggested_preread_sort_options,
}

const getSortValue = (x, key, sort_criteria) => {
    let sort_value = undefined;
    if(sort_criteria=='Newly added'){
        sort_value = x[key];
    } else {
        let sc = sort_options[sort_criteria];
        if (sc.s != '') {
            // sort value is in sub-dictionary
            if (sc.s in x[key]) {
                if (sc.field in x[key][sc.s]) {
                    sort_value = x[key][sc.s][ sc.field ];
                }
            }
        } else {
            if (sc.field in x[key]) {
                sort_value = x[key][ sc.field ];
            }
        }
        if (sort_value === undefined) {
            if ( sort_options[sort_criteria].is_value) {
                sort_value = -1;
            } else {
                sort_value = '-';
            }
        }
    }
    return sort_value;
}

export const sortManga = (x, sort_criteria, sort_reverse, extra_label) => {
    let sorted_manga_list = [];

    // Create items array with a sort value corresponding to selected sort criteria
    var manga_by_criteria = Object.keys(x).map(function(key) {
        return [key, getSortValue(x,key,sort_criteria)];
    });
 
    let reverse = sort_reverse ^ sort_options[sort_criteria].rev;
    if (sort_options[sort_criteria].is_value) {
        // Sort the array based on the sort value (which is a value)
        manga_by_criteria.sort(function(first, second) {
            if (reverse) {
                return second[1] - first[1];
            }
            return first[1] - second[1];
        });
    } else {
        // Sort the array based on the sort value (which is a string)
        if (reverse) {
            if('Newly added'===sort_criteria) {
                manga_by_criteria.reverse();
            } else {
                manga_by_criteria.sort((a,b)=>{return b[1].toLowerCase().localeCompare(a[1].toLowerCase())});
            }
        } else {
            if('Newly added' !==sort_criteria) {
            manga_by_criteria.sort((a,b)=>{return a[1].toLowerCase().localeCompare(b[1].toLowerCase())});
            } 
            // 'Newly added' is already in the correct order
        }
    }

    // reconstruct the manga list and add additional subheading (the sort criteria+value) if necessary
    for(let i = 0; i < manga_by_criteria.length; i++) {
        let manga_sort_tuple = manga_by_criteria[i];
        let idx = manga_sort_tuple[0];
        let sort_value = manga_sort_tuple[1];
        if ((sort_value == -1) || (sort_value == '-')) {
            sort_value = "NA";
        }
        sorted_manga_list[i] = x[idx];
        sorted_manga_list[i]['sort_value'] = String(sort_value);
        sorted_manga_list[i]['subheading'] = 
            sort_options[sort_criteria].subheading_template.replace('_', String(sort_value));

        if (extra_label != 'None') {
            let label_value = getSortValue(x,idx,extra_label);
            if ((label_value == -1) || (sort_value == '-')) {
                label_value = "NA";
            }
            sorted_manga_list[i]['subheading2'] = 
                sort_options[extra_label].subheading_template.replace('_', String(label_value));
        } else {
            sorted_manga_list[i]['subheading2'] = '';
        }
    }
    return sorted_manga_list;
};
