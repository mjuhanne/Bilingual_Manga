<script>
import { createEventDispatcher } from 'svelte';
import { STAGE, learning_stage_colors, source_to_name, 
    word_classes, timestamp2date 
} from '$lib/LearningData.js'
import LearningStageButtons from '$lib/LearningStageButtons.svelte'
import { deserialize } from '$app/forms';
const dispatch = createEventDispatcher();
let dialog; // HTMLDialogElement

export let showModal = false;

let seq_list = [];
let ready_seq_list = [];
let detected_senses_by_seq = {};
let selected_seq = -1;
let show_update_priority_word_button = true;

export let word_id_index_list;
export let word_id_list;
export let word_history = [];
export let word_learning_stages;

let first_meaning = '';
let learning_stage_by_seq = {};
let word_by_seq = {};
$: word_info_by_seq = [];

let wide_dialog = false;

$: {
    if (dialog && showModal) {
        detected_senses_by_seq = {}
        learning_stage_by_seq = {}
        word_by_seq = {}
        seq_list = [];
        for (let widx of word_id_index_list) {
            let word_id = word_id_list[widx];
            let sw = word_id.split(':')
            let seq_sense = sw[0];
            let word = sw[1];
            seq_sense = seq_sense.split('/');
            let seq = seq_sense[0];
            if (seq_list.indexOf(seq) == -1) {
                seq_list.push(seq);
                detected_senses_by_seq[seq] = [];
            }
            if (seq_sense.length>1) {
                let sense = seq_sense[1];
                detected_senses_by_seq[seq].push(sense);
            } else {
                detected_senses_by_seq[seq].push(-1); // all senses were detected
            }
            if (selected_seq == -1) {
                selected_seq = seq;
            }
            // Keep only the first seq entry occurrence (to avoid confusion when
            // multiple hiragana readings are detected (e.g. そうね / そうねえ))
            if (!(seq in learning_stage_by_seq)) {
                learning_stage_by_seq[seq] = word_learning_stages[widx];
                word_by_seq[seq] = word;
            }
        }
        fetchWordInfo(seq_list);
        if (word_id_index_list.length>1) {
            wide_dialog = true;
        }
        dialog.showModal();
    }
};
$: if (dialog && !showModal) { selected_seq = -1; dialog.close(); }

const learningStageChanged = (e) => {
    let new_learning_stage = e.detail;
    let old_learning_stage = learning_stage_by_seq[selected_seq];
    if (new_learning_stage != old_learning_stage) {
        learning_stage_by_seq[selected_seq] = new_learning_stage;
        showModal = false;
        dispatch('learning_stage_changed', { 
            'word_id': selected_seq + ':' + word_by_seq[selected_seq],
            'stage':new_learning_stage,
        });
    }
}

function selectedWord(seq) {
    selected_seq = seq;
}

async function fetchWordInfo(seq_list) {
    let body = JSON.stringify({
        'func' : 'get_word_info', 
        'seq_list' : seq_list,
    });
    const response = await fetch( "/jmdict", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });
    const result = deserialize(await response.text());
    word_info_by_seq = result.word_info;
    first_meaning=word_info_by_seq[selected_seq]['meanings'][0]
    ready_seq_list = seq_list;
    //console.log(JSON.stringify(result))
};

async function set_priority_word_manually() {
    let wid = selected_seq + ':' + word_by_seq[selected_seq];
    let widx = word_id_list.indexOf(wid);
    // Move the index of new seq to the beginning of word id index list
    word_id_index_list.splice(word_id_index_list.indexOf(widx),1)
    word_id_index_list.unshift(widx)
    dispatch('priority_word_updated_manually', { 
        'word_id': wid,
    });
    word_id_index_list = word_id_index_list; // Force update
}

</script>

<dialog id="popup-dialog" class="popup-dialog" class:wide-dialog={wide_dialog}
	bind:this={dialog}
	on:close={() => {showModal = false; wide_dialog = false;}}
	on:click|self={() => dialog.close()}
>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div on:click|stopPropagation>
		<div class="word" on:click={()=>{wide_dialog=true}}>{word_by_seq[selected_seq]}</div>
        <div class="first_meaning">{first_meaning}</div>
        <div class="enclosure">
            <div>
            <LearningStageButtons bind:selected_stage={learning_stage_by_seq[selected_seq]} on:clicked={learningStageChanged}/>
            {#if show_update_priority_word_button}
            <button class="update_priority_word_button" on:click={() => set_priority_word_manually()}>Manually set correct meaning </button>
            {/if}
            </div>
            <div class="details">
                    {#each ready_seq_list as seq}
                    <table class="word_info_table" class:selected_seq={seq == selected_seq} on:click={()=>{selectedWord(seq)}}>
                        {#if word_info_by_seq[seq]['kanji_elements'].length>0}
                        <tr style="background:{learning_stage_colors[learning_stage_by_seq[seq]]}">
                            <td colspan=2>{word_info_by_seq[seq]['kanji_elements']}</td>
                        </tr>
                        {/if}
                        <tr style="background:{learning_stage_colors[learning_stage_by_seq[seq]]}">
                            <td>{word_info_by_seq[seq]['readings']}</td><td>{seq}</td>
                        </tr>
                        <tr style="background:{learning_stage_colors[learning_stage_by_seq[seq]]}">
                            <td>PRI #{word_info_by_seq[seq]['priority_seq_order']}:{word_info_by_seq[seq]['priority_seq_count']}</td>
                            <td>ALL #{word_info_by_seq[seq]['seq_order']}:{word_info_by_seq[seq]['seq_count']}</td>
                        </tr>
                        {#if word_info_by_seq[seq]['priority_tags'].length>0}
                            <tr style="background:{learning_stage_colors[learning_stage_by_seq[seq]]}">
                                <td colspan=2>{word_info_by_seq[seq]['priority_tags'][0]}</td>
                            </tr>
                        {/if}
                        <!--
                        {#if (word_info_by_seq[seq]['kanji_element_only_priority_tags'][0].length>0) || (word_info_by_seq[seq]['reading_only_priority_tags'][0].length>0)}
                            <tr style="background:{learning_stage_colors[learning_stage_by_seq[seq]]}">
                                <td>{word_info_by_seq[seq]['kanji_element_only_priority_tags']}</td>
                                <td>{word_info_by_seq[seq]['reading_only_priority_tags']}</td>
                            </tr>
                        {/if}
                        -->
                        {#each word_info_by_seq[seq]['meanings'] as sense_meanings,i}
                        <tr style="background:{learning_stage_colors[learning_stage_by_seq[seq]]}">
                            <td class="meaning_td" colspan=2>{i+1}. 
                                {#each sense_meanings as meaning}
                                {meaning}<br>
                                {/each}
                            </td>
                        </tr>
                        {/each}
                        <tr style="height:3px"></tr>
                    </table>
                {/each}
            </div>
        </div>
    </div>
</dialog>

<style>
    .word {
        color: white;
        font-size: 0.8rem;
        padding-bottom: 3px;
    }
    .word_class {
        color: rgb(8, 249, 229);
        font-size: 0.6rem;
        padding-bottom: 3px;
    }
    .first_meaning {
        color: #bbb;
        font-size: 0.5rem;
        padding-bottom: 3px;
    }
    .word_info_table {
        width: 100%;
        padding: 3px;
    }
    .update_priority_word_button {
        background-color: #55f;
        color: #fff;
        font-size: 0.4rem;
        padding-bottom: 3px;
        border-radius: 5px;
        border:0;
    }
    .update_priority_word_button:hover {
        background-color: #77f;
    }

    .selected_seq {
        background-color: #999;
        border-radius: 5px;
        border-color: #fff;
    }

    .enclosure {
        color: #eee;
        display: grid;
        grid-template-columns: 2fr 4fr;
        grid-gap: 0px;
    }

    .details {
        margin-left: 4px;
        background-color: #555;
        border-radius: 3px;
    }

	dialog {
        width: 60px;
		border-radius: 0.5em;
		border: none;
		padding: 3px;
        background: #666;
        margin: 0;
	}

    .wide-dialog {
        width: 200px;
    }

    th {
        font-size: 0.5rem;
        color: white;
    }
    td {
        font-size: 0.5rem;
        color: black;
    }
    .meaning_td {
        text-align: left;
        padding-left: 8px;
    }

</style>