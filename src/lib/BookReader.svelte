<script>
  import { afterUpdate } from 'svelte';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation'
  import { page } from '$app/stores'
  import { bind } from "svelte/internal";

	import BookDashboard from "./BookDashboard.svelte";
  import WordPopup from '$lib/WordPopup.svelte';
  //import AnkiCardDialog from '$lib/AnkiCardDialog.svelte';
  import { book_learning_stage_colors_day, book_learning_stage_colors_night, STAGE, SOURCE } from '$lib/LearningData.js';
  import { getWordIdIndexList, UpdatePriorityWordManually, updateWordDecorations, setWordPopupToElementPosition, learningStageChanged } from '$lib/WordPopupHelper.js'

	export let id=''; // manga id
	export let cid=''; // chapter id
	export let lang="JP";
	export let indicator={a:0,b:0,c:false,d:false};
	export let chaptersen=[];
	export let chaptersjp=[];
	export let volumesen={};
	export let volumesjp={};
	export let vi=0;
	export let vj=0;
	export let iii; // eng vol
	export let jjj; // jap vol
  export let endata;
  export let jpdata;
  export let ipfsgate;
	let jpcolor="";
	let encolor="";
	let edit_mode=false;
  let mounted = false;
  let night_mode = true;
  let loaded_timestamp;

  let reader_root;
  let hovered_block_id = -1;
  let hovered_sentence_id = -1;
  let selected_word_id_index_list;
  let selected_block; // Selected OCR block number in current page
  let selected_sentence_id; // Selected sentence id number in current page
  let selected_item_id; // OCR item in selected block
  let selected_text; // Clicked item text
  /*
  let selected_word; // back-propagated exact word from WordPopup dialog
  let selected_word_readings; // back-propagated word readings from WordPopup dialog
  let selected_word_glossary; // back-propagated word glossary from WordPopup dialog
  let selected_block_content; // text from selected block
  */
  let showWordPopUpDialog;

  let word_id_list;
  let word_learning_stages;
  let word_history;
  let colorize = true;
  let parsed_page;

  let fetched_en_chapter_id = '';
  let fetched_jp_chapter_id = '';
  let pages_jp = '';
  let pages_en = '';
  let en_text_loaded = false;
  let jp_text_processed = false;
  let jp_decoration_done = false;

  let auto_scroll = true;
  let jp_scroll_pct = 0;
  let en_scroll_pct = 0;
  let jap_scroll_timestamp = Date.now();
  let eng_scroll_timestamp = Date.now();
  let manual_en_scroll_offset = 0;

  $: jp_chapter_id = jpdata['chapter_ids'][jjj];
  $: en_chapter_id = endata['chapter_ids'][iii];

  let en_items = {
    p_pos : [],
    p_chars : [],
    total_chars : 0,
  }
  let jp_items = {
    p_pos : [],
    p_chars : [],
    total_chars : 0,
  }

	$:j=0;
	$: langds=lang==="JP"?"ENG":"JP";

  let book_learning_stage_colors;

  $: {
    book_learning_stage_colors= (night_mode ? book_learning_stage_colors_night : book_learning_stage_colors_day)
    if (mounted && colorize) {
      updateWordDecorations(reader_root, word_id_list, word_learning_stages, false, undefined, book_learning_stage_colors);
    }
  }

  export let jpp = [0];  // jap page
	export let enp = [0];  // eng page

  function fetchContent() {

      if (jp_chapter_id != fetched_jp_chapter_id) {

          let ipfspath=ipfsgate.replace('%@cid@%',jp_chapter_id);

          fetch( ipfspath + "/pages.html").then(
              (response) => {
              if (response.ok) {
                  response.text().then((text) => {
                      text = text.replaceAll('%@ipfs_cid@%',ipfspath);
                      text = text.replaceAll('%@img_style@%',"max-width:100%;max-height:100%;");
                      pages_jp = text
                  });
              } else {
                  pages_jp =  '<div>JP pages not found</div>'
              }
          }).catch(error => {
              pages_jp = '<div>JP pages not found</div>'
          });

          fetch( "/book", {
              headers: {"Content-Type" : "application/json" },
              method: 'POST',
              body: JSON.stringify({'func': 'fetch_book_chapter', 'chapter_id':jp_chapter_id}),
          }).then(response => response.json()).then(
              (response) => {
              if (response.success) {
                  processChapterData(response.chapter_data);
                  refresh();
              } else {
                  console.log("Error fetching chapter data for" + jp_chapter_id)
              }
          });

          fetched_jp_chapter_id = jp_chapter_id;
        }

      if (en_chapter_id != fetched_en_chapter_id) {

          let ipfspath=ipfsgate.replace('%@cid@%',en_chapter_id);

          fetch( ipfspath + "/pages.html").then(
              (response) => {
              if (response.ok) {
                  response.text().then((text) => {
                      text = text.replaceAll('%@ipfs_cid@%',ipfspath);
                      text = text.replaceAll('%@img_style@%',"max-width:100%;max-height:100%;");
                      pages_en = text;
                      en_text_loaded = true;
                  });
              } else {
                  //pages_en =  '<div>EN pages not found</div>'
              }
          }).catch(error => {
              //pages_en = '<div>EN pages not found</div>'
          });

          fetched_en_chapter_id = en_chapter_id;
        }

    }

    function processChapterData(chapter_data) {

        console.log("Process chapter data")

        word_id_list = chapter_data['parsed_data']['word_id_list']
        word_learning_stages = chapter_data['word_learning_stages']
        word_history = chapter_data['word_history']
        colorize = chapter_data['settings']['colorize']

        parsed_page = chapter_data['0'];
        let p;
        let sentence_id = 0;
        for (let i = 0; i < parsed_page.length; i++) {
            p = parsed_page[i];
            //oc["writing-mode"] = "vertical-rl"
            p["writing-mode"] = "horizontal-rl"
            let lines = "";
            let fontsize = 15;
            let j = 0;
            p["lines"].forEach((line) => {
                lines =
                lines +
                `<span class="ocrtext1" sid="${sentence_id}">${line}</span>`;
                sentence_id += 1;
            });

            let styleh = "";

            styleh = `"font-size:${fontsize}px;writing-mode:${
                p["writing-mode"]
                };display:inline-block;z-index:${
                1000
                };`;
            styleh += '"';

            let elems = document.querySelectorAll(`[block_id="${i}"]`);
            for (let elem of elems) {
                //let hoc = `<p class="ocrtext" block_id=${i} style=${styleh}>${lines}</p>`;
                elem.innerHTML = lines;
                if (elem.className.indexOf("ocrtext") == -1) {
                    elem.className += " ocrtext";
                }
                for (let s_elem of elem.children) {
                  s_elem.addEventListener('mouseenter', hover_sentence_on);
                  s_elem.addEventListener('mouseleave', hover_sentence_off);
                }
                elem.addEventListener('mouseenter', hoverm);
                elem.addEventListener('mouseleave', hovero);
            }
        }
        loaded_timestamp = Date.now();
        jp_text_processed = true;
        console.log("Process chapter data - end")
    }

    const heading_tags = ['h1','h2','h3','h4','h5'];

    function doProcessElementPositions(sub_elem, items, lang) {
      for (let elem of sub_elem.children) {
          if (elem.localName=='p') {
            items.p_pos.push(elem.offsetTop+elem.offsetHeight);
            items.p_chars.push(elem.innerText.length+1)
            items.total_chars += elem.innerText.length+1
          } else if ((heading_tags.indexOf(elem.localName) != -1) && (elem.innerText.length>0)) {
            // faux text length for headings
            let faux_chars = parseInt((elem.offsetWidth/15)*elem.offsetHeight/15);
            //console.log(lang,"faux char",faux_chars);
            items.p_pos.push(elem.offsetTop+elem.offsetHeight);
            items.p_chars.push(faux_chars);
            items.total_chars += faux_chars
          } else if (elem.localName=='div' || elem.localName=='section') {
            doProcessElementPositions(elem,items,lang);
          } else {
            // faux text length for other items
            items.p_pos.push(elem.offsetTop+elem.offsetHeight);
            items.p_chars.push(5);
            items.total_chars += 5
          }
        }
    }

    // save element positions for side-by-side scrolling
    function processElementPositions(page_container_elem, items, lang) {

      if (page_container_elem.children.length==0) {
        return;
      }

      items.p_pos = [];
      items.p_chars = [];
      items.total_chars = 0;

      doProcessElementPositions(page_container_elem, items, lang);

      // stub element for lower margin
      items.p_pos.push(page_container_elem.scrollHeight)
      items.p_chars.push(1);
      items.total_chars += 1
    }

  afterUpdate(() => {
    if (!jp_decoration_done)
      return;

    if (en_text_loaded) {
      let jp_elem = document.getElementById("jp_chapter_page")
      processElementPositions(jp_elem, jp_items,"jp");
    
      let en_elem = document.getElementById("en_chapter_page")
      processElementPositions(en_elem, en_items,"en");
    }

    let pos = getChapterPosition(cid)
    if (Math.abs(jp_scroll_pct-pos)>1) {
      jp_elem.scrollTop = pos*jp_elem.scrollHeight/100 - jp_elem.clientHeight
      onJapScroll(undefined);
    }
  });

  $: if (jjj != '' || iii != '') fetchContent();

	onMount(() => {
        mounted = true;
        refresh();
        console.log("onMount")
    });

	const allquerys=()=>{
		let nlang=lang==="JP"?"jp":"en";		
		$page.url.searchParams.set('lang',nlang);
		$page.url.searchParams.set('chjp',jjj);
		$page.url.searchParams.set('chen',iii);
		//$page.url.searchParams.set('enp',enp[0]);
		//$page.url.searchParams.set('jpp',jpp[0]);
		setTimeout(()=>{      
      goto(`?${$page.url.searchParams.toString()}#img_store`,{replaceState:true})
    },200);
      refresh();	
	};
	
	$:{if(lang==="ENG")
	{		
			//j=enp[0];
			encolor="background-color:rgba(255,255,255,0.3);"
			jpcolor=""

	}
	else if(lang==="JP")
	{	
		//j=jpp[0];
		jpcolor="background-color:rgba(255,255,255,0.3);"
		encolor=""

	}}		

	const refresh=()=>{
        if (mounted) {
            if (colorize && jp_text_processed) {
            updateWordDecorations(reader_root, word_id_list, word_learning_stages, false, undefined, book_learning_stage_colors);
            jp_decoration_done = true;
            }
            setClickEventListeners();
            document.addEventListener('keydown', keyPressListener, false);
        }
        console.log("refresh")
	}
	
	const change=()=>{
		lang=lang==="JP"?"ENG":"JP";
		allquerys();
		refresh();
	};

  const translateHoveredBlock=()=>{
    if (hovered_block_id != -1) {
      let elems = document.querySelectorAll(`[block_id="${hovered_block_id}"]`);
      let body = JSON.stringify({
      'func' : 'translate', 
      'text' : elems[0].innerText,
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
         elems[0].insertAdjacentHTML("beforeend", '<br><span class="translation">' + txt + '</span>');
        });
      });

    }
  }

	const handleKeydown=(e)=>{		
		if (!edit_mode) {
			let key = e.key;
      if (key == 'w') {
        manual_en_scroll_offset += 20;
        onJapScroll(undefined);
      } else if (key == 's') {
        manual_en_scroll_offset -= 20;
        onJapScroll(undefined);
      } else if (key == 't') {
        translateHoveredBlock();
      }
      // stub
		}
	}

const sli1=()=>{
	if(lang==="JP")
	{
		//j=jpp[0];
		refresh();
	}
  document.getElementById("dash").style="position:static;right:2.5vw;left:2.5vw;z-index: 999;background-color:rgba(0,0,0,0.6);"
	//document.getElementById("dash").style="position:fixed;bottom:1px;right:2.5vw;left:2.5vw;z-index: 999;background-color:rgba(0,0,0,0.6);"
	allquerys();
}

const sli2=()=>{
	if(lang==="ENG")
	{
		//j=enp[0];		
		refresh();
	}
  document.getElementById("dash").style="position:static;right:2.5vw;left:2.5vw;z-index: 999;background-color:rgba(0,0,0,0.6);"
	allquerys();
	
}


function on_resize() {

}
function on_scroll() {

}

async function debugParser() {
    if (hovered_sentence_id != -1) {
      let elems = document.querySelectorAll(`[sid="${hovered_sentence_id}"]`);
      let body = JSON.stringify({
      'func' : 'parse', 
      'text' : [elems[0].innerText],
      });
      const response = await fetch( "/jmdict", {
        headers: {"Content-Type" : "application/json" },
        method: 'POST',
        body: body,
      });
    }
  }

  async function debugOcr() {
    if (hovered_sentence_id != -1) {
      let body = JSON.stringify({
      'func' : 'debug_ocr',
      'chapter_id' : jp_chapter_id,
      'page_ref' : '0',
      'block_id' : hovered_block_id,
      'sentence_id' : hovered_sentence_id,
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
      //setHoveredBlockWordsKnown(false);
    } else if (keyName == 'K') {
      //setHoveredBlockWordsKnown(true);
    } else if (keyName == 'e') {
      //editHoveredBlock();
    }
  }


function clicked(text, word_id_index_list, block_id, sentence_id, item_id) {
  selected_block = block_id;
  selected_sentence_id = sentence_id;
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
    let word_elements = reader_root.querySelectorAll(".ocrtext1 span");
    for (let elem of word_elements) {
      let word_id_index_list = getWordIdIndexList(elem);
      if (word_id_index_list.length > 0) {
        elem.addEventListener("click", (e) => {
          if (!showWordPopUpDialog) { // prevent numerous click events
            
            //setWordPopupToElementPosition(e.target, document.getElementById("jp_chapter_page"), reader_root);
            setWordPopupToElementPosition(e.target, document.getElementById("pagescontainer"), reader_root);
            let block_element = elem.parentElement.parentElement;
            let block_id = parseInt(block_element.getAttribute("block_id"));
            let sentence_element = elem.parentElement;
            let sentence_id = parseInt(sentence_element.getAttribute("sid"));
            let item_id = parseInt(elem.getAttribute("ii"));
            clicked(elem.innerText,word_id_index_list, block_id, sentence_id, item_id);
          }
        });
      }
    }
  }

  const ShowAnkiCardDialog = (e) => {
    // TODO
    /*
    selected_word = e.detail['word']
    selected_word_glossary = e.detail['glossary']
    selected_word_readings = e.detail['readings']
    selected_block_content = ocrpage[selected_block]["og_lines"];
    openAnkiCardDialog();
    */
  }

  const learningStageChangedFromPopUpDialog = (e) => {
    learningStageChanged(word_id_list, word_learning_stages, e.detail['word_id'], e.detail['stage'], selected_block, jp_chapter_id, -1, '0');
    if (colorize) {
        updateWordDecorations(reader_root, word_id_list, word_learning_stages, false, undefined, book_learning_stage_colors);
    }
  }

  async function PriorityWordUpdatedManuallyFromPopUpDialog(e) {
    let paragraph = parsed_page[selected_block]["og_lines"];
    await UpdatePriorityWordManually(
        reader_root, id, jp_chapter_id, e.detail['word_id'], e.detail['scope'], paragraph, 
      selected_text, selected_block, selected_item_id, -1, '0', word_id_list
    )
    if (colorize) {
        updateWordDecorations(reader_root, word_id_list, word_learning_stages, false, undefined, book_learning_stage_colors);
    }
  }

  function hoverm(e) {
    let a = e.srcElement;
    hovered_block_id = parseInt(a.getAttribute("block_id"));
  }

  function hovero(e) {
    hovered_block_id = -1;
  }

  function hover_sentence_on(e) {
    let a = e.srcElement;
    hovered_sentence_id = parseInt(a.getAttribute("sid"));
    //console.log("hover",hovered_sentence_id)
  }

  function hover_sentence_off(e) {
    hovered_sentence_id = -1;
  }

  function getChapterPosition(id) {
    let p = localStorage.getItem("chapter_positions");
    if (p !=null) {
      let positions = JSON.parse(p);
      if (id in positions) {
        return positions[id];
      } else {
        return 0;
      }
    } else {
      return 0;
    }
  }

  function setChapterPosition(id,pos) {
    console.log(id,pos);
    let positions = {};
    let p = localStorage.getItem("chapter_positions");
    if (p !=null) {
      positions = JSON.parse(p);
    }
    positions[id] = pos;
    localStorage.setItem("chapter_positions", JSON.stringify(positions));
  }


  function getScrolledCharactersPercentFromScrollPosition(scroll_pos, lang_items) {
    let lang_p = -1;
    let lang_chars = 0;
    let lang_p_i=0;
    while ((lang_p_i<lang_items.p_pos.length) && (lang_items.p_pos[lang_p_i] < scroll_pos)) {
      lang_p = lang_p_i;
      lang_chars += lang_items.p_chars[lang_p_i]
      lang_p_i++;
    }
    let lang_p_pct = 0;
    let interval;
    if (lang_p == lang_items.p_pos.length-1) {
      return 100;
    }
    if (lang_p == -1) {
      //
    } else {
      interval = lang_items.p_pos[lang_p+1] - lang_items.p_pos[lang_p];
      lang_p_pct = 100*(scroll_pos - lang_items.p_pos[lang_p])/interval;
      lang_chars += lang_items.p_chars[lang_p+1]*lang_p_pct/100;
    }
    //console.log("1: lang_p ",lang_p,"lang_chars",lang_chars,"interval",interval,"lang_p_pct",lang_p_pct.toFixed(2))
    return 100*lang_chars/lang_items.total_chars;
  }

  function getScrollPositionFromCharacterPercent(chars_pct, lang_items) {
    let lang_p = 0;
    let lang_chars = 0;
    if (chars_pct > 100) {
      chars_pct = 100;
    }
    while ( lang_p<lang_items.p_chars.length && ( 100*(lang_chars+lang_items.p_chars[lang_p])/lang_items.total_chars < chars_pct) ) {
      lang_chars += lang_items.p_chars[lang_p]
      lang_p++;
    }
    let lang_pos = 0;
    let p_interval = 0;
    if (lang_p == lang_items.p_pos.length-1) {
      return lang_items.p_pos[lang_p];
    }
    if (lang_p == 0) {
      lang_pos = 0; 
      p_interval = lang_items.p_pos[lang_p];
    } else {
      lang_pos = lang_items.p_pos[lang_p-1];
      p_interval = lang_items.p_pos[lang_p]-lang_items.p_pos[lang_p-1];
    }
    let this_p_pct = 100*lang_chars/lang_items.total_chars
    let next_p_pct = 100*(lang_chars+lang_items.p_chars[lang_p])/lang_items.total_chars
    let lang_offset = (chars_pct-this_p_pct)/(next_p_pct-this_p_pct)*(p_interval);

    //console.log("en_chars_pct",en_chars_pct,"en_p",en_p,en_p_pct,"ch",en_chars)
    console.log("lang_p",lang_p,this_p_pct.toFixed(2),"next_p_pct",next_p_pct.toFixed(2),"lang_pos",lang_pos,"ofs",lang_offset.toFixed(2),"/",p_interval)
    return lang_pos + lang_offset
  }


  function onEngScroll(e) {
    if (Date.now() - jap_scroll_timestamp < 500)
      return; // prevent undulating scroll events
    eng_scroll_timestamp = Date.now();
    console.log("enscroll");
  
    let elem = document.getElementById("en_chapter_page");
    let scroll_pos = elem.scrollTop+elem.clientHeight;
    scroll_pos += manual_en_scroll_offset;
    if (scroll_pos < 0) {
      scroll_pos = 0;
    } else if (scroll_pos > elem.scrollHeight) {
      scroll_pos = elem.scrollHeight;
    }

    en_scroll_pct = 100*scroll_pos/elem.scrollHeight;

    if (auto_scroll) {
      let en_chars_pct = getScrolledCharactersPercentFromScrollPosition(scroll_pos, en_items);
      console.log("en_scroll_pct",en_scroll_pct.toFixed(2),"en_chars_pct",en_chars_pct.toFixed(2))

      elem = document.getElementById("jp_chapter_page");
      let scroll_2_pos = getScrollPositionFromCharacterPercent(en_chars_pct, jp_items) - elem.clientHeight;
      if (scroll_2_pos < 0) {
        scroll_2_pos = 0;
      }
      elem.scrollTop = scroll_2_pos;
      jp_scroll_pct = en_scroll_pct;

      setChapterPosition(cid,jp_scroll_pct)
    }
  }

  function onJapScroll(e) {
    if (Date.now() - eng_scroll_timestamp < 500)
      return; // prevent undulating scroll events
    jap_scroll_timestamp = Date.now();
    //console.log("japscroll");

    let elem = document.getElementById("jp_chapter_page");
    let scroll_pos = elem.scrollTop+elem.clientHeight;
    jp_scroll_pct = 100*scroll_pos/elem.scrollHeight;

    setChapterPosition(cid,jp_scroll_pct)

    if (auto_scroll && en_text_loaded) {
      let jp_chars_pct = getScrolledCharactersPercentFromScrollPosition(scroll_pos, jp_items);
      console.log("jp_scroll_pct",jp_scroll_pct.toFixed(2),"jp_chars_pct",jp_chars_pct.toFixed(2))

      elem = document.getElementById("en_chapter_page");
      let scroll_2_pos = getScrollPositionFromCharacterPercent(jp_chars_pct, en_items) - elem.clientHeight;
      scroll_2_pos += manual_en_scroll_offset;
      if (scroll_2_pos < 0) {
        scroll_2_pos = 0;
      } else if (scroll_2_pos > elem.scrollHeight) {
        scroll_2_pos = elem.scrollHeight;
      }
      elem.scrollTop = scroll_2_pos;
      en_scroll_pct = jp_scroll_pct;
    }
  }

</script>

<svelte:window on:keydown={handleKeydown} on:resize={on_resize}  on:scroll={on_scroll} />

<div id="reader" class="reader" bind:this={reader_root}>

    <WordPopup bind:word_id_index_list={selected_word_id_index_list} 
        {word_id_list} {word_history} {word_learning_stages} 
        bind:showModal={showWordPopUpDialog} on:learning_stage_changed={learningStageChangedFromPopUpDialog}
        on:priority_word_updated_manually={PriorityWordUpdatedManuallyFromPopUpDialog}
        on:anki_button_clicked={ShowAnkiCardDialog}
    />
    {#if en_text_loaded}
    <div class="sidebysidecontainer" id="pagescontainer">
      <div class="chapter_page" on:scroll={onEngScroll} class:chapter_page_dark={night_mode} id="en_chapter_page">
        {@html pages_en}
      </div>
      <div class="chapter_page" on:scroll={onJapScroll} class:chapter_page_dark={night_mode} id="jp_chapter_page">
          {@html pages_jp}
      </div>
    </div>
    {:else}
    <div id="pagescontainer">
      <div class="chapter_page"  on:scroll={onJapScroll} class:chapter_page_dark={night_mode} id="jp_chapter_page">
          {@html pages_jp}
      </div>
      </div>
    {/if}

<div id="dash" >

<BookDashboard
  bind:edit_mode={edit_mode}
  bind:night_mode={night_mode}
  bind:auto_scroll={auto_scroll}
  bind:chaptersen={chaptersen}
  bind:chaptersjp={chaptersjp}
  bind:vj={vj}
  bind:jjj={jjj}
  bind:vi={vi}
  bind:iii={iii}
  bind:langds={langds}
  change={change}
  bind:indicator={indicator}
  allquerys={allquerys}
  refresh={refresh}
  bind:volumesjp={volumesjp}
  bind:volumesen={volumesen}
  sli1={sli1}
  sli2={sli2}
  {jp_scroll_pct}
  {en_scroll_pct}
/>
</div>

</div>	

<style>
	#reader{
		margin: auto;
		text-align: center;		
		
	}

  .reader {
      display: ruby;
  }
  .sidebysidecontainer {
      display: grid;
      grid-template-columns: 50% 50%;
      grid-gap: 10px;
  }

  .chapter_page {
      /*writing-mode: vertical-rl;*/
      max-width:40vw;
      /*max-height:100vh;
      text-wrap: break-word;*/
      background-color: #f5f5f0;
      color: black;
      padding: 15px;
      text-align: left;
      overflow-y:scroll;
      max-height:40vw;
      position: relative;
  }

  .chapter_page_dark {
      background-color: #1b1b1a;
      color: rgb(112, 111, 111);
  }
  .ocrtext1 {
      margin : 0;
      text-align:left;
      display:inline-block;
      vertical-align: top;
      letter-spacing: 0.1em;
      line-height: 1.4em;
  }
  .ocrtext1 p {
      margin-block-start: 0;
      margin-block-end: 0;
  }

  :global(.translation) {
    color: #7e5984;
  }

</style>