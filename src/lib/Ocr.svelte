<script>
  import { onMount } from "svelte";
  import { afterUpdate } from 'svelte';
  import { deserialize } from '$app/forms';
  import WordPopup from '$lib/WordPopup.svelte';
  import { learning_stage_colors, STAGE, SOURCE } from '$lib/LearningData.js';

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
  let word_list;
  let word_sense_list;
  let word_class_list;
  let word_learning_stages;
  let word_history;

  let ocr_root;
  let mounted = false;
  let page_ref = undefined;

  let selected_word;
  let selected_word_senses;
  let selected_word_class;
  let selected_word_stage;
  let selected_word_history;
  let selected_block; // OCR block number in current page
  let showModal;
  let hovered_block_id = -1;

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

  function clicked(word_id, block_id) {
    selected_block = block_id;
    selected_word = word_list[word_id];
    selected_word_senses = word_sense_list[word_id];
    selected_word_class = "NA"; // word_class_list[word_id];
    selected_word_stage = word_learning_stages[word_id];
    selected_word_history = word_history[word_id];
    console.log("clicked " + JSON.stringify(selected_word));
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
        let wid = parseInt(elem.getAttribute("wid"));
        let stage = word_learning_stages[wid];
        if ( (stage != STAGE.NONE) && (stage != STAGE.IGNORED) ) {
          if (stage != STAGE.KNOWN) {
            all_known = false;
            if (stage > highest_stage) {
              highest_stage = stage;
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

  function setClickEventListeners() {
    let word_elements = ocr_root.querySelectorAll(".ocrtext1 span");
    for (let elem of word_elements) {
      let word_id = elem.getAttribute("wid");
      if (word_id != 0) {
        elem.addEventListener("click", (e) => {
          if (!showModal) { // prevent numerous click events
            var rect = e.target.getBoundingClientRect();
            ocr_root.querySelector('.popup-dialog').style.left = rect.left-70 + "px"; 
            ocr_root.querySelector('.popup-dialog').style.top = rect.top-40 + "px";
            let block_id = parseInt(elem.parentElement.parentElement.getAttribute("block_id"));
            clicked(word_id, block_id);
          }
        });
      }
    }
  }

  async function sendChangedLearningStage(word_id, block_id, learning_stage) {
    let word = word_list[word_id];
    let body = JSON.stringify({
      'func' : 'update_manually_set_word_learning_stage', 
      'stage_data' : {
        'word' : word,
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

    // add event to history temporarily like this before it gets updated after next page flip
    let new_entry = {
        's' : learning_stage,
        't' : new Date()/1000,
        'm' : {
            'src' : SOURCE.USER,
            'comment' : 'Current update',
        }
    };
    let history = word_history[word_id];
    if (result.replaced_last_entry) {
      history[history.length-1] = new_entry;
    } else {
        history.push(new_entry);
    }
  };

  const learningStageChanged = (word,new_learning_stage,block_id) => {
    let word_id = word_list.indexOf(word);
    let old_stage = word_learning_stages[word_id];
    word_learning_stages[word_id] = new_learning_stage;
    console.log("learningStageChanged " + word + " " + old_stage + " > " + new_learning_stage)
    updateWordDecorations();
    sendChangedLearningStage(word_id, block_id, new_learning_stage);
  }

  const learningStageChangedFromPopUpDialog = (e) => {
    learningStageChanged(e.detail['word'], e.detail['stage'], selected_block);
  }

  const setHoveredBlockWordsKnown = (all_stages) => {
    if (hovered_block_id != -1) {
      let block_elements = ocr_root.querySelectorAll(".ocrtext");
      for (let b_elem of block_elements) {
        let block_id = parseInt(b_elem.getAttribute("block_id"));
        if (block_id == hovered_block_id) {
          let word_elements = b_elem.querySelectorAll(".ocrtext1 span");
          for (let elem of word_elements) {
            let word_id = parseInt(elem.getAttribute("wid"));
            let word = word_list[word_id];
            if (word != '') {
              let stage = word_learning_stages[word_id];
              if (stage != STAGE.KNOWN) {
                if (all_stages || (stage == STAGE.PRE_KNOWN) || (stage == STAGE.FORGOTTEN)) {
                  learningStageChanged(word,STAGE.KNOWN,block_id);
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

  const keyPressListener = (event) => {
    var keyName = event.key;
    if (keyName == 'p') {
      debugParser();
    } else if (keyName == 'k') {
      setHoveredBlockWordsKnown(false);
    } else if (keyName == 'K') {
      setHoveredBlockWordsKnown(true);
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
          word_list = ocr1['parsed_data']['word_list']
          word_sense_list = ocr1['parsed_data']['word_senses']
          //word_class_list = ocr1['word_class_list']
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

<WordPopup bind:word={selected_word} bind:word_class={selected_word_class} bind:word_sense_list={selected_word_senses} bind:history={selected_word_history} bind:learning_stage={selected_word_stage} bind:showModal on:learning_stage_changed={learningStageChangedFromPopUpDialog}/>

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
