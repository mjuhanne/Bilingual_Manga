<script>
    import {obj} from '$lib/store.js';
    import { page } from '$app/stores';
    import MangaShowcase from '$lib/MangaShowcase.svelte';
    let meta;
    obj.subscribe(value => { meta=value;});
    let cdncdn=meta['0'].cdn;
    let cdncdn1=meta['0'].cdn1;
    
    </script>
    <div style="margin-top:20px;font-weight: bold;font-size: 2rem;">Favourite Manga</div>
    <MangaShowcase fixed_filter_name="Favourite" fixed_filter_value={true} cdncdn={cdncdn} cdncdn1={cdncdn1}/>
   
    <svelte:head>
    <title>Favourites - Bilingual Manga</title>
    {@html meta[0].inhtml['metades']}
    </svelte:head>
    <style></style>