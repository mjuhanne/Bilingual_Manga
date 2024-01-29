<script>
import { onMount } from 'svelte';
import {obj} from '$lib/store.js';
import ToggleSwitch from './ToggleSwitch.svelte';
let all_meta_data;
obj.subscribe(value => { all_meta_data=value;});

export let meta;
export let manga_data;

export let current_set = meta.total_statistics
export let avg_set = all_meta_data[0].average_manga.total_statistics;

let individual_set = false;
let w_per_v_set = false;

const toggleIndividual = () => {
    console.log("toggleIndividual " + individual_set);
    if (individual_set) {
        current_set = meta.individual_statistics
        avg_set = all_meta_data[0].average_manga.individual_statistics;
    } else {
        current_set = meta.total_statistics
        avg_set = all_meta_data[0].average_manga.total_statistics;
    }
    draw_graphs();
}

const toggleWordsPerVolume = () => {
    console.log("toggleWordsPerVolume " + w_per_v_set);
    draw_graphs();
}

Chart.defaults.color = '#fff';

const table_fields = [
    ['JLPT word content (%)','jlpt_word_content_pct'],
    ['Words per page','w_per_p'],
    ['Words per volume','w_per_v'],
    ['Total # of words in series','num_words'],
    ['Non-JLPT words in series','num_non_jlpt_words'],
    ['Non-JLPT words per volume','num_non_jlpt_words_per_v'],
    ['',''],
    ['JLPT kanji content (%)','jlpt_kanji_content_pct'],
    ['Kanjis per page','k_per_p'],
    ['Kanjis per volume','k_per_v'],
    ['Total # of kanjis in series','num_kanjis'],
    ['Non-JLPT kanjis in series','num_non_jlpt_kanjis'],
    ['Non-JLPT kanjis per volume','num_non_jlpt_kanjis_per_v'],
    ['',''],
    ['Kanjis per word (%)','k_per_w_pct'],
    ['Weighted intermediate JLPT word content','weighted_intermediate_jlpt_word_content_pts'],
];

let jlpt_word_data, jlpt_kanji_data;

const set_jlpt_graph_set = () => {

    jlpt_word_data =  {
        labels: ['non-JLPT', 'JLPT1', 'JLPT 2', 'JLPT 3', 'JLPT 4', 'JLPT 5','non-JLPT katakana'],
        datasets: [
            {
            label: 'Current',
            data: w_per_v_set ? current_set.jlpt_word_level_per_v : current_set.jlpt_word_level_pct,
            borderWidth: 1,
            borderColor: '#005500',
            backgroundColor: '#009900',
            },
            {
            label: 'Average',
            data: w_per_v_set ? avg_set.jlpt_word_level_per_v : avg_set.jlpt_word_level_pct,
            borderWidth: 1,
            borderColor: '#707070',
            backgroundColor: '#606060',
            },
        ]
    };

    jlpt_kanji_data =  {
        labels: ['non-JLPT', 'JLPT1', 'JLPT 2', 'JLPT 3', 'JLPT 4', 'JLPT 5'],
        datasets: [
            {
            label: 'Current',
            data: w_per_v_set ? current_set.jlpt_kanji_level_per_v : current_set.jlpt_kanji_level_pct,
            borderWidth: 1,
            borderColor: '#335500',
            backgroundColor: '#009900',
            },
            {
            label: 'Average',
            data: w_per_v_set ? avg_set.jlpt_kanji_level_per_v : avg_set.jlpt_kanji_level_pct,
            borderWidth: 1,
            borderColor: '#707070',
            backgroundColor: '#606060',
            },
        ]
    };
};

let chart_instances = {}

const draw = (canvas, data, title) => {
    const ctx = document.getElementById(canvas);

    if (canvas in chart_instances) {
        console.log("Deleting "+canvas);
        chart_instances[canvas].destroy()
        delete(chart_instances[canvas]);
    }

    let inst = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            aspectRatio: 1, 
            scales: {
            y: {
                beginAtZero: true
            }
            },
            layout: {
                padding: 50
            },
            plugins: {
                title: {
                    display: true,
                    text: title
                }
            }        
        }
    });
    chart_instances[canvas] = inst;
}

const draw_graphs = () => {
    set_jlpt_graph_set();
    let txt = 'JLPT ' + (individual_set?'individual':'total') + ' word distribution ' + 
        (w_per_v_set?'per volume':'(%)')
    draw('JLPT_word_chart', jlpt_word_data,txt);
    txt = 'JLPT ' + (individual_set?'individual':'total') + ' kanji distribution ' + 
        (w_per_v_set?'per volume':'(%)')
    draw('JLPT_kanji_chart', jlpt_kanji_data,txt);
}

onMount(async () => {
    draw_graphs();
});


const colorizeDifference = (a,b) => {
    let d = 100*(a-b)/b;
    d = Math.round(d * 10) / 10;
    if (d < -10) {
        return "<td bgcolor='#700'>" + d + "</td>";
    } 
    if (d > 10) {
        return "<td bgcolor='#070'>" + d + "</td>";
    } 
    return '<td>' + d + '</td>';
};

</script>

<div class="container">
    <div class="subcontainer">
        <div>
            <ToggleSwitch onLabel="Individual kanjis/words" offLabel="All kanjis/words" bind:switchPosition={individual_set} on:switchChanged={toggleIndividual}></ToggleSwitch>
        </div>
        <table>
            <tr>
                <th></th>
                <th>Current</th>
                <th>Average</th>
                <th>Diff (%)</th>
            </tr>
            {#each table_fields as field}
            {#if field[0] != ''}
            <tr>
                <th>{field[0]}</th>
                <td>{current_set[field[1]]}</td>
                <td>{avg_set[field[1]]}</td>
                {@html colorizeDifference(current_set[field[1]], avg_set[field[1]])}
            </tr>
            {:else}
                <tr style="height: 15px;"/>
            {/if}
            {/each}
        </table>
    </div>

    <div class="subcontainer">
        <div>
            <ToggleSwitch onLabel="Quantity per volume" offLabel="Percentage" bind:switchPosition={w_per_v_set} on:switchChanged={toggleWordsPerVolume}></ToggleSwitch>
        </div>
        <div>
            <canvas id="JLPT_word_chart"></canvas>
        </div>
        <div>
            <canvas id="JLPT_kanji_chart"></canvas>
        </div>
    </div>
</div>


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

canvas{
    width:550px !important;
    height:550px !important;
}

.container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 10px;
}

.subcontainer {
    margin: 20px;
}
</style>