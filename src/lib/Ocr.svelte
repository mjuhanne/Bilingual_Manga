<script>
  import { onMount } from "svelte";
  import { afterUpdate } from 'svelte';
  import WordPopup from '$lib/WordPopup.svelte';
  import { learning_stage_colors, STAGE } from '$lib/LearningStages.js';

  export let id; // manga id
  export let cid; // chapter id
  export let page_jp; // jap page
  export let ocr1 = {};
  export let src = {};
  export let ocrbor = false;
  export let ocroff = false;
  export let ocron = false;

  let interactive_ocr = false;
  let colorize = false;
  let word_list;
  let word_class_list;
  let word_learning_stages;
  let word_history;

  let ocr_root;
  let mounted = false;
  let page_ref = undefined;

  let selected_word;
  let selected_word_class;
  let selected_word_stage;
  let selected_word_history;
  let selected_block;
  let showModal;

  function hoverm(e) {
    let a = e.srcElement.children[0];
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
  }


  function clicked(word_id, block_id) {
    selected_block = block_id;
    selected_word = word_list[word_id];
    selected_word_class = word_class_list[word_id];
    selected_word_stage = word_learning_stages[word_id];
    selected_word_history = word_history[word_id];
    console.log("clicked " + JSON.stringify(selected_word));
    showModal = true;
  	}

  function updateWordDecorations() {
    if (!colorize)
      return;
    let word_elements = ocr_root.querySelectorAll(".ocrtext1 span");
    for (let elem of word_elements) {
      let wid = parseInt(elem.getAttribute("wid"));
      let stage = word_learning_stages[wid];
      let col = learning_stage_colors[stage];
      elem.setAttribute("style",`border-radius: 3px; background-color:${col}`);
    }
  }

  function setClickEventListeners() {
    let word_elements = ocr_root.querySelectorAll(".ocrtext1 span");
    for (let elem of word_elements) {
      elem.addEventListener("click", (e) => {
        if (!showModal) { // prevent numerous click events
          var mousePos = {};
          var rect = e.target.getBoundingClientRect(); // get some poition, scale,... properties of the item
          mousePos.x = e.clientX - rect.left; // get the mouse position relative to the element
          mousePos.y = e.clientY - rect.top;
          //ocr_root.querySelector('.popup-dialog').style.left = mousePos.x + "px"; // set the modal position to the last stored position
          //ocr_root.querySelector('.popup-dialog').style.top = mousePos.y + "px";

          ocr_root.querySelector('.popup-dialog').style.left = rect.left-70 + "px"; // set the modal position to the last stored position
          ocr_root.querySelector('.popup-dialog').style.top = rect.top-40 + "px";

          console.log(`rect: ${rect.left}.${rect.top}  e ${e.clientX}.${e.clientY}`);
          console.log(`mousePos ${mousePos.x}.${mousePos.y}`);
          let word_id = elem.getAttribute("wid");
          let block_id = parseInt(elem.parentElement.parentElement.getAttribute("block_id"));
          clicked(word_id, block_id);
        }
      });
    }
  }

  const learningStageChanged = (e) => {
    let word = e.detail['word'];
    let new_learning_stage = e.detail['stage'];
    let idx = word_list.indexOf(word);
    let old_stage = word_learning_stages[idx];
    word_learning_stages[idx] = new_learning_stage;
    console.log("learningStageChanged " + word + " " + old_stage + " > " + new_learning_stage)
    updateWordDecorations();
  }

  afterUpdate(() => {
    if (mounted) {
      console.log("afterUpdate")
      if (interactive_ocr) {
        updateWordDecorations();
        setClickEventListeners();
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

        if ('settings' in ocr1) {
          word_list = ocr1['word_list']
          word_class_list = ocr1['word_class_list']
          word_learning_stages = ocr1['word_learning_stages']
          word_history = ocr1['word_history']
          interactive_ocr = true;
          colorize = ocr1['settings']['colorize']
        }
        console.log("Setting OCR")
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
          let fontsize = oc["font-size"] * 0.85 * ratio;
          if (oc["writing-mode"] != "vertical-rl") {
            if (oc["lines"].length > 1) fontsize /= 2;
          }
          oc["lines"].forEach((line) => {
            lines =
              lines +
              `<p class="ocrtext1"style="margin : 0;background-color:white;text-align:center;display:${ocrnon};vertical-align: top;white-space: nowrap;letter-spacing: 0.1em;line-height: 1.4em;">${line}</p>`;
          });

          let styledd = `"font-size:${fontsize}px;writing-mode:${
            oc["writing-mode"]
          };position:absolute;top:${oc.top * ratioh + src.offsetTop}px;left:${
            oc.left * ratiow + src.offsetLeft
          }px;width:${oc.width * ratiow}px;height:${
            oc.height * ratioh
          }px;border:solid ${
            2 * ratiow
          }px #41FF00;display:block;white-space: nowrap;z-index:${
            1000 - oc["font-size"]
          };"`;

          let stylebor = `"font-size:${fontsize}px;writing-mode:${
            oc["writing-mode"]
          };position:absolute;top:${oc.top * ratioh + src.offsetTop}px;left:${
            oc.left * ratiow + src.offsetLeft
          }px;width:${oc.width * ratiow}px;height:${
            oc.height * ratioh
          }px;display:block;white-space: nowrap;z-index:${
            1000 - oc["font-size"]
          };"`;

          let styleh = "";

          if (ocrbor) {
            styleh = stylebor;
          } else {
            styleh = styledd;
          }

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

<WordPopup bind:word={selected_word} bind:word_class={selected_word_class} bind:history={selected_word_history} bind:learning_stage={selected_word_stage} bind:showModal on:learning_stage_changed={learningStageChanged} bind:manga_id={id} bind:chapter_id={cid} bind:block={selected_block} bind:page={page_jp} bind:page_ref={page_ref}/>

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

  /*
  .non-jp {
    color: darkgrey;
  }
  span.known {
    color: green;
    background-color: blue;
  }
  .unknown {
    color: red;
  }
  .recog {
    color: yellow;
  }
  */
</style>
