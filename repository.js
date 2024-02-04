import fetch from "node-fetch"
import fs from "fs"
import util from "node:util";
import {exec} from "node:child_process";

const execSync = util.promisify(exec);

let manob = {};
let cdn;

let stopProcessing = false;

// Repository status
const STATUS_DOWNLOADED = 'Downloaded';
const STATUS_INCOMPLETE = 'Incomplete';
const STATUS_NOT_DL = 'Not downloaded';

// Process status
const STATUS_DOWNLOADING = 'Downloading';
const STATUS_CHECKING = 'Checking';
const STATUS_ARCHIVING = 'Archiving';
const STATUS_QUEUED = 'Queued';
const STATUS_ERROR = 'Error';
const STATUS_NONE = '';

const log_dir = "./ipfs/log/"
let ipfsgate = "http://localhost:3300/ipfs/%@cid@%";

let manga_repo_status = {};  // 'Not downloaded', 'Downloaded', 'Incomplete'
let manga_archived = [];
let manga_process_status = {};  // 'Downloading', 'Checking', 'Queued'

let process_status = {'status':'', 'total_process_msg':'', 'manga_id':0, 'manga_process_msg':''};
let log_file_paths = {};
let archive_dir = './archive';

let send_event_func;

function delay(time) {
  return new Promise(resolve => setTimeout(resolve, time));
}

function getMetadata(oid) {
  let manga_tit = manob['meta'].manga_titles;
  for (let t of manga_tit) {
    if (t.enid == oid) {
      return t;
    }
  }
}

function saveRepositoryJson() {
  let pm = [];
  let incomplete = [];
  for (let id in manga_repo_status) {
    let status = manga_repo_status[id];
    if (status==STATUS_DOWNLOADED) {
      pm.push(id);
    } else
    if (status==STATUS_INCOMPLETE) {
      incomplete.push(id);
    }
  }
  
  let data = {'pm':pm,'incomplete':incomplete,'archived':manga_archived,'archive_directory':archive_dir};
  fs.writeFileSync ("./json/dw.json", JSON.stringify(data));
}

function setArchivedStatus(manga_id, archived, defer_broadcast=false) {
  if (archived) {
    manga_archived.push(manga_id);
  } else {
    manga_archived = manga_archived.filter((el) => el != manga_id);
  }
  saveRepositoryJson();
  if (!defer_broadcast) {
    send_event_func();
  }
}

function updateMangaRepositoryStatus(manga_id, status, defer_broadcast=false) {
  manga_repo_status[manga_id] = status;
  saveRepositoryJson();
  if (!defer_broadcast) {
    send_event_func();
  }
}

function sendProcessErrorMessage(manga_id, message) {
  console.log(`Error processing ${manga_id}: ${message}`);
  process_status['msg'] = message;
  process_status['status'] = STATUS_ERROR;
  manga_process_status = {};
  send_event_func();
}


function updateTotalProcessStatus(status, defer_broadcast, progress, progress_max) {
  if (progress_max != 0) {
    process_status['msg'] = `${status} ${progress}/${progress_max}`;
  } else {
    process_status['msg'] = `${status}`;
  }
  process_status['status'] = status;
  if (!defer_broadcast) {
    send_event_func();
  }
}


function updateMangaProcessStatus(manga_id, status, defer_broadcast=false, progress=0, progress_max=0, ) {
  if (manga_id in manga_process_status) {
    delete manga_process_status[manga_id];
  }
  if (status != STATUS_NONE) {
    if (progress_max != 0) {
      manga_process_status[manga_id] = `${status} ${progress}/${progress_max}`;
    } else {
      manga_process_status[manga_id] = `${status}`;
    }
  }
  if (!defer_broadcast) {
    send_event_func();
  }
}

function clearProcessStatus() {
  process_status['status'] = STATUS_NONE;
  process_status['msg'] = '';
  manga_process_status = {};
  send_event_func();
}

export function getStatus() {
  return {
    'manga_repo_status': manga_repo_status,
    'manga_process_status' : manga_process_status,
    'process_status':process_status, 
    'log_files':log_file_paths,
    'manga_archived':manga_archived,
  }
}


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


export function getDownloadLog(manga_id) {
  let log_path = log_dir + manga_id + ".json";
  if (fs.existsSync(log_path)) {
    let data = fs.readFileSync(log_path, "utf8");
    console.log("getLog " + manga_id);
    return {'log_file':log_path,'log_data':data};
  }
  console.log("getLog " + manga_id + " not found");
  return undefined;
}


function getLogFile(manga_id) {
  let log_path = log_dir + manga_id + ".json";
  if (fs.existsSync(log_path)) {
    return log_path;
  }
  return '';
}


function generateLogFile(manga_id, msg, queue) {
  if (!fs.existsSync(log_dir)) {
    fs.mkdirSync(log_dir, { recursive: true });
  }
  let log_path = log_dir + manga_id + ".json";
  fs.writeFileSync (log_path, JSON.stringify({'message':msg,'queue':queue}));
  log_file_paths[manga_id] = log_path;
}


function clearLogFile(manga_id) {
  let log_path = log_dir + manga_id + ".json";
  if (fs.existsSync(log_path)) {
    fs.rmSync(log_path, { recursive: true, force: true });
  }
  if (manga_id in log_file_paths) {
    delete log_file_paths[manga_id];    
  }
}


async function downloadQueues(queue_per_manga) {
  let total_count = 0;
  let num_total_files = 0;
  for (let manga_id in queue_per_manga) {
    let queue = queue_per_manga[manga_id];
    num_total_files += getQueueStats(queue).total;
  }
  for (let manga_id in queue_per_manga) {
    let queue = queue_per_manga[manga_id];
    let error_queue = [];
    let queue_count = 0;
    updateMangaRepositoryStatus(manga_id,STATUS_INCOMPLETE);
    for (let dl_task of queue) {
      updateTotalProcessStatus(STATUS_DOWNLOADING, true, total_count, num_total_files);
      updateMangaProcessStatus(manga_id, STATUS_DOWNLOADING, false, queue_count+1, queue.length);
      console.log(`[${total_count}/${num_total_files}] (${dl_task.url})`);
      const res = await fetch(dl_task.url);
      if (res.ok) {
        let filename = decodeURIComponent(decodeURIComponent(dl_task.p));
        console.log(`[${total_count}/${num_total_files}] (${dl_task.ch}) : [${filename}`);
        const temp2 = await res.body.pipe(fs.createWriteStream(filename));  
      } else {
        console.log("Error downloading " + dl_task.uri)
        error_queue.push(dl_task)
      }
      queue_count += 1;
      total_count += 1;

      if (stopProcessing) {
        console.log("Stopping downloading");
        clearLogFile(manga_id);
        clearProcessStatus();
        stopProcessing=false;
        return;
      }
    }
    updateMangaProcessStatus(manga_id, STATUS_NONE, false);

    if (error_queue.length==0) {
      clearLogFile(manga_id);
      updateMangaRepositoryStatus(manga_id,STATUS_DOWNLOADED);
    } else {
      generateLogFile(manga_id,"Error downloading files",error_queue);
      console.error(`Error downloading ${error_queue.length} files:`)
      console.error(JSON.stringify(error_queue));
      // The manga repo status is kept as 'Incomplete'
    }
  }
  clearProcessStatus();
}


// filter existing files and create target directories if necessary
function filterQueue(queue, create_dirs, select_existing=false) {
  let filtered_queue = [];

  if (create_dirs) {
    if (!fs.existsSync("./ocr/")) {
      fs.mkdirSync("./ocr/", { recursive: true });
    }
  }

  for (let ii in queue) {
    let img_file_path = queue[ii].p;

    let pat2 = img_file_path.split("/");
    let img_directory = pat2.slice(0, pat2.length - 1).join("/");

    if (create_dirs) {
      if (!fs.existsSync(img_directory)) {
        fs.mkdirSync(img_directory, { recursive: true });
      }
    }
    let decoded_path = decodeURIComponent(decodeURIComponent(img_file_path));

    if (!fs.existsSync(decoded_path) ^ select_existing) {
      filtered_queue.push(queue[ii]);
    }
  }
  return filtered_queue;
}


function createQueueForLanguage(title, lang, imgs, ocrtt) {
  let queue = [];
  for (let eliix in imgs) {
    let chapter = imgs[eliix];
    let ocr_files = [];
    for (let xnnn in chapter) {
      let pat0 = chapter[xnnn];
      let pat1 = `.${pat0.replace("http://localhost:3300", "")}`;
      while (!(manob["meta"].ipfsgate.length > 0)) {}
      let ipfsgatemm = manob["meta"].ipfsgate.replace("%@cid@%", "");
      let img_url = `${ipfsgatemm}${pat1.replace("./ipfs/", "")}`;

      if (ocrtt) {
        let cid = img_url.split("/");
        let seljs = 3;
        if (`${cid[cid.length - seljs]}` === "ipfs") {
          seljs = 2;
        }
    
        let ocr = `${manob["meta"].cdn}/ocr/${cid[cid.length - seljs]}.json`;
        let ocrp = `./ocr/${cid[cid.length - seljs]}.json`;
        if (!ocr_files.includes(ocrp)) { // avoid duplicates
          queue.push({'l':lang, 'ocr':true, 'ch':eliix, 'url':ocr,'p':ocrp});
          ocr_files.push(ocrp);
        }
      }
      queue.push({'l':lang, 'ocr':false, 'ch':eliix, 'url':img_url,'p':pat1});
    }
  }
  return queue;
}


function createQueue(metadata, data) {
  let imgs_engo = imgscon(data.en_data.ch_en, data.en_data.ch_enh);
  let imgs_jpo = imgscon(data.jp_data.ch_jp, data.jp_data.ch_jph);
  let queue = [];
  queue = createQueueForLanguage(metadata.entit, "en", imgs_engo, false);
  queue = queue.concat(createQueueForLanguage(metadata.entit, "jp", imgs_jpo, true));
  return queue;
}


function getQueueStats(queue) {
  let stats = {'en':0, 'jp':0, 'ocr':0}
  for (let ii in queue) {
    let lang = queue[ii].l;
    if (queue[ii].ocr) {
      stats['ocr'] += 1;
    } else {
      stats[lang] += 1;
    }
  }
  stats.images = stats.en + stats.jp;
  stats.total = stats.images + stats.ocr;
  return stats;
}


export function downloadMangas(manga_ids) {
  console.log("downloadMangas " + manga_ids);

  for (let id of manga_ids) {
    updateMangaProcessStatus(id, STATUS_QUEUED, true);
  } 

  let queue_per_manga = {};
  for (let ii in manob['data']) {
    let mdata = manob['data'][ii];
    let idd = mdata._id.$oid;
    let metadata = getMetadata(idd);

    if (manga_ids.includes(idd)) {
      console.log("Queue " + metadata.entit);
      let queue = createQueue(metadata, mdata);
      queue_per_manga[idd] = filterQueue(queue,true);
    }
  }
  downloadQueues(queue_per_manga);
}


export function stopProcess() {
  console.log("stopProcess");
  stopProcessing = true;
}


export function removeMangas(manga_ids) {
  console.log("removeMangas " + manga_ids);

  let removed = 0;
  for (let ii in manob['data']) {
    let mdata = manob['data'][ii];
    let idd = mdata._id.$oid;
    let metadata = getMetadata(idd);

    if (manga_ids.includes(idd)) {
      console.log("Remove " + metadata.entit);
      let chapter_sets = [mdata.en_data["ch_enh"], mdata.jp_data["ch_jph"]];
      for (let chapter_set of chapter_sets) {
        for (let icc in chapter_set) {
          let ch = chapter_set[icc].split("/");
          let rmdd = `./ipfs/${ch[0]}`;
          if (fs.existsSync(rmdd)) {
            console.log(" * " + rmdd);
            fs.rmSync(rmdd, { recursive: true, force: true });
            removed += 1;
          }
        }
      }
      clearLogFile(idd);
      updateMangaRepositoryStatus(idd, STATUS_NOT_DL);
    }
  }
  console.log("Removed " + removed + " chapters");
}


export async function checkRepository(manga_ids) {
  console.log("checkRepository " + manga_ids);

  for (let id of manga_ids) {
    updateMangaProcessStatus(id, STATUS_QUEUED, true);
  } 

  let checked_count=0;
  for (let ii in manob['data']) {
    let mdata = manob['data'][ii];
    let idd = mdata._id.$oid;
    let metadata = getMetadata(idd);

    if (manga_ids.includes(idd)) {
      console.log("Check " + metadata.entit);

      let archive_file = `${archive_dir}/${idd}.tar`
      if (fs.existsSync(archive_file)) {
        if (!(manga_archived.includes(idd))) {
          // Archive was missing from dw.json
          console.log("  * Found archive file " + archive_file);
          setArchivedStatus(idd, true);
          clearLogFile(idd);
        }
      } else {
        if (manga_archived.includes(idd)) {
          // Couldn't find the archive file anymore
          console.log("  * Missing archive file " + archive_file);
          setArchivedStatus(idd, false);
          clearLogFile(idd);
        }
      }

      // check if all the manga files are present
      updateTotalProcessStatus(STATUS_CHECKING, true, checked_count, manga_ids.length);
      updateMangaProcessStatus(idd,STATUS_CHECKING,false);
      await delay(50); // checking is too fast :)
      // Full manga file list
      let all_files = createQueue(metadata, mdata);
      let a_stats = getQueueStats(all_files);
      // Missing files
      let missing_files = filterQueue(all_files,false);
      let m_stats = getQueueStats(missing_files);

      if (m_stats.total>0) {
        if (m_stats.images>0) {
          if (m_stats.images != a_stats.images) {
            console.log("Missing " + m_stats.images + "/" + a_stats.images + " files");
            generateLogFile(idd,`Missing ${m_stats.images}/${a_stats.images} files (${m_stats.ocr}/${a_stats.ocr} OCR)`, missing_files);
            updateMangaRepositoryStatus(idd, STATUS_INCOMPLETE);
            for (let mi in missing_files) {
              console.log(" * " + missing_files[mi].p);
            }
          } else {
            // just a non downloaded manga
            updateMangaRepositoryStatus(idd, STATUS_NOT_DL);
            clearLogFile(idd);
          }
        } else {
          if (m_stats.ocr > 0) {
            console.log("Missing " + m_stats.ocr + "/" + a_stats.ocr + " ocr");
            generateLogFile(idd,`Missing ${m_stats.ocr}/${a_stats.ocr} OCR files`, missing_files);
            updateMangaRepositoryStatus(idd, STATUS_INCOMPLETE);
            for (let mi in missing_files) {
              console.log(" * " + missing_files[mi].p);
            }
          }
        }
      } else {
        if (manga_repo_status[idd] != STATUS_DOWNLOADED) {
          // Completely downloaded but missing from dw.json
          console.log("  * Found all manga files");
          updateMangaRepositoryStatus(idd,STATUS_DOWNLOADED);
          clearLogFile(idd);
        }
      }
      updateMangaProcessStatus(idd,STATUS_NONE,false);
      checked_count += 1;
    }
  }
  clearProcessStatus();
}


// TODO: checking the fileames doesn't work because for some reason the shell command output
// uses weird octal utf-8 coding for non-ascii characters
/*
function checkArchiveFileIntegrity(metadata, mdata, archive_file) {
  let temp_file = "./tar-list.temp";
  let cmd = `tar tf ${archive_file} > ${temp_file}`
  const { stdout, stderr } = await execSync(cmd, {'encoding': 'UTF-8'});
  let data = fs.readFileSync(temp_file, "utf8");
  let arc_files = data.split('\n');
  let all_files = createQueue(metadata, mdata);
  let existing_files = filterQueue(all_files,false, true);
  let missing_files = [];
  for (let q_item of existing_files) {
    let q_p = decodeURIComponent(q_item.p);
    if (arc_files.indexOf(q_p) == -1) {
      missing_files.push(q_item);
    }
  }
  if (missing_files.length>0) {
    return false;
  }
  return true;
}
*/

// Here we just check that the output archive file size is larger than the input files combined
function checkArchiveFileIntegrity(metadata, mdata, archive_file) {

  let all_files = createQueue(metadata, mdata);
  let existing_files = filterQueue(all_files,false, true);
  let total_size = 0;
  for (let q_item of existing_files) {
    let q_p = decodeURIComponent(q_item.p);
    let stats = fs.statSync(q_p);
    total_size += stats.size;
  }
  let stats = fs.statSync(archive_file);
  if (stats.size < total_size) {
    return false;
  }
  return true;
}

export async function archiveMangas(selected_manga_ids) {
  console.log("archiveMangas " + selected_manga_ids);

  let manga_ids = [];
  for (let id of selected_manga_ids) {
    let status = manga_repo_status[id]
    if (id in manga_archived) {
      console.log(` * wont process ${id} because already archived`);
    } else if (status != STATUS_DOWNLOADED && status != STATUS_INCOMPLETE) {
      console.log(` * wont process ${id} because status is ${status}`);
    } else {
      updateMangaProcessStatus(id, STATUS_QUEUED, true);
      manga_ids.push(id);
    }
  } 

  if (!fs.existsSync(archive_dir)) {
    fs.mkdirSync(archive_dir, { recursive: true });
  }

  let archived_count=0;
  for (let ii in manob['data']) {
    let mdata = manob['data'][ii];
    let idd = mdata._id.$oid;
    let metadata = getMetadata(idd);

    if (manga_ids.includes(idd)) {
      let archive_file = `${archive_dir}/${idd}.tar`
      console.log(`Archive ${metadata.entit} to ${archive_file}`);

      if (fs.existsSync(archive_file)) {
        console.log(" * Deleting previous incomplete archive file")
        fs.rmSync(archive_file);
      }

      updateTotalProcessStatus(STATUS_ARCHIVING, true, archived_count, manga_ids.length);
      updateMangaProcessStatus(idd,STATUS_ARCHIVING,false);

      let chapter_sets = [mdata.en_data["ch_enh"], mdata.jp_data["ch_jph"]];
      let processed_chapters=0, total_chapters=0;
      for (let chapter_set of chapter_sets) {
          total_chapters += chapter_set.length;
      }

      for (let cs_i in chapter_sets) {
        let chapter_set = chapter_sets[cs_i];
        for (let icc in chapter_set) {

          if (stopProcessing) {
            console.log("Stopping archiving process")
            if (fs.existsSync(archive_file)) {
              fs.rmSync(archive_file);
            }
            clearProcessStatus();
            stopProcessing=false;
            return false;
          }

          updateMangaProcessStatus(idd,STATUS_ARCHIVING,false,processed_chapters+1,total_chapters);

          let ch = chapter_set[icc].split("/");
          let chapter_dir = `./ipfs/${ch[0]}`;

          let ocrp = '';
          if (cs_i==1) {
            ocrp = `./ocr/${ch[0]}.json`
            if (!fs.existsSync(ocrp)) {
              ocrp = ''; // skip occasional missing OCR file
            }
          }

          let cmd = '';
          if (processed_chapters==0) {
            cmd = `tar cf ${archive_file} ${chapter_dir} ${ocrp}`
          } else {
            cmd = `tar rf ${archive_file} ${chapter_dir} ${ocrp}`
          }
          console.log(` * Chapter ${icc} : ${chapter_dir}`)
          try {
            const { stdout, stderr } = await execSync(cmd);
          } catch (error) {
            sendProcessErrorMessage(idd, error.stderr);
            return false;      
          }
          processed_chapters +=1;
        }
      }

      // double check that the archive contains all files before marking it as archived
      if (!fs.existsSync(archive_file)) {
        sendProcessErrorMessage(idd, `Error creating archive ${archive_file}`);
        return false;
      }
      if (checkArchiveFileIntegrity(metadata, mdata, archive_file)) {
        updateMangaProcessStatus(idd,STATUS_NONE,false);
        clearLogFile(idd);
        setArchivedStatus(idd, true);
      } else {
        sendProcessErrorMessage(idd, `Archive ${archive_file} incomplete!`);
        return false;
      }
      archived_count += 1;
    }
  }
  clearProcessStatus();
}


export async function fetchCoverImages() {
  let manga_tit = manob["meta"].manga_titles;

  for (let i in manga_tit) {
    let path_lists = [manga_tit[i].coveren, manga_tit[i].coverjp]
    for (let p_i in path_lists) {
      let pat = path_lists[p_i];
      let pat1 = pat.split("/");
      let pat2 = pat1.slice(0, pat1.length - 1).join("/");
      if (!fs.existsSync(pat2)) {
        fs.mkdirSync(pat2, { recursive: true });
      }
      if (!fs.existsSync(pat)) {
        const temp1 = await fetch(`${cdn}/${pat}`);
        pat = decodeURIComponent(decodeURIComponent(pat));
        const temp2 = await temp1.body.pipe(fs.createWriteStream(pat));
      }
    }
  }
}


export function initRepository(send_event_callback_func) {
  send_event_func = send_event_callback_func;

  let data = fs.readFileSync("./json/admin.manga_data.json", "utf8");
  let mdata = JSON.parse(data);
  manob["data"] = mdata;
  console.log("Loaded manga_data")

  data = fs.readFileSync("./json/admin.manga_metadata.json", "utf8");
  mdata = JSON.parse(data);
  let re1 = mdata[0];
  manob["meta"] = re1;
  cdn = re1["cdn"];
  console.log("Loaded manga_metadata")
      
  data = fs.readFileSync("./json/dw.json", "utf8" );
  data = JSON.parse(data);
  let pm = data["pm"];
  let incomplete = [];
  if ('incomplete' in data) {
    incomplete = data["incomplete"];
  }
  if ('archived' in data) {
    manga_archived = data["archived"];
  }
  if ('archive_directory' in data) {
    archive_dir = data["archive_directory"];
  }

  for (let i in manob["meta"].manga_titles) {
    let id = manob["meta"].manga_titles[i].enid;

    if (pm.includes(id)) {
      manga_repo_status[id] = STATUS_DOWNLOADED;
    } else if (incomplete.includes(id)) {
      manga_repo_status[id] = STATUS_INCOMPLETE;
    } else {
      manga_repo_status[id] = STATUS_NOT_DL;
    }

    let log_file = getLogFile(id);
    if (log_file != '') {
      log_file_paths[id] = log_file;
    }
  }
  send_event_func();
}
