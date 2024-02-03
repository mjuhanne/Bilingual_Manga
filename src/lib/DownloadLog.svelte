<script>
import Modal from './Modal.svelte';

export let manga_id;
export let title='';
export let log_file='';
export let queue = [];
export let cdncdn1;

let showModal = false;

async function fetchLog() {
    const response = await fetch(`${cdncdn1}/getLog`,  { 
        method: "post",
        headers: {'Accept': 'application/json','Content-Type': 'application/json'},
        body: JSON.stringify([manga_id])}
    );
    const data = await response.json();
    const log_data = JSON.parse(data.log_data);
    title = `${log_data.message}`;
    log_file = `Log file: ${data.log_file}`;
    queue = log_data.queue;
};

async function openModal() {
    await fetchLog();
    showModal = true;   
}
</script>

<button on:click={() => openModal()}>Log</button>

<Modal bind:showModal>
	<h4 slot="header">
        <h5>
	    	{title}
        </h5> 
        <h5>
	    	{log_file}
        </h5> 
	</h4>
    
    <div class="enclosure">
          <div class="body">
            <table>
                {#each queue as row}
                <tr>
                    <td>{row.l} Chapter {row.ch}</td>
                </tr>
                <tr><td>URL: {row.url}</td></tr>
                <tr><td>PATH: {row.p}</td></tr>
                <tr></tr>
                {/each}
            </table>
          </div>
    </div>
</Modal>

<style>

.enclosure {
    color: #eee;
    font-size: 0.7rem;
    width: 800px;

}

.body {
    height: 300px;
    overflow: auto
}        

div {
    padding: 2px;
}

h4 {
    text-align: center;
    color: whitesmoke;
}

button{
    text-align: center;
    color: whitesmoke;
    border:0;

    text-decoration: none;
    padding:5px;
    margin: 1px;
    background:#611;
    border-radius:5px;
    font-size: 0.7rem;
    font-weight:bold;
}
</style>