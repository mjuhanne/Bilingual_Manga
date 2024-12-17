<script>
import { createEventDispatcher } from "svelte";

let dispatch = createEventDispatcher();

export let label_options;
export let selected_label;
export let selected_label_scope;

let new_label_list = [];
const scope_list = ['series','volume','chapter'];


$: {
    let label_list = Object.keys(label_options);
    new_label_list = label_list.filter( (l) => l != 'Newly added'); new_label_list.unshift('None');
}

export let width = 280;

const onLabelChanged = () => {
    dispatch("LabelChanged",{'label':selected_label,'scope':selected_label_scope});
};
</script>

<div style='width:{width}px'>
Info
<select id='label' bind:value={selected_label} on:change={onLabelChanged}  >
    {#each new_label_list as c}
        <option value="{c}">{c}</option>
    {/each}
</select>
{#if selected_label != 'None' && selected_label in label_options && label_options[selected_label].sc}
<select id='scope' bind:value={selected_label_scope} on:change={onLabelChanged}  >
    {#each scope_list as c}
        <option value="{c}">{c}</option>
    {/each}
</select>
{/if}
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