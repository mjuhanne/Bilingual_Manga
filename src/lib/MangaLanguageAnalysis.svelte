<script>
import { onMount } from 'svelte';
import {obj} from '$lib/store.js';
import ToggleSwitch from './ToggleSwitch.svelte';
import UpdateAnalysisButton from './UpdateAnalysisButton.svelte';
let all_meta_data;
obj.subscribe(value => { all_meta_data=value;});

export let meta;
export let current_set = 'total_statistics'
let avg_set;
let avg_ci_sentence_count;
$: {
    let avg_title = (meta.is_book ? all_meta_data[0].average_book : all_meta_data[0].average_manga);
    avg_set = avg_title.total_statistics;
    avg_ci_sentence_count = avg_title.series.avg_ci_sentence_count
}

let unique_items_set = false;
let w_per_v_set = false;
$: custom_analysis_available = 'analysis' in meta;

const toggleUnique = () => {
    console.log("toggleUnique " + unique_items_set);
    if (unique_items_set) {
        current_set = 'unique_statistics'
        avg_set = (meta.is_book ? all_meta_data[0].average_book.unique_statistics : all_meta_data[0].average_manga.unique_statistics);
    } else {
        current_set = 'total_statistics'
        avg_set = (meta.is_book ? all_meta_data[0].average_book.total_statistics : all_meta_data[0].average_manga.total_statistics);
    }
    draw_graphs();
}

const toggleWordsPerVolume = () => {
    console.log("toggleWordsPerVolume " + w_per_v_set);
    draw_graphs();
}

const table_fields = [
    ['JLPT word content (%)','jlpt_word_content_pct'],
    ['Words per sentence','w_per_s'],
    ['Words per page','w_per_p'],
    ['Words per volume','w_per_v'],
    ['Total # of words in series','num_words'],
    ['Non-JLPT words in series','num_non_jlpt_words'],
    ['Non-JLPT words per volume','num_non_jlpt_words_per_v'],
    ['Total # of characters in series','num_characters'],
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

const list_kanji_func = (kanji_list) => {
    if (kanji_list.length>10) {
        return "Many";
    } else {
        return kanji_list.join(' ');
    }
}

const table_fields2 = [
    ['Comprehensible input %','/comprehensible_input_pct',null],
    ['Comprehensible input (ex katakana) %','/comprehensible_input_ex_katakana_pct',null],
    ['CI score','/comprehensible_input_score',null],
    ['Known words %','words.pct_known_pre_known',null],
    ['Unknown/unfamiliar words','words.num_unknown_unfamiliar',null],
    ['Unknown/unfamiliar words needed for 90% CI','/showstopper_word_count_for_ci90',null],
    ['Unknown/unfamiliar kanjis','kanjis.num_unknown_unfamiliar',null],
    ['Num unknown/unfamiliar JLPT kanjis','kanjis.jlpt_unknown_num',null],
    ['Unknown/unfamiliar JLPT kanjis','',(dataset) => {return list_kanji_func(dataset.unique_statistics.kanjis.jlpt_unknown_list)}],
    ['Num unknown/unfamiliar non-JLPT kanjis','kanjis.non_jlpt_unknown_num',null],
    ['Unknown/unfamiliar non-JLPT kanjis','',(dataset) => {return list_kanji_func(dataset.unique_statistics.kanjis.non_jlpt_unknown_list)}],
];

let jlpt_word_data, jlpt_kanji_data;

let ci_data =  {
        labels: ['All known', '<5K', '<10K', '<20K', '<50K', 'Katakana','Low Freq','>=2 unknown'],
        datasets: [
            {
            label: 'This title (all volumes)',
            data: meta.analysis.series.comprehensible_input_sentence_grading,
            borderWidth: 1,
            borderColor: '#555555',
            backgroundColor: '#eeeeee',
            },
            {
            label: 'This title (next volume)',
            data: meta.analysis.next_unread_volume.comprehensible_input_sentence_grading,
            borderWidth: 1,
            borderColor: '#005500',
            backgroundColor: '#009900',
            },
            {
            label: 'Average manga',
            data: all_meta_data[0].average_manga.series.avg_ci_sentence_count,
            borderWidth: 1,
            borderColor: '#707070',
            backgroundColor: '#606060',
            }
        ]
    };


const set_jlpt_graph_set = () => {

    jlpt_word_data =  {
        labels: ['non-JLPT', 'JLPT1', 'JLPT 2', 'JLPT 3', 'JLPT 4', 'JLPT 5','non-JLPT katakana'],
        datasets: [
            {
            label: 'This manga',
            data: w_per_v_set ? meta.lang_summary[current_set].jlpt_word_level_per_v : meta.lang_summary[current_set].jlpt_word_level_pct,
            borderWidth: 1,
            borderColor: '#555555',
            backgroundColor: '#eeeeee',
            },
            {
            label: 'This manga (known / pre-known)',
            data: w_per_v_set ? meta.analysis.series[current_set].words.jlpt_level_per_v : meta.analysis.series[current_set].words.jlpt_level_pct,
            borderWidth: 1,
            borderColor: '#005500',
            backgroundColor: '#009900',
            },
            {
            label: 'Average manga',
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
            label: 'This manga',
            data: w_per_v_set ? meta.lang_summary[current_set].jlpt_kanji_level_per_v : meta.lang_summary[current_set].jlpt_kanji_level_pct,
            borderWidth: 1,
            borderColor: '#555555',
            backgroundColor: '#eeeeee',
            },
            {
            label: 'This manga (known / pre-known)',
            data: w_per_v_set ? meta.analysis.series[current_set].kanjis.jlpt_level_per_v : meta.analysis.series[current_set].kanjis.jlpt_level_pct,
            borderWidth: 1,
            borderColor: '#005500',
            backgroundColor: '#009900',
            },
            {
            label: 'Average manga',
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

    Chart.defaults.color = '#fff';
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
    draw('CI_chart',ci_data,'Word frequency of the unknown word in sentence');
    set_jlpt_graph_set();
    let txt = 'JLPT ' + (unique_items_set?'unique':'total') + ' word distribution ' + 
        (w_per_v_set?'per volume':'(%)')
    draw('JLPT_word_chart', jlpt_word_data,txt);
    txt = 'JLPT ' + (unique_items_set?'unique':'total') + ' kanji distribution ' + 
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

function get_value(item,value_fields,value_func) {
    if (value_func != null) {
        return value_func(item)
    }
    if (value_fields[0] == '/') {
        return item[value_fields.split('/')[1]]
    }
    let value_path = value_fields.split('.');
    let i = 0;
    let value = undefined;
    let element = item[current_set]
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

<div class="container">
    <div class="subcontainer">
        <div class="left_widget">
            <div><UpdateAnalysisButton meta={meta}/></div>
            <div>
                <ToggleSwitch onLabel="Unique kanjis/words" offLabel="All kanjis/words" bind:switchPosition={unique_items_set} on:switchChanged={toggleUnique}></ToggleSwitch>
            </div>
        </div>
        {#if meta.is_summary_stale}
            <span class="warning">Analysis calculated using old parser version {meta.parser_version}</span>
        {/if}

        {#if custom_analysis_available}
        <table>
            <tr>
                <th>Your statistics</th>
                <th>Whole series</th>
                {#if meta.lang_summary.num_volumes > 1}
                    {#if meta.analysis.next_unread_volume.unread_idx != -1}
                        <th>Next unread volume (#{meta.analysis.next_unread_volume.unread_idx})</th>
                    {:else}
                        <th>(All volumes already read)</th>
                    {/if}
                {/if}
                {#if meta.is_book}
                    {#if meta.analysis.next_unread_chapter.unread_idx != -1}
                        <th>Next unread chapter (#{meta.analysis.next_unread_chapter.unread_idx})</th>
                    {:else}
                        <th>(All chapters already read)</th>
                    {/if}
                {/if}
            </tr>

            {#key current_set}
                {#each table_fields2 as field}
                {#if field[0] != ''}
                <tr>
                    <th>{field[0]}</th>
                    <td>{get_value(meta.analysis.series,field[1],field[2])}</td>
                    {#if meta.lang_summary.num_volumes > 1}
                        {#if meta.analysis.next_unread_volume.unread_idx != -1}
                        <td>{get_value(meta.analysis.next_unread_volume,field[1],field[2])}</td>
                        {:else}
                            <td></td>
                        {/if}
                    {/if}
                    {#if meta.is_book}
                        {#if meta.analysis.next_unread_chapter.unread_idx != -1}
                        <td>{get_value(meta.analysis.next_unread_chapter,field[1],field[2])}</td>
                        {:else}
                            <td></td>
                        {/if}
                    {/if}
                </tr>
                {:else}
                    <tr style="height: 15px;"/>
                {/if}
                {/each}
            {/key}
        </table>
        {/if}
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
                <td>{meta.lang_summary[current_set][field[1]]}</td>
                <td>{avg_set[field[1]]}</td>
                {@html colorizeDifference(meta.lang_summary[current_set][field[1]], avg_set[field[1]])}
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
            <canvas id="CI_chart"></canvas>
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

.left_widget {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 10px;
}

.warning {
    color: red;
}
</style>