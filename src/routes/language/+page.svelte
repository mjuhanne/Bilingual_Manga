<script>
    import Tabs from '$lib/Tabs.svelte';
    import LanguageSettings from '$lib/LanguageSettings.svelte';
    import AnkiSettings from '$lib/AnkiSettings.svelte';
    export let selectedTab;
</script>

<Tabs titles={['Language settings','Anki settings']} bind:selectedTab>
    {#if selectedTab==0}
        <LanguageSettings/>
    {:else if selectedTab==1}
        <AnkiSettings/>
    {/if}
</Tabs>

<style>

</style>