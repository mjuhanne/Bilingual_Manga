<script>
import Modal from './Modal.svelte';
import { deserialize } from '$app/forms';

export let manga_data;
export let chapter_ids;
export let title;

let showModal = false;
let buttonLabel = '';

let status_list = ['Unread','Reading','Read'];
let partly_read = 'Partly read';

let comprehension_list = [0,1,2,3,4,5];
let various_comprehension = 'Various';

let comprehension;
let status;

const comprehension_levels = {
    0: ["None", "I did read it but it was a long time ago and cannot recollect barely anything."],
    1: ["Poor", "It was a quick inattentative browse. I didn't look up any unknown words in the dictionary."],
    2: ["Moderate","It was a quite challenging experience. I did look up most of the unknown words in the dictionary but I think the difficulty level was a bit too high for my current skills."],
    3: ["Earnest","It was a bit challenging reading experience but I did look up every unknown word in the dictionary and I think my comprehension was pretty good. (This is the default option)" ],
    4: ["Very good","It was a pretty easy read. I did look up every unknown word but almost all of them were familiar to me already."],
    5: ["Excellent","It was a breeze. I basically knew every word in the manga without consulting dictionary. Every word in this volume/chapter is marked as known."],
    "Various":["Various","You have selected different comprehension levels for each chapter/volume under this item."],
};

const updateReadingData = (status_updated) => {
    if (chapter_ids.length==1) {
        // this is a single chapter
        status = manga_data.jp_data.chapter_reading_status[chapter_ids[0]].status;
        comprehension = manga_data.jp_data.chapter_reading_status[chapter_ids[0]].comprehension;
    } else {
        // this is a volume. Infer volume reading status and comprehension level
        // from its chapter reading statuses
        let vol_status = undefined;
        let vol_comprehension = undefined;
        for (let c_id in manga_data.jp_data.chapter_reading_status) {
            if (chapter_ids.includes(c_id)) {
                let cs = manga_data.jp_data.chapter_reading_status[c_id];
                if ( cs.status != vol_status) {
                    if (vol_status == undefined) {
                        vol_status = cs.status;
                    } else {
                        vol_status = partly_read;
                    }
                }
                if ((cs.comprehension != vol_comprehension) && (cs.status == 'Read')) {
                    if (vol_comprehension == undefined) {
                        vol_comprehension = cs.comprehension;
                    } else {
                        vol_comprehension = various_comprehension;
                    }
                }
            }
        }
        status = vol_status;
        comprehension = vol_comprehension;
    }
}

$: updateReadingData(manga_data.jp_data.status_updated);

async function sendChangedReadingData(ids, update_only_comprehension) {
    let chapter_names = []
    for (let c_id of ids) {
        chapter_names.push(manga_data.jp_data.chapter_names[c_id]);
    }
    console.log("statusChanged " + chapter_names + ':' + comprehension);

    let body;
    if (update_only_comprehension) {
        body = JSON.stringify({
            'func' : 'update_comprehension', 
            'chapters' : ids,
            'comprehension' : comprehension,
        })
    } else {
        body = JSON.stringify({
            'func' : 'set_reading_status', 
            'chapters' : ids,
            'reading_data': {
                'status' : status,
                'comprehension' : comprehension,
            }
        })
    }
    const response = await fetch( "/user_data", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });

    const result = deserialize(await response.text());

    /*
    if (result.success) {
        meta.favourite = result.favourite;
    }
    */
    for (let c_id of ids) {
        if (!update_only_comprehension) {
            manga_data.jp_data.chapter_reading_status[c_id].status = status;
        }
        manga_data.jp_data.chapter_reading_status[c_id].comprehension = comprehension;
    }
    // propagate the change to other MangaReadingStatus componenents
    manga_data.jp_data.status_updated = true;
};

const statusChanged = (new_status) => {
    if (new_status != status) {
        console.log("StatusChanged: new_status: " + new_status + "old_status: " + status);
        if (new_status == 'Read') {
            comprehension = 3;
        } else {
            comprehension = 0;
        }
        status = new_status;
        sendChangedReadingData(chapter_ids, false);
    }
}

const comprehensionChanged = (new_comprehension) => {
    if (new_comprehension != comprehension) {
        if (status==partly_read) {
            // change comprehension level for only those volumes/chapters that we have set as read
            let ids = chapter_ids.filter( (id) => (manga_data.jp_data.chapter_reading_status[id].status=='Read') );
            comprehension = new_comprehension;
            sendChangedReadingData(ids, true);
        } else {
            status = 'Read';
            comprehension = new_comprehension;
            sendChangedReadingData(chapter_ids, false);
        }
    }
}

$: {
    buttonLabel = status;
    if (status == 'Read') {
        buttonLabel += " with " + comprehension_levels[comprehension][0].toLowerCase() + " comprehension";
    }
}
</script>

<button on:click={() => (showModal = true)}>{buttonLabel}</button>

<Modal bind:showModal>
	<h2 slot="header">
		{title} reading status
	</h2>
    
    <div class="enclosure">
        <div class="status_buttons_div">
        {#each status_list as s}            
            <button class:selected={status==s} on:click={() => statusChanged(s)}>{s}</button>
        {/each}

        {#if status==partly_read}
            <button class="selected" on:click={() => statusChanged(partly_read)}>{partly_read}</button>
        {/if}
        </div>

        <hr />

        <h4>Comprehension and effort level</h4>
        <div class="selectiongrid">
            {#each comprehension_list as c}            
            <div>
                <button class:selected={(comprehension==c) && (status=='Read' || status==partly_read)} on:click={() => comprehensionChanged(c)}>{comprehension_levels[c][0]}</button>
            </div>
            <div>
                <div>{comprehension_levels[c][1]}</div>
            </div>
            {/each}

            {#if comprehension==various_comprehension}
            <div>
                <button class="selected" on:click={() => comprehensionChanged(various_comprehension)}>{comprehension_levels[various_comprehension][0]}</button>
            </div>
            <div>
                <div>{comprehension_levels[various_comprehension][1]}</div>
            </div>
            {/if}
        </div>
    </div>
</Modal>

<style>

.enclosure {
    color: #eee;
    font-size: 1.0rem;
}

.status_buttons_div {
    text-align: center;
    margin: 5px;
}

div {
    padding: 2px;
}

h2 {
    text-align: center;
    color: whitesmoke;
}

h4 {
    text-align: center;
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

.selected {
    background: #262;
}
button:hover{
    cursor: pointer;
    background:rgb(125, 125, 125)
}
.selected:hover {
    background: #292;
}

.selectiongrid {
        display: grid;
        grid-template-columns: 2fr 8fr;
        grid-gap: 5px;
}

</style>