<script>
import Modal from './Modal.svelte';
import { STAGE, learning_stage_colors, source_to_name, 
    word_classes, timestamp2date 
} from '$lib/LearningData.js'

export let showModal;
export let word = ''
export let history = [];
let selected_index = -1;


export function openDialog() {
    showModal = true;
}

function modalOpened() {
}

function modalClosed(e) {
}

function selectedEvent(index) {
    selected_index = index;
}
</script>

<Modal bind:showModal buttons={['Close']} 
    on:modalOpened={modalOpened} on:modalClosed={modalClosed}>
	<h4 slot="header">
        {word} history
	</h4>

    {#if showModal}
        <div class="enclosure">
            {#each history as word_event,i}
            <table class="word_event_table" class:selected_event={i == selected_index} on:click={()=>{selectedEvent(i)}}>

                <tr style="background:{learning_stage_colors[word_event.s]}">
                    <td>{timestamp2date(word_event.t*1000)}</td>
                    <td>{source_to_name[word_event.m.src]}</td>
                </tr>
                <tr style="background:{learning_stage_colors[word_event.s]}">
                    <td colspan=2>{word_event.m.comment}</td>
                </tr>
                <tr style="height:3px"></tr>
            </table>
            {/each}
        </div>
    {/if}
</Modal>

<style>

.enclosure {
    width: 250px;
    color: #040404;
    font-size: 0.6rem;
}

.selected_event {
        background-color: #999;
        border-radius: 5px;
        border-color: #fff;
    }

.word_event_table {
    width: 100%;
    padding: 1px;
    margin: 0px;
}



div {
    padding: 2px;
}

h4 {
    text-align: center;
    color: whitesmoke;
    margin: 0px;
}

</style>