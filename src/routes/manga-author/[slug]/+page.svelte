<script>
    import {obj} from '$lib/store.js';
    import { page } from '$app/stores';
    import MangaShowcase from '$lib/MangaShowcase.svelte';
    let meta;
    obj.subscribe(value => { meta=value;});
    let x = meta['0'].manga_titles;
    let cdncdn=meta['0'].cdn;
    let cdncdn1=meta['0'].cdn1;
    let y=[]
    let match=$page.params.slug

    const newslug=(el,match1)=>{
        let tempbol=false;
        el.Author.forEach((elem)=>{
            let s = elem.replaceAll(" ","-");
            s = s.replaceAll("'",'');
            s=s.toLowerCase();
           
            
            if((`${elem}`===`${match1}`)||(`${s}`===`${match1}`))
            {
               
                tempbol=true;
                return tempbol;
            }
            

        });
        return tempbol;
    }

    let match2 = match.replaceAll(" ","-");
    match2 = match2.replaceAll("'",'');
    match2=match2.toLowerCase();

    x.forEach((el,i) => {
        
        

        if(newslug(el,match2)===true)
        {
            y.push(el);
        }
        
    });

    
    </script>
    <div style="margin-top:20px;font-weight: bold;font-size: 2rem;">{match}'s Manga</div>
    {#if (y.length!=0)}
    <MangaShowcase x={y} cdncdn={cdncdn} cdncdn1={cdncdn1}/>
    {:else}
    <div style="font-size: 1.5rem;font-weight:bold;margin-top:10vh;">No Manga Found</div>
    {/if}
    <svelte:head>
    <title>{match} Archives - Bilingual Manga</title>
    {@html meta[0].inhtml['metades']}
    </svelte:head>
    
    <style></style>