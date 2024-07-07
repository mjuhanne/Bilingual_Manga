<script>
    import {obj} from '$lib/store.js';
    import {onMount} from 'svelte'
    import { anki_invoke, DEFAULT_ANKI_SETTINGS, ANKI_FIELD_TYPES } from "$lib/AnkiHelper.js";
    import { EVENT_TYPE } from "$lib/UserDataTools.js";

    let anki_settings = DEFAULT_ANKI_SETTINGS;
    let settings_changed = false;

    let models = [];
    let decks = [];

    let cards = {'kanji':[]}
    let card_fields = {'kanji':[],'output':[]};

    $: console.log(JSON.stringify(anki_settings))
    let eventSource;

    let meta;

    obj.subscribe(value => { 
        meta=value;
        let user_data=meta['0'].user_data
        if ('anki_settings' in user_data) {
            for (let k of Object.keys(user_data['anki_settings'])) {
                anki_settings[k] = user_data['anki_settings'][k];
            }
        }
    });

    let status_msg = 'Not connected';

    onMount( () => {
        eventSource = new EventSource('/anki');
        eventSource.onmessage = (event) => {
            const parsedData = JSON.parse(event.data);
            if (parsedData.event_type != 'stream connected') {
                status_msg = parsedData.event_type;
            }
            console.log("New status event:",status_msg)
            //alert(`${parsedData.status_msg}`)
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

    async function loadFields(collection) {
        card_fields[collection] = [];
        cards[collection] = await anki_invoke(anki_settings['address'], 'findCards', 6, {"query":"deck:"+anki_settings[collection]['deck']});
        if (cards[collection].length>0) {
            status_msg = 'Fetching fields..'
            const first_card_info = await anki_invoke(anki_settings['address'], 'cardsInfo', 6, {"cards":[cards[collection][0]]});
            anki_invoke(anki_settings['address'], 'modelFieldNames', 6, {'modelName':first_card_info[0]['modelName']}).then((value)=>{status_msg='OK'; card_fields[collection] = value});
        }
    }
    async function onDeckChanged(collection) {
        saveSettings();
        anki_settings[collection]['field'] = '';
        loadFields(collection);
    }

    async function onValueFieldChanged(deck_type) {
        saveSettings();
    }

    async function fetchValues(collection) {
        if (anki_settings[collection]['field'] != '') {
            const response = await fetch( "/anki", {
                headers: {"Content-Type" : "application/json" },
                method: 'POST',
                body: JSON.stringify({
                    'func' : 'fetch_values', 
                    'settings' : anki_settings,
                    'collection': collection,
                })
            });
        }
    }
    
    async function onModelChanged() {
        card_fields['output'] = await anki_invoke(anki_settings['address'], 'modelFieldNames', 6, {'modelName':anki_settings['output']['model']});
        for (let field of card_fields['output']) {
            anki_settings['output']['fields'][field] = ANKI_FIELD_TYPES.NONE
        }
    }

    async function fetchConfig() {
        const result = await 
        anki_invoke(anki_settings['address'], 'deckNamesAndIds', 6).then( (res)=>{
            status_msg = "Connected"
            decks = res;
            anki_invoke(anki_settings['address'], 'modelNamesAndIds', 6).then( (mresult) => {
                models = mresult;
                saveSettings();
                if (anki_settings['kanji']['deck']!='') {
                    loadFields("kanji");
                }
                if (anki_settings['output']['deck']!='') {
                    loadFields("output");
                }
            });
        }, (error) => {
            status_msg ="Error";
            alert(`Error connecting to AnkiConnect!\n\nIs Anki running and AnkiConnect installed?\n\nDon't forget to add the local address(http://localhost:5173) to allowed hosts (Anki -> Tools -> Add-ons -> Anki Connect -> Config -> webCorsOriginList`);
        });
    }

    async function saveSettings() {
        const response = await fetch( "/user_data", {
            headers: {"Content-Type" : "application/json" },
            method: 'POST',
            body: JSON.stringify({
                'func' : 'update_anki_settings', 
                'settings' : anki_settings,
             })
        });
    }


</script>
<div class="main-container">
    <div class="left-side-container">

        <div class="section">
            <h4 class="subheading">Anki connection</h4>
            <div class="subsection">
                <span>AnkiConnect address</span>
                <input id='url' bind:value={anki_settings['address']}>
                <button id='connect' on:click={fetchConfig}>Connect</button>
            </div>
            <div class="subsection">
                <span>Status: {status_msg}</span>
            </div>
        </div>

        <div class="section">
            <h4 class="subheading">Kanji</h4>
            <div class="subsection">
                {#if Object.keys(decks).length>0}
                    <span>Kanji deck</span>
                    <select style="width:300px" id='kanji_deck' bind:value={anki_settings['kanji']['deck']} on:change={() => {onDeckChanged("kanji")}}>
                        <option value="">Select deck..</option>
                        {#each Object.keys(decks) as deck}
                            <option value={deck}>{deck}</option>
                        {/each}
                    </select>
                {:else if anki_settings['kanji']['deck'] != ''}
                    <span>Deck: {anki_settings['kanji']['deck']}</span>
                {:else}
                    <span>Decks not found</span>
                {/if}

            </div>
            <div class="subsection">
                {#if card_fields['kanji'].length>0}
                    <span>Character field</span>
                    <select style="width:300px" id='character_field' bind:value={anki_settings['kanji']['field']} on:change={() => {onValueFieldChanged("kanji")}}>
                        <option value="">Select field..</option>
                        {#each card_fields['kanji'] as field}
                            <option value={field}>{field}</option>
                        {/each}
                    </select>
                {:else if anki_settings['kanji']['field'] != ''}
                    <span>Character field: {anki_settings['kanji']['field']}</span>
                {/if}
            </div>
            <div class="subsection">
                {#if anki_settings['kanji']['field'] != ''}
                    <button id='fetchValues' on:click={() => {fetchValues("kanji")}}>Load kanjis</button>
                {/if}
            </div>
            <div class="subsection">
                <span>{cards['kanji'].length} cards found</span>
            </div>
        </div>
                
        <div class="section">
            <h4 class="subheading">Output</h4>
            <div class="subsection">
                {#if Object.keys(decks).length>0}
                    <span>Output deck</span>
                    <select style="width:300px" id='output_deck' bind:value={anki_settings['output']['deck']} on:change={() => {onDeckChanged("output")}}>
                        <option value="">Select deck..</option>
                        {#each Object.keys(decks) as deck}
                            <option value={deck}>{deck}</option>
                        {/each}
                    </select>
                {:else if anki_settings['output']['deck'] != ''}
                    <span>Deck: {anki_settings['output']['deck']}</span>
                {:else}
                    <span>Decks not found</span>
                {/if}
            </div>
            <div class="subsection">
                {#if Object.keys(models).length>0}
                    <span>Models</span>
                    <select style="width:300px" id='model' bind:value={anki_settings['output']['model']} on:change={() => {onModelChanged()}}>
                        <option value="">Select model..</option>
                        {#each Object.keys(models) as model}
                            <option value={model}>{model}</option>
                        {/each}
                    </select>
                {:else if anki_settings['output']['model'] != ''}
                    <span>Model: {anki_settings['output']['model']}</span>
                {/if}
            </div>
            {#each Object.keys(anki_settings['output']['fields']) as field}
                <div class="subsection">
                    <span>{field}</span>
                    <select style="width:300px" id='${field}_field' bind:value={anki_settings['output']['fields'][field]} on:change={() => {onValueFieldChanged("output")}}>
                        {#each Object.keys(ANKI_FIELD_TYPES) as field_type}
                            <option value={ANKI_FIELD_TYPES[field_type]}>{ANKI_FIELD_TYPES[field_type]}</option>
                        {/each}
                    </select>
                </div>
            {/each}
        </div>
    </div>
</div>
    
<svelte:head>
<title>Language settings - Bilingual Manga</title>
{@html meta[0].inhtml['metades']}
</svelte:head>
<style>

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


.subheading {
    margin: 0px;
    background-color: #444;
    text-align: left;
    padding: 10px;
}

.section {
    display: float;
    background-color: #333;
    margin: 5px;
    padding: 0px;
}

.subsection {
    text-align: left;
    padding-top: 10px;
    padding-bottom: 10px;
    padding-left: 15px;
    padding-right: 15px;
}


input {
    font-family: Arial, Helvetica,'Noto Sans Symbols 2',sans-serif;
}

</style>