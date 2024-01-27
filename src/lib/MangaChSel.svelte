<script>
import MangaReadingStatus from '$lib/MangaReadingStatus.svelte';
import { onMount } from 'svelte';
import { page } from '$app/stores';
export let ch=[];
export let vol={};
export let la="jp";
export let manga_data;

let vna=Object.keys(vol);
let url1=""

url1=`${$page.url}`.split('?')[0]
const btnel=(e)=>{
    let tar=e.target;
    console.log(tar);
    let htt=tar.innerHTML;
    let httarr=htt.split("#r@e%r@e#");
    let volo=document.getElementById(`vol${httarr[1]}`);
    console.log(volo);
    if(htt.indexOf('🮦')!=-1)
    {   
        volo.style.display="grid";
        htt=htt.replace('🮦','🮧');
    }
    else if(htt.indexOf('🮧')!=-1)
    {
        volo.style.display="none";
        htt=htt.replace('🮧','🮦');
    }
    tar.innerHTML=htt;
}
</script>
<div id="chlist">
{#each vna as v,jji}
{#if (jji==0)}
<div style="font-size: 1.15rem;margin:10px 0px;"><button on:click={btnel}>{v}<span class="arrowch">🮧<span class="invi" style="display:none;">#r@e%r@e#{jji}#r@e%r@e#</span></span><span class="invi" style="display:none;">#r@e%r@e#{jji}#r@e%r@e#</span></button>
    {#if la==="jp"}
    <MangaReadingStatus title={v} chapter_ids={vol[v].chapter_ids} bind:manga_data={manga_data}/>
    {/if}
</div>
<div id="vol{jji}" class:chaptergrid={la==="jp"}>
{#each ch.slice(vol[v].s, ((vol[v].e)+1)) as c,i }
    {#if (la==="en")}
    <a href="{url1}?lang={la}&chen={i+vol[v].s}&chjp=0&enp=0&jpp=0#img_store" data-sveltekit:prefetch target="_top" rel="noopener noreferrer"><div class="chsingle">{c}</div></a>
    {/if}
    {#if (la==="jp")}
    <a href="{url1}?lang={la}&chen=0&chjp={i+vol[v].s}&enp=0&jpp=0#img_store" data-sveltekit:prefetch target="_top" rel="noopener noreferrer"><div class="chsingle">{c}</div></a>
    <div>
        <MangaReadingStatus title={c} chapter_ids={[manga_data.jp_data.chapter_ids[vol[v].s+i]]} bind:manga_data={manga_data}/>
    </div>
    {/if}

{/each}
</div>
{:else}
<div style="font-size: 1.15rem;margin:10px 0px;"><button on:click={btnel}>{v}<span class="arrowch">🮦<span class="invi" style="display:none;">#r@e%r@e#{jji}#r@e%r@e#</span></span><span class="invi" style="display:none;">#r@e%r@e#{jji}#r@e%r@e#</span></button>
    {#if la==="jp"}
    <MangaReadingStatus title={v} chapter_ids={vol[v].chapter_ids} bind:manga_data={manga_data}/>
    {/if}
</div>
<div id="vol{jji}" class:chaptergrid={la==="jp"} style="display:none">
{#each ch.slice(vol[v].s, ((vol[v].e)+1)) as c,i }
    
    {#if (la==="en")}
    <a href="{url1}?lang={la}&chen={i+vol[v].s}&chjp=0&enp=0&jpp=0#img_store" data-sveltekit:prefetch target="_top" rel="noopener noreferrer"><div class="chsingle">{c}</div></a>
    {/if}
    {#if (la==="jp")}
    <a href="{url1}?lang={la}&chen=0&chjp={i+vol[v].s}&enp=0&jpp=0#img_store" data-sveltekit:prefetch target="_top" rel="noopener noreferrer"><div class="chsingle">{c}</div></a>
    <div>
        <MangaReadingStatus title={c} chapter_ids={[manga_data.jp_data.chapter_ids[vol[v].s+i]]} bind:manga_data={manga_data}/>
    </div>
    {/if}

{/each}
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
    .arrowch{
        float: right;
    }
</style>