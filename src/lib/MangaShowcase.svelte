    <script>
    import MangaCard from '$lib/MangaCard.svelte';
    import MangaSortDashboard from '$lib/MangaSortDashboard.svelte';
    import MangaLabelDashboard from '$lib/MangaLabelDashboard.svelte';
    import MangaFilterDashboard from '$lib/MangaFilterDashboard.svelte';
    import AddMangaFilter from './AddMangaFilter.svelte';
    import { deserialize } from '$app/forms';
    import { page } from '$app/stores';
    import { goto } from "$app/navigation";
    import { showcase_sort_options, category_showcase_sort_options, addLabeling, resolveScopeFieldName } from '$lib/MangaSorter.js';
    import { available_filters, filterManga, getFixedFilter } from '$lib/MangaFilter.js';
	import { onMount } from 'svelte';
    import {DEFAULT_USER_ID} from '$lib/UserDataTools.js'
    export let x;
    export let cdncdn;
    export let cdncdn1;
    export let selected_category = '';
    export let fixed_filter_name = '';
    export let fixed_filter_value = '';

    let title_metadata = [];
    let title_count = 0;
    let filtered_title_count = 0;
    let numoe=12
    let pagen=1

    let sort_options = showcase_sort_options;
    if (selected_category != '') {
        sort_options = category_showcase_sort_options;
    }

    let user_filter_list = [];
	onMount(() => {
        user_filter_list = localStorage.getItem("user_filter_list");
        if (user_filter_list === null || user_filter_list == "")  {
            user_filter_list = [];
        } else {
            user_filter_list = JSON.parse(user_filter_list);
        }
        fetchMetadataForTitles() 
    });

    async function fetchMetadataForTitles() {
        let sort_field = sort_options[sort_criteria]['field']
        let scope_field_prefix = ''
        if (sort_options[sort_criteria]['sc']) {
            sort_field = resolveScopeFieldName(sort_field, sort_scope)
        }
        let reverse = sort_reverse ^ sort_options[sort_criteria].rev

        let filters = [];
        console.log("User Filters:",user_filter_list)
        for (let filter of user_filter_list) {
            if (filter.en) {
                let filter_field = available_filters[filter.f].field
                if ('sc' in filter) {
                    if (filter.sc != '') {
                        filter_field = resolveScopeFieldName(filter_field, filter.sc)
                    }
                }
                filters.push({'field':filter_field,'op':filter.op,'value':filter.v,'type':available_filters[filter.f].type});
            }
        }

        // fixed filter (e.g.. manga-author, manga-status ..) is kept separate
        // to get initial title count before applying user created filters
        let fixed_filter = getFixedFilter(fixed_filter_name, fixed_filter_value)

        let limit = numoe
        console.log("pagen" + pagen)
        let skip = (pagen - 1) * numoe
        let body = JSON.stringify({
            'func' : 'get_title_metadata', 
            'param' : {
                'user_id' : DEFAULT_USER_ID,
                'sort_field' : sort_field,
                'fixed_filter' : fixed_filter,
                'variable_filters' : filters,
                'reverse' : reverse,
                'limit' : limit,
                'skip' : skip,
            }
        });
        const response = await fetch( "/titles", {
            headers: {"Content-Type" : "application/json" },
            method: 'POST',
            body: body,
        });
        const result = deserialize(await response.text());
        title_count = result['response']['unfiltered_title_count']
        filtered_title_count = result['response']['filtered_title_count']
        title_metadata = result['response']['title_metadata']
        console.log("fetched titles:" + title_metadata.length)
    };


    let pagenew=1;
    let url1=""

    url1=`${$page.url}`.split('?')[0]
    pagen=$page.url.searchParams.get('page');
    if (pagen === null) {
        pagen = 1
    } else {
        pagen = parseInt(pagen)
    }
    let ls=$page.url.searchParams.get('ls');
    let sort_criteria=$page.url.searchParams.get('sort');
    let sort_scope=$page.url.searchParams.get('scope');
    let sort_reverse=$page.url.searchParams.get('reverse') == "true" ? true : false;
    let selected_label=$page.url.searchParams.get('label');
    let selected_label_scope=$page.url.searchParams.get('label_scope');
    if (sort_criteria === null) {
        if (selected_category == '') {
            sort_criteria = 'Newly added';
        } else {
            sort_criteria = 'Category score';
        }
    } else {
        sort_criteria = decodeURIComponent(sort_criteria); 
    }
    if (sort_scope === null) {
        sort_scope = 'series';
    }
    if (selected_label === null) {
        selected_label = 'None';
    } else {
        selected_label = decodeURIComponent(selected_label); 
    }
    if (selected_label_scope === null) {
        selected_label_scope = 'series';
    }

    $: url_param = "ls=" + ls + "&sort=" + encodeURIComponent(sort_criteria) +  "&scope=" + sort_scope +"&reverse=" + (sort_reverse ? "true" : "false") + "&label=" + encodeURIComponent(selected_label); // + "&filters=" + encodeURIComponent(JSON.stringify(filters));

    $: addLabeling(title_metadata, sort_criteria, selected_label, selected_label_scope)

    if(ls==="en" || ls==="jp")
    {
        numoe=24;
        pagenew=pagen;
        
    }
    else
    {
        ls="all"
    }
    

    $: pages_num=Math.ceil(filtered_title_count/numoe)
    let page_idx_array=[];
    $: {
        page_idx_array=[];
        for(let i=1;i<=pages_num;i++)
        {
            page_idx_array.push(i)
        }
    }

    let page_idx=1;
    
$: {
    if(pagen>=1&&pagen<=pages_num)
    {
        page_idx=parseInt(pagen);
    }
}

$: prev_page_idx=page_idx-1;
$: next_page_idx=page_idx+1;


    const pagchang=(pi)=>{
        pi=pi+1;
        let tempp = Math.ceil(pi/numoe);
        if(tempp===page_idx)
        {
            return true;
        }
        else
        {
            return false;
        }
    }
    const sortCriteriaChanged = (e) => {
        sort_criteria = e.detail['criteria'];
        sort_scope = e.detail['scope']
		$page.url.searchParams.set('sort',encodeURIComponent(sort_criteria));
		$page.url.searchParams.set('scope',sort_scope);
		$page.url.searchParams.set('page',1);
        pagen = 1;
        goto(`?${$page.url.searchParams.toString()}`);
        fetchMetadataForTitles()
    };

    const LabelChanged = (e) => {
        selected_label = e.detail['label'];
        selected_label_scope = e.detail['scope']
		$page.url.searchParams.set('label',encodeURIComponent(selected_label));
		$page.url.searchParams.set('label_scope',selected_label_scope);
        goto(`?${$page.url.searchParams.toString()}`);
        title_metadata = title_metadata // force update
    };

    const sortReverseChanged = (e) => {
        sort_reverse = e.detail;
		$page.url.searchParams.set('reverse',sort_reverse);
        goto(`?${$page.url.searchParams.toString()}`);
        fetchMetadataForTitles()
    };

    const FiltersUpdated = (e) => {
        user_filter_list = e.detail; // force update
        localStorage.setItem("user_filter_list", JSON.stringify(user_filter_list));
        fetchMetadataForTitles()
    };

    </script>
    <div class="selgrid">
        <div class="lssel">
            <a href="{url1}?page={pagenew}&ls=en" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">ENG TL</a>
            <a href="{url1}?page={pagenew}&ls=jp" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">JP RAW</a>
            <a href="{url1}?page=1&ls=all" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">ALL</a>
        </div>
        <div class="sortsel">
            <AddMangaFilter manga_titles={title_metadata} filter_options={available_filters} 
                filter_list={user_filter_list} on:onFiltersUpdated={FiltersUpdated}
            />
        </div>
        <div class="sortsel">
            <MangaSortDashboard {sort_criteria} {sort_scope} {sort_reverse} 
                {sort_options} 
                on:SortCriteriaChanged={sortCriteriaChanged}
                on:SortReverseChanged={sortReverseChanged}
            />
        </div>
        <div class="sortsel">
            <MangaLabelDashboard {selected_label} {selected_label_scope}
                label_options={sort_options}
                on:LabelChanged={LabelChanged}
            />
        </div>
    </div>
    <div>
        <MangaFilterDashboard filter_list={user_filter_list} filtered_num={filtered_title_count} total_num={title_count}
            on:onFiltersUpdated={FiltersUpdated}
        />
    </div>
<div id="cardholderid" class="cardholder">
    {#each title_metadata as manga,pi }
    {#if page_idx }
    <MangaCard data={manga} subheading={manga.subheading} subheading2={manga.subheading2} ls={ls} cdncdn={cdncdn1}/>
    {/if}        
    {/each}
    {#if pages_num>1}
    <div id="pagesnum">
        {#if (page_idx!=1)}
        <a href="{url1}?page=1&{url_param}" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">First</a>&nbsp
        {/if} 
        {#if (prev_page_idx>0)}
        <a href="{url1}?page={prev_page_idx}&{url_param}" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">-</a>&nbsp   
        {/if}  
        {#each page_idx_array as page_selector_idx }
            {#if Math.ceil(page_selector_idx/5)==(Math.ceil(page_idx/5))}
            <a href="{url1}?page={page_selector_idx}&{url_param}" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">{page_selector_idx}</a>&nbsp
            {/if}
        {/each}
        {#if (next_page_idx<=pages_num)}
        <a href="{url1}?page={next_page_idx}&{url_param}" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">+</a>&nbsp 
        {/if}
        {#if (page_idx!=pages_num)}
        &nbsp<a href="{url1}?page={pages_num}&{url_param}" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">Last</a>&nbsp   
        {/if}
    </div>
    {/if}
    </div>

    <style>
        .cardholder{
            position: absolute;
            left: 5vw;
            right: 5vw;
            display: flex;
            flex-wrap: wrap;

            justify-content: center;
            text-align: center;
            width: 90vw;
        }

        #pagesnum{

            padding-top: 30px;
            padding-bottom:30px;
            width: 100%;
            min-width: 100%;

        }

        #pagesnum>a{
            text-decoration: none;
            color: whitesmoke;
            font-size: 1.2rem;
            margin-right:5px;
            padding: 5px;
            border-radius: 5px;
        }

        #pagesnum>a:hover{
            background-color: rgba(255,255,255,0.4);
        }
        .selgrid {
            display: grid;
            grid-template-columns: 1fr 0.5fr 1fr 1fr;
            grid-gap: 5px;
        }
        .lssel{
            margin-top:25px;
            margin-bottom:15px;
        }
        .lssel>a{
            text-decoration: none;
            color: whitesmoke;
            font-size: 1.1 rem;
            margin-right:5px;
            padding: 10px;
            border-radius: 5px;
            background:#444;
        }
        .lssel>a:hover{
            background-color: rgba(255,255,255,0.4);
        }
        .sortsel{
            margin-top:15px;
            margin-bottom:15px;
        }
    </style>

    