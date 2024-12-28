from ebooklib import epub
import ebooklib
from book2bm_helper import *
from bs4 import BeautifulSoup
from helper import *

epub_regex = [
    # 壁際族に花束を_（上）_(角川文庫).epub
    ["([^\s(\d（上中下]*)(?:[_\s])*（([^）]+){1}",2],

    # [村上春樹]国境の南、太陽の西
    #["(?:\[[^\]]*\])([^（上中下]*)",1],

]

def get_info_from_epub_file_name(root_path,source_item):
    for reg in epub_regex:
        res = re.search(reg[0],source_item)
        if res is not None:
            gr = res.groups()
            title = res.groups()[0]
            if reg[1] == 2:
                vol_name = res.groups()[1]
            else:
                if '（上）' in source_item:
                    vol_name = '上'
                elif '（下）' in source_item:
                    vol_name = '下'
                elif '（中）' in source_item:
                    vol_name = '中'
                else:
                    vol_name = title
            return title, {'type':'epub','volume_name':vol_name,'path':root_path,'filename': source_item, 'translator':''}

    # if no regex matches, simply use the filename as title and volume name
    title = source_item[:-5]
    return title, {'type':'epub','path':root_path,'volume_name':title,'filename':source_item, 'translator':''}


def save_cover_image_from_epub(t_metadata, book,lang,title):
    cover = None
    cover_img_id = None

    cover_entry = book.get_metadata('OPF', 'cover')
    if len(cover_entry)>0:
        cover_img_id = cover_entry[0][1]['content']
        cover = book.get_item_with_id(cover_img_id)
    else:
        covers = book.get_items_of_type(ebooklib.ITEM_COVER)
        for c in covers:
            if cover is None:
                cover = c
    
    if cover is None:
        images = book.get_items_of_type(ebooklib.ITEM_IMAGE)
        for img in images:
            if cover_img_id is not None:
                if img.id == cover_img_id:
                    cover = img
            else:
                if cover is None:
                    cover = img

    if cover is not None:
        cover_name = cover.get_name()
        cover_f_name = cover_name.split('/')[-1]
        cover_f_ext = cover_f_name.split('.')[-1]
        content = cover.get_content()

        target_img_f_name = clean_name(title) + '.' + cover_f_ext
        target_img_path = 'manga_cover/' + lang + '/'
        t_metadata['cover'+lang] = target_img_path + target_img_f_name

        print("Writing %s cover image %s" % (lang,target_img_path + target_img_f_name))
        item_f = open(target_img_path + target_img_f_name,'wb')
        item_f.write(content)
        item_f.close()


def save_image_from_epub(chapter_id, book, img_name):
    for image in book.get_items_of_type(ebooklib.ITEM_IMAGE):
        item_name = image.get_name()
        item_f_name = item_name.split('/')[-1]
        if img_name == item_f_name:
            content = image.get_content()
            ch_ipfs_path = target_ipfs_path + chapter_id
            if not os.path.exists(ch_ipfs_path):
                os.mkdir(ch_ipfs_path)
            item_f = open(ch_ipfs_path + '/' + item_f_name,'wb')
            item_f.write(content)
            item_f.close()
            return
    print("Image %s not found in epub!" % img_name)

def get_clean_title_from_epub(book):
    # get rid of of the volume part in title
    vol_title,_ = book.get_metadata('DC', 'title')[0]
    clean_title = vol_title.split(' 上 ')[0]
    clean_title = clean_title.split(' 中 ')[0]
    clean_title = clean_title.split(' 下 ')[0]
    clean_title = clean_title.replace('_',' ')

    vol_title, publisher = extract_publisher_from_title(clean_title)
    return vol_title, clean_title, publisher

def get_language_from_epub(book):
    lang_item = book.get_metadata('DC', 'lang')
    if len(lang_item) == 0:
        lang_item = book.get_metadata('DC', 'language')
    if len(lang_item) == 0:
        raise Exception("No language!")
    lang, _ = lang_item[0]
    if lang == 'ja':
        lang = 'jp'
    return lang

def get_metadata_from_epub(t_metadata, t_data, lang, book, title):
    desc_meta = book.get_metadata('DC', 'description')
    if len(desc_meta)>0:
        desc,_ = desc_meta[0]
        t_data['syn_'+lang] = desc

    vol_title, clean_title, publisher = get_clean_title_from_epub(book)

    if t_metadata[lang + 'tit'] == PLACEHOLDER:
        t_metadata[lang + 'tit'] = clean_title
    creator, _ = book.get_metadata('DC', 'creator')[0]
    creator2 = creator.replace(' ','')
    if creator not in t_metadata['Author'] and creator2 not in t_metadata['Author']:
        if t_metadata['Author'] == [PLACEHOLDER]:
            t_metadata['Author'] = [creator]
        else:
            t_metadata['Author'].append(creator)

    if lang == 'jp':
        if t_metadata['Release'] == PLACEHOLDER:
            try:
                released, _ = book.get_metadata('DC', 'date')[0]
                t_metadata['Release'] = int(released.split('-')[0])
            except:
                pass

        if t_metadata['Publisher'] == PLACEHOLDER:
            if publisher is not None:
                t_metadata['Publisher'] = publisher
            else:
                try:
                    publisher, _ = book.get_metadata('DC', 'publisher')[0]
                    t_metadata['Publisher'] = publisher
                except:
                    pass

    return vol_title


def get_chapters_from_epub(book, verbose=False):
    # There are two scenarios how chapters are constructed:
    #
    # 1) Each chapter can consist of many items (each is a single html) which are then combined
    # OR
    # 2) single item(html file) can contain many chapters, which are then referred with html tag ID
    # We must handle both scenarios here

    # first check the Table of Contents which provides a reference 
    # for the beginning of each chapter (item and possible html tag id).
    # Note that the html tag id is different from item id
    chapter_titles = []
    item_list_per_chapter = []
    last_item_id = None
    for toc_item in book.toc:

        if not isinstance(toc_item, ebooklib.epub.Link):
            toc_item = toc_item[0]
        href = toc_item.href
        ctitle = toc_item.title
        # remove the id in order to fetch the item
        if '#' in href:
            tag_id = href.split('#')[1]
            href = href.split('#')[0]
        else:
            tag_id = None
        item = book.get_item_with_href(href)

        if item is not None and ctitle is not None and ctitle[0] != '◆':
            title = toc_item.title
            while title in chapter_titles:
                title += ' -'  # to avoid collision of OIDs should there be duplicate chapter names

            if len(item_list_per_chapter)>0:
                if item_list_per_chapter[-1][0]['item'].id == item.id:
                    # chapter for this and the last item is the same
                    # so we must mark the end of the chapter to avoid overlap
                    if tag_id is not None:
                         item_list_per_chapter[-1][0]['next_ch_start_id'] = tag_id
                    else:
                        # shouldn't happen
                        raise Exception("Something is wrong here! TOC contains overlapping references!")                    

            chapter_titles.append(title)
            item_list_per_chapter.append([{'item':item,'content':item.content,'start_id':tag_id,'next_ch_start_id':None}])  # 1st file in the chapter

    # 2nd step is to go through the 'spine' which contains a list of html files in physical
    # order. If a chapter contains more than 1 item(html file) then we must add the 
    # rest of the items to the chapter item list.
    # Also, the Table of Contents omits the first few pages (front page etc) so we must 
    # Create a extra "Heading" chapter which includes these
    heading_chapter_items = []
    active_chapter_idx = -1
    if verbose:
        print("\t\tChapter Heading:")
    for (item_id, _) in book.spine:
        item = book.get_item_with_id(item_id)
        chapter_changed = False
        while active_chapter_idx+1 < len(item_list_per_chapter) and item_id == item_list_per_chapter[active_chapter_idx+1][0]['item'].id:
            active_chapter_idx += 1
            chapter_changed = True
            if verbose:
                print("\t\tChapter: %s" % chapter_titles[active_chapter_idx])
                print("\t\t\t(%s) %s [#%s]" % (item_id,item.file_name, item_list_per_chapter[active_chapter_idx][0]['start_id']))
        if not chapter_changed:
            if active_chapter_idx == -1:
                heading_chapter_items.append({'item':item,'content':item.content,'start_id':None,'next_ch_start_id':None})
            else:
                item_list_per_chapter[active_chapter_idx].append({'item':item,'content':item.content,'start_id':None,'next_ch_start_id':None})
            if verbose:
                print("\t\t\t(%s) %s" % (item_id,item.file_name))

    if len(heading_chapter_items)>0:
        chapter_titles = ['Heading'] + chapter_titles
        item_list_per_chapter = [heading_chapter_items] + item_list_per_chapter


    if len(chapter_titles) == 2:
        # it seems there is only heading and everything else is dumped into chapter 1, 
        # so the TOC is unfinished..  Try to split into chapters by <h2> tag
        # Usually they already exist as separate html files
        split_chapter_names = []
        split_item_list_per_chapter = []

        valid = True
        for ch_item_data in item_list_per_chapter[1]:
            item = ch_item_data['item']
            content = item.content
            soup = BeautifulSoup(content,features="html.parser")
            h2_list = soup.find_all('h2')
            if len(h2_list) == 1:
                split_chapter_names.append(h2_list[0].text)

                split_item_list_per_chapter.append([{'item':item,'content':item.content,'start_id':None,'next_ch_start_id':None}])
            elif len(h2_list) == 0:
                if len(split_item_list_per_chapter)==0:
                    item_list_per_chapter[0].append({'item':item,'content':item.content,'start_id':None,'next_ch_start_id':None})
                else:
                    split_item_list_per_chapter[-1].append({'item':item,'content':item.content,'start_id':None,'next_ch_start_id':None})
            else:
                # don't yet handle the case where there are multiple chapters in one html file
                valid = False

        if valid:
            chapter_titles = [chapter_titles[0]] + split_chapter_names
            item_list_per_chapter = [item_list_per_chapter[0]] + split_item_list_per_chapter

        # split again by <h3> tags
        new_chapter_names = [chapter_titles[0]]
        new_item_list_per_chapter = [item_list_per_chapter[0]]

        chapter_count = 0
        for ch_name, ch_item_list in zip(chapter_titles[1:],item_list_per_chapter[1:]):

            for ch_item_i, ch_item_data in enumerate(ch_item_list):
                item = ch_item_data['item']
                content = item.content
                soup = BeautifulSoup(content,features="html.parser")
                h3_list = soup.find_all('h3')
                if len(h3_list)>0:
                    for h3_elem in h3_list:
                        if ch_name != '':
                            new_ch_name = ch_name + ' - ' + h3_elem.text
                        else:
                            new_ch_name = h3_elem.text
                        new_chapter_names.append(new_ch_name)
                        ch_html_id = 'parser_h3_chapter_id_' + str(chapter_count)
                        h3_elem['id'] = ch_html_id
                        chapter_count += 1
                        new_content = str(soup)
                        if len(new_item_list_per_chapter)>0:
                            if new_item_list_per_chapter[-1][-1]['item'].id == item.id:
                                new_item_list_per_chapter[-1][-1]['next_ch_start_id'] = ch_html_id
                                new_item_list_per_chapter[-1][-1]['content'] = new_content
                        new_item_list_per_chapter.append([{'item':item,'content':new_content,'start_id':ch_html_id,'next_ch_start_id':None}])
                    
                else:
                    if ch_item_i == 0:
                        new_item_list_per_chapter.append([{'item':item,'content':item.content,'start_id':None,'next_ch_start_id':None}])
                        new_chapter_names.append(ch_name)
                    else:
                        new_item_list_per_chapter[-1].append({'item':item,'content':item.content,'start_id':None,'next_ch_start_id':None})
        chapter_titles = new_chapter_names
        item_list_per_chapter = new_item_list_per_chapter

    return chapter_titles, item_list_per_chapter


def extract_paragraphs_recursively(soup, element, paragraphs):
    p = None
    el_idx = 0
    if len(element.contents) > 100:
        pass
    while el_idx < len(element.contents):
        #for elem in element.contents:
        elem = element.contents[el_idx]
        if isinstance(elem,str):
            stripped_chunk = elem.strip().replace('　','').replace('\n','')
            if len(stripped_chunk)>0:
                if p is None:
                    # start a new paragraph
                    p = soup.new_tag('p')
                    paragraphs.append(p)
                    elem.insert_before(p)
                    el_idx += 1
                # move the text chunk inside the paragraph
                elem.extract()
                el_idx -= 1
                p.append(elem)
        else:
            if elem.name == 'div':
                extract_paragraphs_recursively(soup, elem, paragraphs)
            elif elem.name == 'p':
                paragraphs.append(elem)
            elif elem.name == 'br':
                # delete the <br> and start a new paragraph
                elem.extract()
                el_idx -= 1
                p = None
            elif elem.name == 'ruby' or elem.name == 'span':
                if p is None:
                    # start a new paragraph
                    p = soup.new_tag('p')
                    paragraphs.append(p)
                    elem.insert_before(p)
                    el_idx += 1
                # move the tag inside the paragraph
                elem.extract()
                el_idx -= 1
                p.append(elem)
        el_idx += 1
    pass


def process_epub(t_data, title_id, book, lang, vol_id, vol_name, verbose, ask_confirmation_for_new_chapters):

    lang_data_field = lang + '_data'
    ch_name_field = 'ch_na' + lang
    ch_lang_h_field = 'ch_' + lang + 'h'
    ch_lang_field = 'ch_' + lang
    vol_lang_field = 'vol_' + lang

    start_ch_idx = len(t_data[lang_data_field][ch_lang_h_field])
    print("Process vol/book %s [%s]" % (vol_name,vol_id))

    items = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            items.append(item)

    chapter_titles, item_list_per_chapter = get_chapters_from_epub(book,verbose)

    if len(chapter_titles) == 0:
        print("Title %s volume %s [%s] has no detected chapters!" % (title_id, vol_name, vol_id))
        return 0

    vol_num = len(t_data[lang_data_field][vol_lang_field])
    t_data[lang_data_field][vol_lang_field][vol_name] = {'id':vol_id,'s':start_ch_idx,'e':start_ch_idx + len(chapter_titles)-1}

    ch_idx = 0
    target_ocr_file_path = None
    ch_name = None
    chapter_paragraphs = []
    chapter_pages = []
    total_num_characters = 0
    total_num_pages = 0

    for ch_idx, (ch_name, chapter_items) in enumerate(zip(chapter_titles, item_list_per_chapter)):

        ch_id = create_oid("%s/%s/%s/%s" % (title_id,lang,vol_id,ch_name), "chapter", ask_confirmation=ask_confirmation_for_new_chapters, title_id=title_id, vol_id=vol_id)
        if ch_id is None:
            print("Skipping chapter and subsequent chapters")
            return -1
        t_data[lang_data_field][ch_name_field].append(ch_name)
        t_data[lang_data_field][ch_lang_h_field].append(ch_id + '/%@rep@%')
        t_data[lang_data_field][ch_lang_field][start_ch_idx+ch_idx+1] = ['pages.html']
        print("Chapter %s [%s]: %s " % (lang, ch_id, ch_name))

        add_chapter_lookup_entry(title_id, vol_id, vol_num, vol_name, ch_id, ch_idx, ch_name, lang)

        ocr_dict = dict()
        chapter_paragraphs = []
        chapter_pages = []
        num_sentences = 0
        num_characters = 0
        num_words = 0

        for ch_item_data in chapter_items:
            item = ch_item_data['item']
            start_id = ch_item_data['start_id']
            stop_id = ch_item_data['next_ch_start_id']

            item_name = item.get_name()
            item_f_name = item_name.split('/')[-1]
            if 'xhtml' in item_f_name:
                item_f_name_base = item_f_name.split('.xhtml')[0]
            elif 'html' in item_f_name:
                item_f_name_base = item_f_name.split('.html')[0]
            elif 'htm' in item_f_name:
                item_f_name_base = item_f_name.split('.htm')[0]
            else:
                raise Exception("Unknown content file type %s" % item_f_name)

            content = ch_item_data['content']

            # extracts text from the HTML content
            soup = BeautifulSoup(content,features="html.parser")
            body = soup.find('body')

            # if this html file contains other chapters besides the one which is processed,
            # we must remove all the other content
            if start_id is not None:
                # remove all elements before the start_id (this level)
                start_elem = soup.find(id=start_id)
                if start_elem is None:
                    raise Exception("Chapter %d/%s start_id %s not found!" % (ch_idx,ch_name,start_id))

                if start_elem.parent != body:
                    # start_id element isn't directly below body, so remove all the preceding parent elements 
                    container_elems = start_elem.parent.parent.contents
                    while len(container_elems) > 0 and container_elems[0] != start_elem.parent:
                        container_elems[0].extract()
                    # TODO: this should actually be done recursively

                container_elems = start_elem.parent.contents
                while len(container_elems) > 0 and container_elems[0] != start_elem:
                    container_elems[0].extract()


            if stop_id is not None:
                # remove all elements after (and including) the stop_id
                stop_elem = soup.find(id=stop_id)
                if stop_elem is None:
                    raise Exception("Chapter %d/%s stop_id %s not found!" % (ch_idx,ch_name,stop_id))

                if stop_elem.parent != body:
                    # stop_id element isn't directly below body, so remove all the following parent elements
                    container_elems = stop_elem.parent.parent.contents
                    elem_idx = 0
                    while elem_idx < len(container_elems) and container_elems[elem_idx] != stop_elem.parent:
                        elem_idx += 1
                    elem_idx += 1
                    while elem_idx < len(container_elems):
                        container_elems[elem_idx].extract()

                # remove the following elements from this level
                container_elems = stop_elem.parent.contents
                elem_idx = 0
                while elem_idx < len(container_elems) and container_elems[elem_idx] != stop_elem:
                    elem_idx += 1
                while elem_idx < len(container_elems):
                    container_elems[elem_idx].extract()

            paragraphs = []
            extract_paragraphs_recursively(soup, body, paragraphs)

            if lang == 'jp':
                target_ocr_file_path = target_ocr_path + ch_id + '.json'
                for p in paragraphs:
                    if len(p.text)>0 and (has_cjk(p.text) or has_word_hiragana(p.text) or has_word_katakana(p.text)):

                        p['block_id'] = len(chapter_paragraphs)
                        p_dict = dict()
                        p_ruby_items = []
                        line = ''
                        lines = []
                        p_len = 0
                        for chunk in p.contents:
                            chunk_text = ''
                            if isinstance(chunk,str):
                                chunk_text = chunk.strip()
                            else:
                                # extract ruby
                                if chunk.name == 'ruby':
                                    ruby_items = [chunk]
                                else:
                                    ruby_items = chunk.find_all('ruby')
                                if len(ruby_items)>0:
                                    for ruby in ruby_items:
                                        # concat all rb (and rt) elements correspondingly
                                        ruby_dict = dict()
                                        ruby_rb = ''
                                        ruby_rb_elems = ruby.find_all('rb')
                                        if len(ruby_rb_elems) == 0:
                                            ruby_rb = ruby.text
                                        else:
                                            for ruby_rb_elem in ruby_rb_elems:
                                                ruby_rb += ruby_rb_elem.text
                                        ruby_rt = ''
                                        for ruby_rt_elem in ruby.find_all('rt'):
                                            ruby_rt += ruby_rt_elem.text
                                        
                                        p_ruby_items.append({'s':p_len,'l':len(ruby_rb),'rt':ruby_rt})
                                        line += ruby_rb
                                        p_len += len(ruby_rb)
                                else:
                                    chunk_text = chunk.text

                            # separate paragraphs into sentences (lines)
                            while '。' in chunk_text:
                                chunk2 = chunk_text[:chunk_text.find('。')+1]
                                p_len += len(chunk2)
                                line += chunk2
                                lines.append(line)
                                line = ''
                                chunk_text =  chunk_text[chunk_text.find('。')+1:]
                            p_len += len(chunk_text)
                            line += chunk_text # add remaining

                        if len(line.strip())>0:
                            lines.append(line)
                        num_sentences += len(lines)
                        num_characters += p_len

                        if len(p_ruby_items)>0:
                            p_dict['ruby'] = p_ruby_items

                        p_dict['lines'] = convert_vertical_to_horizontal(lines)

                        chapter_paragraphs.append(p_dict)

            else:
                for p in paragraphs:
                    if len(p.text)>0:
                        p['en_block_id'] = len(chapter_paragraphs)
                        num_sentences += len(p.text.split('.'))
                        num_characters += len(p.text)
                        num_words += len(p.text.split(' '))
                        chapter_paragraphs.append([p.text])

            svgs = soup.find_all('svg')
            for svg in svgs:
                for img in svg.find_all('image'):
                    if img.has_attr('xlink:href'):
                        svg_path = img['xlink:href']
                        if '/' in svg_path:
                            # get only the file name
                            svg_name = svg_path.split('/')[-1]
                        else:
                            svg_name = svg_path
                        img['xlink:href'] = '%@ipfs_cid@%/' + svg_name
                        save_image_from_epub(ch_id, book, svg_name)

            # modify img links
            images = soup.find_all('img')
            for img in images:
                src = img['src']
                if '/' in src:
                    img_name = src.split('/')[-1]
                else:
                    img_name = src
                img['src'] = '%@ipfs_cid@%/' + img_name
                img['style'] = '%@img_style@%'

                save_image_from_epub(ch_id, book, img_name)

            chapter_pages.append(body.prettify())

        if lang == 'jp':
            t_data[lang_data_field]['virtual_chapter_page_count'].append(get_virtual_page_count_from_characters(num_characters))
        else:
            t_data[lang_data_field]['virtual_chapter_page_count'].append(get_virtual_page_count_from_words(num_words))

        print("\t.. with %s pages / %d paragraphs / %d sentences / %d characters" % (
            t_data[lang_data_field]['virtual_chapter_page_count'][-1],
            len(chapter_paragraphs),num_sentences,num_characters))

        if lang == 'jp':
            if len(chapter_paragraphs)>0:
                print("\t\tWriting OCR file %s" % target_ocr_file_path)
                ocr_dict['0'] = chapter_paragraphs
                target_ocr_f = open(target_ocr_file_path,'w',encoding="UTF-8")
                target_ocr_f.write(json.dumps(ocr_dict))
                target_ocr_f.close()

        save_chapter_pages(ch_id, chapter_pages)
        total_num_characters += num_characters
        total_num_pages += t_data[lang_data_field]['virtual_chapter_page_count'][-1]

    print("** Total %d pages and %d characters" % (total_num_pages, total_num_characters))
    return len(chapter_titles)
