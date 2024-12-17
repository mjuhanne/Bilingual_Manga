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

{#if (meta.mangaupdates_data.category_list.length>0)}
<b style="font-size: 1.1rem;">Categories</b>
{/if}
<div class="metae">
    {#each meta.mangaupdates_data.category_list as category}
        {#if meta.mangaupdates_data.category_scores[category] == 1}
        <a class="category_weak" href="/manga-category/{encodeURIComponent(category)}">{category}</a>
        {:else if meta.mangaupdates_data.category_scores[category] == 3}
        <a class="category_average" href="/manga-category/{encodeURIComponent(category)}">{category}</a>
        {:else}
        <a class="category_strong" href="/manga-category/{encodeURIComponent(category)}">{category}</a>
        {/if}
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
    <div style="margin-left:10px;">
        <b style="font-size: 1.1rem;">Volumes</b>
        <div class="metae">
            <a>{meta.series.num_volumes}</a>
        </div>
    </div>
    <div style="margin-left:10px;">
        <b style="font-size: 1.1rem;">Chapters</b>
        <div class="metae">
            <a>{meta.series.num_chapters}</a>
        </div>
    </div>
    <div style="margin-left:10px;">
        <b style="font-size: 1.1rem;">Pages</b>
        <div class="metae">
            <a>{meta.series.num_pages}</a>
        </div>
    </div>
    <div style="margin-left:10px;">
    <b style="font-size: 1.1rem;">Rating</b>
    <div class="metae">
    <a href="{meta.mangaupdates_data.url}" target="_blank" title="Mangaupdates.com ({meta.mangaupdates_data.last_updated})">{meta.mangaupdates_data.rating} ({meta.mangaupdates_data.votes} votes)</a>
    </div>
    </div>
    <div tyle="margin-left:10px;">
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

a.category_weak {
    background:#292929;
}
a.category_average {
    background:#3b3b3b;
}
a.category_strong {
    background:#666;
}

a:hover {
  background-color:rgba(255,255,255,0.3);
}

</style>