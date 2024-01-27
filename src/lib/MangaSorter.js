export let sort_options = {
    'Newly added': { field: '',         is_value:false, subheading_template:'', rev:false },
    'A-Z'        : { field: 'entit',    is_value:false, subheading_template:'', rev:false },
    'Release'    : { field: 'Release',  is_value:true, subheading_template:'Release _', rev:true },
    'Rating'     : { field: '',         is_value:true, subheading_template:'Rating: _', rev:true },
    'Status'     : { field: 'Status',   is_value:false, subheading_template:'_', rev:false },
    'Read status': { field: 'read_chapter_pct',   is_value:true, subheading_template:'Read _ %', rev:true },
};
    
export const sortManga = (x, sort_criteria, sort_reverse) => {
    let sorted_manga_list = [];

    // Create items array with a sort value corresponding to selected sort criteria
    var manga_by_criteria = Object.keys(x).map(function(key) {
        let sort_value;
        if (sort_criteria=='Rating') {
            sort_value = x[key]['rating_data']['rating'];
        } else if(sort_criteria=='Newly added'){
            sort_value = x[key];//enid isn't right for half of the manga(Yotsuba is the oldest not Emanon).They are already in that order in manga_titles array. 
        }
        else {
            sort_value = x[key][ sort_options[sort_criteria].field ];
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
        sorted_manga_list[i] = x[idx];
        sorted_manga_list[i]['subheading'] = 
            sort_options[sort_criteria].subheading_template.replace('_', String(manga_sort_tuple[1]));
    }
    return sorted_manga_list;
};
