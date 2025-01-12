<script>
import Modal from './Modal.svelte';

let showModal = false;
let title = ''
let content = ''

export function show(_title, _content) {
    title = _title;
    content = _content;
    showModal = true;
}
</script>


<Modal bind:showModal>
	<h4 slot="header">
        {title}
	</h4>
    
    <div class="enclosure">
        {@html content}
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

</style>