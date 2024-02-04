
import cors from "cors"
import { initRepository, fetchCoverImages, downloadMangas, stopProcess, archiveMangas, removeMangas, checkRepository, getStatus, getDownloadLog } from "./repository.js";

import express from "express"
import { fileURLToPath } from 'url';
import { dirname } from 'path';

let clients = [];

var app = express();
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

app.use(cors())
app.use(express.json({limit: '50mb'}));

app.use('/getLog',(req, res) => {
  let log = getDownloadLog(req.body);
  res.send(log);
});

app.use('/check',(req,res)=>{checkRepository(req.body)});

app.use('/remove',(req, res) => {
  let manga_ids=req.body
  removeMangas(manga_ids);
  res.send("ok")
});

app.use('/archive',(req, res) => {
  let manga_ids=req.body
  archiveMangas(manga_ids);
  res.send("ok")
});

app.use('/download',(req, res) => {
  let manga_ids=req.body
  downloadMangas(manga_ids);
  res.send("ok")
});

app.use('/stop',(req, res) => {
  stopProcess();
  res.send("ok")  
});

app.use("/", express.static(__dirname));
app.listen(3300, function () {
    console.log('Listening on http://localhost:3300/');
    
});



app.get('/status', (request, response) => response.json({clients: clients.length}));


function eventsHandler(request, response, next) {
  const headers = {
    'Content-Type': 'text/event-stream',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache'
  };
  response.writeHead(200, headers);

  const data = `data: ${JSON.stringify(getStatus())}\n\n`;

  response.write(data);

  const clientId = Date.now();

  const newClient = {
    id: clientId,
    response
  };

  clients.push(newClient);
  console.log(`${clientId} New connection`);

  request.on('close', () => {
    console.log(`${clientId} Connection closed`);
    clients = clients.filter(client => client.id !== clientId);
  });
}

app.get('/events', eventsHandler);

function broadcastEvent() {
  clients.forEach(client => client.response.write(`data: ${JSON.stringify(getStatus())}\n\n`))
}

initRepository(broadcastEvent);
await fetchCoverImages();
