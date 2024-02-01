<script>
    import {obj} from '$lib/store.js';
    import {onMount} from 'svelte'
    import MangaSortDashboard from '$lib/MangaSortDashboard.svelte';
    import { sort_options, sortManga } from '$lib/MangaSorter.js';

    const hide_sort_columns = ['Newly added','Rating','Volumes'];

    onMount(dwdata)
    let meta;
    obj.subscribe(value => { meta=value;});

    let sort_criteria='Newly added';
    let sort_reverse=false;
    let sx;

    $: {
        console.log("sorted");
        sx = sortManga(meta['0'].manga_titles, sort_criteria, sort_reverse);
        dwdata();
    }

    sx = sortManga(meta['0'].manga_titles, sort_criteria, sort_reverse);
    
    $: x12 = sx; //meta['0'].manga_titles;
    //$: x12 = x11.slice().reverse()
    let cdncdn1=meta['0'].cdn1;


    let lan="JPN"
    function clic()
    {
        if(lan==="JPN")
        {
            lan="ENG"
        }
        else if(lan === "ENG")
        {
            lan="JPN"
        }
    }
    cdncdn1
    let chk={}
    function chkclr(chk,xa=true)
    {
        for(let chel in chk)
        {
            if(chk[chel])
            {
                if(xa)
                {document.getElementById(`#s${chel}`).style.color="green"}
                else
                {document.getElementById(`#s${chel}`).style.color="white"}
            }
        }
    }
    function getSelectedChapterIds() {
        let chapters = [];
        for (let idx in chk) {
            if (chk[idx]) {
                chapters.push(x12[idx].enid);
            }
        }
        return chapters;
    }
    function downloadSelected()
    {
        fetch(`${cdncdn1}/download`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(getSelectedChapterIds())}).then( (response) => {let aaafdfv = response;}).then(()=>{chkclr(chk);refr1();dwdata();});
        
    }
    function deleteSelected()
    {
        fetch(`${cdncdn1}/remove`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(getSelectedChapterIds())}).then( (response) => {let aaafdfv = response;}).then(()=>{chkclr(chk,false);refr1();});
    }

    function dwdata()
    {
        fetch(`${cdncdn1}/json/dw.json`)
        .then(response => response.json())
	    .then((data3)=>{
            let pmd = data3["pm"]
            for(let xx in x12)
            {   if(pmd.includes(x12[xx].enid))
                {
                    document.getElementById(`#s${xx}`).style.color="green"
                }

            }
        })
        .catch(err => {console.log(err);})
    }

    function refr1()
    {
        for(let elm in chk)
        {
            chk[elm]=false
        }
    }

    function refr()
    {
        for(let elm in chk)
        {
            chk[elm]=false
            document.getElementById(`#s${elm}`).style.color="white"
        }
        dwdata()
    }

    function sela()
    {
        for(let i in x12)
        {
            chk[`${i}`]=true
        }
    }
    function seld()
    {
        fetch(`${cdncdn1}/json/dw.json`)
        .then(response => response.json())
	    .then((data3)=>{
            let pmd = data3["pm"]
            for(let xx in x12)
            {   if(pmd.includes(x12[xx].enid))
                {
                    chk[`${xx}`]=true
                }

            }
        })
        .catch(err => {console.log(err);})
    }
    function seldu()
    {
        fetch(`${cdncdn1}/json/dw.json`)
        .then(response => response.json())
	    .then((data3)=>{
            let pmd = data3["pm"]
            for(let xx in x12)
            {   if(pmd.includes(x12[xx].enid))
                {
                    chk[`${xx}`]=false
                }

            }
        })
        .catch(err => {console.log(err);})
    }

    const sortCriteriaChanged = (e) => {
        sort_criteria = e.detail;
        console.log("sortcriteria " + sort_criteria)
    };

    const sortReverseChanged = (e) => {
        sort_reverse = e.detail;
    };

</script>
<div class="header">

<div class="header_buttons">
    <button on:click={clic}>{lan}</button>
    <button on:click={downloadSelected}>Download</button>
    <button on:click={deleteSelected}>Delete Manga</button>
    <button on:click={sela}>Select All</button>
    <button on:click={refr}>unSelect All</button>
    <button on:click={seld}>Select Downloaded</button>
    <button on:click={seldu}>unSelect Downloaded</button>
    <MangaSortDashboard {sort_criteria} {sort_reverse} 
        sort_criteria_list={Object.keys(sort_options)} 
        on:SortCriteriaChanged={sortCriteriaChanged}
        on:SortReverseChanged={sortReverseChanged}
    />
</div>
<div class="header_list">
    <div>Sel</div>
    <div>Name</div>
    <div>{#if !hide_sort_columns.includes(sort_criteria)}{sort_criteria}{/if}</div>
    <div>Rating</div>
    <div>Vols.</div>
</div>
</div>
<div style="text-align: left;font-size:15pt; font-weight:550">
<ol class="manga-list">
{#key x12}

    {#each x12 as name,index}
    <div class="list-item" id=#s{index}>
    {#if lan==="JPN"}
    <div id=#d{index}>
        <li><input id=#{index} type=checkbox bind:checked={chk[`${index}`]} on:change={()=>{if(chk[`${index}`]){document.getElementById(`#s${index}`).style.color="yellow"}else{document.getElementById(`#s${index}`).style.color="white";dwdata()}}}></li>
    </div>
    <div>{name.entit}</div>
    {/if}
    {#if lan==="ENG"}
    <div id=#d{index}>
        <li><input id=#{index} type=checkbox bind:checked={chk[`${index}`]} on:change={()=>{if(chk[`${index}`]){document.getElementById(`#s${index}`).style.color="yellow"}else{document.getElementById(`#s${index}`).style.color="white";dwdata()}}}></li>
    </div>
    <div>{name.jptit}</div>
    {/if}
    <div>{#if !hide_sort_columns.includes(sort_criteria)}{name.sort_value}{/if}</div>
    <div>{name.rating_data.rating} ({name.rating_data.votes})</div>
    <div>{name.num_volumes}</div>
    </div>

    {/each}
{/key}
</ol>
</div>

<style>
    .header {
        top:0;
        position:sticky;
    }
    .header_buttons {
        padding:1px;
        font-size: 1.15rem;
        background:#333;
        text-align: center;
        display: flex;
        padding-left: 20px;
    }
    .header_list {
        background:#666;
        display: grid;
        grid-template-columns:  0.2fr 4fr 0.5fr 0.6fr 0.5fr;
        grid-gap: 5px;
        text-align: left;
        margin:0px;
        padding:3px;
        padding-left: 70px;
    }
    .list-item {
        display: grid;
        grid-template-columns:  0.2fr 4fr 0.5fr 0.6fr 0.5fr;
        grid-gap: 5px;
        text-align: left;
        margin:1px;
        padding: 0px;
        padding-left: 70px;
    }
    .list-item:nth-child(odd) {
        background: #333;
    }
    .manga-list {
        margin:0px;
        padding:0px;

    }

    button {
        font-family: Arial, Helvetica,'Noto Sans Symbols 2',sans-serif;
        color: whitesmoke;
        background:#444;
        padding: 0px;
        padding-left: 10px;
        padding-right: 10px;
        margin-right: 15px;
        border-radius: 5px;
        font-size: 0.9rem;
        border-style:hidden;
    }
    button:hover {
        background:#666;
    }
    

 
</style>