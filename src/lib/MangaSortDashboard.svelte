<script>
import { createEventDispatcher } from "svelte";

let dispatch = createEventDispatcher();

export let sort_criteria_list;
export let sort_criteria;
export let sort_reverse;

// repository status (is manga downloaded) is not yet correctly propagated to MangaShowcase
// so hide it by default 
export let show_repo_status=false; 

const onCriteriaChanged = () => {
    dispatch("SortCriteriaChanged",sort_criteria);
};
const onReverseChanged = () => {
    dispatch("SortReverseChanged",sort_reverse);
};
</script>

<div>
Sort by
<select id='sort_criteria' bind:value={sort_criteria} on:change={onCriteriaChanged}  >
    {#each sort_criteria_list as c}
        {#if (c!='Repository status' || show_repo_status)}
            <option value="{c}">{c}</option>
        {/if}
    {/each}
</select>
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
    width: 350px;
    text-decoration: none;
    color: whitesmoke;
    font-size: 1.1 rem;
    padding: 0px;
    border-radius: 5px;
    background:#444;
}

</style>