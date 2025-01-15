<script>
    import MangaMeta from '$lib/MangaMeta.svelte';
    import MangaChSel from '$lib/MangaChSel.svelte';
    import Tabs from './Tabs.svelte';
    import MangaLanguageAnalysis from './MangaLanguageAnalysis.svelte';
    import MangaSuggestPreread from './MangaSuggestPreread.svelte';
    export let data;    
    export let ll;

    let available_tabs = ['Series info','Volumes']
    if (ll.analysis !== undefined) {
        available_tabs = ['Series info','Volumes','Language analysis','Suggested preread']
    }
    
    export let cdncdn1;

    export let selectedTab;

    let chapters, volumes, cover, title, syn, secondary_title
    let syn_en_deepl = '';
    if (data.l=="en") {
        chapters=data.manga_data.en_data.ch_naen;
        volumes=data.manga_data.en_data.vol_en;
        cover=ll.coveren;
        title=ll.entit;
        secondary_title=ll.jptit;
        syn=data.manga_data.syn_en;
    } else {
        chapters=data.manga_data.jp_data.ch_najp;
        volumes=data.manga_data.jp_data.vol_jp;
        cover=ll.coverjp;
        title=ll.jptit;
        secondary_title=ll.entit;
        syn=data.manga_data.syn_jp;
    }
    if ('syn_en_deepl' in data.manga_data) {
        syn_en_deepl = data.manga_data.syn_en_deepl
    }
</script>

<div id="mainimagec" style="background:url({cdncdn1}/{cover}) no-repeat; background-size: cover;background-position: center;" >
<img src="{cdncdn1}/{cover}" alt="{cover}" id="mainimage"/>
<div id="spreads" ></div>
<div style="display: block;z-index:4;">
<div id="mainimagetitle">{title}</div>
<div id="secondaryimagetitle">{secondary_title}</div>
</div>
</div>
<Tabs titles={available_tabs} lang={data.l} bind:selectedTab>
    {#if selectedTab==0}
        <MangaMeta meta={ll} {syn} {syn_en_deepl}/>
    {:else if selectedTab==1}
        <MangaChSel ch={chapters} vol={volumes} manga_data={data.manga_data} la={data.l}/>
    {:else if selectedTab==2}
        <MangaLanguageAnalysis meta={ll}/>
    {:else if selectedTab==3}
        <MangaSuggestPreread meta={ll} manga_data={data.manga_data}/>
    {/if}
</Tabs>

<style>
    #mainimage{
        max-height:250px;
        margin-left:5vw ;
        z-index: 3;
        border-radius: 3px;
    }
    #mainimagec{
        display: flex;
        height:250px;
        max-height:250px;
        width: 100vw;

        position: relative;
        z-index: 1;
        outline: none;
    }
    #spreads{
        position: absolute;
        top: 0px;
        left: 0px;
        background-color:rgba(0,0,0,0.7);

        height: 100%;
        width: 100%;
        z-index: 2;
    }

    #mainimagetitle{
        text-align: left;
        font-size: 1.5rem;
        font-weight: bold;
        z-index: 4;
        word-wrap: break-word;
        overflow: hidden;

        margin:10px 0px 10px 5px;
    }
    #secondaryimagetitle{
        text-align: left;
        font-size: 1.0rem;
        font-weight: bold;
        z-index: 4;
        word-wrap: break-word;
        overflow: hidden;

        margin:20px 0px 10px 5px;
    }
</style>