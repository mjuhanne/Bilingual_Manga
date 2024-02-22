<script>
import { createEventDispatcher } from 'svelte';
import { learning_stage_explanation, learning_stages, learning_stage_colors } from '$lib/LearningData.js'
const dispatch = createEventDispatcher();

export let selected_stage;
export let colors = learning_stage_colors;
export let embedded_to_settings_screen = false;

function clicked(stage) {
    dispatch('clicked', parseInt(stage));
}

</script>
<div class="selectiongrid">
    {#each Object.keys(learning_stages) as s}            
    <div class:buttondiv={embedded_to_settings_screen}>
        <button style="background:{colors[s]}" class:settings_screen_button={embedded_to_settings_screen} class:selected={(selected_stage==s)} on:click={() => clicked(s)}>{learning_stages[s]}</button>
    {#if embedded_to_settings_screen}
        <span class="explanation">{learning_stage_explanation[s]}</span>
    {/if}
    </div>
    {/each}
</div>

<style>
    .selected {
        filter: brightness(100%);
        color: #000;
        text-decoration: underline;
    }

    .selectiongrid {
            display: grid;
            grid-template-columns: 1fr;
            grid-gap: 5px;
    }

    .explanation {
        padding-left: 10px;
        padding-bottom: 5px;
    }
    .buttondiv {
        display: grid;
        grid-template-columns: 1fr 4fr;
        padding: 0px;
    }
	button {
		display: block;
        text-align: center;
        color: #444;
        border:0;

        text-decoration: none;
        padding:5px;
        margin: 0 auto;
        background:#333;
        border-radius:5px;
        font-weight:bold;
        filter: brightness(85%);

        font-size: 0.6rem;
        width: 60px;
        height: 20px;
	}

    .settings_screen_button {
        font-size: 0.8rem;
        width: 80px;
        height: 30px;
    }

    button:hover{
        cursor: pointer;
        filter: brightness(120%);
    }
</style>