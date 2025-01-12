<script>
  import { onMount } from "svelte";
  import { afterUpdate } from 'svelte';
  import { deserialize } from '$app/forms';
  import WordPopup from '$lib/WordPopup.svelte';
  import AnkiCardDialog from '$lib/AnkiCardDialog.svelte';
  import { learning_stage_colors, STAGE, SOURCE } from '$lib/LearningData.js';
  import Edit_OCR_Dialog from '$lib/Edit_OCR_Dialog.svelte'
  import { getWordIdIndexList, UpdatePriorityWordManually, updateWordDecorations, setWordPopupToElementPosition, learningStageChanged } from '$lib/WordPopupHelper.js'
  import InfoPopUp from '$lib/InfoPopUp.svelte'

  let infopopup;
  export let id; // manga id
  export let cid; // chapter id
  export let page_jp; // jap page
  export let ocr1 = {};
  export let src = {};
  export let ocrbor;
  export let ocroff = false;
  export let ocron = false;
  export let img_id;
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
  let selected_word; // back-propagated exact word from WordPopup dialog
  let selected_word_readings; // back-propagated word readings from WordPopup dialog
  let selected_word_glossary; // back-propagated word glossary from WordPopup dialog
  let selected_block_content; // text from selected block
  let showWordPopUpDialog;
  let showEditOCRDialog;
  let hovered_block_id = -1;
  export let edit_mode = false; // signaled back to Reader to turn off keypress handling during textual editing
  let edited_ocr_block = [];
  export let img_eng = ''
  export let img_jap = ''
  let openAnkiCardDialog;

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
    showWordPopUpDialog = true;
  	}


  function setClickEventListeners() {
    let word_elements = ocr_root.querySelectorAll(".ocrtext1 span");
    for (let elem of word_elements) {
      let word_id_index_list = getWordIdIndexList(elem);
      if (word_id_index_list.length > 0) {
        elem.addEventListener("click", (e) => {
          if (!showWordPopUpDialog) { // prevent numerous click events
            setWordPopupToElementPosition(e.target, document.getElementById(img_id), ocr_root);
            let block_element = elem.parentElement.parentElement;
            let block_id = parseInt(block_element.getAttribute("block_id"));
            let item_id = parseInt(elem.getAttribute("ii"));
            clicked(elem.innerText,word_id_index_list, block_id, item_id);
          }
        });
      }
    }
  }


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


  const learningStageChangedFromPopUpDialog = (e) => {
    learningStageChanged(word_id_list, word_learning_stages, e.detail['word_id'], e.detail['stage'], selected_block, cid, page_jp, page_ref);
    if (colorize) {
      updateWordDecorations(ocr_root, word_id_list, word_learning_stages, ocrbor, border_thickness, learning_stage_colors);
    }
  }

  const ShowAnkiCardDialog = (e) => {
    selected_word = e.detail['word']
    selected_word_glossary = e.detail['glossary']
    selected_word_readings = e.detail['readings']
    selected_block_content = ocrpage[selected_block]["og_lines"];
    openAnkiCardDialog();
  }

  async function PriorityWordUpdatedManuallyFromPopUpDialog(e) {
    let ocr_block = ocrpage[selected_block]["og_lines"];
    UpdatePriorityWordManually(
      ocr_root, id, cid, e.detail['word_id'], e.detail['scope'], ocr_block, 
      selected_text, selected_block, selected_item_id, page_jp, page_ref, word_id_list
    )
    if (colorize) {
      updateWordDecorations(ocr_root, word_id_list, word_learning_stages, ocrbor, border_thickness, learning_stage_colors);
    }
  }

  const OCRBlockUpdated = (e) => {
    let new_ocr_block = e.detail['ocr_block'];
    sendChangedOCRBlock(ocrpage[selected_block]["og_lines"], new_ocr_block, selected_block );
    ocrpage[selected_block]["lines"] = new_ocr_block;
    //selected_block);
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
          showEditOCRDialog = true;
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
                  learningStageChanged(word_id_list, word_learning_stages, wid0, STAGE.KNOWN, block_id, cid, page_jp, page_ref);
                  if (colorize) {
                    updateWordDecorations(ocr_root, word_id_list, word_learning_stages, ocrbor, border_thickness, learning_stage_colors);
                  }
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

async function translateHoveredBlock() {
    if (hovered_block_id != -1) {
      let block_text = ''
      let oc = ocrpage[hovered_block_id];
      oc["og_lines"].forEach((line) => {
        block_text += line
        });
      let body = JSON.stringify({
      'func' : 'translate', 
      'text' : block_text,
      });
      fetch( "/deepl", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
      }).then(response => {
        response.json().then(result => {
          let txt;
          if (result.success) {
            txt = result.translation;
          } else {
            txt = result.error;
          }
          infopopup.show("DeepL translation",`<p>${block_text}</p><p>${txt}</p>`)
        });
      });
    }
  }

async function adjustHoveredBlockSize(adjustment) {
    function adjustPx(elem, style_name, adjust) {
        let px_value = elem.style[style_name]
        let val = parseInt(px_value.split('px')[0]);
        px_value = (val + adjust).toString() + "px"
        elem.style[style_name] = px_value
    }
    if (hovered_block_id != -1) {
        let block_elements = ocr_root.querySelectorAll(".ocrtext");
        for (let b_elem of block_elements) {
            let block_id = parseInt(b_elem.getAttribute("block_id"));
            if (block_id == hovered_block_id) {
                console.log(b_elem.style);
                adjustPx(b_elem, "font-size", adjustment )
                adjustPx(b_elem, "left", -10*adjustment )
                adjustPx(b_elem, "height", 10*adjustment )
                adjustPx(b_elem, "width", 10*adjustment )
                console.log(b_elem.style.height);
            }
        }
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
    } else if (keyName == 't') {
      translateHoveredBlock();
    } else if (keyName == '-') {
      adjustHoveredBlockSize(-1);
    } else if (keyName == '+') {
      adjustHoveredBlockSize(1);
    }
  }

  afterUpdate(() => {
    if (mounted) {
      if (interactive_ocr) {
        if (colorize) {
          updateWordDecorations(ocr_root, word_id_list, word_learning_stages, ocrbor, border_thickness, learning_stage_colors);
        }
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
          let fontsize = oc["font-size"];
          if (fontsize.toString().indexOf("px") != -1) {
            fontsize = parseInt(fontsize.split("px")[0])
          }
          fontsize *= ratio;
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

<WordPopup bind:word_id_index_list={selected_word_id_index_list} 
  {word_id_list} {word_history} {word_learning_stages} 
  bind:showModal={showWordPopUpDialog} on:learning_stage_changed={learningStageChangedFromPopUpDialog}
  on:priority_word_updated_manually={PriorityWordUpdatedManuallyFromPopUpDialog}
  on:anki_button_clicked={ShowAnkiCardDialog}
/>
<InfoPopUp bind:this={infopopup}/>
<Edit_OCR_Dialog bind:ocr_block={edited_ocr_block} bind:showModal={showEditOCRDialog} bind:edit_mode={edit_mode} on:ocr_block_updated={OCRBlockUpdated}/>
<AnkiCardDialog bind:openDialog={openAnkiCardDialog} bind:edit_mode={edit_mode} word={selected_word} glossary={selected_word_glossary} readings={selected_word_readings} sentence_lines={selected_block_content} {img_jap} {img_eng}/>


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
