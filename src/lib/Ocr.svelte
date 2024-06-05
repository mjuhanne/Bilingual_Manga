<script>
  import { onMount } from "svelte";
  import { afterUpdate } from 'svelte';
  import { deserialize } from '$app/forms';
  import WordPopup from '$lib/WordPopup.svelte';
  import { learning_stage_colors, STAGE, SOURCE } from '$lib/LearningData.js';
  import Edit_OCR_Dialog from '$lib/Edit_OCR_Dialog.svelte'

  export let id; // manga id
  export let cid; // chapter id
  export let page_jp; // jap page
  export let ocr1 = {};
  export let src = {};
  export let ocrbor;
  export let ocroff = false;
  export let ocron = false;
  let border_thickness = [];

  let interactive_ocr = false;
  let colorize = false;
  let word_id_list;
  let word_learning_stages;
  let word_history;

  let ocr_root;
  let mounted = false;
  let page_ref = undefined;

  let selected_word_id_index_list;
  let selected_block; // Selected OCR block number in current page
  let selected_item_id; // OCR item in selected block
  let selected_text; // Clicked item text
  let showModal;
  let hovered_block_id = -1;
  export let edit_mode = false;
  let edited_ocr_block = [];

  function hoverm(e) {
    let a = e.srcElement.children[0];
    hovered_block_id = parseInt(a.getAttribute("block_id"));
    let l = a.children;
    for (let i = 0; i < l.length; i++) {
      l[i].style.display = "table";
    }
  }

  function hovero(e) {
    let a = e.srcElement.children[0];
    let l = a.children;
    for (let i = 0; i < l.length; i++) {
      if (!ocron) {
        l[i].style.display = "none";
      }
    }
    hovered_block_id = -1;
  }
  $: console.log(hovered_block_id);

  function clicked(text, word_id_index_list, block_id, item_id) {
    selected_block = block_id;
    selected_item_id = item_id;
    selected_text = text;
    selected_word_id_index_list = word_id_index_list;
    console.log(`clicked block ${block_id} item ${item_id} [${text}]:`);
    for (let idx of word_id_index_list) {
      console.log(word_id_list[idx]);
    }
    showModal = true;
  	}

  function updateWordDecorations() {
    if (!colorize)
      return;
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
        let col = learning_stage_colors[stage];
        elem.setAttribute("style",`border-radius: 3px; background-color:${col}`);
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

  function setWordPopupToElementPosition(elem) {
    var rect = elem.getBoundingClientRect();
    ocr_root.querySelector('.popup-dialog').style.left = rect.left-70 + "px"; 
    ocr_root.querySelector('.popup-dialog').style.top = rect.top-40 + "px";
  }

  function setClickEventListeners() {
    let word_elements = ocr_root.querySelectorAll(".ocrtext1 span");
    for (let elem of word_elements) {
      let word_id_index_list = getWordIdIndexList(elem);
      if (word_id_index_list.length > 0) {
        elem.addEventListener("click", (e) => {
          if (!showModal) { // prevent numerous click events
            setWordPopupToElementPosition(e.target);
            let block_id = parseInt(elem.parentElement.parentElement.getAttribute("block_id"));
            let item_id = parseInt(elem.getAttribute("ii"));
            clicked(elem.innerText,word_id_index_list, block_id, item_id);
          }
        });
      }
    }
  }

  async function sendChangedLearningStage(word_id, block_id, learning_stage) {
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


  async function sendChangedOCRBlock(old_block,new_block,block_id) {
    let body = JSON.stringify({
      'func' : 'update_ocr_block', 
      'cid' : cid,
      'ocr_data' : {
        'pr' : page_ref,
        'b' : block_id,
        'old_block' : old_block,
        'new_block' : new_block,
        },
      }
    );
    const response = await fetch( "/ocr", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });
    const result = deserialize(await response.text());
  };

  const learningStageChanged = (word_id,new_learning_stage,block_id) => {
    sendChangedLearningStage(word_id, block_id, new_learning_stage);
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
    updateWordDecorations();
  }

  const learningStageChangedFromPopUpDialog = (e) => {
    learningStageChanged(e.detail['word_id'], e.detail['stage'], selected_block);
  }

  async function PriorityWordUpdatedManuallyFromPopUpDialog(e) {
    let wid = e.detail['word_id'];
    console.log(`Update ${selected_text} priority word to ${wid}`)
    let ocr_block = ocrpage[selected_block]["og_lines"];

    let body = JSON.stringify({
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
        },
    });
    const response = await fetch( "/ocr", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
    });
    const result = deserialize(await response.text());

    // Update current page to avoid total page refresh
    let block_elements = ocr_root.querySelectorAll(".ocrtext");
    for (let b_elem of block_elements) {
      let block_id = parseInt(b_elem.getAttribute("block_id"));
      if (block_id == selected_block) {
        let word_elements = b_elem.querySelectorAll(".ocrtext1 span");
        for (let elem of word_elements) {
          let item_id = elem.getAttribute("ii");
          if (item_id == selected_item_id) {
            UpdateWordIdIndexList(elem, word_id_list.lastIndexOf(wid));
          }
        }
      }
    }
    updateWordDecorations();
  }
  

  const OCRBlockUpdated = (e) => {
    let new_ocr_block = e.detail['ocr_block'];
    sendChangedOCRBlock(ocrpage[selected_block]["og_lines"], new_ocr_block, selected_block );
    ocrpage[selected_block]["lines"] = new_ocr_block;
    //selected_block);
  }

  const getWordIdIndexList = (elem) => {
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


  const editHoveredBlock = () => {
    if (hovered_block_id != -1) {
      let block_elements = ocr_root.querySelectorAll(".ocrtext");
      for (let b_elem of block_elements) {
        let block_id = parseInt(b_elem.getAttribute("block_id"));
        if (block_id == hovered_block_id) {
          edited_ocr_block = []
          let oc = ocrpage[hovered_block_id];
          oc["og_lines"].forEach((line) => {
            edited_ocr_block.push(line)
            });
          console.log("EditHoveredBlock block_id" + edited_ocr_block);
          selected_block = block_id;
          edit_mode = true;
        }
      }
      console.log("EditHoveredBlock" + hovered_block_id);
    }
  }

  const setHoveredBlockWordsKnown = (all_stages) => {
    if (hovered_block_id != -1) {
      let block_elements = ocr_root.querySelectorAll(".ocrtext");
      for (let b_elem of block_elements) {
        let block_id = parseInt(b_elem.getAttribute("block_id"));
        if (block_id == hovered_block_id) {
          let word_elements = b_elem.querySelectorAll(".ocrtext1 span");
          for (let elem of word_elements) {
            let particle = elem.innerText;

            let word_id_index_list = getWordIdIndexList(elem);
            if (word_id_index_list.length>0) {
              console.log("Inspecting " + particle + " with " + word_id_index_list.length + " refs");
              let word_idx = word_id_index_list[0];
              let word_id = word_id_list[word_idx];

              let ws = word_id.split(':')
              let ss = ws[0].split('/')
              let wid0 = ss[0] + ':' + ws[1];

              let stage = word_learning_stages[word_idx];
              if (stage != STAGE.KNOWN) {
                if (all_stages || (stage == STAGE.PRE_KNOWN) || (stage == STAGE.FORGOTTEN)) {
                  console.log(`Setting learning stage of ${particle} (${wid0}) to KNOWN`);
                  learningStageChanged(wid0,STAGE.KNOWN,block_id);
                }
              }
            }
          }
        }
      }
    }
  }

  async function debugParser() {
    if (hovered_block_id != -1) {
      let block_text = []
      let oc = ocrpage[hovered_block_id];
      oc["og_lines"].forEach((line) => {
        block_text.push(line)
        });
      let body = JSON.stringify({
      'func' : 'parse', 
      'text' : block_text,
      });
      const response = await fetch( "/jmdict", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
      });
    }
  }

  async function debugOcr() {
    if (hovered_block_id != -1) {
      let body = JSON.stringify({
      'func' : 'debug_ocr',
      'chapter_id' : cid,
      'page_ref' : page_ref,
      'block_id' : hovered_block_id,
      });
      const response = await fetch( "/ocr", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
      });
    }
  }

  const keyPressListener = (event) => {
    var keyName = event.key;
    if (keyName == 'p') {
      debugParser();
    } else if (keyName == 'o') {
      debugOcr();
    } else if (keyName == 'k') {
      setHoveredBlockWordsKnown(false);
    } else if (keyName == 'K') {
      setHoveredBlockWordsKnown(true);
    } else if (keyName == 'e') {
      editHoveredBlock();
    }
  }

  afterUpdate(() => {
    if (mounted) {
      if (interactive_ocr) {
        updateWordDecorations();
        setClickEventListeners();
        document.addEventListener('keydown', keyPressListener, false);
      }
    }
	});    

  onMount(() => {
    mounted = true;
  });

  $: na = src.src;
  $: ocrpage = {};
  $: tocr = [];
  $: {

    let ocrnon = "none";
    if (ocron && !ocroff) {
      ocrnon = "table";
    } else {
      ocrnon = "none";
    }
    if (na != undefined) {
      let nam = `${na.split("/").pop()}`;
      nam = `${nam.substring(0, nam.lastIndexOf("."))}`;
      nam = decodeURI(nam);

      if (`${nam}` in ocr1 && ocr1[`${nam}`] != undefined && !ocroff) {

        if ('version' in ocr1) {
          word_id_list = ocr1['parsed_data']['word_id_list']
          word_learning_stages = ocr1['word_learning_stages']
          word_history = ocr1['word_history']
          interactive_ocr = true;
          colorize = ocr1['settings']['colorize']
        }
        page_ref = nam;
        ocrpage = ocr1[`${nam}`];
        let oc;
        let temp = [];
        for (let i = 0; i < ocrpage.length; i++) {
          oc = ocrpage[i];
          let ratioh = src.height / oc.img_h;
          let ratiow = src.width / oc.img_w;
          let ratio = (ratioh + ratiow) / 2;
          let lines = "";
          let fontsize = oc["font-size"] * 1 * ratio;
          oc["lines"].forEach((line) => {
            lines =
              lines +
              `<p class="ocrtext1"style="margin : 0;background-color:white;text-align:center;display:${ocrnon};vertical-align: top;white-space: nowrap;letter-spacing: 0.1em;line-height: 1.4em;">${line}</p>`;
          });

          border_thickness[i] = 2 * ratiow;
          let styleh = "";

          styleh = `"font-size:${fontsize}px;writing-mode:${
              oc["writing-mode"]
            };position:absolute;top:${oc.top * ratioh + src.offsetTop}px;left:${
              oc.left * ratiow + src.offsetLeft
            }px;width:${oc.width * ratiow}px;height:${
              oc.height * ratioh
            }px;display:block;white-space: nowrap;z-index:${
              1000 - oc["font-size"]
            };`;
          if (ocrbor == 'always_on') {
            styleh += `border:solid ${
              2 * ratiow
            }px #41FF00`;
          }
          styleh += '"';

          let hoc = `<div class="ocrtext" block_id=${i} style=${styleh}>${lines}</div>`;
          temp.push(hoc);
        }
        tocr = temp;

        const boxes = document.querySelectorAll(".ocrtext");

        boxes.forEach((box) => {
          box.style.display = "block";
        });

      } else {
        const boxes = document.querySelectorAll(".ocrtext");

        boxes.forEach((box) => {
          box.style.display = "none";
        });
      }
    }
  }

</script>

<div bind:this={ocr_root}>

<WordPopup bind:word_id_index_list={selected_word_id_index_list} {word_id_list} {word_history} {word_learning_stages} bind:showModal on:learning_stage_changed={learningStageChangedFromPopUpDialog} on:priority_word_updated_manually={PriorityWordUpdatedManuallyFromPopUpDialog}/>
<Edit_OCR_Dialog bind:ocr_block={edited_ocr_block} bind:showModal={edit_mode} on:ocr_block_updated={OCRBlockUpdated}/>

{#each tocr as tdi}
  <div class="ocrsp" on:mouseenter={hoverm} on:mouseleave={hovero}>
    {@html tdi}
  </div>
{/each}
</div>

<style>
  .ocrsp {
    cursor: auto;
    color: black;
  }
</style>
