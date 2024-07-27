<script>
	import { onMount } from 'svelte';
	
    export let chaptersen;
    export let chaptersjp;
    export let vj;
    export let jjj;
    export let vi;
    export let iii;
    export let change;
    export let indicator;
    export let allquerys;
    export let refresh;
    export let volumesjp;
    export let volumesen;
    export let sli1;
    export let sli2;

	export let edit_mode;
    export let night_mode;
    export let auto_scroll;
    export let jp_scroll_pct;
    export let en_scroll_pct;

    onMount(() => {
        allst();
    });
	

	const handleKeydown=(e)=>{
		if (!edit_mode) {
			let key = e.key;
			if(key=="l")
			{
				change()
            } else if (key == 'n') {
                night_mode = !night_mode;
                setfunc();
			}
		}
	}


const allst=()=>{
	if(localStorage.getItem("night_mode")!=null)
	{night_mode=localStorage.getItem("night_mode")==="false"?false:true;}
	else
	{night_mode=false;}	

	if(localStorage.getItem("auto_scroll")!=null)
	{auto_scroll=localStorage.getItem("auto_scroll")==="false"?false:true;}
	else
	{auto_scroll=false;}	
}

const setfunc=()=>{
	localStorage.setItem("night_mode", night_mode);
	localStorage.setItem("auto_scroll", auto_scroll);
}


</script>
<svelte:window on:keydown={handleKeydown}/>

<div id="slider" >
	<input type=checkbox bind:checked={night_mode} on:change={setfunc}>Night mode
	<input type=checkbox bind:checked={auto_scroll} on:change={setfunc}>Auto scroll
	<div id="jpslider">
        <button on:click={()=>{indicator.b=2;indicator.d=true;allquerys();refresh();}}>❮❮❮</button><button on:click={()=>{indicator.b=1;indicator.d=true;allquerys();refresh();}}>❯❯❯</button>
        <span>JP</span>
        <select id='volumejp' bind:value={vj}>
            <option value="" disabled selected>Volumes</option>
            <option value="" disabled selected>----------</option>
            {#each  Object.keys(volumesjp) as vol_n1,volj}
            <option value={volj}>{vol_n1}</option>  
            {/each}
        </select>

        <select id="selectjp" bind:value={jjj} on:change={sli1} >
            <option value="" disabled selected>Chapters</option>
            {#each chaptersjp as chapter_n1,jjjj}
            {#if (volumesjp[Object.keys(volumesjp)[vj]].s<=jjjj&&volumesjp[Object.keys(volumesjp)[vj]].e>=jjjj)}
            <option value="" disabled selected>----------</option>
            <option value={jjjj}>{chapter_n1}</option> 
            {:else}
            <option value={jjjj}  hidden>{chapter_n1}</option> 
            {/if}
            {/each}
        </select>
        <span>{jp_scroll_pct.toFixed(1)}%</span>
    </div>
    <div id="enslider">
        <div style="display: flexbox;">
            <button on:click={()=>{indicator.a=2;indicator.c=true;allquerys();refresh();}}>❮❮❮</button><button on:click={()=>{indicator.a=1;indicator.c=true;allquerys();refresh();}}>❯❯❯</button>
            <span>ENG</span>

            <select id='volumeen' bind:value={vi}>
                <option value="" disabled selected>Volumes</option>
                <option value="" disabled selected>----------</option>
                {#each  Object.keys(volumesen) as vol_n,voli}
                <option value={voli}>{vol_n}</option>  
                {/each}
            </select>

            <select id="selecten" bind:value={iii} on:change={sli2} >
                <option value="" disabled selected>Chapters</option>
                {#each chaptersen as chapter_n,ii}
                {#if (volumesen[Object.keys(volumesen)[vi]].s<=ii&&volumesen[Object.keys(volumesen)[vi]].e>=ii)}
                <option value="" disabled selected>----------</option>
                <option value={ii}>{chapter_n}</option>  
                {:else}
                <option value={ii}  hidden>{chapter_n}</option> 
                {/if}
                {/each}
            </select>
            <span>{en_scroll_pct.toFixed(1)}%</span>
        </div>
    </div>
</div> 
<style>

#slider
	{
		margin:auto;

		text-align: center;
		width:95vw;
		font-size:auto;

	}

#jpslider{

	margin-left:1vw;margin-right:1vw;
}
#enslider{
	margin-left:1vw;margin-right:1vw;
}


#selecten{
	max-width: 60vw;

}
#selectjp{
	max-width: 60vw;

}
#volumeen{
	max-width: 60vw;

}
#volumejp{
	max-width: 60vw;

}

</style>