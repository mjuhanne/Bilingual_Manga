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
const STATUS_RESTORING = 'Restoring';
const STATUS_REMOVING = 'Removing';
const STATUS_VERIFYING_ARCHIVE = 'Verifying archive';
const STATUS_QUEUED = 'Queued';
const STATUS_ERROR = 'Error';
const STATUS_NONE = '';

// Download errors
const DL_OK = 0;
const DL_FILE_NOT_FOUND = 1;
const DL_TIMEOUT = 2;
const DL_NO_SPACE = 3;

// Archive status
const ARCHIVE_NONE = 0;
const ARCHIVE_INCOMPLETE = 1;
const ARCHIVE_COMPLETE = 2;

const log_dir = "./ipfs/log/"
let ipfsgate = "http://localhost:3300/ipfs/%@cid@%";

let manga_repo_status = {};  // 'Not downloaded', 'Downloaded', 'Incomplete'
let manga_archived = [];
let manga_archive_incomplete = [];
let manga_process_status = {};  // 'Downloading', 'Checking', 'Queued'

let process_status = {'status':'', 'total_process_msg':'', 'manga_id':0, 'manga_process_msg':''};
let log_file_paths = {};
let archive_dir = './archive';

let send_event_func;

function delay(time) {
  return new Promise(resolve => setTimeout(resolve, time));
}
const delaySync = util.promisify(delay);

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
  let data = {
    'pm':pm,
    'incomplete':incomplete,
    'archived':manga_archived,
    'archive_incomplete':manga_archive_incomplete,
    'archive_directory':archive_dir
  };
  fs.writeFileSync ("./json/dw.json", JSON.stringify(data));
}

function getArchivedStatus(manga_id) {
  if (manga_archived.includes(manga_id)) {
    return ARCHIVE_COMPLETE;
  } else if (manga_archive_incomplete.includes(manga_id)) {
    return ARCHIVE_INCOMPLETE;
  }
  return ARCHIVE_NONE;
}

function setArchivedStatus(manga_id, archive_status, defer_broadcast=false) {
  manga_archived = manga_archived.filter((el) => el != manga_id);
  manga_archive_incomplete = manga_archive_incomplete.filter((el) => el != manga_id);

  if (archive_status == ARCHIVE_COMPLETE) {
      manga_archived.push(manga_id);
  } else if (archive_status == ARCHIVE_INCOMPLETE) {
    manga_archive_incomplete.push(manga_id);
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
  process_status['id'] = manga_id;
  process_status['msg'] = message;
  process_status['status'] = STATUS_ERROR;
  manga_process_status = {};
  send_event_func();
  process_status['status'] = STATUS_NONE; // clear error
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
    'manga_archive_incomplete':manga_archive_incomplete,
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

async function downloadFile(manga_id, dl_task) {
  let retries=8;
  let retry_wait=1;
  let res;
  do {
    try {
      res = await fetch(dl_task.url);
      if (res.ok) {
        const temp2 = await res.body.pipe(fs.createWriteStream(dl_task.p));
        return DL_OK;
      } else {
        return DL_FILE_NOT_FOUND;
      }
    } catch (err) {
          sendProcessErrorMessage(manga_id, err.message);
          retries -= 1;
          if (retries>0) {
            await delay(retry_wait*1000);
            retry_wait *= 2;
          }
    }
  } while(retries>0);
  return DL_TIMEOUT;
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
      console.log(`[${total_count}/${num_total_files}] (${dl_task.ch}) : [${dl_task.p}`);
      let ret = await downloadFile(manga_id, dl_task)
      if (ret==DL_FILE_NOT_FOUND) {
        console.log("Error downloading " + dl_task.uri)
        error_queue.push(dl_task)
      } else if (ret>DL_FILE_NOT_FOUND) {
        return;
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

    if (!fs.existsSync(img_file_path) ^ select_existing) {
      filtered_queue.push(queue[ii]);
    }
  }
  return filtered_queue;
}

// Replace uncommon characters in local file names with '_'
function cleanFileName(filename) {
  let new_filename = filename.replace(/[^A-Za-z0-9 ,+'!_&@#\-\[\].\/()]+/g, '_');
  if (filename != new_filename) {
    console.log(` * Warning: '${filename}' -> '${new_filename}'`)
  }
  return new_filename;
}

function createQueueForLanguage(title, lang, imgs, ocrtt, selected_chapter_id) {
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

      let cid = img_url.split("/");
      let seljs = 3;
      if (`${cid[cid.length - seljs]}` === "ipfs") {
        seljs = 2;
      }
      let chapter_id = cid[cid.length - seljs];

      if (selected_chapter_id == '' || (chapter_id==selected_chapter_id)) {
        if (ocrtt) {    
          let ocr = `${manob["meta"].cdn}/ocr/${chapter_id}.json`;
          let ocrp = `./ocr/${chapter_id}.json`;
          if (!ocr_files.includes(ocrp)) { // avoid duplicates
            queue.push({'l':lang, 'ocr':true, 'ch':eliix, 'url':ocr,'p':ocrp});
            ocr_files.push(ocrp);
          }
        }
        let decoded_path = decodeURIComponent(decodeURIComponent(pat1));
        let cleaned_path = cleanFileName(decoded_path);
        queue.push({'l':lang, 'ocr':false, 'ch':eliix, 'url':img_url,'p':cleaned_path});
      }
    }
  }
  return queue;
}


function createQueue(metadata, data, chapter_id='') {
  let imgs_engo = imgscon(data.en_data.ch_en, data.en_data.ch_enh);
  let imgs_jpo = imgscon(data.jp_data.ch_jp, data.jp_data.ch_jph);
  let queue = [];
  queue = createQueueForLanguage(metadata.entit, "en", imgs_engo, false, chapter_id);
  queue = queue.concat(createQueueForLanguage(metadata.entit, "jp", imgs_jpo, true, chapter_id));
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


export async function removeMangas(manga_ids) {
  console.log("removeMangas " + manga_ids);

  for (let id of manga_ids) {
    updateMangaProcessStatus(id, STATUS_QUEUED, true);
  } 

  let num_removed_ch = 0, num_removed_mangas = 0;
  for (let ii in manob['data']) {
    let mdata = manob['data'][ii];
    let idd = mdata._id.$oid;
    let metadata = getMetadata(idd);

    if (manga_ids.includes(idd)) {
      console.log("Remove " + metadata.entit);

      updateTotalProcessStatus(STATUS_REMOVING, true, num_removed_mangas+1, manga_ids.length);
      updateMangaProcessStatus(idd,STATUS_REMOVING);

      await delay(2000); // doing deliberately slow to allow user to regret and stop the process

      if (stopProcessing) {
        console.log("Stopping removing process")
        clearProcessStatus();
        stopProcessing=false;
        return false;
      }

      let chapter_sets = [mdata.en_data["ch_enh"], mdata.jp_data["ch_jph"]];
      for (let chapter_set of chapter_sets) {
        for (let icc in chapter_set) {
          let ch = chapter_set[icc].split("/");
          let rmdd = `./ipfs/${ch[0]}`;
          if (fs.existsSync(rmdd)) {
            console.log(" * " + rmdd);
            fs.rmSync(rmdd, { recursive: true, force: true });
            num_removed_ch += 1;
          }
        }
      }
      num_removed_mangas += 1;
      clearLogFile(idd);
      updateMangaRepositoryStatus(idd, STATUS_NOT_DL, true);
      updateMangaProcessStatus(idd,STATUS_NONE);
      console.log("Removed " + metadata.entit);

    }
  }
  clearProcessStatus();
  console.log("Removed " + num_removed_ch + " chapters");
}


async function checkArchiveFileIntegrity(metadata, mdata, archive_file, chapter_id) {
  let temp_file = "./zip-list.temp";
  try {
    let cmd = `unzip -Z -1 ${archive_file} > ${temp_file}`
    let stdout = await execSync(cmd, {'encoding': 'utf-8'});
  } catch (err) {
    return err.message;
  }

  let data = fs.readFileSync(temp_file, "utf-8");
  let arc_files = data.split('\n');
  let all_files = createQueue(metadata, mdata, chapter_id);
  let missing_files = [];
  for (let q_item of all_files) {
    let q_p = q_item.p;
    if (q_p.substring(0,2) == './') {
      q_p = q_p.substring(2);
    }
    if (arc_files.indexOf(q_p) == -1) {
      missing_files.push(q_item);
    }
  }
  if (missing_files.length>0) {
    let msg = `${archive_file} is missing ${missing_files.length} files`;
    generateLogFile(metadata.enid, msg, missing_files);
    console.log(msg);
    return msg;
  }
  let cmd = `unzip -t -q ${archive_file}`
  const { stdout, stderr } = await execSync(cmd, {'encoding': 'UTF-8'});
  if (stdout.includes('No errors detected')) {
    return '';
  }
  return stdout;
}

async function checkMangaArchives(manga_id, metadata, mdata) {

  let chapter_sets = [mdata.en_data["ch_enh"], mdata.jp_data["ch_jph"]];
  let total_chapters=0, num_archives_intact = 0;
  for (let chapter_set of chapter_sets) {
      total_chapters += chapter_set.length;
  }

  let archive_title_dir = `${archive_dir}/${manga_id}`
  if (fs.existsSync(archive_title_dir)) {

    let processed_chapters=0;

    for (let cs_i in chapter_sets) {
      let chapter_set = chapter_sets[cs_i];

      for (let icc in chapter_set) {

        if (stopProcessing) {
          return false;
        }
  
        updateMangaProcessStatus(manga_id,STATUS_VERIFYING_ARCHIVE,false,processed_chapters+1,total_chapters);
        let ch = chapter_set[icc].split("/")[0];
        let archive_file = `${archive_title_dir}/${ch}.zip`
        if (fs.existsSync(archive_file)) {
          let res = await checkArchiveFileIntegrity(metadata, mdata, archive_file, ch);
          if (res != '') {
            // incomplete
            console.log(res);
          } else {
            num_archives_intact += 1;
          }
        } else {
          console.log("  * Missing archive file " + archive_file);
        }
        processed_chapters += 1;
      }
    }
  }

  let archive_status = getArchivedStatus(manga_id);
  if (num_archives_intact == total_chapters) {
    if (archive_status != ARCHIVE_COMPLETE) {
      // Archive was missing from dw.json
      console.log("  * Found all archived chapters (previously unmarked)");
      setArchivedStatus(manga_id, ARCHIVE_COMPLETE);
      clearLogFile(manga_id);
    }
  } else {
    if ((archive_status != ARCHIVE_INCOMPLETE) && (num_archives_intact>0) )  {
      console.log("  * Some archived chapters found");
      setArchivedStatus(manga_id, ARCHIVE_INCOMPLETE);
      clearLogFile(manga_id);
    } else if ((archive_status != ARCHIVE_NONE) && (num_archives_intact==0) )  {
      // Couldn't find the archive file(s) anymore
      console.log("  * Removing archived status ");
      setArchivedStatus(manga_id, ARCHIVE_NONE);
      clearLogFile(manga_id);
    }
  }
}

async function checkMangaFiles(manga_id, metadata, mdata) {

  updateMangaProcessStatus(manga_id,STATUS_CHECKING,false);
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
        generateLogFile(manga_id,`Missing ${m_stats.images}/${a_stats.images} files (${m_stats.ocr}/${a_stats.ocr} OCR)`, missing_files);
        updateMangaRepositoryStatus(manga_id, STATUS_INCOMPLETE);
        for (let mi in missing_files) {
          console.log(" * " + missing_files[mi].p);
        }
      } else {
        // just a non downloaded manga
        updateMangaRepositoryStatus(manga_id, STATUS_NOT_DL);
        clearLogFile(manga_id);
      }
    } else {
      if (m_stats.ocr > 0) {
        console.log("Missing " + m_stats.ocr + "/" + a_stats.ocr + " ocr");
        generateLogFile(manga_id,`Missing ${m_stats.ocr}/${a_stats.ocr} OCR files`, missing_files);
        updateMangaRepositoryStatus(manga_id, STATUS_INCOMPLETE);
        for (let mi in missing_files) {
          console.log(" * " + missing_files[mi].p);
        }
      }
    }
  } else {
    if (manga_repo_status[manga_id] != STATUS_DOWNLOADED) {
      // Completely downloaded but missing from dw.json
      console.log("  * Found all manga files");
      updateMangaRepositoryStatus(manga_id,STATUS_DOWNLOADED);
      clearLogFile(manga_id);
    }
  }
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

      if (stopProcessing) {
        console.log("Stopping verifying process")
        clearProcessStatus();
        stopProcessing=false;
        return false;
      }

      updateTotalProcessStatus(STATUS_CHECKING, true, checked_count, manga_ids.length);

      // check if all the manga archives and files are present
      await checkMangaArchives(idd, metadata, mdata);
      await checkMangaFiles(idd, metadata, mdata);

      updateMangaProcessStatus(idd,STATUS_NONE,false);
      checked_count += 1;
    }
  }
  clearProcessStatus();
}

export async function archiveMangas(selected_manga_ids) {
  console.log("archiveMangas " + selected_manga_ids);

  let manga_ids = [];
  for (let id of selected_manga_ids) {
    let status = manga_repo_status[id]
    if (manga_archived.includes(id)) {
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
      console.log(`Archive ${metadata.entit}`);

      updateTotalProcessStatus(STATUS_ARCHIVING, true, archived_count, manga_ids.length);
      updateMangaProcessStatus(idd,STATUS_ARCHIVING,false);

      let archive_title_dir = `${archive_dir}/${idd}`
      if (!fs.existsSync(archive_title_dir)) {
        fs.mkdirSync(archive_title_dir);
      }

      // at first the archive status is incomplete
      setArchivedStatus(idd, ARCHIVE_INCOMPLETE, true);

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

          let ch = chapter_set[icc].split("/")[0];

          let archive_file = `${archive_title_dir}/${ch}.zip`

          let process_this_chapter = true;
          let num_archives_intact = 0
          if (fs.existsSync(archive_file)) {
            let res = await checkArchiveFileIntegrity(metadata, mdata, archive_file, ch);
            if (res == '') {
              process_this_chapter = false;
              num_archives_intact += 1;
              console.log(` * Chapter ${cs_i}/${icc} : ${archive_file} already exists`)
            } else {
              console.log(" * Deleting previous incomplete archive file")
              fs.rmSync(archive_file);  
            }
          }
    
          if (process_this_chapter) {

            let chapter_dir = `./ipfs/${ch}`;

            let ocrp = '';
            if (cs_i==1) {
              ocrp = `./ocr/${ch}.json`
              if (!fs.existsSync(ocrp)) {
                ocrp = ''; // skip occasional missing OCR file
              }
            }

            let cmd = `zip -r0 ${archive_file} ${chapter_dir} ${ocrp}`
            console.log(` * Chapter ${cs_i}/${icc} : ${chapter_dir}`)
            try {
              const { stdout, stderr } = await execSync(cmd);
            } catch (error) {
              sendProcessErrorMessage(idd, error.stderr);
              return false;      
            }
          }
          processed_chapters += 1;
        }
      }

      updateTotalProcessStatus(STATUS_VERIFYING_ARCHIVE, true, archived_count, manga_ids.length);
      // this will also set the archived status
      await checkMangaArchives(idd, metadata, mdata);

      updateMangaProcessStatus(idd,STATUS_NONE,false);
      clearLogFile(idd);
      console.log(`Archiving ${metadata.entit} completed!`);
      archived_count += 1;
    }
  }
  clearProcessStatus();
}


export async function restoreMangas(selected_manga_ids) {
  console.log("restoreMangas " + selected_manga_ids);

  let manga_ids = [];
  for (let id of selected_manga_ids) {
    let status = getArchivedStatus(id);
    if (status != ARCHIVE_COMPLETE && status != ARCHIVE_INCOMPLETE) {
      console.log(` * wont process ${id} because not archived`);
    } else {
      updateMangaProcessStatus(id, STATUS_QUEUED, true);
      manga_ids.push(id);
    }
  } 

  let restored_count=0;
  for (let ii in manob['data']) {
    let mdata = manob['data'][ii];
    let idd = mdata._id.$oid;
    let metadata = getMetadata(idd);

    if (manga_ids.includes(idd)) {
      console.log(`Restore ${metadata.entit}`);

      updateTotalProcessStatus(STATUS_RESTORING, true, restored_count, manga_ids.length);
      updateMangaProcessStatus(idd,STATUS_RESTORING,false);

      let archive_title_dir = `${archive_dir}/${idd}`
      if (!fs.existsSync(archive_title_dir)) {
        console.log(" * Deleting previous incomplete archive file")
        sendProcessErrorMessage(idd, `Archive directory ${archive_title_dir} does not exist!`);
        return false;
      }

      let chapter_sets = [mdata.en_data["ch_enh"], mdata.jp_data["ch_jph"]];
      let processed_chapters=0, total_chapters=0;
      for (let chapter_set of chapter_sets) {
          total_chapters += chapter_set.length;
      }

      for (let cs_i in chapter_sets) {
        let chapter_set = chapter_sets[cs_i];
        for (let icc in chapter_set) {

          if (stopProcessing) {
            console.log("Stopping restoring process")
            clearProcessStatus();
            stopProcessing=false;
            return false;
          }

          updateMangaProcessStatus(idd,STATUS_RESTORING,false,processed_chapters+1,total_chapters);

          let ch = chapter_set[icc].split("/")[0];

          let archive_file = `${archive_title_dir}/${ch}.zip`

          let cmd = `unzip -o ${archive_file}`
          console.log(` * Chapter ${cs_i}/${icc} from ${archive_file}`)
          try {
            const { stdout, stderr } = await execSync(cmd);
          } catch (error) {
            sendProcessErrorMessage(idd, error.stderr);
            return false;      
          }
          processed_chapters += 1;
        }
      }

      // check for missing files and set repository status
      await checkMangaFiles(idd, metadata, mdata);

      updateMangaProcessStatus(idd,STATUS_NONE,false);
      clearLogFile(idd);
      console.log(`Restoring ${metadata.entit} completed!`);
      restored_count += 1;
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

  let data = fs.readFileSync("./json/BM_data.manga_data.json", "utf8");
  let mdata = JSON.parse(data);
  manob["data"] = mdata;
  console.log("Loaded manga_data")

  data = fs.readFileSync("./json/BM_data.manga_metadata.json", "utf8");
  mdata = JSON.parse(data);
  let re1 = mdata[0];
  manob["meta"] = re1;
  cdn = re1["cdn"];
  console.log("Loaded manga_metadata")
      
  data = fs.readFileSync("./json/dw.json", "utf8" );
  data = JSON.parse(data);
  let pm = data["pm"];
  let incomplete = [];
  manga_archived = [];
  if ('incomplete' in data) {
    incomplete = data["incomplete"];
  }
  if ('archived' in data) {
    manga_archived = data["archived"];
  }
  if ('archive_incomplete' in data) {
    manga_archive_incomplete = data["archive_incomplete"];
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
