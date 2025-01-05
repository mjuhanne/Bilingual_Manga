<script>
import { deserialize } from '$app/forms';
export let datav;
export let val;
export let blurring;
let marr =datav[0].manga_titles;
let ser=[];
const blur_off=()=>{blurring=false;}
let search_id = 0

async function doTitleSearch(search_term) {
    search_id += 1;
    var my_search_id = search_id
    let body = JSON.stringify({
        'func' : 'search',
        'param' : {
            'search_term' : search_term,
            'limit' : 50,
        }
    });
    const response = await fetch( "/titles", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });
    var res = deserialize(await response.text());
    if (search_id == my_search_id) {
        // make sure we update only the latest response (earlier searches with shorter search term
        // might take longer)
        if (res.success) {
            ser = res.response
        } else {
            ser = [];
        }
    }
};

$: doTitleSearch(val)

</script>
{#if (val!=""&&val!=undefined)}
<div>
    {#if (ser.length!=0)}
    <h3 id="B_title">Manga</h3>
    <div id ="search_inbox">
        {#each ser as m }
        <a href="/manga/{m.enid}?lang=en" data-sveltekit:prefetch style="color: #f2f2f2;text-decoration: none;" on:click={blur_off} target="_top" rel="noopener noreferrer"><div id="search_resultsen" class="search_results">{m.entit}</div></a>
        <a href="/manga/{m.enid}?lang=jp" data-sveltekit:prefetch style="color: #f2f2f2;text-decoration: none;" on:click={blur_off} target="_top" rel="noopener noreferrer"><div id="search_resultsjp" class="search_results">{m.jptit}</div></a>
         {/each}
    </div>
    {:else}
    <div id="search_notfound">Manga Not Found</div>
    {/if}
</div>
    
{/if}
<style>

    #search_inbox{
        background-color:#484848;
        border-radius:5px ;
        margin: 2vh;
        padding: 10px;
        font-weight: bold;
    }

    .search_results{
        margin: 2px 0px;
        text-align:left ;
        padding: 20px 10px;
        background: #303030;
        border-radius: 5px;
        border:#484848 solid 1px;
    
    }
    .search_results:hover{
        background-color:rgba(255,255,255,0.3);

    }
    #search_notfound{
        margin: 2px 0px;
        text-align:center ;
        padding: 20px 10px;
        font-weight: bold;
        background: #303030;
        border-radius: 5px;
        border:#484848 solid 1px;
    }



</style>