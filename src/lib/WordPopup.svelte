<script>
import { createEventDispatcher } from 'svelte';
import { deserialize } from '$app/forms';
import { STAGE, learning_stage_colors, SOURCE, source_to_name, word_classes } from '$lib/LearningStages.js'
import LearningStageButtons from '$lib/LearningStageButtons.svelte'
const dispatch = createEventDispatcher();
let dialog; // HTMLDialogElement

export let showModal = false;

export let word;
export let word_class;
export let history = [];
//export let manga_id;
export let chapter_id;
export let page;
export let page_ref; // image name (without extension), also reference to entry in OCR file
export let block; // OCR block number in current page
export let learning_stage;

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

$: if (dialog && showModal) dialog.showModal();
$: if (dialog && !showModal) dialog.close()

function timestamp2date(ts) {
    if (ts === undefined) {
        return today_date();
    } else {
        return (new Date(ts)).toISOString().substr(0, 10);
    }
}

async function sendChangedData() {

    let body = JSON.stringify({
        'func' : 'update_manually_set_word_learning_stage', 
        'stage_data' : {
            'word' : word,
            'stage' : learning_stage,
            'metadata' : {
                //'id' : manga_id,
                'cid' : chapter_id,
                'p' : page,
                'b' : block,
                'pr' : page_ref,
            },
        }
    })
    const response = await fetch( "/user_data", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });
    const result = deserialize(await response.text());

    // add to history temporarily like this before it gets updated after next page flip
    let new_entry = {
        's' : learning_stage,
        't' : new Date()/1000,
        'm' : {
            'src' : SOURCE.USER,
            'comment' : 'Current update',
        }
    };
    if (result.replaced_last_entry) {
        history[history.length-1] = new_entry;
    } else {
        history.push(new_entry);
    }
};

const learningStageChanged = (e) => {
    let new_learning_stage = e.detail;
    if (new_learning_stage != learning_stage) {
        learning_stage = new_learning_stage;
        showModal = false;
        sendChangedData();
        dispatch('learning_stage_changed', { 'word':word, 'stage':new_learning_stage});
    }
}
</script>

<dialog id="popup-dialog" class="popup-dialog" class:wide-dialog={show_history}
	bind:this={dialog}
	on:close={() => {showModal = false; show_history = false;}}
	on:click|self={() => dialog.close()}
>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div on:click|stopPropagation>
		<div class="word" on:click={()=>{show_history=true}}>{word}</div>
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