<script>
import { onMount } from 'svelte';
import {obj} from '$lib/store.js';
//import { deserialize } from '$app/forms';
import MangaSortDashboard from '$lib/MangaSortDashboard.svelte';
import { suggested_preread_sort_options, sortManga } from '$lib/MangaSorter.js';
import { EVENT_TYPE } from "$lib/UserDataTools.js";

let all_meta_data;
obj.subscribe(value => { all_meta_data=value[0].manga_titles;});

let sort_criteria='Relative CI improvement' //'Newly added';
let sort_reverse=false;

$: custom_analysis_available = 'pct_known_words' in meta.total_statistics;

let message = ''

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
                fetchData(all_meta_data);
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

$: sorted_suggested_preread = sortManga(suggested_preread, sort_criteria, sort_reverse, "None");

let fetched = false;
async function fetchData(meta_data) {
    const response = await fetch( "/user_data", {
            headers: {"Content-Type" : "application/json" },
            method: 'POST',
            body: JSON.stringify({'func': 'get_suggested_preread', 'manga_id':meta.enid}),
        });

    const data = JSON.parse(await response.text());

    if (data.success == false) {
        message = data.error_message;
    } else {
        for (let manga of meta_data) {
            if (manga.enid in data.suggested_preread) {
                let preread = data.suggested_preread[manga.enid];
                manga.ncuuw = preread['num_common_unique_weak_words'];
                manga.ncuuw_per_vol = preread['num_common_unique_weak_words_per_vol'];
                manga.improvement_ci_pct = preread['improvement_ci_pct'];
                manga.improvement_pct = preread['improvement_pct'];
                manga.relative_improvement = preread['relative_improvement'];
                manga.relative_ci_improvement = preread['relative_ci_improvement'];

                suggested_preread.push(manga);
            }
        }
        suggested_preread=suggested_preread;
        fetched = true;
    }
}


$: if (custom_analysis_available) fetchData(all_meta_data);

const sortCriteriaChanged = (e) => {
    sort_criteria = e.detail;
    console.log("sortcriteria " + sort_criteria)
};
const sortReverseChanged = (e) => {
    sort_reverse = e.detail;
};

</script>

{#if custom_analysis_available}
<table>
    <tr>
        <th>Your statistics</th>
        <th>Whole series</th>
        <th>Next unread volume(chapter)</th>
    </tr>
    <tr>
        <th>Comprehensible input %</th>
        <td>{meta.comprehensible_input_pct}</td>
        <td>{meta.comprehensible_input_pct_next_ch}</td>
    </tr>
    <tr>
        <th>Known words %</th>
        <td>{meta.total_statistics.pct_known_words}</td>
        <td>{meta.total_statistics.pct_known_words_next_ch}</td>
    </tr>
    <tr>
        <th>Unknown unique words</th>
        <td>{meta.unique_statistics.num_unknown_words}</td>
        <td>{meta.unique_statistics.num_unknown_words_next_ch}</td>
    </tr>
    <tr>
        <th>Unknown unique kanjis</th>
        <td>{meta.unique_statistics.num_unknown_kanjis}</td>
        <td>{meta.unique_statistics.num_unknown_kanjis_next_ch}</td>
    </tr>
</table>

{#if !fetched}
<div>{message}</div>
{:else}
<div class="container">
    <div class="subcontainer">
        <MangaSortDashboard {sort_criteria} {sort_reverse} 
        sort_criteria_list={Object.keys(suggested_preread_sort_options)} 
        on:SortCriteriaChanged={sortCriteriaChanged}
        on:SortReverseChanged={sortReverseChanged}
        width='420',
    />


        <table>
            <tr>
                <th>Manga</th>
                <th>Volumes</th>
                <th>Rating</th>
                <th>Comprehensible input %</th>
                <th>Comprehensible input % next ch</th>
                <th>Known words %</th>
                <th>Common weak words</th>
                <th>Common weak words / vol</th>
                <th>Comprehension % improvement</th>
                <th>Known words % improvement</th>
                <th>Relative improvement</th>
                <th>Relative CI improvement</th>
            </tr>

            {#key sorted_suggested_preread}
            {#each sorted_suggested_preread as manga}
            <tr>
                <td><a href="/manga/{manga.enid}?lang=en" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">{manga.title}</a></td>
                <td>{manga.num_volumes}</td>
                <td>{manga.mangaupdates_data.rating}</td>
                <td>{manga.comprehensible_input_pct}</td>
                <td>{manga.comprehensible_input_pct_next_ch}</td>                
                <td>{manga.total_statistics.pct_known_words}</td>
                <td>{manga.ncuuw}</td>
                <td>{manga.ncuuw_per_vol}</td>
                <td>{manga.improvement_ci_pct}</td>
                <td>{manga.improvement_pct}</td>
                <td>{manga.relative_improvement}</td>
                <td>{manga.relative_ci_improvement}</td>
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