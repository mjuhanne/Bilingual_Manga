<script>
import Modal from './Modal.svelte';
import { date2timestamp, today_timestamp, today_date, timestamp2date} from '$lib/LearningData.js'

export let manga_data;
export let chapter_ids;
export let title;

let showModal = false;

let status_list = ['Unread','Reading','Read'];
let partly_read = 'Partly read';

let comprehension_list = [0,1,2,3,4,5];
let various_comprehension = 'Various';

const comprehension_levels = {
    0: ["None", "I did read it but it was a long time ago and cannot recollect barely anything."],
    1: ["Poor", "It was a quick inattentative browse. I didn't look up any unknown words in the dictionary."],
    2: ["Moderate","It was a quite challenging experience. I did look up most of the unknown words in the dictionary but I think the difficulty level was a bit too high for my current skills."],
    3: ["Earnest","It was a bit challenging reading experience but I did look up every unknown word in the dictionary and I think my comprehension was pretty good. (This is the default option)" ],
    4: ["Very good","It was a pretty easy read. I did look up every unknown word but almost all of them were familiar to me already."],
    5: ["Excellent","It was a breeze. I basically knew every word in the manga without consulting dictionary. Every word in this volume/chapter is marked as known."],
    "Various":["Various","You have selected different comprehension levels for each chapter/volume under this item."],
};

// Variables for button label
let buttonLabel = '';
let current_data = {};

 // a copy of reading status(es) (per chapter) for status changing dialog
let new_chapter_reading_status;
let new_data = {};

// for mass setting completion dates
let first_chapter_completion_date = undefined;
let last_chapter_completion_date = undefined;

function updateLabel() {
    buttonLabel = current_data.status;
    if (current_data.status == 'Read') {
        buttonLabel += " with " + comprehension_levels[current_data.comprehension][0].toLowerCase() + " comprehension";
        if (current_data.completion_date != '') {
            buttonLabel += " [" + current_data.completion_date + "]"
        } else {
            buttonLabel += " [Unknown date]"
        }
    }
}

const updateReadingData = (status_updated) => {
    if (chapter_ids.length==1) {

        // this is a single chapter (or a volume in a multi-volume set)
        current_data = Object.assign({}, manga_data.jp_data.chapter_reading_status[ chapter_ids[0]]);
        if ('completion_timestamp' in current_data) {
            current_data.completion_date = timestamp2date(current_data['completion_timestamp'])
        } else {
            current_data.completion_date = '';
        }
    } else {
        // this is a volume (or a multi-volume set). Infer the volume reading status 
        // and comprehension level
        // from its chapter(or child volume) reading statuses
        let status = undefined;
        let comprehension = undefined;
        let first_chapter_completion_timestamp = undefined;
        let last_chapter_completion_timestamp = undefined;
        for (let c_id in manga_data.jp_data.chapter_reading_status) {
            if (chapter_ids.includes(c_id)) {
                let cs = manga_data.jp_data.chapter_reading_status[c_id];
                if ( cs.status != status) {
                    if (status === undefined) {
                        status = cs.status;
                    } else {
                        status = partly_read;
                    }
                }
                if ((cs.comprehension != comprehension) && (cs.status == 'Read')) {
                    if (comprehension === undefined) {
                        comprehension = cs.comprehension;
                    } else {
                        comprehension = various_comprehension;
                    }
                }
                // get the first and last read timestamps
                if (cs.status == 'Read') {
                    if ('completion_timestamp' in cs) {
                        if ( (first_chapter_completion_timestamp === undefined) || (cs.completion_timestamp < first_chapter_completion_timestamp ) ) {
                            first_chapter_completion_timestamp = cs.completion_timestamp;
                        }
                        if ( (last_chapter_completion_timestamp === undefined) || (cs.completion_timestamp > last_chapter_completion_timestamp ) ) {
                            last_chapter_completion_timestamp = cs.completion_timestamp;
                        }
                    }
                }
            }
        }
        current_data.status = status;
        current_data.comprehension = comprehension;

        first_chapter_completion_date = timestamp2date(first_chapter_completion_timestamp);
        last_chapter_completion_date = timestamp2date(last_chapter_completion_timestamp);
    }
    updateLabel();
}

$: updateReadingData(manga_data.jp_data.status_updated);

async function sendChangedReadingData() {

    for (let c_id of chapter_ids) {
        let ch_name = manga_data.jp_data.chapter_names[c_id];
        let data = new_chapter_reading_status[c_id];
        let old_data = manga_data.jp_data.chapter_reading_status[c_id];

        for (let k of Object.keys(data)) {
            if (k in old_data) {
                if (old_data[k] != data[k]) {
                    console.log(` ${ch_name} / ${k}: ${old_data[k]} -> ${data[k]}`)
                }
            } else {
                console.log(` ${ch_name} / ${k}: ${data[k]} (NEW)`)
            }
        }
    }

    let body = JSON.stringify({
            'func' : 'mass_set_chapter_reading_status', 
            'status_list': new_chapter_reading_status,
        })
    const response = await fetch( "/user_data", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });

    /*
    const result = deserialize(await response.text());
    if (result.success) {
        meta.favourite = result.favourite;
    }
    */
};

const statusChanged = (changed_status) => {
    if (new_data.status != changed_status) {
        console.log("StatusChanged: new_status: " + changed_status + "old_status: " + new_data.status);

        for (let c_id of chapter_ids) {
            if (changed_status == 'Read') {
                if (new_chapter_reading_status[c_id].status != 'Read') {
                    new_chapter_reading_status[c_id].comprehension = 3;
                }
                // do not overwrite completion date if already set
                if (!('completion_timestamp' in new_chapter_reading_status[c_id])) {
                    new_chapter_reading_status[c_id].completion_timestamp=today_timestamp();
                }
            } else {
                new_chapter_reading_status[c_id].comprehension = 0;
            }
            new_chapter_reading_status[c_id].status=changed_status;
        }

        if (changed_status == 'Read') {
            if (new_data.completion_date == '') {
                new_data.completion_date = today_date();
            }
        }
        new_data.status = changed_status;

        // finally we check if comprehension level was forcefully changed
        new_data.comprehension = new_chapter_reading_status[chapter_ids[0]].comprehension;
        for (let c_id of chapter_ids) {
            if (new_chapter_reading_status[c_id].comprehension != new_data.comprehension) {
                new_data.comprehension = various_comprehension;
            }
        }
    }
}

const comprehensionChanged = (changed_comprehension) => {
    if (new_data.comprehension != changed_comprehension) {
        console.log("comprehensionChanged: new_compr: " + changed_comprehension + "old_status: " + new_data.comprehension);
        if (new_data.status==partly_read) {
            // change comprehension level for only those volumes/chapters that we have set as read
            for (let c_id of chapter_ids) {
                if (new_chapter_reading_status[c_id].status=='Read') {
                    new_chapter_reading_status[c_id].comprehension=changed_comprehension;
                }
            }
            new_data.comprehension = changed_comprehension;
        } else {

            for (let c_id of chapter_ids) {
                new_chapter_reading_status[c_id].comprehension=changed_comprehension;
            }

            // when setting comprehension when all chapters are 'Not read' or 'Reading'
            // then we auto-switch also to 'Read' status
            if (new_data.status != 'Read') {
                statusChanged('Read')
            } else {
                new_data.comprehension = changed_comprehension;
            }
        }
    }
}

function completionDateChanged() {
    console.log('*' + new_data.completion_date + '*');
    if (new_data.completion_date == '') {
        new_data.completion_date = today_date(); // clearing date sets it to today
    }
    if (chapter_ids.length==1) {
        new_chapter_reading_status[chapter_ids[0]].completion_timestamp = date2timestamp(new_data.completion_date);
    } else {
        // TODO
        throw("not impl");
    }
}

function saveStatus() {
    for (let c_id of chapter_ids) {
        let data = new_chapter_reading_status[c_id];
        if (data.status != 'Read') {
            if ('completion_timestamp' in data) {
                delete data.completion_timestamp;
            }
        }
    }

    sendChangedReadingData();
    for (let c_id of chapter_ids) {
        manga_data.jp_data.chapter_reading_status[c_id] = Object.assign({},new_chapter_reading_status[c_id]);
    }
    // propagate the change to other MangaReadingStatus components
    manga_data.jp_data.status_updated = true;
    showModal = false;
}

function openDialog() {
    new_chapter_reading_status = {}
    // create a copy of the reading status(es) (per chapter) for status changing dialog
    for (let c_id of chapter_ids) {
        new_chapter_reading_status[c_id] = Object.assign({}, manga_data.jp_data.chapter_reading_status[c_id]);
    }
    new_data = Object.assign({}, current_data);
    if (chapter_ids.length==1) {
        if (new_data.completion_date == '') {
            new_data.completion_date = today_date();
            new_chapter_reading_status[chapter_ids[0]].completion_timestamp = today_timestamp();
        }
    }
    showModal = true;
}

function interpolateDates() {
    let num_read_chapters = 0
    for (let c_id of chapter_ids) {
        if (new_chapter_reading_status[c_id].status == 'Read') {
            num_read_chapters += 1;
        }
    }

    let first_chapter_completion_timestamp = date2timestamp(first_chapter_completion_date);
    let last_chapter_completion_timestamp = date2timestamp(last_chapter_completion_date);
    let timestamp = first_chapter_completion_timestamp;
    let time_delta = 0;

    if (num_read_chapters == 0) {
        return;
    } else if (num_read_chapters > 1) {
        time_delta = (last_chapter_completion_timestamp - first_chapter_completion_timestamp)/(num_read_chapters-1);
    }

    for (let c_id of chapter_ids) {
        if (new_chapter_reading_status[c_id].status == 'Read') {
            new_chapter_reading_status[c_id].completion_timestamp = timestamp;
            timestamp += time_delta;
        }
    }
}
</script>

<button on:click={() => (openDialog())}>{buttonLabel}</button>

<Modal bind:showModal buttons={['Save','Close']} on:buttonClicked={saveStatus}>
	<h3 slot="header">
        {#if chapter_ids.length==1}
		{title} reading status
        {:else}
		{title} [{chapter_ids.length} chapters] reading status
        {/if}
	</h3>
    
    <div class="enclosure">
        <div class="status_buttons_div">
        {#each status_list as s}            
            <button class:selected={new_data.status==s} on:click={() => statusChanged(s)}>{s}</button>
        {/each}
        {#if new_data.status==partly_read}
            <button disabled class="selected">{partly_read}</button>
        {/if}
        {#if chapter_ids.length==1 && new_data.status=='Read'}
            <label for="completion_date">Completed on</label>
            <input class="datepicker" name="completion_date" bind:value={new_data.completion_date} on:change={completionDateChanged} type="date" />
        {/if}
        </div>

        <hr />

        {#if chapter_ids.length>1}
            {#if new_data.status=='Read' || new_data.status==partly_read}
                <div class="selectiongrid">
                <button class="interpolate_button" on:click={() => interpolateDates()}>Interpolate dates</button>
                <div>
                    <label for="fc_completion_date">Completion dates for first / last chapters</label>
                    <input class="datepicker" name="fc_completion_date" bind:value={first_chapter_completion_date} type="date" />
                    <label for="lc_completion_date">/</label>
                    <input class="datepicker" name="lc_completion_date" bind:value={last_chapter_completion_date} type="date" />
                    <p class="explanation">
                    This will set the completion dates for read chapters evenly between the selected dates. 
                    <p>
                </div>
                </div>
            {/if}
            <hr />
        {/if}

        <h4>Comprehension and effort level</h4>
        <div class="selectiongrid">
            {#each comprehension_list as c}            
            <div>
                <button class="comprehension" class:selected={(new_data.comprehension==c) && (new_data.status=='Read' || new_data.status==partly_read)} on:click={() => comprehensionChanged(c)}>{comprehension_levels[c][0]}</button>
            </div>
            <div>
                <div>{comprehension_levels[c][1]}</div>
            </div>
            {/each}

            {#if new_data.comprehension==various_comprehension}
            <div>
                <button class="selected comprehension">{comprehension_levels[various_comprehension][0]}</button>
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

.explanation {
    font-size: 0.9rem;
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

.interpolate_button {
    width: 100px;
    background: #22a;

}
.comprehension {
    width: 80px;
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
        grid-gap: 1px;
}

.datepicker {
    font-size: 0.9rem;
}
</style>