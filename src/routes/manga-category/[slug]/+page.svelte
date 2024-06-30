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
    let match=decodeURIComponent($page.params.slug)
    const newslug=(el,match1)=>{
        let tempbol=false;
        el.mangaupdates_data.category_list.forEach((elem)=>{
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

    x.forEach((el,i) => {

        if(newslug(el,match)===true)
        {
            let score = el.mangaupdates_data.category_scores[match];
            let votes = el.mangaupdates_data.category_votes[match];
            let global_avg_vote_count = meta['0'].average_category_vote_count
            if (score > 1) {
                if (votes > global_avg_vote_count*4/3) {
                    score += 3;
                } else if (votes < global_avg_vote_count*2/3){
                    score += 1;
                } else {
                    score += 2;
                }
            }
            el.category_score = score;
            y.push(el);
        }
        
    });

    
    </script>
    <div style="margin-top:20px;font-weight: bold;font-size: 2rem;">{match} Manga</div>
    {#if (y.length!=0)}
    <MangaShowcase x={y} cdncdn={cdncdn} cdncdn1={cdncdn1} selected_category={match}/>
    {:else}
    <div style="font-size: 1.5rem;font-weight:bold;margin-top:10vh;">No Manga Found</div>
    {/if}
   
    <svelte:head>
    <title>{match} Archives - Bilingual Manga</title>
    {@html meta[0].inhtml['metades']}
    </svelte:head>
    
    <style></style>