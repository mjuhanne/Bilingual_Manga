<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();
	export let showModal; // boolean

	let dialog; // HTMLDialogElement

	export let buttons = ['Close']

	$: if (dialog && showModal) dialog.showModal();
	$: if (dialog && !showModal) dialog.close();

	function clicked(button) {
		dispatch('buttonClicked', button);
	}
	
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
<dialog
	bind:this={dialog}
	on:close={() => (showModal = false)}
	on:click|self={() => dialog.close()}
>
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div on:click|stopPropagation>
		<slot name="header" />
		<hr />
		<slot />
		<hr />
		<!-- svelte-ignore a11y-autofocus -->
		<div class="buttons-div">
			{#each buttons as b}
				{#if b=='Close'}
				<button autofocus on:click={() => dialog.close()}>Close</button>
				{:else}
				<button on:click={() => clicked(b)}>{b}</button>
				{/if}
			{/each}
		</div>
	</div>
</dialog>

<style>
	dialog {
		max-width: 40em;
		border-radius: 0.5em;
		border: none;
		padding: 0;
        background: #555;
	}
	dialog::backdrop {
		background: rgba(0, 0, 0, 0.2);
	}
	dialog > div {
		padding: 1em;
	}
	dialog[open] {
		animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}
	@keyframes zoom {
		from {
			transform: scale(0.95);
		}
		to {
			transform: scale(1);
		}
	}
	dialog[open]::backdrop {
		animation: fade 0.2s ease-out;
	}
	@keyframes fade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
	button {
		display: block;
        text-align: center;
        color: whitesmoke;
        border:0;

        text-decoration: none;
        padding:7px;
        margin: 0;
		margin-right: 10px;
        background:#333;
        border-radius:5px;
        font-size: 0.9rem;
        font-weight:bold;
		display:inline-block;
	}
    button:hover{
        cursor: pointer;
        background:rgb(125, 125, 125)
    }
	.buttons-div {
		text-align: right;
	}

</style>
