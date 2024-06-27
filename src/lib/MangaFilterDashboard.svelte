<script>
import { createEventDispatcher } from "svelte";

let dispatch = createEventDispatcher();

export let filter_list;
export let filtered_num;
export let total_num;

const onFilterSwitched = (filter_index) => {
    dispatch("onFiltersUpdated", filter_list);
};


const onFilterRemoved = (filter_index) => {
    filter_list = filter_list.slice(0, filter_index).concat(filter_list.slice(filter_index+1))
    dispatch("onFiltersUpdated", filter_list);
};

</script>

{#if filter_list.length > 0}
<div class='dashboard'>
    <span class="filter_title">
        Filtered: {filtered_num} / {total_num}
    </span>
    {#each filter_list as filter,fi}
        <span class="filter">
            <input type=checkbox bind:checked={filter['en']} on:change={() => onFilterSwitched(fi)}> 
            {filter['f']}
            {filter['op']}
            {filter['v']}
            <button on:click={() => (onFilterRemoved(fi))}>X</button>
        </span>
    {/each}
</div>
{/if}

<style>

div {
    text-decoration: none;
    color: whitesmoke;
    font-size: 1.1 rem;
    padding: 0px;
    border-radius: 5px;
    background:#333;
}

div.dashboard {
    padding: 5px;
}

button {
    color: whitesmoke;
    background:#633;
}
button:hover {
    background:#a33;
}

span.filter_title {
    padding: 5px;
    margin: 5px;
    font-weight:bold;
    background:#444;
}

span.filter {
    padding: 5px;
    margin: 5px;
}

</style>