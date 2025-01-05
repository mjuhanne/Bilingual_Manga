<script>
import { onMount } from 'svelte';
import {obj} from '$lib/store.js';
//import { deserialize } from '$app/forms';
import MangaSortDashboard from '$lib/MangaSortDashboard.svelte';
import { suggested_preread_sort_options, sortManga } from '$lib/MangaSorter.js';
import { EVENT_TYPE } from "$lib/UserDataTools.js";

let sort_criteria='Relative CI improvement' //'Newly added';
let sort_reverse=false;

$: custom_analysis_available = 'words' in meta.series.total_statistics;


let message = ''

let source_selection = 'next_unread_volume'
let source_filter = 'book'
let target_selection = 'next_unread_volume'

let sort_scope = 'series';
$: if (target_selection == 'next_unread_volume') {sort_scope='volume'} else {sort_scope='series'}

let eventSource;

onMount( () => {
        eventSource = new EventSource('/user_data');
        eventSource.onmessage = (event) => {
            const parsedData = JSON.parse(event.data);
            let event_type = parsedData.event_type;
            if (event_type== EVENT_TYPE.ANALYSIS_ERROR) {
                message = `Error while analyzing: ${parsedData.msg}`
                //alert(`Error: ${parsedData.msg}`)
            } else if (event_type == EVENT_TYPE.CONNECTED) {
            } else if (event_type == EVENT_TYPE.UPDATED_SUGGESTED_PREREAD) {
                fetchData();
            } else {
                message = `${parsedData.msg}`
            }
        };
        eventSource.onerror = (event) => {
            console.log("error: " + JSON.stringify(event));
        };
        return () => {
            if (eventSource.readyState === 1) {
                eventSource.close();
            }
        };
    });


export let meta;
export let manga_data;

let suggested_preread = [];

$: sorted_suggested_preread = sortManga(suggested_preread, sort_criteria, sort_scope, sort_reverse, "None",undefined);

async function fetchData() {
    const response = await fetch( "/user_data", {
            headers: {"Content-Type" : "application/json" },
            method: 'POST',
            body: JSON.stringify({'func': 'get_suggested_preread', 'title_id':meta.enid,'target_selection':target_selection,'source_selection':source_selection,'source_filter':source_filter}),
        });

    const result = JSON.parse(await response.text());

    if (result.success == false) {
        message = result.error_message;
    } else {
        if (result.suggested_preread.length > 0) {
            suggested_preread = result.suggested_preread;
        } else {
            message = 'Not yet calculated'
            suggested_preread = [];
        }
    }
    console.log(result.suggested_preread.length)
}


$: if (custom_analysis_available) fetchData();

const sortCriteriaChanged = (e) => {
    sort_criteria = e.detail['criteria'];
    sort_scope = e.detail['scope']
    console.log("sortcriteria " + sort_criteria)
};
const sortReverseChanged = (e) => {
    sort_reverse = e.detail;
};

async function refreshCalculation() {
    const response = await fetch( "/user_data", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: JSON.stringify({
            'func': 'calculate_suggested_preread',
            'title_id':meta.enid,
            'target_selection':target_selection,
            'source_selection':source_selection,
            'source_filter':source_filter
       }),
    });
    message = "Starting to calculate.."
}

const table_fields = [
    ['Comprehensible input %','/comprehensible_input_pct'],
    ['Known words %','total_statistics.words.pct_known_pre_known'],
    ['Unknown unique words','unique_statistics.words.num_unknown_unfamiliar'],
    ['Unknown unique kanjis','unique_statistics.kanjis.num_unknown_unfamiliar'],
];

function get_value(item,value_fields) {
    if (value_fields[0] == '/') {
        return item[value_fields.split('/')[1]]
    }
    let value_path = value_fields.split('.');
    let i = 0;
    let value = undefined;
    let element = item
    while (i < value_path.length && value_path[i] in element) {
        element = element[value_path[i]]
        i += 1
    }
    if (i == value_path.length) {
        value = element;
    }
    return value;
}


</script>

{#if custom_analysis_available}
<div class="header_grid">
    <div>
        <table>
            <tr>
                <th>Your statistics</th>
                <th>Whole series</th>
                {#if meta.series.num_volumes > 1}
                    {#if meta.volume.unread_idx != -1}
                        <th>Next unread volume (#{meta.volume.unread_idx})</th>
                    {:else}
                        <th>(All volumes already read)</th>
                    {/if}
                {/if}
                {#if meta.is_book}
                    {#if meta.chapter.unread_idx != -1}
                        <th>Next unread chapter (#{meta.chapter.unread_idx})</th>
                    {:else}
                        <th>(All chapters already read)</th>
                    {/if}
                {/if}
            </tr>

            {#each table_fields as field}
            <tr>
                <th>{field[0]}</th>
                <td>{get_value(meta.series,field[1])}</td>
                {#if meta.series.num_volumes > 1}
                    {#if meta.volume.unread_idx != -1}
                    <td>{get_value(meta.volume,field[1])}</td>
                    {:else}
                        <td></td>
                    {/if}
                {/if}
                {#if meta.is_book}
                    {#if meta.chapter.unread_idx != -1}
                    <td>{get_value(meta.chapter,field[1])}</td>
                    {:else}
                        <td></td>
                    {/if}
                {/if}
            </tr>
            {/each}
        </table>
    </div>
    <div class="parameters">
        <p>
            Target selection
            <select id='target_selection' bind:value={target_selection} on:change={fetchData}>
                <option value="title">Whole title</option>
                <option value="next_unread_volume">Next unread volume</option>
                <option value="next_unread_chapter">Next unread chapter</option>
            </select>
        </p>
        <p>
            Source selection
            <select id='source_selection' bind:value={source_selection} on:change={fetchData}>
                <option value="title">Whole title</option>
                <option value="next_unread_volume">Next unread volume</option>
            </select>
        </p>
        <p>
            Source filter
            <select id='source_filter' bind:value={source_filter} on:change={fetchData}>
                <option value="all">All sources</option>
                <option value="manga">Only manga</option>
                <option value="book">Only books</option>
            </select>
        </p>
        <p>
            <button class="refreshbutton"  on:click={()=>refreshCalculation()}>
                Recalculate
            </button>
        </p>
        <p>{message}</p>
    </div>
</div>


{#if suggested_preread.length > 0}
<div class="container">
    <div class="subcontainer">
        <MangaSortDashboard {sort_criteria} {sort_scope} {sort_reverse} 
        sort_options={suggested_preread_sort_options} 
        on:SortCriteriaChanged={sortCriteriaChanged}
        on:SortReverseChanged={sortReverseChanged}
        width='420',
    />


        <table>
            <tr>
                <th class="title">Title</th>
                <th>Author</th>
                {#if source_filter == 'book'}
                    <th>Pages</th>
                {:else}
                    <th>Volumes</th>
                {/if}
                <th>Rating</th>
                {#if source_selection == 'next_unread_volume'}
                    <th>Next vol</th>
                    <th>CI % next vol</th>
                {:else}
                    <th class="title">CI %</th>
                {/if}
                <th>Known words %</th>
                <th>Common weak words</th>
                <th>Common weak words / vol</th>
                <th>CI % improvement</th>
                <th>Known words % improvement</th>
                <th>Relative CI improvement</th>
                <th>Relative w % improvement</th>
            </tr>

            {#key sorted_suggested_preread}
            {#each sorted_suggested_preread as title_data}
            <tr>
                {#if title_data.entit != "Placeholder"}
                <td><a href="/manga/{title_data.enid}?lang=jp" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">{title_data.entit}</a></td>
                {:else}
                <td><a href="/manga/{title_data.enid}?lang=jp" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">{title_data.jptit}</a></td>
                {/if}
                <td>{title_data.Author}</td>
                {#if source_filter == 'book'}
                    <td>{title_data.suggestion.num_analyzed_pages}</td>
                {:else}
                    <td>{title_data.suggestion.num_analyzed_volumes}</td>
                {/if}
                {#if ('mangaupdates_data' in title_data)}
                <td>{title_data.mangaupdates_data.rating}</td>
                {:else}
                <td>N/A</td>
                {/if}
                {#if source_selection == 'next_unread_volume'}
                    <td>{title_data.suggestion.volume}</td>
                {/if}
                <td>{title_data.suggestion.comprehensible_input_pct}</td>
                <td>{title_data.suggestion.pct_known_pre_known_word}</td>
                <td>{title_data.suggestion.num_common_unique_weak_words}</td>
                <td>{title_data.suggestion.num_common_unique_weak_words_per_vol}</td>
                <td>{title_data.suggestion.improvement_ci_pct}</td>
                <td>{title_data.suggestion.improvement_pct}</td>
                <td>{title_data.suggestion.relative_ci_improvement}</td>
                <td>{title_data.suggestion.relative_improvement}</td>
            </tr>
            {/each}
            {/key}
        </table>
    </div>
</div>
{/if}

{:else}
<div><h4>Custom language analysis has not yet been done. Please see the Language settings screen.</h4></div>
{/if}

<style>

.parameters {
    padding: 20px;
    text-align: left;
}

table {
    padding: 20px;
}
td, th {
    text-align: left;
    font-size: 15px;
    padding: 5px;
    outline: 1px solid #30305b;
}
th {
    font-size: 17px;
}

th.title {
    min-width: 150px;
}

.header_grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 10px;
}

.container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 10px;
}

.subcontainer {
    margin: 20px;
}

a {
  text-decoration: none;
  color: #b2b2ff;
}

a:hover {
  text-decoration: underline;
}
</style>