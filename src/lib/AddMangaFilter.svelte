<script>
import Modal from './Modal.svelte';
import { createEventDispatcher } from "svelte";
import { getValue, scopes } from '$lib/MangaSorter.js';

let dispatch = createEventDispatcher();

let showModal = false;
export let manga_titles;
export let filter_list;
export let filter_options;
let available_filters = Object.keys(filter_options);
let new_filter = {'en':true,'f':'Rating','op':'>','v':8,'sc':''}
let filter_values = [];

function openDialog() {
    showModal = true;
}

function saveStatus() {
    // clone the filter struct and add to the filter list
    filter_list.push(JSON.parse(JSON.stringify(new_filter))); 
    dispatch("onFiltersUpdated", filter_list);
    showModal = false;
}

function onFilterChanged() {
    let fo = filter_options[new_filter['f']];
    if (fo.type != 'val') {
        filter_values = [];
        for (let m of manga_titles) {
            let val = undefined;
            if (fo.sc) {
                    val = getValue(m, fo, new_filter['sc'])
                } else {
                    val = getValue(m, fo, '')
                }
            if (val !== undefined) {
                if (fo.type == 'list') {
                    for (v of values) {
                        if (filter_values.indexOf(v) == -1) {
                            filter_values.push(v);
                        }
                    }
                }
            } else {
                if (filter_values.indexOf(val) == -1) {
                    filter_values.push(val);
                }
            } 
        }
        
        if (new_filter['op'] != '=' && new_filter['op'] != '!=') {
            new_filter['op'] = '=';
        }
        if (filter_values.length > 0) {
            new_filter['v'] = filter_values[0];
        }
    } else {

    }
    if (fo.sc) {
        new_filter['sc'] = 'series';
    }
    filter_values.sort()
}

</script>

<button on:click={() => (openDialog())}>Add Filter</button>

<Modal bind:showModal buttons={['Save','Close']} on:buttonClicked={saveStatus}>
	<h3 slot="header">
        Add Manga Filter
	</h3>
    
    <div class="enclosure">
        <select id='selected_filter' bind:value={new_filter['f']} on:change={onFilterChanged}>
            {#each available_filters as filter,fi}
                {#if (filter != 'Newly added') && (filter != 'A-Z')}
                    <option value="{filter}">{filter}</option>
                {/if}
            {/each}
        </select>
        <select id='op' bind:value={new_filter['op']}>
            <option value="=">equal to</option>
            {#if filter_options[new_filter['f']].type!='boolean'}
                <option value="!=">is not</option>
            {/if}
            {#if filter_options[new_filter['f']].type=='val'}
                <option value=">">higher than</option>
                <option value=">=">higher or equal to</option>
                <option value="<">lower than</option>
                <option value="<=">lower or equal to</option>
            {/if}
        </select>
        {#if filter_options[new_filter['f']].type=='val'}
            <input id='val' type="number" bind:value={new_filter['v']}/>
        {:else}
            {#key filter_values}
                <select id='val' bind:value={new_filter['v']}>
                    {#each filter_values as val}
                    <option value="{val}">{val}</option>
                    {/each}
                </select>
            {/key}
        {/if}
        {#if filter_options[new_filter['f']].sc}
            in
            <select id='scope' bind:value={new_filter['sc']}>
                {#each Object.keys(scopes) as scope}
                <option value="{scope}">{scopes[scope]}</option>
                {/each}
            </select>
        {/if}
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
    padding:9px;
    margin: 0px;
    background:#444;
    border-radius:5px;
    font-size: 1.1rem;
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