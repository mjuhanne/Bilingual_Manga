from ebooklib import epub
import ebooklib
from book2bm_helper import *
from bs4 import BeautifulSoup
from helper import *

epub_regex = [
    # 壁際族に花束を_（上）_(角川文庫).epub
    ["([^\s(\d（上中下]*)(?:[_\s])*（([^）]+){1}",2]
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
            return title, {'type':'epub','volume_name':vol_name,'path':root_path,'filename': source_item}

    # if no regex matches, simply use the filename as title and volume name
    title = source_item[:-5]
    return title, {'type':'epub','path':root_path,'volume_name':title,'filename':source_item}


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
            item_list_per_chapter.append([{'item':item,'start_id':tag_id,'next_ch_start_id':None}])  # 1st file in the chapter

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
                heading_chapter_items.append({'item':item,'start_id':None,'next_ch_start_id':None})
            else:
                item_list_per_chapter[active_chapter_idx].append({'item':item,'start_id':None,'next_ch_start_id':None})
            if verbose:
                print("\t\t\t(%s) %s" % (item_id,item.file_name))

    if len(heading_chapter_items)>0:
        chapter_titles = ['Heading'] + chapter_titles
        item_list_per_chapter = [heading_chapter_items] + item_list_per_chapter
    return chapter_titles, item_list_per_chapter

def process_epub(t_data, title_id, book, lang, vol_id, vol_name, start_ch_idx, verbose):

    lang_data_field = lang + '_data'
    ch_name_field = 'ch_na' + lang
    ch_lang_h_field = 'ch_' + lang + 'h'
    ch_lang_field = 'ch_' + lang
    vol_lang_field = 'vol_' + lang

    print("Process vol/book %s [%s]" % (vol_name,vol_id))

    items = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            items.append(item)

    chapter_titles, item_list_per_chapter = get_chapters_from_epub(book,verbose)

    t_data[lang_data_field][vol_lang_field][vol_name] = {'s':start_ch_idx,'e':start_ch_idx + len(chapter_titles)-1}

    ch_idx = 0
    current_chapter = None
    target_ocr_file_path = None
    target_page_file_path = None
    ch_name = None
    chapter_paragraphs = []
    chapter_pages = []
    total_num_characters = 0

    for ch_idx, (ch_name, chapter_items) in enumerate(zip(chapter_titles, item_list_per_chapter)):

        ch_id = get_oid(title_id + '/' + lang + '/' + vol_id + '/' + ch_name)
        ch_ipfs_path = target_ipfs_path + ch_id
        t_data[lang_data_field][ch_name_field].append(ch_name)
        t_data[lang_data_field][ch_lang_h_field].append(ch_id + '/%@rep@%')
        t_data[lang_data_field][ch_lang_field][start_ch_idx+ch_idx+1] = ['pages.html']
        print("Chapter %s [%s]: %s " % (lang, ch_id, ch_name))

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

            # don't use get_content() because it loses all <body> attributes!
            #content = item.get_content()
            content = item.content

            # extracts text from the HTML content
            soup = BeautifulSoup(content,features="html.parser")

            # if this html file contains other chapters besides the one which is processed,
            # we must remove all the other content
            if start_id is not None:
                # remove all elements before the start_id
                start_elem = soup.find(id=start_id)
                if start_elem is None:
                    raise Exception("Chapter %d/%s start_id %s not found!" % (ch_idx,ch_name,start_id))
                container_elems = start_elem.parent.findChildren()
                elem_idx = 0
                while elem_idx < len(container_elems) and container_elems[elem_idx] != start_elem:
                    container_elems[elem_idx].extract()
                    elem_idx += 1

            if stop_id is not None:
                # remove all elements after (and including) the stop_id
                stop_elem = soup.find(id=stop_id)
                if stop_elem is None:
                    raise Exception("Chapter %d/%s stop_id %s not found!" % (ch_idx,ch_name,stop_id))
                container_elems = stop_elem.parent.findChildren()
                elem_idx = 0
                while elem_idx < len(container_elems) and container_elems[elem_idx] != stop_elem:
                    elem_idx += 1
                while elem_idx < len(container_elems):
                    container_elems[elem_idx].extract()
                    elem_idx += 1

            paragraphs = soup.find_all('p')

            # TODO: create a different approach for those epubs in which text is not
            # divided inside <p> paragraphs, but are inside a single <span> and the
            # paragraphs are divided by simple <br> tags: 
            # For example title うふふな日々

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

            body = soup.find('body')
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

    print("** Total %d characters" % (total_num_characters))
    return len(chapter_titles)
