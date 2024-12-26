
export const scopes = {'series':'series','volume':'next unread volume','chapter':'next unread chapter'}

let common_sort_options = {
    'Newly added'   : { sc:false, field: '',         type:'str', subheading_template:'', rev:false },
    'A-Z'           : { sc:false, field: 'entit',    type:'str', subheading_template:'', rev:false },
    'Release'       : { sc:false, field: 'Release',  type:'val', subheading_template:'Release _', rev:true },
    'Rating'        : { sc:false, field: 'mangaupdates_data.rating', type:'val', subheading_template:'Rating: _', rev:true },
    'Status'        : { sc:false, field: 'Status',   type:'str', subheading_template:'_', rev:false },
    'Read status'   : { sc:false, field: 'read_chapter_pct',   type:'val', subheading_template:'Read _ %', rev:true },
    'JLPT content'  : { sc:false, field: 'total_statistics.jlpt_word_content_pct',  type:'val', subheading_template:'JLPT _ %', rev:true },
    'Advanced JLPT' : { sc:false, field: 'total_statistics.advanced_jlpt_word_content_pct',   type:'val', subheading_template:'JLPT1 _ %', rev:true },
    'Intermediate JLPT (w)': { sc:false, field: 'total_statistics.weighted_intermediate_jlpt_word_content_pts',   type:'val', subheading_template:'JLPT2-3 _', rev:true },
    'non-JLPT words/vol': { sc:false, field: 'unique_statistics.num_non_jlpt_words_per_v',   type:'val', subheading_template:'non-JLPT w/v _', rev:false },
    'Volumes'       : { sc:false, field: 'num_volumes',type:'val', subheading_template:'_ volumes', rev:true },
    'Pages'         : { sc:true, field: 'num_pages',     type:'val', subheading_template:'_ pages', rev:true },
    'Total words'   : { sc:true, field: 'total_statistics.words.num_all',     type:'val', subheading_template:'_ words', rev:true },
    'Words/page'    : { sc:false, field: 'total_statistics.w_per_p',       type:'val', subheading_template:'_ words/page', rev:true },
    'Kanji/word'    : { sc:false, field: 'total_statistics.k_per_w_pct',  type:'val', subheading_template:'Kanjis/word _ %', rev:true },
    'Comp input pct': { sc:true, field: 'comprehensible_input_pct',  type:'val', subheading_template:'CI _ %', rev:true },
    'Comp input ex kk pct': { sc:true, field: 'comprehensible_input_ex_katakana_pct',  type:'val', subheading_template:'CI(-K) _ %', rev:true },
    'Comp input score': { sc:true, field: 'comprehensible_input_score',  type:'val', subheading_template:'CI score _', rev:true },
    'Known w %'     : { sc:true, field: 'total_statistics.words.pct_known_pre_known',  type:'val', subheading_template:'Known w _ %', rev:true },
    'Unknown words' : { sc:true, field: 'unique_statistics.words.num_unknown_unfamiliar',  type:'val', subheading_template:'_ unk words', rev:true },
    'Unkn JLPT kanjis': { sc:true, field: 'unique_statistics.kanjis.jlpt_unknown_num',  type:'val', subheading_template:'_ unk JLPT kanjis', rev:true },
    'JLPT improvement': { sc:false, field: 'series_analysis_for_jlpt.relative_improvement_pts',  type:'val', subheading_template:'_ pts', rev:true },
};


export let download_view_sort_options = {
    ...{
        'Repository status': { sc:false, field: 'repo_status',   type:'str', subheading_template:'_', rev:false },
    },
    ...common_sort_options,
}

export let suggested_preread_sort_options = {
    ...{
        'Common unknown words':     { sc:false, field: 'ncuuw',   type:'val', subheading_template:'_', rev:true },
        'Common unknown words/vol': { sc:false, field: 'ncuuw_per_vol',   type:'val', subheading_template:'_', rev:true },
        'Comprehension % improvement': { sc:false, field: 'improvement_pct',   type:'val', subheading_template:'_', rev:true },
        'Relative improvement'      : { sc:false, field: 'relative_improvement',   type:'val', subheading_template:'_', rev:true },
        'Relative CI improvement'   : { sc:false, field: 'relative_ci_improvement',   type:'val', subheading_template:'_', rev:true },
    },
    ...common_sort_options,
}

export let category_showcase_sort_options = {
    ...{
        'Category score': { sc:false, field: 'category_score',   type:'val', subheading_template:'Score _', rev:true },
    },
    ...common_sort_options,
}

export let showcase_sort_options = common_sort_options;

let sort_options = {
    ...download_view_sort_options,
    ...suggested_preread_sort_options,
    ...category_showcase_sort_options,
}

export const getValue = (elem, params, sort_scope) => {
    let value = undefined;
    let value_path = params['field'].split('.');
    if (params.sc) {
        value_path = [sort_scope, ...value_path]
    }

    let i = 0;
    while (i < value_path.length && value_path[i] in elem) {
        elem = elem[value_path[i]]
        i += 1
    }
    if (i == value_path.length) {
        value = elem;
    }
    return value
}

export const getSortValue = (elem, sort_criteria, sort_scope) => {
    let sort_value = undefined;
    if(sort_criteria=='Newly added'){
        sort_value = elem;
    } else {
        sort_value = getValue(elem, sort_options[sort_criteria], sort_scope)
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

export const sortManga = (x, sort_criteria, sort_scope, sort_reverse, extra_label, extra_label_scope) => {
    let sorted_manga_list = [];

    // Create items array with a sort value corresponding to selected sort criteria
    var manga_by_criteria = Object.keys(x).map(function(key) {
        return [key, getSortValue(x[key],sort_criteria, sort_scope)];
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
            let label_value = getSortValue(x[idx],extra_label, extra_label_scope);
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
