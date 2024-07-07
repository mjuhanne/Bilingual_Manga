<script>
import Modal from './Modal.svelte';
import {CROP_STATE, ImageCrop} from "@novacbn/svelte-image-crop";
import { checkAnkiSettings, augmentNote, createNote, getNoteIds } from "$lib/AnkiHelper.js";

let showModal = false;
export let edit_mode;
export let word = ''
export let readings = [];
export let glossary = '';
export let img_eng = ''
export let img_jap = ''
export let sentence_lines = [];

let edited_sentence;
let existing_note_ids = []

let default_image_urls;
let image_blobs;
let image_crops;
let current_image_urls;
let image_states;

let action;

async function updateCard() {
    console.log("NoteIds:",existing_note_ids);
    if (existing_note_ids.length == 0) {
        if (image_blobs['jap']==undefined) {
            image_blobs['jap'] = await image_crops["jap"].get_cropped_blob()
        }
        if (image_blobs['eng']==undefined) {
            image_blobs['eng'] = await image_crops["eng"].get_cropped_blob()
        }
        createNote(word,readings,edited_sentence,glossary,image_blobs);
    } else if (existing_note_ids.length > 1) {
        alert(`More than one anki card for word ${word} found!`);
    } else {
        if (image_blobs['jap']==undefined) {
            image_blobs['jap'] = await image_crops["jap"].get_cropped_blob()
        }
        if (image_blobs['eng']==undefined) {
            image_blobs['eng'] = await image_crops["eng"].get_cropped_blob()
        }
        augmentNote(existing_note_ids[0],word,image_blobs,edited_sentence);
    }
    showModal = false;
}

export function openDialog() {
    if (!checkAnkiSettings()) {
        alert("Anki settings unfinished");
        return;
    }
    default_image_urls = {'eng':img_eng,'jap':img_jap}
    image_blobs = {'eng':undefined,'jap':undefined}
    image_crops = {'eng':undefined,'jap':undefined}
    current_image_urls = {'eng':img_eng,'jap':img_jap}
    image_states = {'eng':CROP_STATE.default,'jap':CROP_STATE.default}
    showModal = true;
}

    async function on_commit_click(lang) {
        image_blobs[lang] = await image_crops[lang].get_cropped_blob();
        if (current_image_urls[lang] !== default_image_urls[lang]) URL.revokeObjectURL(current_image_urls[lang]);
        current_image_urls[lang] = URL.createObjectURL(image_blobs[lang]);
        image_crops[lang].reset();
    }

    function on_clear_click(lang) {
        image_crops[lang].reset();
    }

    function on_reset_click(lang) {
        if (current_image_urls[lang] !== default_image_urls[lang]) URL.revokeObjectURL(current_image_urls[lang]);
        image_blobs[lang] = null;
        current_image_urls[lang] = default_image_urls[lang];
        image_crops[lang].reset();
    }

    function on_eng_state(event) {
        image_states["eng"] = event.detail.state;
    }
    function on_jap_state(event) {
        image_states["jap"] = event.detail.state;
    }

    function modalOpened() {
        edited_sentence = sentence_lines.join('\n');
        getNoteIds(word).then(
            (res) => {
                existing_note_ids=res;
                console.log("AnkiCardDialog. ",word," has existing note Ids: ",existing_note_ids)
                if (existing_note_ids.length>0) {
                    action = "Augment";
                } else {
                    action = "Create";
                }
                edit_mode = true;
            }
        ).catch(err => {
            alert("Error connecting to Anki!");
            showModal = false;
        });
    }

    function modalClosed(e) {
        edit_mode = false;
    }
</script>

<Modal bind:showModal buttons={[action + ' card','Close']} on:buttonClicked={updateCard}
    on:modalOpened={modalOpened} on:modalClosed={modalClosed}>
	<h3 slot="header">
        {action} Anki card
	</h3>

    {#if showModal}
        <div class="sentence">
            <span class="label">Sentence</span>
            <textarea id='sentence' rows="{sentence_lines.length+1}" cols="60" bind:value={edited_sentence}></textarea>
        </div>

        <div class="enclosure">
            <div>
                <ImageCrop bind:this={image_crops["jap"]} src={current_image_urls["jap"]} on:state={on_jap_state} />
                <button
                    disabled={current_image_urls["jap"] === default_image_urls["jap"]}
                    on:click={()=>on_reset_click("jap")}>Reset
                </button>
                <button
                    disabled={image_states["jap"] === CROP_STATE.default}
                    on:click={()=>on_clear_click("jap")}>Clear
                </button>
                <button
                    disabled={image_states["jap"] === CROP_STATE.default}
                    on:click={()=>on_commit_click("jap")}>Crop
                </button>
            </div>
            <div>
                <ImageCrop bind:this={image_crops["eng"]} src={current_image_urls["eng"]} on:state={on_eng_state} />
                <button
                    disabled={current_image_urls["eng"] === default_image_urls["eng"]}
                    on:click={()=>on_reset_click("eng")}>Reset
                </button>
                <button
                    disabled={image_states["eng"] === CROP_STATE.default}
                    on:click={()=>on_clear_click("eng")}>Clear
                </button>
                <button
                    disabled={image_states["eng"] === CROP_STATE.default}
                    on:click={()=>on_commit_click("eng")}>Crop
                </button>
            </div>
        </div>    
    {/if}
</Modal>

<style>

.enclosure {
    color: #eee;
    font-size: 1.0rem;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 10px;
}

div {
    padding: 2px;
}

.label {
    text-align: left;
    color: whitesmoke;
}

h3 {
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
    font-size: 0.9rem;
    font-weight:bold;
}

button:hover{
    cursor: pointer;
    background:rgb(125, 125, 125)
}

</style>