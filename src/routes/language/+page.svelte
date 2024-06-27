<script>
    import {obj} from '$lib/store.js';
    import {onMount} from 'svelte'
    import { EVENT_TYPE } from "$lib/UserDataTools.js";
    import LearningStageButtons from '$lib/LearningStageButtons.svelte'
    import { 
        STAGE, learning_stages, learning_stage_colors, DEFAULT_LEARNING_SETTINGS,
        date2timestamp, today_date, timestamp2date,
    } from '$lib/LearningData.js'

    const MAX_THRESHOLD = 30;
    const MAX_DAYS = 999

    let known_word_stats = {};
    let settings_changed = false;
    let jlpt_settings_changed = false;
    let cw_settings_changed = false;
    let lr_settings_changed = false;

    let custom_analysis_available = false;

    let learning_settings = DEFAULT_LEARNING_SETTINGS;
    let jlpt_word_level = String(DEFAULT_LEARNING_SETTINGS.jlpt_word_level)
    let jlpt_kanji_level = String(DEFAULT_LEARNING_SETTINGS.jlpt_kanji_level)
    let enable_jlpt_forgetting = false;
    let learned_jlpt_date;
    let enable_custom_forgetting = false;
    let learned_custom_date;

    let eventSource;
    let files;

    let meta;

    obj.subscribe(value => { 
        meta=value;
        let user_data=meta['0'].user_data
        if ('learning_settings' in user_data) {
            for (let k of Object.keys(user_data['learning_settings'])) {
                learning_settings[k] = user_data['learning_settings'][k];
            }
            jlpt_word_level = String(learning_settings.jlpt_word_level)
            jlpt_kanji_level = String(learning_settings.jlpt_kanji_level)
            enable_jlpt_forgetting = learning_settings.learned_jlpt_timestamp > 0
            enable_custom_forgetting = learning_settings.learned_custom_timestamp > 0
            learned_jlpt_date = timestamp2date(learning_settings.learned_jlpt_timestamp)
            learned_custom_date = timestamp2date(learning_settings.learned_custom_timestamp)
        }
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
		fetch(`${cdncdn1}/lang/user/learning_data.json`)
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
                status_msg = "Up to date";
            } else if (status_msg== EVENT_TYPE.ANALYSIS_WARNING) {
                alert(`${parsedData.msg}`)
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
        learning_settings.jlpt_word_level = parseInt(jlpt_word_level)
        learning_settings.jlpt_kanji_level = parseInt(jlpt_kanji_level)
        const response = await fetch( "/user_data", {
            headers: {"Content-Type" : "application/json" },
            method: 'POST',
            body: JSON.stringify({
                'func' : 'update_learning_settings', 
                'settings' : learning_settings,
             })
        });
       /*
        const result = deserialize(await response.text());
        if (result.success) {
            // pass
        }
        */
    }

function setLearningStageColor(stage) {
    // TODO
}

function onChangedJlptForgetting() {
    console.log("onChangedJlptForgetting " + enable_jlpt_forgetting)
    if (enable_jlpt_forgetting) {
        if (learning_settings.learned_jlpt_timestamp == 0) {
            learned_jlpt_date=today_date()
        }
        learning_settings.learned_jlpt_timestamp=date2timestamp(learned_jlpt_date)
    } else {
        learning_settings.learned_jlpt_timestamp = 0
    }
    jlpt_settings_changed=true;
    onSettingsChanged();
}

function onChangedCustomForgetting() {
    console.log("onChangedCustomForgetting " + enable_custom_forgetting)
    if (enable_custom_forgetting) {
        if (learning_settings.learned_custom_timestamp == 0) {
            learned_custom_date=today_date()
        }
        learning_settings.learned_custom_timestamp=date2timestamp(learned_custom_date)
    } else {
        learning_settings.learned_custom_timestamp = 0
    }
    onSettingsChanged();
}

function colorizeByStage(text,stage) {
    return `<span style="color:${learning_stage_colors[stage]}">${text}</span>`
}

function colorizeStage(stage) {
    return colorizeByStage(learning_stages[stage],stage);
}

</script>
<div style="margin-top:20px;font-weight: bold;font-size: 2rem;">Language settings</div>

<div class="main-container">
    <div class="left-side-container">

        <div class="knowledge-section">
            <h4 class="subheading">Core knowledge</h4>
            <div class="knowledge-subsection">
                <span>JLPT word level</span>
                <select id='jlpt_word_level' bind:value={jlpt_word_level} on:change={() => {jlpt_settings_changed=true;onSettingsChanged()}}>
                    {#each Object.keys(jlpt_word_levels) as wl}
                        <option value={wl}>{jlpt_word_levels[wl]}</option>
                    {/each}
                </select>
            </div>
            <div class="knowledge-subsection">
                <span>JLPT kanji level</span>
                <select id='jlpt_kanji_level' bind:value={jlpt_kanji_level} on:change={() => {jlpt_settings_changed=true;onSettingsChanged()}}>
                    {#each Object.keys(jlpt_kanji_levels) as kl}
                        <option value={kl}>{jlpt_kanji_levels[kl]}</option>
                    {/each}
                </select>
            </div>
            
            <div class="knowledge-subsection">
                <label for="enable_jlpt_forgetting">Enable forgetting</label>
                <input name="enable_jlpt_forgetting" type="checkbox" bind:checked={enable_jlpt_forgetting} on:change={onChangedJlptForgetting}/>
                {#if enable_jlpt_forgetting}
                <label for="jlpt_learned_date">Learned on</label>
                <input class="datepicker" name="jlpt_learned_date" bind:value={learned_jlpt_date} on:change={onChangedJlptForgetting} type="date" />
                {/if}
            </div>
            <div class="knowledge-subsection">
                <label for="always_know_particles">Always know particles</label>
                <input name="always_know_particles" type="checkbox" bind:checked={learning_settings.always_know_particles} on:change={onSettingsChanged}/>
            </div>
            <div class="knowledge-subsection">
                <label for="omit_particles">Omit particles from freq analysis</label>
                <input name="omit_particles" type="checkbox" bind:checked={learning_settings.omit_particles} on:change={onSettingsChanged}/>
            </div>
            <div class="knowledge-table-div">
                <table class="knowledge-table" class:settings_changed={jlpt_settings_changed}>
                    <tr>
                        <th>Unique known words</th>
                        <td>{known_word_stats.num_unique_known_jlpt_base_words}</td>
                    </tr>
                    <tr>
                        <th>Unique known kanjis</th>
                        <td>{known_word_stats.num_unique_known_jlpt_base_kanjis}</td>
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
                <p class="explanation">Upload here JSON file containing {@html colorizeByStage("known",STAGE.KNOWN)} and {@html colorizeByStage("learning",STAGE.LEARNING)} stage words exported from Language Reactor</p>
            </div>
            <div>
                <div class="knowledge-table-div" class:settings_changed={lr_settings_changed}>
                    <table class="knowledge-table">
                        <tr>
                            <th>Unique known words</th>
                            <td>{known_word_stats.num_unique_known_words_lr}</td>
                        </tr>
                        <tr>
                            <th>Unique {@html colorizeByStage("learning",STAGE.LEARNING)} stage words</th>
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
            <div class="knowledge-subsection">
                <label for="enable_custom_forgetting">Enable forgetting</label>
                <input name="enable_custom_forgetting" type="checkbox" bind:checked={enable_custom_forgetting} on:change={onChangedCustomForgetting}/>
                {#if enable_custom_forgetting}
                <label for="custom_learned_date">Learned on</label>
                <input class="datepicker" name="custom_learned_date" bind:value={learned_custom_date} on:change={onChangedCustomForgetting} type="date" />
                {/if}
            </div>
            <div class="knowledge-table-div" class:settings_changed={cw_settings_changed}>
                <table class="knowledge-table">
                    <tr>
                        <th>Unique known words</th>
                        <td>{known_word_stats.num_unique_known_words_custom}</td>
                    </tr>
                    <tr>
                        <th>Unique known kanjis</th>
                        <td>{known_word_stats.num_unique_known_kanjis_custom}</td>
                    </tr>
                    <tr>
                        <th>Unique {@html colorizeStage(STAGE.LEARNING)} stage words</th>
                        <td>{known_word_stats.num_unique_learning_words_custom}</td>
                    </tr>
                    <tr>
                        <th>Unique {@html colorizeStage(STAGE.LEARNING)} stage kanjis</th>
                        <td>{known_word_stats.num_unique_learning_kanjis_custom}</td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
    <div class="middle-container">
        <div class="knowledge-section">
            <h4 class="subheading">Learning stages</h4>
            <div class="knowledge-subsection">
                <LearningStageButtons on:clicked={setLearningStageColor} embedded_to_settings_screen=true/>
            </div>
            <div class="knowledge-subsection">
                <table>
                    <tr>
                        <th>Colorize words in manga</th>
                        <td>
                            <input type="checkbox" bind:checked={learning_settings.colorize} on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <tr>
                        <th>Enable Automatic learning</th>
                        <td>
                            <input type="checkbox" bind:checked={learning_settings.automatic_learning_enabled} on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <p class="explanation">This setting will automatically change the learning stage of read words and kanjis when their occurrence reaches the thresholds configured below</p>
                    Occurrence thresholds
                    <tr>
                        <th>Graduate word to {@html colorizeStage(STAGE.LEARNING)} stage</th>
                        <td>
                            <input type="number" bind:value={learning_settings.learning_word_threshold} min="0" max="{MAX_THRESHOLD}" on:change={onSettingsChanged}/>
                        </td>
                        
                    </tr>
                    <tr>
                        <th>Graduate kanji to  {@html colorizeStage(STAGE.LEARNING)} stage</th>
                        <td>
                            <input type="number" bind:value={learning_settings.learning_kanji_threshold} min="0" max="{MAX_THRESHOLD}" on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <tr>
                        <th>Graduate word to {@html colorizeStage(STAGE.KNOWN)}/{@html colorizeStage(STAGE.PRE_KNOWN)} stage</th>
                        <td>
                            <input type="number" bind:value={learning_settings.known_word_threshold} min="0" max="{MAX_THRESHOLD}" on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <tr>
                        <th>Graduate kanji to {@html colorizeStage(STAGE.KNOWN)}/{@html colorizeStage(STAGE.PRE_KNOWN)} stage</th>
                        <td>
                            <input type="number" bind:value={learning_settings.known_kanji_threshold} min="0" max="{MAX_THRESHOLD}" on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <tr>
                        <th>Maximum # regarded encounters per chapter</th>
                        <td>
                            <input type="number" bind:value={learning_settings.max_encounters_per_chapter} min="0" max="{MAX_THRESHOLD}" on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <tr>
                        <th>Automatic graduation to {@html colorizeStage(STAGE.KNOWN)}</th>
                        <td>
                            <input type="checkbox" bind:checked={learning_settings.automatic_graduation_to_known} on:change={onSettingsChanged}/>
                        </td>
                    </tr>
                    <tr>
                        <th>Set status to {@html colorizeStage(STAGE.FORGOTTEN)} if not encountered in x days (0 = disabled)</th>
                        <td>
                            <input type="number" bind:value={learning_settings.initial_remembering_period} min="0" max={MAX_DAYS} on:change={onSettingsChanged}/>
                        </td>
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
                <div class="timestamp">
                    User data updated<br>{new Date(meta['0'].user_data_timestamp).toLocaleString()}
                    User data timestamp<br>{meta['0'].user_data_timestamp}
                </div>
                <div class="timestamp">
                        Lang analysis updated<br>{new Date(meta['0'].custom_lang_summary_timestamp).toLocaleString()}
                </div>
            </div>
        </div>


        <div class="knowledge-section">
            <h4 class="subheading">Reading statistics</h4>
            <div class="knowledge-subsection" class:settings_changed={settings_changed}>
                <table>
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
                        <th>New known words after reading</th>
                        <td>{known_word_stats.num_unique_known_words_by_reading}</td>
                    </tr>
                    <tr>
                        <th>New known kanjis after reading</th>
                        <td>{known_word_stats.num_unique_known_kanjis_by_reading}</td>
                    </tr>
                    <tr>
                        <th>New {@html colorizeByStage("pre-known",STAGE.PRE_KNOWN)} words after reading</th>
                        <td>{known_word_stats.num_unique_pre_known_words_by_reading}</td>
                    </tr>
                    <tr>
                        <th>New {@html colorizeByStage("pre-known",STAGE.PRE_KNOWN)} kanjis after reading</th>
                        <td>{known_word_stats.num_unique_pre_known_kanjis_by_reading}</td>
                    </tr>
                    <tr>
                        <th>New {@html colorizeByStage("learning",STAGE.LEARNING)} stage words</th>
                        <td>{known_word_stats.num_unique_learning_words_by_reading}</td>
                    </tr>
                    <tr>
                        <th>New {@html colorizeByStage("learning",STAGE.LEARNING)} stage kanjis</th>
                        <td>{known_word_stats.num_unique_learning_kanjis_by_reading}</td>
                    </tr>
                    <tr>
                        <th>{@html colorizeByStage("Forgotten",STAGE.FORGOTTEN)} words</th>
                        <td>{known_word_stats.num_unique_forgotten_words}</td>
                    </tr>
                    <tr>
                        <th>{@html colorizeByStage("Forgotten",STAGE.FORGOTTEN)} kanjis</th>
                        <td>{known_word_stats.num_unique_forgotten_kanjis}</td>
                    </tr>
                </table>
            </div>
        </div>


        <div class="knowledge-section">
            <h4 class="subheading">Total statistics</h4>
            <div class="knowledge-subsection" class:settings_changed={settings_changed}>
                <table class="knowledge-table">
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
    grid-template-columns: 5fr 5fr 5fr;
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
    font-size: 14px;
}
th {
    text-align: left;
    font-size: 14px;
}

.subheading {
    margin: 0px;
    background-color: #444;
    text-align: left;
    padding: 10px;
}

.timestamp {
    margin: 5px;
}

.knowledge-section {
    display: float;
    background-color: #333;
    margin: 5px;
    padding: 0px;
}

.knowledge-subsection {
    text-align: left;
    padding-top: 10px;
    padding-bottom: 10px;
    padding-left: 15px;
    padding-right: 15px;
}

.knowledge-table-div {
    padding-top: 0px;
    padding-left: 15px;
    padding-bottom: 15px;
}
.knowledge-table {
    width: 90%;
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

input {
    font-family: Arial, Helvetica,'Noto Sans Symbols 2',sans-serif;
}

</style>