<script>
import MangaFavouriteButton from "./MangaFavouriteButton.svelte";
import GoogleBooksButton from "./GoogleBooksButton.svelte";
export let meta;
export let syn;
export let syn_en_deepl;

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

<div style="display: flex;">
    <div>
        {#if (meta.authors.length<=1)}
        <b style="font-size: 1.1rem;">Author</b>
        {:else}
        <b style="font-size: 1.1rem;">Authors</b>
        {/if}
        <div class="metae">
            {#each meta.authors as Author }
                <a href="/manga-author/{Author}">{Author}</a>
            {/each}    
        </div>
    </div>
    {#if (meta.translator.length>0)}
        <div style="margin-left:20px;">
            <b style="font-size: 1.1rem;">Translator</b>
            <div class="metae">
                <a href="/manga-translator/{meta.translator}">{meta.translator}</a>
            </div>
        </div>
    {/if}
    {#if (meta.artists.length>0)}
        <div style="margin-left:20px;">
            {#if (meta.artists.length==1)}
            <b style="font-size: 1.1rem;">Artist</b>
            {:else}
            <b style="font-size: 1.1rem;">Artists</b>
            {/if}
            <div class="metae">
                {#each meta.artists as Artist }
                    <a href="/manga-artist/{Artist}">{Artist}</a>
                {/each}    
            </div>
        </div>
    {/if}
</div>

<div style="display: flex;">
    <div>
    <b style="font-size: 1.1rem;">Release</b>
    <div class="metae">
    <a href="/manga-release/{meta.release}">{meta.release}</a>
    </div>
    </div>
    <div style="margin-left:20px;">
    <b style="font-size: 1.1rem;">Status</b>
    <div class="metae">
    <a href="/manga-status/{meta.status}">{meta.status}</a>
    </div>
    </div>
    {#if (meta.lang_summary !== undefined)}
    <div style="margin-left:10px;">
        <b style="font-size: 1.1rem;">Volumes</b>
        <div class="metae">
            <a>{meta.lang_summary.num_volumes}</a>
        </div>
    </div>
    <div style="margin-left:10px;">
        <b style="font-size: 1.1rem;">Chapters</b>
        <div class="metae">
            <a>{meta.lang_summary.num_chapters}</a>
        </div>
    </div>
    <div style="margin-left:10px;">
        <b style="font-size: 1.1rem;">Pages</b>
        <div class="metae">
            <a>{meta.lang_summary.num_pages}</a>
        </div>
    </div>
    {:else}
    <div>Language analysis not yet done!</div>
    {/if}
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
    <div tyle="margin-left:10px;">
        <b style="font-size: 1.1rem;">Google Books</b>
        <div class="metae">
        <GoogleBooksButton {meta}/>
        </div>
        </div>
    </div>

<div class="metaesyn" style="margin-top:10px;">
    {@html syn}
</div>

{#if syn_en_deepl != ''}
<div class="metaesyn deepl" style="margin-top:10px;">
    DeepL translation:
    {@html syn_en_deepl}
</div>
{/if}
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

.deepl {
    color: rgb(249, 174, 246);
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