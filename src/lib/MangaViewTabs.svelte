<script>
    import { page } from '$app/stores';

	export let titles;
	export let selectedTab = 0;
	export let lang;
		
	let lang_button_text = (lang=="jp") ? "EN" : "JP";
    let url1=`${$page.url}`.split('?')[0]
	let lang_button_url = url1 + "?lang=" + ( (lang=="jp") ? "en" : "jp" );
</script>

<style>
	.tab-content {
		padding: 5px;
	}
	.tabs {
        display: grid;
        grid-template-columns: 7fr 1fr;
		justify-items: start;
        grid-gap: 0px;
		background-color: #333;
		padding-left:50px;
		padding-right:50px;
	}
	.tab {
        font-size: 1.1rem;
		border: none;
		background: #222;
		margin: 0;
        padding: 5px;
        padding-left: 15px;
        padding-right: 15px;
        margin: 3px;
		cursor: pointer;
        border-radius:7px;
        color: #eee;
        font-family: Arial, Helvetica,'Noto Sans Symbols 2',sans-serif;        
	}
	.tab.selected {
		background: #151;
        color: whitesmoke;
		cursor: default;
	}
	.tab:hover {
		background: #282;
	}
	.lang_div {
		justify-self: end;
	}
	.langbutton {
        color: #fff;
		background: rgb(36, 71, 115);
	}
	.langbutton:hover {
		background: rgb(45, 98, 255);
	}
</style>

<div class="tab-control">
	<div class="tabs">
		<div>
			{#each titles as t,i}
				<button type="button" class="tab"
				class:selected={selectedTab==i}
					on:click={() => selectedTab = i}>
					{titles[i]}
				</button>
			{/each}
		</div>
		<div class="lang_div">
			<a href="{lang_button_url}" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">
				<button class="tab langbutton">{lang_button_text}
				</button>
			</a>
		</div>
	</div>
	<div class="tab-content">
		<slot/>
	</div>
</div>