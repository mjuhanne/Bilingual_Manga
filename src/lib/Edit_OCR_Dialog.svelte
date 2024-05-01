<script>
import Modal from './Modal.svelte';
import { createEventDispatcher } from 'svelte';

export let showModal = false;
export let ocr_block = [];
const dispatch = createEventDispatcher();
let ocr_block_lines = ''


function saveStatus() {
    let new_ocr_block = ocr_block_lines.split('\n')
    showModal = false;
    dispatch('ocr_block_updated', { 
            'ocr_block': new_ocr_block,
        });
}

function modalOpened() {
    ocr_block_lines = ocr_block.join('\n')
}

</script>


<Modal bind:showModal buttons={['Save','Close']} on:buttonClicked={saveStatus} on:modalOpened={modalOpened}>
	<h4 slot="header">
		Update OCR block
	</h4>
    
    <div class="enclosure">
        <textarea rows="8" columns="20" bind:value={ocr_block_lines} />
    </div>
    
</Modal>

<style>
.enclosure {
    color: #eee;
    font-size: 1.0rem;
}


div {
    padding: 2px;
}

h4 {
    text-align: center;
    color: whitesmoke;
    margin: 15px;
}

h3 {
    text-align: center;
    color: whitesmoke;
}

input {
    font-family: Arial, Helvetica,'Noto Sans Symbols 2',sans-serif;
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
    font-size: 0.9rem;
    font-weight:bold;
}

button:hover{
    cursor: pointer;
    background:rgb(125, 125, 125)
}

</style>