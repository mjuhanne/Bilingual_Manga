<script>
    import {onMount} from 'svelte'
    import { invalidateAll } from '$app/navigation';
    import { EVENT_TYPE } from "$lib/UserDataTools.js";
    export let meta;

    let eventSource;
    let status_msg = (meta.analysis.status == "up_to_date" ? 'Up to date (Force update)' : 'Update')

    onMount( () => {
        eventSource = new EventSource('/user_data');
        eventSource.onmessage = (event) => {
            const parsedData = JSON.parse(event.data);
            let event_type = parsedData.event_type;
            if (event_type == EVENT_TYPE.UPDATING_ANALYSIS) {
                status_msg = "Updating";
            } else if (event_type == EVENT_TYPE.UPDATED_ANALYSIS) {
                status_msg = "Up to date";
                invalidateAll();
            } else if (event_type== EVENT_TYPE.ANALYSIS_WARNING) {
                alert(`${parsedData.msg}`)
            } else if (event_type== EVENT_TYPE.ANALYSIS_ERROR) {
                status_msg = "Error while updating"
                alert(`Error: ${parsedData.msg}`)
            } else if (event_type== EVENT_TYPE.ANALYSIS_PROGRESS) {
                status_msg = parsedData.msg;
            } else if (event_type == EVENT_TYPE.CONNECTED) {
            }
        };
        eventSource.onerror = (event) => {
            console.log("error: " + JSON.stringify(event));
        };
        return () => {
            if (eventSource.readyState === 1) {
                eventSource.close();
            }
        };
    });



async function handleUpdateButtonClick(event) {

    const response = await fetch( "/user_data", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: JSON.stringify({'func' : 'update_custom_language_analysis_for_title', 'title_id' : meta._id })
    });
    meta.analysis.status = "stale";
}
</script>

Analysis done on {new Date(meta.analysis.series.custom_lang_analysis_metadata.timestamp)}
<button class:updated={meta.analysis.status == "up_to_date"} on:click={handleUpdateButtonClick}>{status_msg}</button>

<style>
button{
    display: inline-block;
    text-decoration: none;
    padding:7px;
    margin: 5px 5px;
    color: whitesmoke;
    background: rgba(210, 29, 255, 0.5);
    border-radius:5px;
    border: 2px solid black;
    font-family: Arial, Helvetica,'Noto Sans Symbols 2',sans-serif;
}

button:hover {
   background: rgba(227, 112, 250, 0.5);
}

.updated:hover {
  background-color:rgba(209, 248, 233, 0.5);
}

.updated {
    background: rgba(1, 253, 199, 0.5);
}
</style>
