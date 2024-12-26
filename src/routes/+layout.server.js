import db from "$lib/db"
import ip from "ip"
import { DEFAULT_USER_ID } from "$lib/UserDataTools.js"
import { getUserData, getMetadata } from "$lib/collections.js"

/** @type {import('./$types').LayoutServerLoad} */
export async function load(event) 
{

    let xreq=await event.request.headers.get('x-requested-with')

    let jsonc = await getMetadata(DEFAULT_USER_ID, 0,10000) // TODO
    let user_data = await getUserData(DEFAULT_USER_ID)

    jsonc[0].user_data = user_data
    jsonc[0].cdn1=jsonc[0].cdn1.replace("localhost",ip.address())
    jsonc[0].ipfsgate1=jsonc[0].ipfsgate1.replace("localhost",ip.address())
     if(true)
     {
      jsonc[0].inhtml["ad-sp"]=""
      jsonc[0].inhtml["ad-up"]=""
      jsonc[0].inhtml["ad-down"]=""
      jsonc[0].inhtml["tracker"]="" 
    }

    for (let meta_data of jsonc[0]['manga_titles']) {
        let id = meta_data['enid']
        if (user_data['favourites'].includes(id)) {
            meta_data["favourite"] = true;
        } else {
            meta_data["favourite"] = false;
        }
    }

    jsonc = JSON.parse(JSON.stringify(jsonc));

     return {'metadata':jsonc};
     
   }
   

