<script>
    import {obj} from '$lib/store.js';
    import { page } from '$app/stores';
    import { goto } from "$app/navigation";
    import {onMount} from 'svelte'
    import MangaSortDashboard from '$lib/MangaSortDashboard.svelte';
    import { download_view_sort_options, sortManga } from '$lib/MangaSorter.js';
    import DownloadLog from '$lib/DownloadLog.svelte';
    import Modal from '$lib/Modal.svelte';

    // Repository status
    const STATUS_DOWNLOADED = 'Downloaded';
    const STATUS_INCOMPLETE = 'Incomplete';
    const STATUS_ARCHIVED = 'Archived';
    const STATUS_ARCHIVE_INCOMPLETE = 'Archive incomplete';
    const STATUS_NOT_DL = 'Not downloaded';

    // Process status
    const STATUS_DOWNLOADING = 'Downloading';
    const STATUS_VERIFYING_ARCHIVE = 'Verifying archive';
    const STATUS_CHECKING = 'Checking';
    const STATUS_ARCHIVING = 'Archiving';
    const STATUS_RESTORING = 'Restoring';
    const STATUS_REMOVING = 'Removing';
    const STATUS_QUEUED = 'Queued';
    const STATUS_ERROR = 'Error';
    const STATUS_NONE = '';
    const STATUS_SELECTED = 'Selected';

    const list_item_colors = {
        [STATUS_ARCHIVE_INCOMPLETE] : '#AF601A',
        [STATUS_DOWNLOADED] : 'ForestGreen',
        [STATUS_ARCHIVING] : 'violet',
        [STATUS_RESTORING] : 'violet',
        [STATUS_DOWNLOADING] : 'CornflowerBlue',
        [STATUS_INCOMPLETE] : '#EC7063',
        [STATUS_ARCHIVED] : '#b0b',
        [STATUS_REMOVING] : 'red',
        [STATUS_ERROR] : 'crimson',
        [STATUS_VERIFYING_ARCHIVE] : 'orange',
        [STATUS_CHECKING] : 'orange',
        [STATUS_QUEUED] : 'grey',
        [STATUS_SELECTED] : 'yellow',
    };

    // Prevent double column insertion when sorting based on these values 
    const hide_sort_columns = ['A-Z','Newly added','Rating','Volumes','Repository status'];

    let events;
    let meta;
    let meta_by_id = {};

    obj.subscribe(value => { 
        meta=value;
        if ('0' in meta) {
            let manga_titles = meta[0].manga_titles;
            for(let xx in manga_titles) {
                let id = manga_titles[xx].enid;
                meta_by_id[id] = manga_titles[xx];
            }
        }
    });

    let showErrorModal = false;

    let sort_criteria=$page.url.searchParams.get('sort');
    if (sort_criteria === null) {
        sort_criteria = 'Repository status';
    }
    let sort_reverse=$page.url.searchParams.get('reverse') == "true" ? true : false;

    let manga_repo_status={};
    let manga_repo_labels={};
    let manga_process_status={};
    let process_status={'status':0};
    let log_file_paths={};
    let manga_archived=[];

    let list_colors = [];

    let x12 = [];

    $: {
        if (Object.keys(manga_repo_status).length>0) {
            // wait until valid repo status is available
            x12 = sortManga(meta['0'].manga_titles, sort_criteria, sort_reverse);
            console.log(`sorted '${sort_criteria}'`);
            console.log("first is " + x12[0].entit);
        }
    }
    $: colorizeList(x12, selected_manga_ids);

    function getMangaColor(manga_id) {
        let color = 'white';
        let status = '';
        if (manga_id in manga_repo_labels) {
            status = manga_repo_labels[manga_id];
        }
        if (manga_id in manga_process_status) {
            status = manga_process_status[manga_id];
        }
        if (selected_manga_ids.includes(manga_id)) {
            status = STATUS_SELECTED;
        }

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

    function colorizeItem(manga_id) {
        for(let xx in x12) {
            let id = x12[xx].enid;
            if (id == manga_id) {
                list_colors[xx] = getMangaColor(manga_id);
            }
        }
    }

    function colorizeList(manga_list, selected_manga_ids) {
        for(let xx in manga_list) {
            let manga_id = manga_list[xx].enid;
            //if (manga_id in manga_repo_labels) {
                list_colors[xx] = getMangaColor(manga_id);
            //}
        }
    }

    let cdncdn1=meta['0'].cdn1;

    let errorMessageHeader;
    let errorMessage;
    function showErrorMessage(manga_id,msg) {
        errorMessageHeader=`Error processing ${meta_by_id[manga_id].entit}`;
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
            let manga_archive_incomplete = parsedData.manga_archive_incomplete;

            if (process_status.status=='Error') {
                showErrorMessage(process_status.id, process_status.msg);
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
                    } else if (manga_archive_incomplete.indexOf(id) != -1) {
                        if (manga_repo_status[id] == STATUS_NOT_DL) {
                            manga_repo_labels[id] = STATUS_ARCHIVE_INCOMPLETE;
                        } else {
                            manga_repo_labels[id] += " " + STATUS_ARCHIVE_INCOMPLETE;
                        }
                    }
                    element["repo_status"] = manga_repo_labels[id];
                } else {
                    element["repo_status"] = '';
                    manga_repo_labels[id] = '';
                }
            });
            colorizeList(x12, selected_manga_ids);
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
    let selected_manga_ids=[];

    $: console.log(selected_manga_ids);

    function checkSelected()
    {
        fetch(`${cdncdn1}/check`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(selected_manga_ids)}).then( (response) => {let aaafdfv = response;}).then(()=>{});
        unSelectAll();
    }
    function archiveSelected()
    {
        fetch(`${cdncdn1}/archive`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(selected_manga_ids)}).then( (response) => {let aaafdfv = response;}).then(()=>{});
        unSelectAll();
    }
    function restoreSelected()
    {
        fetch(`${cdncdn1}/restore`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(selected_manga_ids)}).then( (response) => {let aaafdfv = response;}).then(()=>{});
        unSelectAll();
    }
    function downloadSelected()
    {
        fetch(`${cdncdn1}/download`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(selected_manga_ids)}).then( (response) => {let aaafdfv = response;}).then(()=>{});
        unSelectAll();
    }
    function stopProcess()
    {
        fetch(`${cdncdn1}/stop`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: ''}).then( (response) => {let aaafdfv = response;}).then(()=>{});
    }
    function deleteSelected()
    {
        fetch(`${cdncdn1}/remove`, { method: "post",headers: {'Accept': 'application/json','Content-Type': 'application/json'},body: JSON.stringify(selected_manga_ids)}).then( (response) => {let aaafdfv = response;}).then(()=>{});
        unSelectAll();
    }
    function unSelectAll()
    {
        selected_manga_ids = [];
    }
    function selectAll()
    {
        selected_manga_ids = [];
        for(let i in x12)
        {
            selected_manga_ids.push(x12[i].enid);
        }
    }
    function selectDownloaded()
    {
        for(let xx in x12)
        {
            let id = x12[xx].enid;
            if(manga_repo_status[id]==STATUS_DOWNLOADED)
            {
                if (!selected_manga_ids.includes(id)) {
                    selected_manga_ids.push(id);
                }
            }
        }
        selected_manga_ids = selected_manga_ids; // force update
    }
    function unSelectDownloaded()
    {
        for(let xx in x12)
        {
            let manga_id = x12[xx].enid;
            if(manga_repo_status[manga_id]==STATUS_DOWNLOADED)
            {
                selected_manga_ids = selected_manga_ids.filter( (id) => (id != manga_id));
            }
        }
        selected_manga_ids = selected_manga_ids;
    }
    function selectArchived()
    {
        for(let xx in x12)
        {
            let id = x12[xx].enid;
            if(manga_repo_labels[id].includes(STATUS_ARCHIVED))
            {
                if (!selected_manga_ids.includes(id)) {
                    selected_manga_ids.push(id);
                }
            }
        }
        selected_manga_ids = selected_manga_ids; // force update
    }
    function unSelectArchived()
    {
        for(let xx in x12)
        {
            let manga_id = x12[xx].enid;
            if(manga_repo_labels[manga_id].includes(STATUS_ARCHIVED))
            {
                selected_manga_ids = selected_manga_ids.filter( (id) => (id != manga_id));
            }
        }
        selected_manga_ids = selected_manga_ids;
    }
    const sortCriteriaChanged = (e) => {
        sort_criteria = e.detail;
        console.log("sortcriteria " + sort_criteria)
		$page.url.searchParams.set('sort',sort_criteria);
        goto(`?${$page.url.searchParams.toString()}`);
    };
    const sortReverseChanged = (e) => {
        sort_reverse = e.detail;
		$page.url.searchParams.set('reverse',sort_reverse);
        goto(`?${$page.url.searchParams.toString()}`);
    };
    function onMangaSelected(index, manga_id) {
        console.log("changed");
        let selected = selected_manga_ids.includes(manga_id);
        if (selected) {
            selected_manga_ids = selected_manga_ids.filter( (id) => (id != manga_id));
        } else {
            selected_manga_ids.push(manga_id);
        }
        selected_manga_ids = selected_manga_ids;
        colorizeItem(manga_id);
    }

</script>

<Modal bind:showModal={showErrorModal}>
	<h4 slot="header">
	    	{errorMessageHeader}
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
    {#if process_status.status!=STATUS_CHECKING}
        <button disabled={process_status.status!=''} on:click={checkSelected}>Check</button>
    {:else}
        <button on:click={stopProcess}>Stop</button>
    {/if}
    {#if process_status.status!=STATUS_ARCHIVING}
        <button disabled={process_status.status!=''} on:click={archiveSelected}>Archive</button>
    {:else}
        <button on:click={stopProcess}>Stop</button>
    {/if}
    {#if process_status.status!=STATUS_RESTORING}
        <button disabled={process_status.status!=''} on:click={restoreSelected}>Restore</button>
    {:else}
        <button on:click={stopProcess}>Stop</button>
    {/if}
    {#if process_status.status!=STATUS_REMOVING}
        <button disabled={process_status.status!=''} class="danger" on:click={deleteSelected}>Delete Manga</button>
    {:else}
        <button on:click={stopProcess}>Stop</button>
    {/if}
    <button on:click={selectAll}>Sel All</button>
    <button on:click={unSelectAll}>unSel All</button>
    <button on:click={selectDownloaded}>Sel DL'd</button>
    <button on:click={unSelectDownloaded}>unSel DL'd</button>
    <button on:click={selectArchived}>Sel Arch</button>
    <button on:click={unSelectArchived}>unSel Arch</button>
    <MangaSortDashboard {sort_criteria} {sort_reverse} 
        sort_criteria_list={Object.keys(download_view_sort_options)} 
        on:SortCriteriaChanged={sortCriteriaChanged}
        on:SortReverseChanged={sortReverseChanged}
        width='380'
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
        <li><input id=#{index} type=checkbox checked={selected_manga_ids.includes(manga.enid)} on:change={onMangaSelected(index, manga.enid)}/></li>
    </div>
    {#if lan==="JPN"}
    <div><a href="/manga/{manga.enid}?lang=en" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">{manga.entit}</a></div>
    {/if}
    {#if lan==="ENG"}
    <div><a href="/manga/{manga.enid}?lang=en" data-sveltekit:prefetch target="_top" rel="noopener noreferrer">{manga.jptit}</a></div>
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
        padding-left: 5px;
        padding-right: 5px;
        margin-right: 5px;
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
    a {
        text-decoration: none;
        color: inherit;
    }
    a:hover {
        text-decoration: underline;
    }

</style>