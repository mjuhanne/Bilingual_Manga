import fetch from 'node-fetch'
const response = await fetch('http://localhost:3300/json/admin.manga_metadata.json')
const a = await response.json()
const response1 = await fetch('http://localhost:3300/json/admin.manga_data.json')
const b = await response1.json()
const response2 = await fetch('http://localhost:3300/json/ratings.json')
const c = await response2.json()
const admin={"manga_metadata":a,"manga_data":b,"ratings":c}
export default admin
