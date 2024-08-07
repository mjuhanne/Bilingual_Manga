<script>
import { createEventDispatcher } from 'svelte';
import { STAGE, learning_stage_colors, source_to_name, 
    word_classes, timestamp2date 
} from '$lib/LearningData.js'
import LearningStageButtons from '$lib/LearningStageButtons.svelte'
import PriorityWordScopeSelectionDialog from '$lib/PriorityWordScopeSelectionDialog.svelte';
import { deserialize } from '$app/forms';
import WordHistoryDialog from './WordHistoryDialog.svelte';
const dispatch = createEventDispatcher();
let dialog; // HTMLDialogElement

export let showModal = false;

let seq_list = [];
let ready_seq_list = [];
let detected_senses_by_seq = {};
let selected_seq = -1;
let showWordHistoryDialog = false;
let showPriorityWordSelectionDialog = false;

export let word_id_index_list;
export let word_id_list;
export let word_history = [];
export let word_learning_stages;

let first_meaning = '';
let learning_stage_by_seq = {};
let word_by_seq = {};
$: word_info_by_seq = [];

let wide_dialog = true;

let selected_word_history = []
let selected_word_id = ''
let selected_word_id_index = 0
let selected_index = -1
$: {
    if (selected_seq != -1) {
        selected_word_id = selected_seq + ':' + word_by_seq[selected_seq];
        selected_word_id_index = word_id_list.indexOf(selected_word_id);
        console.log("Selected",word_id_list[selected_word_id_index],"widx",selected_word_id_index)
    }
}

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
            // Keep only the first seq entry occurrence (to avoid confusion when
            // multiple hiragana readings are detected (e.g. そうね / そうねえ))
            if (!(seq in learning_stage_by_seq)) {
                learning_stage_by_seq[seq] = word_learning_stages[widx];
                word_by_seq[seq] = word;
            }
            if (selected_seq == -1) {
                selectedWord(seq,0);
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

async function selectedWord(seq,index) {
    selected_seq = seq;
    selected_index = index;
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
    if ('meanings' in word_info_by_seq[selected_seq]) {
        first_meaning=word_info_by_seq[selected_seq]['meanings'][0]
    }
    ready_seq_list = seq_list;
    //console.log(JSON.stringify(result))
};


async function priority_word_button_clicked() {
    if (selected_index > 0) {
        showPriorityWordSelectionDialog = true;
    }
}

async function on_priority_word_scope_selected(e) {
    // Move the index of new seq to the beginning of word id index list
    word_id_index_list.splice(word_id_index_list.indexOf(selected_word_id_index),1)
    word_id_index_list.unshift(selected_word_id_index)
    dispatch('priority_word_updated_manually', { 
        'word_id': selected_word_id,
        'scope' : e.detail['scope']
    });
    word_id_index_list = word_id_index_list; // Force update
}

async function history_button_clicked() {
    selected_word_history = word_history[selected_word_id_index];
    showWordHistoryDialog = true;
}

async function anki_button_clicked() {
    showModal = false;
    dispatch('anki_button_clicked', { 
        'word': word_by_seq[selected_seq],
        'glossary' : word_info_by_seq[selected_seq]['meanings'],
        'readings' : word_info_by_seq[selected_seq]['readings']
    });
}

</script>

<WordHistoryDialog bind:showModal={showWordHistoryDialog} word={word_by_seq[selected_seq]} history={selected_word_history}/>
<PriorityWordScopeSelectionDialog bind:showModal={showPriorityWordSelectionDialog} on:priority_word_scope_selected={on_priority_word_scope_selected}/>

<dialog id="popup-dialog" class="popup-dialog wide-dialog"
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
            </div>
            <div class="details">
                <div class="buttondiv">
                    <button on:click={() => anki_button_clicked()}>Anki card</button>
                    <button on:click={() => history_button_clicked()}>History</button>
                    <button style="grid-column: 1 / span 2" class:disabled_button={selected_index<1} on:click={() => priority_word_button_clicked()}>Manually set correct meaning </button>
                </div>
                <div id="seq_list" class="seq_list">
                {#each ready_seq_list as seq,i}
                    <table class="word_info_table" class:selected_seq={seq == selected_seq} on:click={()=>{selectedWord(seq,i)}}>
                        <tr style="background:{learning_stage_colors[learning_stage_by_seq[seq]]}">
                            <td>{seq}</td><td>PRI_T_C:{word_info_by_seq[seq]['priority_seq_title_count']}</td>
                        </tr>
                        <tr style="background:{learning_stage_colors[learning_stage_by_seq[seq]]}">
                            <td colspan=2>
                                <ol class="element_list">
                                {#each word_info_by_seq[seq]['kanji_elements'] as ke,i}
                                    <li>{ke} ({word_info_by_seq[seq]['k_elem_freq'][i]} {word_info_by_seq[seq]['priority_tags'][ke]})</li>
                                {/each}
                                {#each word_info_by_seq[seq]['readings'] as reading,i}
                                <li>{reading} ({word_info_by_seq[seq]['r_elem_freq'][i]} {word_info_by_seq[seq]['priority_tags'][reading]})</li>
                                {/each}
                                </ol>
                            </td>
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
    </div>
</dialog>

<style>
    .word {
        color: white;
        font-size: 0.9rem;
        padding-bottom: 3px;
    }
    .word_class {
        color: rgb(8, 249, 229);
        font-size: 0.7rem;
        padding-bottom: 3px;
    }
    .first_meaning {
        color: #bbb;
        font-size: 0.6rem;
        padding-bottom: 3px;
    }
    .word_info_table {
        width: 100%;
        padding: 3px;
    }

    .buttondiv {
        margin: 0px;
        padding: 0px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-gap: 0px;
        
    }
    .disabled_button {
        background-color: #bbb;
    }
    .disabled_button:hover {
        background-color: #bbb;
    }

    button {
        background-color: #55f;
        color: #fff;
        font-size: 0.6rem;
        border-radius: 2px;
        border:0;
        margin: 1px;
    }
    button:hover {
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
        position:relative;
    }
    .seq_list {
        height: 200px;
        box-sizing: border-box;
        overflow: scroll;
    }

	dialog {
        width: 60px;
		border-radius: 0.5em;
		border: none;
		padding: 3px;
        background: #666;
        margin: 0;
        position: absolute;
	}

    .wide-dialog {
        width: 220px;
    }

    th {
        font-size: 0.6rem;
        color: white;
    }
    td {
        font-size: 0.6rem;
        color: black;
    }
    .meaning_td {
        text-align: left;
        padding-left: 8px;
    }
    .element_list {
        list-style-type:none;
        padding: 1px;
        padding-left: 4px;
        text-align: left;
        margin: 0px;
    }

</style>