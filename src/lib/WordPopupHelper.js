import { learning_stage_colors, STAGE, SOURCE } from '$lib/LearningData.js';
import { deserialize } from '$app/forms';


export function setWordPopupToElementPosition(elem, container_elem, ocr_root) {
    var rect = elem.getBoundingClientRect();
    var pageRect = container_elem.getBoundingClientRect();
    // Try to fit the popup dialog nicely inside the container (image or page)
    if (rect.left-230 > pageRect.left) {
      ocr_root.querySelector('.popup-dialog').style.left = rect.left-230 + "px"; 
    } else {
      ocr_root.querySelector('.popup-dialog').style.left = rect.right + 20 + "px"; 
    }
    if (rect.top + 270 < pageRect.bottom) {
      ocr_root.querySelector('.popup-dialog').style.top = rect.top + window.scrollY -30 + "px";
    } else {
      ocr_root.querySelector('.popup-dialog').style.top = pageRect.bottom + window.scrollY -270 + "px";
    }
  }

const ignored_characters = 'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ％０１２３４５６７８９０。、？（）　＊～・『』「」─…0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ., <>《》〈〉！〝〟"'

function does_word_consist_of_ignored_characters(word) {
    for (let i=0;i<word.length;i++) {
        let w = word[i];
        let idx = ignored_characters.indexOf(word[i]);
        if (ignored_characters.indexOf(word[i])==-1) {
            return false;
        }
    }
    return true;
}

export function updateWordDecorations(ocr_root, word_id_list, word_learning_stages, ocrbor, border_thickness, learning_stage_palette) {
  let block_elements = ocr_root.querySelectorAll(".ocrtext");
  for (let b_elem of block_elements) {
    let block_id = parseInt(b_elem.getAttribute("block_id"));
    let word_elements = b_elem.querySelectorAll(".ocrtext1 span");
    let highest_stage = 0;
    let all_known = true;

    for (let elem of word_elements) {
      let stage = STAGE.NONE;
      // TODO: show the learning stage of other (than first) references by
      // changing the border color
      let word_id_index_list = getWordIdIndexList(elem);
      if (word_id_index_list.length > 0) {
        let widx = word_id_index_list[0];
        stage = word_learning_stages[widx];
        if (elem.innerText == 'ちり') {
          console.log('chiri',widx,word_id_list[widx],stage)
        }
        if (stage==STAGE.FORGOTTEN) {
          console.log("Forgot" + word_id_list[widx] + ":" + elem.getAttribute("wil"));
        }
        if ( (stage != STAGE.NONE) && (stage != STAGE.IGNORED) ) {
          if (stage != STAGE.KNOWN) {
            all_known = false;
            if (stage > highest_stage) {
              highest_stage = stage;
            }
          }
        }
      }
      if (does_word_consist_of_ignored_characters(elem.innerText)) {
        stage = STAGE.IGNORED;
      }
      let col = learning_stage_palette[stage];
      elem.setAttribute("style",`text-wrap: nowrap; border-radius: 3px; background-color:${col}`);
    }

    // colorize the border with highest learning stage (FORGOTTEN > PRE_KNOWN > LEARNING > UNFAMILIAR)
    // or hide it if all the words are known (or ignored)
    if (ocrbor == 'colorize') {
      if (all_known) {
        b_elem.style.border = `none`
      } else {
        b_elem.style.border = `solid ${border_thickness[block_id]}px ${learning_stage_colors[highest_stage]}`
      }
    }
  }
}


async function sendChangedLearningStage(word_id, block_id, learning_stage, cid, page_jp, page_ref) {
  let body = JSON.stringify({
    'func' : 'update_manually_set_word_learning_stage', 
    'stage_data' : {
      'word_id' : word_id,
      'stage' : learning_stage,
      'metadata' : {
          //'id' : manga_id,
          'cid' : cid,
          'p' : page_jp,
          'b' : block_id,
          'pr' : page_ref,
      },
    }
  });
  const response = await fetch( "/user_data", {
      headers: {"Content-Type" : "application/json" },
      method: 'POST',
      body: body,
  });
  const result = deserialize(await response.text());
};

    
    
export const learningStageChanged = (word_id_list, word_learning_stages, word_id,new_learning_stage,block_id, cid, page_jp, page_ref) => {
    sendChangedLearningStage(word_id, block_id, new_learning_stage, cid, page_jp, page_ref);
    // change the learning stage for all the word senses. This is just
    // a temporary measure until the page changes and OCR file is reloaded and
    // filled with the saved stage
    for (let word_idx in word_id_list) {
      let wid = word_id_list[word_idx];
      let ws = wid.split(':')
      let ss = ws[0].split('/')
      let wid0 = ss[0] + ':' + ws[1];
      if (wid0 == word_id) {
        let old_stage = word_learning_stages[word_idx];
        word_learning_stages[word_idx] = new_learning_stage;
        console.log("learningStageChanged " + wid + " " + old_stage + " > " + new_learning_stage)
      }
    }
  }


  export async function UpdatePriorityWordManually(
    ocr_root, title_id, cid, wid, scope, ocr_block, 
    selected_text, selected_block, selected_item_id, page_jp, page_ref, word_id_list,
  ) {
    console.log(`Update ${selected_text} priority word to ${wid} (scope ${scope})`)
    let body;
    if (scope == 'sentence') {
      body = {
      'func' : 'update_manually_priority_word', 
      'cid' : cid,
      'word_data' : {
        'w' : selected_text,
        'wid' : wid,
        'block' : ocr_block,
        'bid' : selected_block,
        'iid' : selected_item_id,
        'p' : page_jp,
        'pr' : page_ref,
        }
      };
    } else if (scope == 'chapter') {
      body = {
        'func' : 'update_manually_priority_word', 
        'cid' : cid,
        'word_data' : {
          'wid' : wid,
          'pr' : 'ALL',
        }
      }
    } else if (scope == 'title') {
      body = {
        'func' : 'update_manually_priority_word', 
        'cid' : title_id,
        'word_data' : {
          'wid' : wid,
          'pr' : 'ALL',
        }
      }
    } else if (scope == 'all') {
      body = {
        'func' : 'update_manually_priority_word', 
        'cid' : 'ALL',
        'word_data' : {
          'wid' : wid,
          'pr' : 'ALL',
        }
      }
    }

    const response = await fetch( "/ocr", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: JSON.stringify(body),
    });
    const result = deserialize(await response.text());

    // Update current page to avoid total page refresh
    let block_elements = ocr_root.querySelectorAll(".ocrtext");
    let widx = word_id_list.lastIndexOf(wid);
    for (let b_elem of block_elements) {
      let block_id = parseInt(b_elem.getAttribute("block_id"));
      if (block_id == selected_block || scope != 'sentence') {
        let word_elements = b_elem.querySelectorAll(".ocrtext1 span");
        for (let elem of word_elements) {
          let item_id = parseInt(elem.getAttribute("ii"));
          let widx_list = getWordIdIndexList(elem);
          if ( (scope == 'sentence') && (item_id == selected_item_id ) || 
              (scope != 'sentence' && widx_list.indexOf(widx) != -1)
            ) {
            UpdateWordIdIndexList(elem, widx);
            let new_widx_list = getWordIdIndexList(elem);
            console.log("Updated",elem.innerText,"widx_list",new_widx_list,word_id_list[new_widx_list[0]])
          }
        }
      }
    }
  }


  export const getWordIdIndexList = (elem) => {
    let widx_list = elem.getAttribute("wil").split(',');
    if (widx_list[0] == "") {
      return [];
    }
    let wil = [];
    for (let wi of widx_list) {
      wil.push(parseInt(wi))
    }
    return wil
  }

  const UpdateWordIdIndexList = (elem, priority_widx) => {
    let widx_list = elem.getAttribute("wil").split(',');
    let wil = [priority_widx];
    for (let wi of widx_list) {
      if (wi != priority_widx) {
        wil.push(parseInt(wi))
      }
    }
    let wil_str = wil.join(',')
    elem.setAttribute("wil",wil_str)
  }
