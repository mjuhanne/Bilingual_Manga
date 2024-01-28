<script>
import MangaFavouriteButton from "./MangaFavouriteButton.svelte";
export let meta;
export let syn;

</script>
<div id="metac">
<b style="font-size: 1.1rem;">Alternative Titles</b>
<div class="metaesearch" style="margin:0;padding:5px;">
{meta.search}
</div>
{#if (meta.genres.length<=1)}
<b style="font-size: 1.1rem;">Genre</b>
{:else}
<b style="font-size: 1.1rem;">Genres</b>
{/if}
<div class="metae">
    {#each meta.genres as genre }
     <a href="/manga-genre/{genre}">{genre}</a>
    {/each}    
</div>
{#if (meta.Author.length<=1)}
<b style="font-size: 1.1rem;">Author</b>
{:else}
<b style="font-size: 1.1rem;">Authors</b>
{/if}
<div class="metae">
    {#each meta.Author as Author }
        <a href="/manga-author/{Author}">{Author}</a>
    {/each}    
</div>
{#if (meta.Artist.length<=1)}
<b style="font-size: 1.1rem;">Artist</b>
{:else}
<b style="font-size: 1.1rem;">Artists</b>
{/if}
<div class="metae">
    {#each meta.Artist as Artist }
        <a href="/manga-artist/{Artist}">{Artist}</a>
    {/each}    
</div>

<div style="display: flex;">
    <div>
    <b style="font-size: 1.1rem;">Release</b>
    <div class="metae">
    <a href="/manga-release/{meta.Release}">{meta.Release}</a>
    </div>
    </div>
    <div style="margin-left:20px;">
    <b style="font-size: 1.1rem;">Status</b>
    <div class="metae">
    <a href="/manga-status/{meta.Status}">{meta.Status}</a>
    </div>
    </div>
    <div>
    <b style="font-size: 1.1rem;">Rating</b>
    <div class="metae">
    <a href="{meta.rating_data.url}" target="_blank" title="Mangaupdates.com ({meta.rating_data.last_updated})">{meta.rating_data.rating} ({meta.rating_data.votes} votes)</a>
    </div>
    </div>
    <div>
    <b style="font-size: 1.1rem;">Favourite</b>
    <div class="metae">
    <MangaFavouriteButton {meta}/>
    </div>
    </div>
</div>

<div class="metaesyn" style="margin-top:10px;">
    {syn}    
</div>
</div>
<style>
#metac{
display: block;
text-align: left;
margin: 5px 5vw;
margin-bottom: 0px;
height: auto;
max-width: 90vw;
overflow: clip;
border-radius:5px;
}
.metae{

    overflow-wrap: break-word;
    
}
a{
display: inline-block;

text-decoration: none;
padding:7px;
margin: 5px 5px;
color: whitesmoke;
background:#333;
border-radius:5px;

}

a:hover {
  background-color:rgba(255,255,255,0.3);
}

</style>