<script>
import MangaReadingStatus from '$lib/MangaReadingStatus.svelte';
import InfoPopUp from '$lib/InfoPopUp.svelte'
import { page } from '$app/stores';
export let ch=[];
export let vol={};
export let la="jp";
export let manga_data;

let vna=Object.keys(vol);
let url1=""
let volume_info_box;

let ch_num_pages = [];
let ch_files = []
let i=0;
if (la=='jp') {
    ch_num_pages = manga_data.jp_data.num_pages
} else {
    ch_num_pages = manga_data.en_data.num_pages
}

url1=`${$page.url}`.split('?')[0]
const btnel=(e)=>{
    let tar=e.target;
    console.log(tar);
    let htt=tar.innerHTML;
    let httarr=htt.split("#r@e%r@e#");
    let volo=document.getElementById(`vol${httarr[1]}`);
    if(htt.indexOf('W')!=-1)
    {   
        volo.style.display="grid";
        htt=htt.replace('W','M');
    }
    else if(htt.indexOf('M')!=-1)
    {
        volo.style.display="none";
        htt=htt.replace('M','W');
    }
    tar.innerHTML=htt;
}

function showVolumeInfo(vol_id) {
    let content = `<table style="text-align:left">
        <tr><th>Title id</th><td>${manga_data['_id']['$oid']}</td></tr>
        <tr><th>Volume id</th><td>${vol_id}</td></tr>
        <tr><th>Volume name</th><td>${manga_data.vol_info[vol_id].vol_name}</td></tr>
        <tr><th>Collection</th><td>${manga_data.vol_info[vol_id].collection}</td></tr>`
    if ('import_metadata' in manga_data.vol_info[vol_id]) {
        content += `<tr><th>Path</th><td>${manga_data.vol_info[vol_id].import_metadata.path}</td></tr><tr><th>File name</th><td>${manga_data.vol_info[vol_id].import_metadata.filename}</td></tr>`
    }
    content += `</table>`
    volume_info_box.show("Volume info",content)
}
</script>

<InfoPopUp bind:this={volume_info_box}/>

<div id="chlist">
{#each vna as v,jji}
    {#if vol[v].content_ready}
        {#if (jji==0)}
            <div style="font-size: 1.15rem;margin:10px 0px;"><button on:click={btnel}>{v} ({vol[v].num_pages} pages)&nbsp;<span class="arrowch">M<span class="invi" style="display:none;">#r@e%r@e#{jji}#r@e%r@e#</span></span><span class="invi" style="display:none;">#r@e%r@e#{jji}#r@e%r@e#</span></button>
                {#if la==="jp"}
                <MangaReadingStatus title={v} chapter_ids={vol[v].chapter_ids} bind:manga_data={manga_data}/>
                {/if}
                <button class="volinfobutton" on:click={()=>{showVolumeInfo(vol[v].id)}}>Volume info</button>
            </div>
            <div id="vol{jji}" class:chaptergrid={la==="jp"}>
            {#each ch.slice(vol[v].s, ((vol[v].e)+1)) as c,i }
                {#if (la==="en")}
                <a href="{url1}?lang={la}&chen={i+vol[v].s}&chjp=0&enp=0&jpp=0#img_store" data-sveltekit:prefetch target="_top" rel="noopener noreferrer"><div class="chsingle">{c} ({ch_num_pages[i+vol[v].s]} pages)</div></a>
                {/if}
                {#if (la==="jp")}
                <a href="{url1}?lang={la}&chen=0&chjp={i+vol[v].s}&enp=0&jpp=0#img_store" data-sveltekit:prefetch target="_top" rel="noopener noreferrer"><div class="chsingle">{c} ({ch_num_pages[i+vol[v].s]} pages)</div></a>
                <div>
                    <MangaReadingStatus title={c} chapter_ids={[manga_data.jp_data.chapter_ids[vol[v].s+i]]} bind:manga_data={manga_data}/>
                </div>
                {/if}
            {/each}
            </div>
        {:else}
            <div style="font-size: 1.15rem;margin:10px 0px;"><button on:click={btnel}>{v} ({vol[v].num_pages} pages)&nbsp;<span class="arrowch">W<span class="invi" style="display:none;">#r@e%r@e#{jji}#r@e%r@e#</span></span><span class="invi" style="display:none;">#r@e%r@e#{jji}#r@e%r@e#</span></button>
                {#if la==="jp"}
                <MangaReadingStatus title={v} chapter_ids={vol[v].chapter_ids} bind:manga_data={manga_data}/>
                {/if}
                <button class="volinfobutton" on:click={()=>{showVolumeInfo(vol[v].id)}}>Volume info</button>
            </div>
            <div id="vol{jji}" class:chaptergrid={la==="jp"} style="display:none">
            {#each ch.slice(vol[v].s, ((vol[v].e)+1)) as c,i }
                
                {#if (la==="en")}
                <a href="{url1}?lang={la}&chen={i+vol[v].s}&chjp=0&enp=0&jpp=0#img_store" data-sveltekit:prefetch target="_top" rel="noopener noreferrer"><div class="chsingle">{c} ({ch_num_pages[i+vol[v].s]} pages)</div></a>
                {/if}
                {#if (la==="jp")}
                <a href="{url1}?lang={la}&chen=0&chjp={i+vol[v].s}&enp=0&jpp=0#img_store" data-sveltekit:prefetch target="_top" rel="noopener noreferrer"><div class="chsingle">{c} ({ch_num_pages[i+vol[v].s]} pages)</div></a>
                <div>
                    <MangaReadingStatus title={c} chapter_ids={[manga_data.jp_data.chapter_ids[vol[v].s+i]]} bind:manga_data={manga_data}/>
                </div>
                {/if}

            {/each}
            </div>
        {/if}
    {:else}
        <div style="font-size: 1.15rem;margin:10px 0px;"><button>{v} ({vol[v].num_pages} pages)&nbsp;[NOT READY]</button>
            <button class="volinfobutton" on:click={()=>{showVolumeInfo(vol[v].id)}}>Volume info</button>
        </div>
    {/if}
{/each}
</div>
<style>
    #chlist{
       
        display: block;
        text-align: left;
        margin: 5px 5vw;
        margin-bottom: 0px;
        
        max-width: 90vw;
    }

    .chaptergrid {
        display: grid;
        grid-template-columns: 8fr 4fr;
        grid-gap: 0px;
    }

    a{
        text-decoration: none;
        color: whitesmoke;
    }

    .chsingle{
        text-decoration: none;
        padding:7px;
        margin: 5px;
        color: whitesmoke;
        background:#333;
        border-radius:5px;
        font-size: 0.9rem;
        font-weight:bold;

    }
    .chsingle:hover{
        background-color:rgba(255,255,255,0.3);
    }
    button{
        text-align: left;
        color: whitesmoke;
        background:none;
        font-size: 1.15rem;
        border:0;
    }
    button:hover{
        
        cursor: pointer;
        color:rgb(125, 125, 125)
    }

    .volinfobutton{
        text-align: center;
        color: whitesmoke;
        border:0;

        text-decoration: none;
        padding:7px;
        margin: 5px;
        background:#013d5f;
        border-radius:5px;
        font-size: 0.9rem;
        font-weight:bold;
    }

    .arrowch{
        float: right;
    }
</style>