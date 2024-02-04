<script>
    import {obj} from '$lib/store.js';
    import {onMount} from 'svelte'
    import MangaSortDashboard from '$lib/MangaSortDashboard.svelte';
    import { sort_options, sortManga } from '$lib/MangaSorter.js';
    import DownloadLog from '$lib/DownloadLog.svelte';
    import Modal from '$lib/Modal.svelte';

    // Repository status
    const STATUS_DOWNLOADED = 'Downloaded';
    const STATUS_INCOMPLETE = 'Incomplete';
    const STATUS_ARCHIVED = 'Archived';
    const STATUS_NOT_DL = 'Not downloaded';

    // Process status
    const STATUS_DOWNLOADING = 'Downloading';
    const STATUS_CHECKING = 'Checking';
    const STATUS_ARCHIVING = 'Archiving';
    const STATUS_QUEUED = 'Queued';
    const STATUS_ERROR = 'Error';
    const STATUS_NONE = '';
    const STATUS_SELECTED = 'Selected';

    const list_item_colors = {
        [STATUS_DOWNLOADED] : 'ForestGreen',
        [STATUS_ARCHIVING] : 'violet',
        [STATUS_DOWNLOADING] : 'CornflowerBlue',
        [STATUS_INCOMPLETE] : 'pink',
        [STATUS_ARCHIVED] : '#b0b',
        [STATUS_ERROR] : 'crimson',
        [STATUS_CHECKING] : 'orange',
        [STATUS_QUEUED] : 'grey',
        [STATUS_SELECTED] : 'yellow',
    };

    const hide_sort_columns = ['Newly added','Rating','Volumes','Repository status'];

    let events;
    let meta;
    obj.subscribe(value => { meta=value;});

    let showErrorModal = false;

    let sort_criteria='Newly added';
    let sort_reverse=false;
    
    let manga_repo_status={};
    let manga_repo_labels={};
    let manga_process_status={};
    let process_status={'status':0};
    let log_file_paths={};
    let manga_archived=[];

    let list_colors = [];

    $: x12 = sortManga(meta['0'].manga_titles, sort_criteria, sort_reverse);
    $: colorizeList(x12);

    function getMangaColor(status) {
        let color = 'white';
        if (status in list_item_colors) {
            color = list_item_colors[status];
        } else {
            for (let s of Object.keys(list_item_colors)) {
                if (status.includes(s)) { // status is 'Downloading xx/yy'
                   return list_item_colors[s];
                }
            }
        }
        return color;
    }

    function colorizeItem(item, color) {
        document.getElementById(`#s${item}`).style.color  = color;
    }

    function colorizeList(manga_list) {
        for(let xx in manga_list) {
            let manga_id = manga_list[xx].enid;
            if (manga_id in manga_repo_labels) {
                let status = manga_repo_labels[manga_id];

                if (manga_id in manga_process_status) {
                    status = manga_process_status[manga_id];
                }
                list_colors[xx] = getMangaColor(status);
            }
        }
    }

    let cdncdn1=meta['0'].cdn1;

    let errorMessage = '';
    function showErrorMessage(msg) {
        errorMessage=msg;
        showErrorModal=true;
    }

    onMount( () => {

        events = new EventSource('http://localhost:3300/events');
        events.onmessage = (event) => {
            const parsedData = JSON.parse(event.data);
            manga_repo_status = parsedData.manga_repo_status; 
            manga_process_status = parsedData.manga_process_status;
            process_status = parsedData.process_status;
            log_file_paths = parsedData.log_files;
            manga_archived = parsedData.manga_archived;

            if (process_status.status=='Error') {
                showErrorMessage(process_status.msg);
                process_status.status='';
                process_status.msg='';
            }

            // augment metadata with repo status for sorting
            $obj['0'].manga_titles.forEach(element => {
                let id = element.enid;

                if (id in manga_repo_status) {
                    manga_repo_labels[id] = manga_repo_status[id];
                    if (manga_archived.indexOf(id) != -1) {
                        if (manga_repo_status[id] == STATUS_NOT_DL) {
                            manga_repo_labels[id] = STATUS_ARCHIVED;
                        } else {
                            manga_repo_labels[id] += " " + STATUS_ARCHIVED;
                        }
                    }
                    element["repo_status"] = manga_repo_labels[id];
                } else {
                    element["repo_status"] = '';
                    manga_repo_labels[id] = '';
                }
            });
            colorizeList(x12);
        };
    });


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
    function getSelectedChapterIds() {
        let chapters = [];
        for (let idx in chk) {
            if (chk[idx]) {
                chapters.push(x12[idx].enid);
            }
        }
        return chapters;
    }
    function checkSelected()
    {
        fetch(`${cdncdn1}/check`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(getSelectedChapterIds())}).then( (response) => {let aaafdfv = response;}).then(()=>{});
        
    }
    function archiveSelected()
    {
        fetch(`${cdncdn1}/archive`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(getSelectedChapterIds())}).then( (response) => {let aaafdfv = response;}).then(()=>{});
        
    }
    function downloadSelected()
    {
        fetch(`${cdncdn1}/download`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(getSelectedChapterIds())}).then( (response) => {let aaafdfv = response;}).then(()=>{});
        
    }
    function stopProcess()
    {
        fetch(`${cdncdn1}/stop`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: ''}).then( (response) => {let aaafdfv = response;}).then(()=>{});
    }
    function deleteSelected()
    {
        fetch(`${cdncdn1}/remove`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(getSelectedChapterIds())}).then( (response) => {let aaafdfv = response;}).then(()=>{});
    }
    function unSelectAll()
    {
        for(let elm in chk)
        {
            chk[elm]=false
        }
    }
    function selectAll()
    {
        for(let i in x12)
        {
            chk[`${i}`]=true
        }
    }
    function selectDownloaded()
    {
        for(let xx in x12)
        {   if(manga_repo_status[x12[xx].enid]==STATUS_DOWNLOADED)
            {
                chk[`${xx}`]=true
            }
        }
    }
    function unSelectDownloaded()
    {
        for(let xx in x12)
        {   if(manga_repo_status[x12[xx].enid]==STATUS_DOWNLOADED)
            {
                chk[`${xx}`]=false
            }
        }
    }
    const sortCriteriaChanged = (e) => {
        sort_criteria = e.detail;
        console.log("sortcriteria " + sort_criteria)
    };
    const sortReverseChanged = (e) => {
        sort_reverse = e.detail;
    };

</script>


<Modal bind:showModal={showErrorModal}>
	<h4 slot="header">
	    	Error
	</h4>    
    <div>{errorMessage}</div>
</Modal>

<div class="header">

<div class="header_buttons">
    <button on:click={clic}>{lan}</button>
    {#if process_status.status!=STATUS_DOWNLOADING}
        <button disabled={process_status.status!=''} on:click={downloadSelected}>Download</button>
    {:else}
        <button on:click={stopProcess}>Stop</button>
    {/if}
    <button disabled={process_status.status!=''} on:click={checkSelected}>Check</button>
    {#if process_status.status!=STATUS_ARCHIVING}
        <button disabled={process_status.status!=''} on:click={archiveSelected}>Archive</button>
    {:else}
        <button on:click={stopProcess}>Stop</button>
    {/if}
    <button disabled={process_status.status!=''} class="danger" on:click={deleteSelected}>Delete Manga</button>
    <button on:click={selectAll}>Select All</button>
    <button on:click={unSelectAll}>unSelect All</button>
    <button on:click={selectDownloaded}>Select DL'd</button>
    <button on:click={unSelectDownloaded}>unSelect DL'd</button>
    <MangaSortDashboard {sort_criteria} {sort_reverse} 
        sort_criteria_list={Object.keys(sort_options)} 
        on:SortCriteriaChanged={sortCriteriaChanged}
        on:SortReverseChanged={sortReverseChanged}
        show_repo_status=true
    />
</div>
<div class="header_list">
    <div>Sel</div>
    <div>Name</div>
    <div>{#if !hide_sort_columns.includes(sort_criteria)}{sort_criteria}{/if}</div>
    <div>Rating</div>
    <div>Vols.</div>
    <div>{#if process_status.status != ''}{process_status.msg}{:else}Repository Status{/if}</div>
</div>
</div>
<div>
<ol class="manga-list">
{#key x12}

    {#each x12 as manga,index}
    <div class="list-item" style="color:{list_colors[index]}" id=#s{index}>
    <div id=#d{index}>
        <li><input id=#{index} type=checkbox bind:checked={chk[`${index}`]} on:change={()=>{if(chk[`${index}`]){colorizeItem(index,getMangaColor(STATUS_SELECTED))}else{colorizeItem(index,list_colors[index])}}}></li>
    </div>
    {#if lan==="JPN"}
    <div>{manga.entit}</div>
    {/if}
    {#if lan==="ENG"}
    <div>{manga.jptit}</div>
    {/if}
    <div>{#if !hide_sort_columns.includes(sort_criteria)}{manga.sort_value}{/if}</div>
    <div>{manga.rating_data.rating} ({manga.rating_data.votes})</div>
    <div>{manga.num_volumes}</div>
    <div>
        {#if manga.enid in manga_process_status}{manga_process_status[manga.enid]}{:else}{manga_repo_labels[manga.enid]??''}{/if}
        {#if manga.enid in log_file_paths}
        <DownloadLog {cdncdn1} manga_id={manga.enid}/>
        {/if}
    </div>
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
        grid-template-columns:  0.2fr 3fr 0.5fr 0.6fr 0.2fr 1fr;
        grid-gap: 5px;
        text-align: left;
        margin:0px;
        padding:3px;
        padding-left: 70px;
    }
    .list-item {
        display: grid;
        grid-template-columns:  0.2fr 3fr 0.5fr 0.6fr 0.2fr 1fr;
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
        text-align: left;
        font-size:14pt;
        font-weight:550;
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
    button:disabled {
        color: #777;
    }
    button:hover:enabled {
        background:#666;
    }
    .danger {
        background-color: crimson;
    }
</style>