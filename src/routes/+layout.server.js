import ip from "ip"
import { DEFAULT_USER_ID } from "$lib/UserDataTools.js"
import { getUserData, getMetadata } from "$lib/collections.js"

/** @type {import('./$types').LayoutServerLoad} */
export async function load(event) 
{
    let xreq=await event.request.headers.get('x-requested-with')
    let jsonc = await getMetadata(DEFAULT_USER_ID)
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

    jsonc = JSON.parse(JSON.stringify(jsonc));

     return {'metadata':jsonc};
   }
   

