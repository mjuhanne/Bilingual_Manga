<script>
import Modal from './Modal.svelte';
import { createEventDispatcher } from 'svelte';
const dispatch = createEventDispatcher();

export let showModal;

function on_select(selection) {
    showModal = false;
    dispatch('priority_word_scope_selected', { 
        'scope':selection,
    });
}
</script>

<Modal bind:showModal buttons={['Cancel']} on:modalClosed={() => {showModal=false}}>
	<h5 slot="header">
        Select scope for prioritizing the word
	</h5>
    <div>
        <button
            on:click={()=>on_select("sentence")}>This sentence only
        </button>
        <button
            on:click={()=>on_select("chapter")}>This chapter
        </button>
        <button
            on:click={()=>on_select("title")}>This title
        </button>
        <button
            on:click={()=>on_select("all")}>Every title
        </button>
    </div>
</Modal>

<style>

div {
    padding: 2px;
}


h5 {
    text-align: center;
    color: whitesmoke;
}
button{
    text-align: center;
    color: whitesmoke;
    border:0;

    text-decoration: none;
    padding:7px;
    margin: 5px;
    background:#333;
    border-radius:5px;
    font-size: 0.6rem;
    font-weight:bold;
}

button:hover{
    cursor: pointer;
    background:rgb(125, 125, 125)
}

</style>