<script>
    import {obj} from '$lib/store.js';
    import { page } from '$app/stores';
    import MangaShowcase from '$lib/MangaShowcase.svelte';
    let meta;
    obj.subscribe(value => { meta=value;});
    let cdncdn=meta['0'].cdn;
    let cdncdn1=meta['0'].cdn1;
    let y=[]
    let match=$page.params.slug
    
    </script>
    <div style="margin-top:20px;font-weight: bold;font-size: 2rem;">{match} Manga</div>
    <MangaShowcase fixed_filter_name="Status" fixed_filter_value={match} cdncdn={cdncdn} cdncdn1={cdncdn1}/>
   
    <svelte:head>
    <title>{match} Archives - Bilingual Manga</title>
    {@html meta[0].inhtml['metades']}
    </svelte:head>
    
    <style></style>