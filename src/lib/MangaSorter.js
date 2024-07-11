
let common_sort_options = {
    'Newly added': { s:'', field: '',         type:'str', subheading_template:'', rev:false },
    'A-Z'        : { s:'', field: 'entit',    type:'str', subheading_template:'', rev:false },
    'Release'    : { s:'', field: 'Release',  type:'val', subheading_template:'Release _', rev:true },
    'Rating'     : { s:'mangaupdates_data', field: 'rating', type:'val', subheading_template:'Rating: _', rev:true },
    'Status'     : { s:'', field: 'Status',   type:'str', subheading_template:'_', rev:false },
    'Read status': { s:'', field: 'read_chapter_pct',   type:'val', subheading_template:'Read _ %', rev:true },
    'JLPT content': { s:'total_statistics', field: 'jlpt_word_content_pct',  type:'val', subheading_template:'JLPT _ %', rev:true },
    'Advanced JLPT': { s:'total_statistics', field: 'advanced_jlpt_word_content_pct',   type:'val', subheading_template:'JLPT1 _ %', rev:true },
    'Intermediate JLPT (w)': { s:'total_statistics', field: 'weighted_intermediate_jlpt_word_content_pts',   type:'val', subheading_template:'JLPT2-3 _', rev:true },
    'non-JLPT words/vol': { s:'unique_statistics', field: 'num_non_jlpt_words_per_v',   type:'val', subheading_template:'non-JLPT w/v _', rev:false },
    'Volumes':    { s:'', field: 'num_volumes',type:'val', subheading_template:'_ volumes', rev:true },
    'Pages':      { s:'', field: 'num_pages',     type:'val', subheading_template:'_ pages', rev:true },
    'Total words': { s:'total_statistics', field: 'num_words',     type:'val', subheading_template:'_ words', rev:true },
    'Words/page': { s:'total_statistics', field: 'w_per_p',       type:'val', subheading_template:'_ words/page', rev:true },
    'Kanji/word': { s:'total_statistics', field: 'k_per_w_pct',  type:'val', subheading_template:'Kanjis/word _ %', rev:true },
    'Comp input pct': { s:'', field: 'comprehensible_input_pct',  type:'val', subheading_template:'CI _ %', rev:true },
    'Comp input next ch pct': { s:'', field: 'comprehensible_input_pct_next_ch',  type:'val', subheading_template:'CI _ %', rev:true },
    'Opt Comp input': { s:'', field: 'comprehensible_input_score',  type:'val', subheading_template:'OPT CI _', rev:true },
    'Opt Comp input next ch': { s:'', field: 'comprehensible_input_score_next_ch',  type:'val', subheading_template:'OPT CI _', rev:true },
    'Known w %': { s:'total_statistics', field: 'pct_known_words',  type:'val', subheading_template:'Known w _ %', rev:true },
    'Next chp comp': { s:'total_statistics', field: 'pct_known_words_next_ch',  type:'val', subheading_template:'Next chapter comp _ %', rev:true },
    'Next chp unkn words': { s:'unique_statistics', field: 'num_unknown_words_next_ch',  type:'val', subheading_template:'_ unk w in next chp', rev:true },
    'Unkn JLPT kanjis': { s:'unique_statistics', field: 'num_unknown_jlpt_kanjis',  type:'val', subheading_template:'_ unk JLPT kanjis', rev:true },
    'Unkn JLPT kanjis next ch': { s:'unique_statistics', field: 'num_unknown_jlpt_kanjis_next_ch',  type:'val', subheading_template:'_ unk JLPT kanjis', rev:true },
    'JLPT improvement': { s:'', field: 'jlpt_improvement_pts',  type:'val', subheading_template:'_ pts', rev:true },
};


export let download_view_sort_options = {
    ...{
        'Repository status': { s:'', field: 'repo_status',   type:'str', subheading_template:'_', rev:false },
    },
    ...common_sort_options,
}

export let suggested_preread_sort_options = {
    ...{
        'Common unknown words': { s:'', field: 'ncuuw',   type:'val', subheading_template:'_', rev:true },
        'Common unknown words/vol': { s:'', field: 'ncuuw_per_vol',   type:'val', subheading_template:'_', rev:true },
        'Comprehension % improvement': { s:'', field: 'improvement_pct',   type:'val', subheading_template:'_', rev:true },
        'Relative improvement': { s:'', field: 'relative_improvement',   type:'val', subheading_template:'_', rev:true },
        'Relative CI improvement': { s:'', field: 'relative_ci_improvement',   type:'val', subheading_template:'_', rev:true },
    },
    ...common_sort_options,
}

export let category_showcase_sort_options = {
    ...{
        'Category score': { s:'', field: 'category_score',   type:'val', subheading_template:'Score _', rev:true },
    },
    ...common_sort_options,
}

export let showcase_sort_options = common_sort_options;

let sort_options = {
    ...download_view_sort_options,
    ...suggested_preread_sort_options,
    ...category_showcase_sort_options,
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
        if (sort_value === undefined || sort_value == 'Placeholder') {
            if ( sort_options[sort_criteria].type == 'val') {
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
    if (sort_options[sort_criteria].type == 'val') {
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
