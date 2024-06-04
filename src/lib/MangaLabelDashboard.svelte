<script>
import { createEventDispatcher } from "svelte";

let dispatch = createEventDispatcher();

export let label_list;
export let selected_label;

let new_label_list = [];

$: {
    new_label_list = label_list.filter( (l) => l != 'Newly added'); new_label_list.unshift('None');
}

export let width = 280;

const onLabelChanged = () => {
    dispatch("LabelChanged",selected_label);
};
</script>

<div style='width:{width}px'>
Info
<select id='label' bind:value={selected_label} on:change={onLabelChanged}  >
    {#each new_label_list as c}
        <option value="{c}">{c}</option>
    {/each}
</select>
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