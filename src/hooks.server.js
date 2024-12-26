import { connect } from '$lib/mongo.js';

// Connect to MongoDB before starting the server
connect().then(() => {
    console.log("MongoDB started");
}).catch((e) => {
    console.log("MongoDB failed to start");
    console.log(e);
});

/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
  console.log("hooks.server.js " + event.url.pathname);
  if (event.url.pathname.startsWith('/custom')) {
    return new Response('custom response');
  }
 
  const response = await resolve(event);
  return response;
}


