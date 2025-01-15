<script>
import { page } from '$app/stores';
import { invalidateAll } from '$app/navigation';
import Modal from './Modal.svelte';
import { deserialize } from '$app/forms'; // Import the enhance action
export let meta;

let showModal = false;
let googleId = '';
let newGoogleId = ''
let previous_error = ''
let tried_metadata = [];

$: {
    if ((googleId == '') && (Object.keys(meta).includes('google_books'))) { 
        let id = meta.google_books.google_book_id;
        if (id == 'not_found') {
            previous_error = "Previous search attempt failed";
            tried_metadata = meta.google_books.tried_metadata
        } else if (id == 'quota_exceeded') {
            previous_error = "Previous attempt failed because quota exceeded";
        } else {
            googleId = meta.google_books.google_book_id;
            newGoogleId = googleId;
        }
    }
}

async function setGoogleBooksId(event) {


    console.log(JSON.stringify(event))
    const response = await fetch( "/titles", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: JSON.stringify({
            'func' : 'set_google_books_id', 
            'param' : {
                'title_id' : meta.enid,
                'google_book_id' : newGoogleId
            }
        })
    });

    const result = deserialize(await response.text());

    if (result.success) {
        // reload the page
        invalidateAll();
    } else {
        alert(JSON.stringify(result.response))
    }
    googleId = newGoogleId;
    showModal = false;
}

function openDialog() {
    showModal = true;
}

</script>

<button on:click={() => (openDialog())}>{#if googleId != ''}{googleId}{:else}Set Google Books Id{/if}</button>

<Modal bind:showModal buttons={['Save','Close']} on:buttonClicked={setGoogleBooksId}>
	<h3 slot="header">
        Enter Google Books Id
	</h3>
    
    <div class="enclosure">
        {#if previous_error != ''}
            <div>{previous_error}</div>
            {#if tried_metadata.length>0}
                <div>Previous searches:</div>
                <table>
                    <tr>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Translator</th>
                        <th>Publisher</th>
                    </tr>
                    {#each tried_metadata as md}
                    <tr>
                        <td>{md.title}</td>
                        <td>{md.author}</td>
                        <td>{md.translator}</td>
                        <td>{md.publisher}</td>
                    </tr>
                    {/each}
                </table>
            {/if}
        {/if}
    </div>
    <a href="https://www.google.com/search?q={meta.jptit}+inauthor%3A{meta.Author[0]}&tbm=bks" target="_blank" title="Manual Google Books search">Manual search</a>
    <div class="enclosure">
            <label>
            <input placeholder="Enter Google Book Id" bind:value={newGoogleId}>
        </label>
    </div>
    
</Modal>

<style>
.enclosure {
    margin-bottom: 20px;
    color: #eee;
    font-size: 1.0rem;
}

button{
    display: inline-block;
    text-decoration: none;
    padding:7px;
    margin: 5px 5px;
    color: whitesmoke;
    background: rgba(70, 134, 252, 0.5);
    border-radius:5px;
    border: 2px solid black;
    font-family: Arial, Helvetica,'Noto Sans Symbols 2',sans-serif;
}

button:hover {
   background: rgba(121, 178, 253, 0.5);
}

</style>
