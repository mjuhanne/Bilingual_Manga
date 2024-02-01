
import fs from "fs"
import cors from "cors"
import fetch from "node-fetch"
import { fetchCoverImages, updateRepository } from "./repository.js";

import express from "express"
import { fileURLToPath } from 'url';
import { dirname } from 'path';
var app = express();
let manob={}
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
let ipfsgate="http://localhost:3300/ipfs/%@cid@%"


app.use(cors())
app.use(express.json({limit: '50mb'}));
app.use('/mypost',(req, res) => {

  res.send("ok")

});



app.use('/check',(req,res)=>{imgdl("pm")});


app.use('/remove',(req, res) => {

  let chapter_ids=req.body

  console.log("remove " + JSON.stringify(chapter_ids));

  fs.readFile('./json/dw.json', 'utf8', function(err, contents) {
    if (err) {
      throw err;
    } else {
      let data = JSON.parse(contents);

      for(let chapter_id of chapter_ids) {
          if(!data["rm"].includes(chapter_id))
         {data["rm"].push(chapter_id);}        
      }

      fs.writeFile ("./json/dw.json", JSON.stringify(data), function(err) {
        if (err) throw err;
        });

    }
});

  updateRepository("rm")
  res.send("ok")

});


app.use('/download',(req, res) => {

  let chapter_ids=req.body

  console.log("download " + JSON.stringify(chapter_ids));

  fs.readFile('./json/dw.json', 'utf8', function(err, contents) {
    if (err) {
      throw err;
    } else {
      let data = JSON.parse(contents);
      for(let chapter_id of chapter_ids)
      {
          if(!data["dw"].includes(chapter_id))
         {data["dw"].push(chapter_id);}
        
      }
      fs.writeFile ("./json/dw.json", JSON.stringify(data), function(err) {
        if (err) throw err;
        });

    }
});

  updateRepository("dw")
  res.send("ok")
  
});

app.use("/", express.static(__dirname));
app.listen(3300, function () {
    console.log('Listening on http://localhost:3300/');
    
});



await fetchCoverImages();
updateRepository();
