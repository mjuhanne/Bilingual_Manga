<script>
    import {obj} from '$lib/store.js';
    import {onMount} from 'svelte'
    import { EVENT_TYPE } from "$lib/UserDataTools.js";

    const DEFAULT_KNOWN_WORD_THRESHOLD = 5;
    const DEFAULT_KNOWN_KANJI_THRESHOLD = 5;
    const MAX_THRESHOLD = 50;

    let known_word_stats = {};
    let known_word_threshold;
    let known_kanji_threshold;
    let learning_by_reading_enabled = false;
    let settings_changed = false;
    let jlpt_settings_changed = false;
    let cw_settings_changed = false;
    let lr_settings_changed = false;

    let custom_analysis_available = false;

    let eventSource;
    let files;

    let user_data;
    let meta;

    obj.subscribe(value => { 
        meta=value;
        user_data=meta['0'].user_data
        known_word_threshold = user_data.known_word_threshold !== undefined ? user_data.known_word_threshold : DEFAULT_KNOWN_WORD_THRESHOLD;
        known_kanji_threshold = user_data.known_kanji_threshold !== undefined ? user_data.known_kanji_threshold : DEFAULT_KNOWN_KANJI_THRESHOLD;
        learning_by_reading_enabled = user_data.learning_by_reading_enabled !== undefined ? user_data.learning_by_reading_enabled : false;
        if (!('custom_lang_summary_timestamp' in meta['0'])) {
            // Custom language analysis hasn't been run yet ever. Make settings stale
            settings_changed = true; 
        } else {
            custom_analysis_available = true;
        }
    });

    let cdncdn=meta['0'].cdn;
    let cdncdn1=meta['0'].cdn1;

    let status_msg = 'Not ready';

    async function fetchKnownStats() {
		fetch(`${cdncdn1}/lang/user/known.json`)
		.then(response => response.json())
		.then((data)=> {
            known_word_stats=data;
            settings_changed = false;
            cw_settings_changed = false;
            lr_settings_changed = false;
            jlpt_settings_changed = false;
        })
    }

    onMount( () => {

        fetchKnownStats();

        eventSource = new EventSource('/user_data');
        eventSource.onmessage = (event) => {
            const parsedData = JSON.parse(event.data);
            status_msg = parsedData.event_type;
            if (status_msg == EVENT_TYPE.UPDATED_STATS) {
                fetchKnownStats();
            } else if (status_msg == EVENT_TYPE.UPDATED_ANALYSIS) {
                //updateMetadata();
                status_msg = "Up to date";
            } else if (status_msg== EVENT_TYPE.ANALYSIS_ERROR) {
                status_msg = "Error while updating"
                alert(`Error: ${parsedData.msg}`)
            } else if (status_msg == EVENT_TYPE.CONNECTED) {
                if (!custom_analysis_available) {
                    status_msg = "Please check the settings and update the analysis"
                }
            }
        };

        eventSource.onerror = (event) => {
            console.log("error: " + JSON.stringify(event));
        };

        return () => {
            if (eventSource.readyState === 1) {
                eventSource.close();
            }
        };
    });


    async function onSettingsChanged() {
        settings_changed = true;
        status_msg = "Statistics and analysis are stale. Please update"
    }

    const jlpt_word_levels = {
        10:'None',
        5:'JLPT 5 (~800 words)',
        4:'JLPT 4 (~1,500 words)',
        3:'JLPT 3 (~3,700 words)',
        2:'JLPT 2 (~6,000 words)',
        1:'JLPT 1 (~10,000 words)',
    }
    
    const jlpt_kanji_levels = {
        10:'None',
        5:'JLPT 5 (100 Kanji)',
        4:'JLPT 4 (300 Kanji)',
        3:'JLPT 3 (600 Kanji)',
        2:'JLPT 2 (1,000 Kanji)',
        1:'JLPT 1 (2,000 Kanji)',
    }

    async function uploadFile(file_type) {
        if (file_type=="language-reactor-json") {
            lr_settings_changed = true;
        } else {
            cw_settings_changed = true;
        }
        onSettingsChanged();
        if (files === undefined) return;
        const dataArray = new FormData();
        for (const file of files) {
            dataArray.append(file_type, file);
        }
        const result = await fetch('/language', {
            method: 'POST',
            body: dataArray
        });
        if (result.status !== 200) alert("File error");
    }

    async function saveSettings() {
        const response = await fetch( "/user_data", {
            headers: {"Content-Type" : "application/json" },
            method: 'POST',
            body: JSON.stringify({
                'func' : 'update_comprehension_settings', 
                'settings' : {
                'jlpt_word_level' : user_data.jlpt_word_level,
                'jlpt_kanji_level' : user_data.jlpt_kanji_level,
                'learning_by_reading_enabled':learning_by_reading_enabled,
                'known_word_threshold' : known_word_threshold,
                'known_kanji_threshold' : known_kanji_threshold,
                }
             })
        });
       /*
        const result = deserialize(await response.text());
        if (result.success) {
            // pass
        }
        */
    }

</script>
<div style="margin-top:20px;font-weight: bold;font-size: 2rem;">Language settings</div>

<div class="main-container">
    <div class="left-side-container">

        <div class="knowledge-section">
            <h4 class="subheading">Core knowledge</h4>
            <div class="knowledge-subsection">
                <span>JLPT word level</span>
                <select id='jlpt_word_level' bind:value={user_data.jlpt_word_level} on:change={() => {jlpt_settings_changed=true;onSettingsChanged()}}>
                    {#each Object.keys(jlpt_word_levels) as wl}
                        <option value="{wl}">{jlpt_word_levels[wl]}</option>
                    {/each}
                </select>
            </div>
            <div class="knowledge-subsection">
                <span>JLPT kanji level</span>
                <select id='jlpt_kanji_level' bind:value={user_data.jlpt_kanji_level} on:change={() => {jlpt_settings_changed=true;onSettingsChanged()}}>
                    {#each Object.keys(jlpt_kanji_levels) as kl}
                        <option value="{kl}">{jlpt_kanji_levels[kl]}</option>
                    {/each}
                </select>
            </div>
            <div class="knowledge-table">
                <table class:settings_changed={jlpt_settings_changed}>
                    <tr>
                        <th>Unique known words</th>
                        <td>{known_word_stats.num_unique_jlpt_words}</td>
                    </tr>
                    <tr>
                        <th>Unique known kanjis</th>
                        <td>{known_word_stats.num_unique_jlpt_kanjis}</td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="knowledge-section">
            <h4 class="subheading">Language reactor word list</h4>
            <div class="knowledge-subsection">
                <label for="file">Upload your file</label>
                <input type="file" accept=".json"
                bind:files on:change={ () => { uploadFile("language-reactor-json")} }
                />
                <p class="explanation">Upload here JSON file containing 'known' and 'learning' stage words exported from Language Reactor</p>
            </div>
            <div>
                <div class="knowledge-table" class:settings_changed={lr_settings_changed}>
                    <table>
                        <tr>
                            <th>Unique known words</th>
                            <td>{known_word_stats.num_unique_known_words_lr}</td>
                        </tr>
                        <tr>
                            <th>Unique learning stage words</th>
                            <td>{known_word_stats.num_unique_learning_words_lr}</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>

        <div class="knowledge-section">

            <h4 class="subheading">Custom known word and kanji list</h4>
            <div class="knowledge-subsection">
                <div>
                    <label for="file">Upload your word list</label>
                    <input type="file" accept=".csv,.tsv"
                        bind:files on:change={ () => { uploadFile("custom-word-list")} }
                    />
                </div>
                <div>
                    <label for="file">Upload your kanji list</label>
                    <input type="file" accept=".csv,.tsv"
                        bind:files on:change={ () => { uploadFile("custom-kanji-list")} }
                    />
                </div>
                <p class="explanation">Add here a .csv/.tsv file (1 item per line) containing known words and kanjis</p>
            </div>
            <div class="knowledge-table" class:settings_changed={cw_settings_changed}>
                <table>
                    <tr>
                        <th>Unique known words</th>
                        <td>{known_word_stats.num_unique_known_words_custom}</td>
                    </tr>
                    <tr>
                        <th>Unique known kanjis</th>
                        <td>{known_word_stats.num_unique_known_kanjis_custom}</td>
                    </tr>
                    <tr>
                        <th>Unique recognized words</th>
                        <td>{known_word_stats.num_unique_recog_words_custom}</td>
                    </tr>
                    <tr>
                        <th>Unique recognized kanjis</th>
                        <td>{known_word_stats.num_unique_recog_kanjis_custom}</td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
    <div class="right-side-container">

        <div class="knowledge-section">
            <h4 class="subheading">Status</h4>
            <div class="knowledge-subsection">
                <div>
                    <button class="updatebutton" disabled={!settings_changed} on:click={()=>saveSettings()}>
                        Update
                    </button>
                    {status_msg}
                </div>
            </div>
        </div>

        <div class="knowledge-section">
            <h4 class="subheading">Learning by reading</h4>
            <div class="knowledge-subsection">
                <table>
                    <tr>
                        <th>Enabled</th>
                        <td>
                            <input type="checkbox" bind:checked={learning_by_reading_enabled} on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <tr>
                        <th>Known word threshold</th>
                        <td>
                            <input type="number" bind:value={known_word_threshold} min="0" max="{MAX_THRESHOLD}" on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <tr>
                        <th>Known kanji threshold</th>
                        <td>
                            <input type="number" bind:value={known_kanji_threshold} min="0" max="{MAX_THRESHOLD}" on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <p class="explanation">This setting will automatically mark read words and kanjis known when their occurrence reaches the thresholds configured above</p>

                    <table class:settings_changed={settings_changed}>
                        <tr>
                            <th>Total words read</th>
                            <td>{known_word_stats.num_words}</td>
                        </tr>
                        <tr>
                            <th>Total kanjis read</th>
                            <td>{known_word_stats.num_kanjis}</td>
                        </tr>
                        <tr>
                            <th>Total pages read</th>
                            <td>{known_word_stats.num_pages}</td>
                        </tr>
                        <tr>
                            <th>New words by reading</th>
                            <td>{known_word_stats.num_unique_known_words_by_reading}</td>
                        </tr>
                        <tr>
                            <th>New kanjis by reading</th>
                            <td>{known_word_stats.num_unique_known_kanjis_by_reading}</td>
                        </tr>
                        <tr>
                            <th>New recognized words</th>
                            <td>{known_word_stats.num_unique_recog_words_by_reading}</td>
                        </tr>
                        <tr>
                            <th>New recognized kanjis</th>
                            <td>{known_word_stats.num_unique_recog_kanjis_by_reading}</td>
                        </tr>
                    </table>
            </div>
        </div>

        <div class="knowledge-section">
            <h4 class="subheading">Total statistics</h4>
            <div class="knowledge-subsection" class:settings_changed={settings_changed}>
                <table>
                    <tr>
                        <th>Total # of unique words</th>
                        <td>{known_word_stats.num_unique_words}</td>
                    </tr>
                    <tr>
                        <th>Total # of unique kanjis</th>
                        <td>{known_word_stats.num_unique_kanjis}</td>
                    </tr>
                    <tr>
                        <th>Total # of words known</th>
                        <td>{known_word_stats.num_unique_known_words}</td>
                    </tr>
                    <tr>
                        <th>Total # of kanjis known</th>
                        <td>{known_word_stats.num_unique_known_kanjis}</td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
</div>
    
<svelte:head>
<title>Language settings - Bilingual Manga</title>
{@html meta[0].inhtml['metades']}
</svelte:head>
<style>

.explanation {
    font-size: 14px;
}
.main-container {
    display: grid;
    grid-template-columns: 5fr 5fr;
    justify-items: start;
    grid-gap: 0px;
    margin: 10px;
    padding-left:10px;
    padding-right:10px;
}

.left-side-container {
    display: grid;
    /*grid-template-rows: 3fr 3fr 3fr;*/
    grid-gap: 0px;
    margin: 10px;
    padding: 10px;
}

.right-side-container {
    display: grid;
    /*grid-template-rows: 1fr 2fr 2fr;*/
    grid-gap: 0px;
    margin: 10px;
    padding: 10px;
}

td {
    text-align: right;
}
th {
    text-align: left;
}

.subheading {
    margin: 0px;
    background-color: #444;
    text-align: left;
    padding: 10px;
}

.knowledge-section {
    display: float;
    background-color: #333;
    margin: 5px;
    padding: 0px;
}

.knowledge-subsection {
    text-align: left;
    padding: 15px;
}

.knowledge-table {
    padding-top: 0px;
    padding-left: 15px;
    padding-bottom: 15px;
}

.updatebutton {
    font-size: 18px;
    padding: 5px;
    margin: 0px;
    margin-right: 15px;
    border: 3px;
    border-radius: 4px;
    background-color: green;
}

.updatebutton:hover {
    background-color: lightgreen;
}

.updatebutton:disabled {
    background-color: lightgrey;
}

.settings_changed {
    color: #666666;
}
</style>