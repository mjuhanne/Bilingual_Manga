export let sort_options = {
    'Newly added': { field: '',         is_value:false, subheading_template:'', rev:false },
    'A-Z'        : { field: 'entit',    is_value:false, subheading_template:'', rev:false },
    'Release'    : { field: 'Release',  is_value:true, subheading_template:'Release _', rev:true },
    'Rating'     : { field: '',         is_value:true, subheading_template:'Rating: _', rev:true },
    'Status'     : { field: 'Status',   is_value:false, subheading_template:'_', rev:false },
    'Read status': { field: 'read_chapter_pct',   is_value:true, subheading_template:'Read _ %', rev:true },
    'JLPT content': { field: 'jlpt_content_pct',  is_value:true, subheading_template:'JLPT _ %', rev:true },
    'Advanced JLPT': { field: 'advanced_jlpt_content_pct',   is_value:true, subheading_template:'JLPT1 _ %', rev:true },
    'Intermediate JLPT': { field: 'intermediate_jlpt_content_pct',   is_value:true, subheading_template:'JLPT2-3 _ %', rev:true },
    'Volumes':    { field: '',              is_value:true, subheading_template:'_ volumes', rev:true },
    'Pages':      { field: 'num_pages',     is_value:true, subheading_template:'_ pages', rev:true },
    'Words/page': { field: 'w_per_p',       is_value:true, subheading_template:'_ words/page', rev:true },
    'Word count': { field: 'num_words',     is_value:true, subheading_template:'_ words', rev:true },
    'Kanji/word': { field: 'k_per_w_perc',  is_value:true, subheading_template:'Kanjis/word _ %', rev:true },
};
    
export const sortManga = (x, sort_criteria, sort_reverse) => {
    let sorted_manga_list = [];

    // Create items array with a sort value corresponding to selected sort criteria
    var manga_by_criteria = Object.keys(x).map(function(key) {
        let sort_value;
        if (sort_criteria=='Rating') {
            sort_value = x[key]['rating_data']['rating'];
        } else if (sort_criteria=='Volumes') {
            sort_value = Object.keys(x[key]['chapter_names']).length; // tankobons are almost always listed as chapters 
        } else if(sort_criteria=='Newly added'){
            sort_value = x[key];
        }
        else {
            if (sort_options[sort_criteria].field in x[key]) {
                sort_value = x[key][ sort_options[sort_criteria].field ];
            } else {
                if ( sort_options[sort_criteria].is_value) {
                    sort_value = -1;
                } else {
                    sort_value = '-';
                }

            }
        }
        return [key, sort_value ];   
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
        manga_by_criteria.sort(function(first, second) {
            let sorted = [second[1],first[1]].sort();
            if (reverse) {
                return sorted[0] == first[1] ? 1 : -1;
            }
            return sorted[0] == first[1] ? -1 : 1;
        });
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
        sorted_manga_list[i]['subheading'] = 
            sort_options[sort_criteria].subheading_template.replace('_', String(sort_value));
    }
    return sorted_manga_list;
};
