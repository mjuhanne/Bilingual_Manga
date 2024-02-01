import fetch from "node-fetch"
import fs from "fs"

let manob = {};
let ipfsgate = "http://localhost:3300/ipfs/%@cid@%";

const imgscon = (imgsl, rep) => {
  const replaceing = (rstr, str) => {
    let rstrarr = str.split("/");
    let rpsi = str.indexOf(`%@rep@%`);
    let resi = str.substring(0, rpsi);
    resi = ipfsgate.replace("%@cid@%", resi);
    let reti = `${resi}${rstr}`;
    return reti;
  };
  let ximg = {};
  if (imgsl != undefined) {
    rep.forEach((rep1, j1) => {
      let imgsret = [];
      imgsl[j1 + 1].forEach((el) => {
        let repx = replaceing(el, rep1);
        imgsret.push(repx);
      });
      ximg[j1 + 1] = imgsret;
    });
  }
  // console.log(ximg);
  return ximg;
};

function removeele(arrOriginal, elementToRemove) {
  return arrOriginal.filter(function (el) {
    return el !== elementToRemove;
  });
}

export async function fetchCoverImages() {
  let xx = await fetch("http://localhost:3300/json/admin.manga_metadata.json");
  let res = await xx.json();
  let re1 = res[0];
  manob["meta"] = re1;
  let cdn = re1["cdn"];
  let manga_tit = re1.manga_titles;

  for (let i in manga_tit) {
    let pat = manga_tit[i].coveren;
    let pat1 = pat.split("/");
    let pat2 = pat1.slice(0, pat1.length - 1).join("/");
    if (!fs.existsSync(pat2)) {
      fs.mkdirSync(pat2, { recursive: true });
    }
    if (!fs.existsSync(pat)) {
      const temp1 = await fetch(`${cdn}/${pat}`);
      pat = decodeURIComponent(decodeURIComponent(pat));
      //console.log(pat)
      const temp2 = await temp1.body.pipe(fs.createWriteStream(pat));
    }

    pat = manga_tit[i].coverjp;
    pat1 = pat.split("/");
    pat2 = pat1.slice(0, pat1.length - 1).join("/");
    if (!fs.existsSync(pat2)) {
      fs.mkdirSync(pat2, { recursive: true });
    }
    if (!fs.existsSync(pat)) {
      const temp1 = await fetch(`${cdn}/${pat}`);
      pat = decodeURIComponent(decodeURIComponent(pat));
      //console.log(pat)
      const temp2 = await temp1.body.pipe(fs.createWriteStream(pat));
    }
  }
}

async function downloadQueue(queue) {
  let i = 1;
  for (let dl_task of queue) {
    console.log(`[${i}/${queue.length}] (${dl_task[1]})`);
    const temp1 = await fetch(dl_task[1]);
    let filename = decodeURIComponent(decodeURIComponent(dl_task[2]));
    console.log(`[${i}/${queue.length}] (${dl_task[0]}) : [${filename}`);
    const temp2 = await temp1.body.pipe(fs.createWriteStream(filename));  
    i += 1;
  }
}

// create target directories and queue OCR files if necessary
function prepareQueue(lang, img_urls, img_file_paths, ocrtt = false) {
  let queue = [];
  for (let ii in img_urls) {
    let pat2 = img_file_paths[ii].split("/");
    let img_directory = pat2.slice(0, pat2.length - 1).join("/");

    if (ocrtt) {
      let cid = img_urls[ii].split("/");
      let seljs = 3;
      if (`${cid[cid.length - seljs]}` === "ipfs") {
        seljs = 2;
      }
  
      let ocr = `${manob["meta"].cdn}/ocr/${cid[cid.length - seljs]}.json`;
      let ocrp = `./ocr/${cid[cid.length - seljs]}.json`;
      if (!fs.existsSync("./ocr/")) {
        fs.mkdirSync("./ocr/", { recursive: true });
      }

      if (!fs.existsSync(ocrp)) {
        queue.push([lang, ocr,ocrp]);
      }
    }

    if (!fs.existsSync(img_directory)) {
      fs.mkdirSync(img_directory, { recursive: true });
    }
    if (!fs.existsSync(img_file_paths[ii])) {
      queue.push([lang, img_urls[ii],img_file_paths[ii]]);
    }
  }
  return queue;
}

function queueFiles(title, lang, imgs_engo, ocrtt = false) {
  let img_urls = [];
  let img_file_paths = [];
  for (let eliix in imgs_engo) {
    let vol = imgs_engo[eliix];
    for (let xnnn in vol) {
      let pat0 = vol[xnnn];
      let pat1 = `.${pat0.replace("http://localhost:3300", "")}`;
      let pat2 = pat1.split("/");
      while (!(manob["meta"].ipfsgate.length > 0)) {}
      let ipfsgatemm = manob["meta"].ipfsgate.replace("%@cid@%", "");
      let pat4 = `${ipfsgatemm}${pat1.replace("./ipfs/", "")}`;
      //console.log(pat4)

      if (!fs.existsSync(pat1)) {
        img_file_paths.push(pat1);
        img_urls.push(pat4);
        console.log("Queued " + title + " " + lang + " : " + pat4);
      }
    }
  }
  return prepareQueue(lang, img_urls, img_file_paths, ocrtt);
}

function downloadTitle(metadata, data) {
  console.log("Download " + metadata.entit);
  let imgs_engo = imgscon(data.en_data.ch_en, data.en_data.ch_enh);
  let imgs_jpo = imgscon(data.jp_data.ch_jp, data.jp_data.ch_jph);
  let queue = [];
  queue = queueFiles(metadata.entit, "en", imgs_engo);
  queue = queue.concat(queueFiles(metadata.entit, "jp", imgs_jpo, true));
  downloadQueue(queue);
}

function removeTitle(metadata, data) {
  console.log("Remove " + metadata.entit);
  let idd = data._id.$oid;
  let xxxen = data.en_data["ch_enh"];
  let xxxjp = data.jp_data["ch_jph"];
  let removed = 0;
  for (let icc in xxxen) {
    let xxxx = xxxen[icc].split("/");
    let rmdd = `./ipfs/${xxxx[0]}`;
    //console.log(rmdd)
    if (fs.existsSync(rmdd)) {
      fs.rmSync(rmdd, { recursive: true, force: true });
      removed += 1;
    }
  }

  for (let icc in xxxjp) {
    let xxxx = xxxjp[icc].split("/");
    let rmdd = `./ipfs/${xxxx[0]}`;
    if (fs.existsSync(rmdd)) {
      fs.rmSync(rmdd, { recursive: true, force: true });
      removed += 1;
    }
  }
  console.log("Removed " + removed + " files");
}

function getMetadata(oid) {
  let manga_tit = manob['meta'].manga_titles;
  for (let t of manga_tit) {
    if (t.enid == oid) {
      return t;
    }
  }
}

export function updateRepository(sel) {
  console.log("updateRepository " + sel);
  fs.readFile(
    "./json/admin.manga_data.json",
    "utf8",
    function (err1, contents1) {
      if (err1) {
        throw err1;
      } else {
        let mdata = JSON.parse(contents1);

        fs.readFile("./json/dw.json", "utf8", function (err, contents) {
          if (err) {
            throw err;
          } else {
            let data = JSON.parse(contents);
            let dw = data["dw"];
            let pm = data["pm"];
            let rm = data["rm"];
            if (sel === "rm") {
              dw = dw.filter((el) => !rm.includes(el));
              pm = pm.filter((el) => !rm.includes(el));
            }
            for (let ii in mdata) {
              let metadata = getMetadata(mdata[ii]._id.$oid);

              if (sel === "dw") {
                if (dw.includes(mdata[ii]._id.$oid)) {
                  let idd = mdata[ii]._id.$oid;

                  // FIXME
                  //if (!pm.includes(idd)) 
                  {
                    pm.push(idd);

                    downloadTitle(metadata, mdata[ii]);
                  }
                  dw = removeele(dw, idd);
                }
              }

              if (sel === "rm") {
                if (rm.includes(mdata[ii]._id.$oid)) {
                  removeTitle(metadata, mdata[ii]);
                  rm = removeele(rm, mdata[ii]._id.$oid);
                }
              }

              if (sel === "pm") {
              }
            }
            fs.writeFile(
              "./json/dw.json",
              JSON.stringify({ dw: dw, pm: pm, rm: rm }),
              function (err) {
                if (err) throw err;
              }
            );
          }
        });
      }
    }
  );
  console.log("updateRepository - end")
}
