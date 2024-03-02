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

export let word;
export let word_sense_list;
export let word_class;
export let history = [];
export let learning_stage;

let first_meaning = '';
$: meanings = [];
$: if (meanings.length>0) {first_meaning=meanings[0][0]}

let show_history = false;
let processed_history;

const MAXIMUM_HISTORY_EVENTS = 5

// Reverse the history timeline (newest events first)
$: {
    processed_history = [];
    let c = 0;
    let i = history.length - 1
    let last_stage = STAGE.UNKNOWN;
    let last_source = '';
    while ((c < MAXIMUM_HISTORY_EVENTS) && (i>=0)) {
        let h = history[i];
        if ((h.s != last_stage) || (h.m.src != last_source)) { // only show changes
            let comment = '';
            if ('comment' in h.m) {
                comment = h.m.comment;
            }
            processed_history.push(
                {
                    'stage' : h.s,
                    'date' : timestamp2date(h.t*1000),
                    'source' : source_to_name[h.m.src],
                    'comment' : comment,
                }
            )
            c += 1;
            last_stage = h.s;
            last_source = h.m.source;
        }
        i -= 1;
    }
}

$: {
    if (dialog && showModal) {
        fetchMeanings(word_sense_list);
        dialog.showModal();
    }
};
$: if (dialog && !showModal) dialog.close()

const learningStageChanged = (e) => {
    let new_learning_stage = e.detail;
    if (new_learning_stage != learning_stage) {
        learning_stage = new_learning_stage;
        showModal = false;
        dispatch('learning_stage_changed', { 
            'word':word, 
            'stage':new_learning_stage,
        });
    }
}

async function fetchMeanings(sense_list) {
    let body = JSON.stringify({
        'func' : 'get_meanings', 
        'seq_sense_list' : sense_list,
    });
    const response = await fetch( "/jmdict", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });
    const result = deserialize(await response.text());
    meanings = result.meanings;
    console.log(JSON.stringify(result))
};

fetchMeanings(['1052530','1160870']);
</script>

<dialog id="popup-dialog" class="popup-dialog" class:wide-dialog={show_history}
	bind:this={dialog}
	on:close={() => {showModal = false; show_history = false;}}
	on:click|self={() => dialog.close()}
>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div on:click|stopPropagation>
		<div class="word" on:click={()=>{show_history=true}}>{word}</div>
        <div class="first_meaning">{first_meaning}</div>
        <div class="enclosure">
            <div>
            <LearningStageButtons bind:selected_stage={learning_stage} on:clicked={learningStageChanged}/>
            </div>
            <div class="history">
                <div class="word_class" on:click={()=>{show_history=true}}>{word_classes[word_class]}</div>
                <table class="history_table">
                    <tr>
                        <th>Date</th>
                        <th>Source</th>
                    </tr>
                    {#each processed_history as h}
                    <tr style="background:{learning_stage_colors[h.stage]}">
                        <td>{h.date}</td>
                        <td>{h.source}</td>
                    </tr>
                    <tr style="background:{learning_stage_colors[h.stage]}">
                        <td colspan=2>{h.comment}</td>
                    </tr>
                    <tr style="height:3px"></tr>
                    {/each}
                </table>
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
    .history_table {
        width: 100%;
    }

    .enclosure {
        color: #eee;
        display: grid;
        grid-template-columns: 2fr 6fr;
        grid-gap: 0px;
    }

    .history {
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
    /*
	dialog::backdrop {
		background: rgba(0, 0, 0, 0.2);
	}
	dialog > div {
		padding: 0.1em;
	}
	dialog[open] {
		animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}
	@keyframes zoom {
		from {
			transform: scale(0.95);
		}
		to {
			transform: scale(1);
		}
	}
	dialog[open]::backdrop {
		animation: fade 0.2s ease-out;
	}
	@keyframes fade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
    */
</style>