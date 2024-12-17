<script>
import { createEventDispatcher } from "svelte";
import { scopes } from '$lib/MangaSorter.js';

let dispatch = createEventDispatcher();

export let sort_options;
export let sort_criteria;
export let sort_reverse;
export let sort_scope;

export let width = 360;

const onCriteriaChanged = () => {
    dispatch("SortCriteriaChanged",{'criteria':sort_criteria,'scope':sort_scope});
};
const onReverseChanged = () => {
    dispatch("SortReverseChanged",sort_reverse);
};
</script>

<div style='width:{width}px'>
Sort by
<select id='sort_criteria' bind:value={sort_criteria} on:change={onCriteriaChanged}  >
    {#each Object.keys(sort_options) as c}
        <option value="{c}">{c}</option>
    {/each}
</select>
{#if sort_criteria in sort_options && sort_options[sort_criteria].sc}
<select id='sort_scope' bind:value={sort_scope} on:change={onCriteriaChanged}  >
    {#each Object.keys(scopes) as c}
        <option value="{c}">{c}</option>
    {/each}
</select>
{/if}
Reverse
<input type=checkbox bind:checked={sort_reverse} on:change={onReverseChanged}> 
</div>

<style>

select{
    text-align: left;
    color: whitesmoke;
    font-size: 1.15rem;
    border:0;

    text-decoration: none;
    padding:5px;
    margin: 5px;
    background:#333;
    border-radius:5px;
    font-size: 0.9rem;
    font-weight:bold;
}

select:hover{
    cursor: pointer;
    background:rgb(125, 125, 125)
}

div {
    text-decoration: none;
    color: whitesmoke;
    font-size: 1.1 rem;
    padding: 0px;
    border-radius: 5px;
    background:#444;
}

</style>