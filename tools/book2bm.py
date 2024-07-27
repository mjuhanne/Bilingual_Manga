import json
import os
import subprocess
from bs4 import BeautifulSoup
from helper import * 
import shutil
import bson
import argparse
import logging
import ebooklib
import unicodedata as ud
from ebooklib import epub

default_book_path = '/mnt/Your/Book/Directory'

verbose = False

target_ext_oid_path = 'json/ext.oids.json'
target_ocr_path = 'ocr/'
target_ipfs_path = 'ipfs/'

parser = argparse.ArgumentParser(
    prog="books2bm",
    description="Import books to Bilingualmanga.",
)
subparsers = parser.add_subparsers(help='', dest='command')

parser_import = subparsers.add_parser('scan', help='Scan and import all the mokuro manga titles with placeholder metadata and process OCR files')
parser_import.add_argument('--force', '-f', action='store_true', help='Force import')
parser_import.add_argument('--source_dir', '-src', type=str, default=default_book_path, help='Source mokuro directory (with jp/ and en/ subdirectories)')
parser_import.add_argument('--simulate', '-s', action='store_true', help='Scan only (do not create new OIDs or import)')
parser_import.add_argument('-v', '--verbose', action='store_true', help='Verbose')
parser_import.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')

parser_remove = subparsers.add_parser('remove', help='Remove given title)')
parser_remove.add_argument('title_id', type=str, default=None, help='Title id')

parser_search = subparsers.add_parser('search', help='Search title/chapter_ids with given keyword')
parser_search.add_argument('-v', '--verbose', action='store_true', help='Show all subdirectory OIDs as well')
parser_search.add_argument('keyword', type=str, default=None, help='Keyword')

parser_show = subparsers.add_parser('show', help='Show list of all imported manga')

parser_set_en_vol = subparsers.add_parser('set_en_vol', help='Set english vol for title')
parser_set_en_vol.add_argument('title_id', type=str, default=None, help='Title id')
parser_set_en_vol.add_argument('--file', '-f', type=str, help='Source .epub file')


args = vars(parser.parse_args())

if 'verbose' in args:
    verbose = args['verbose']

if verbose:
    print("Args: ",args)

cmd = args.pop('command')

if cmd == 'scan':
    if args['source_dir'][-1] != '/':
        args['source_dir'] += '/'
    src_jp = args['source_dir'] + 'jp/'
    titles = [f_name for f_name in os.listdir(src_jp) if '.epub' in f_name or os.path.isdir(src_jp + f_name)]

    titles.sort()

ext_object_ids = dict()
oid_to_title = dict()
if os.path.exists(target_ext_oid_path):
    with open(target_ext_oid_path,'r',encoding="UTF-8") as oid_f:
        ext_object_ids = json.loads(oid_f.read())
    for title,oid in ext_object_ids.items():
        oid_to_title[oid] = title

def get_oid(path_str, create_new_if_not_found=True):
    # the path can be given in Unicode composed form (i.e. で)
    # or decomposed (i.e. て　+　゙	 mark).  The strings are stored in composed form
    path_str_composed = ud.normalize('NFC',path_str)
    if path_str in ext_object_ids:
        return ext_object_ids[path_str]
    if path_str_composed in ext_object_ids:
        return ext_object_ids[path_str_composed]

    if create_new_if_not_found:
        oid = str(bson.objectid.ObjectId())
        ext_object_ids[path_str_composed] = oid
        oid_to_title[oid] = path_str_composed
        print("\tNew OID [%s] %s" % (oid,path_str_composed))
        with open(target_ext_oid_path,'w',encoding="UTF-8") as oid_f:
            oid_f.write(json.dumps(ext_object_ids, ensure_ascii=False))
        return oid
    else:
        return None

j = 0
manga_metadata_per_id = dict()
manga_data_per_id = dict()

if os.path.exists(ext_manga_metadata_file):
    with open(ext_manga_metadata_file,"r",encoding="utf-8") as f:
        data = f.read()
        _manga_metadata = json.loads(data)
        for mdata in _manga_metadata:
            id = mdata['enid']
            manga_metadata_per_id[id] = mdata

if os.path.exists(ext_manga_data_file):
    with open(ext_manga_data_file,"r",encoding="utf-8") as f:
        data = f.read()
        _manga_data = json.loads(data)
        for mdata in _manga_data:
            id = mdata['_id']['$oid']
            manga_data_per_id[id] = mdata


def clean_name(name):
    s = ''
    for x in name:
        if x.isalnum():
            s += x
    return s

def copy_file(src, target_path, target_file):

    if not os.path.exists(target_path):
        os.mkdir(target_path)
    
    p  = target_path + '/' + target_file
    if os.path.exists(src):
        if not os.path.exists(p):
            print("\tCopying %s to %s" % (src,p))
            shutil.copyfile(src, p)
    else:
        print("\tDoes not exist! %s" % src)


PLACEHOLDER = 'Placeholder'


def save_metadata_files():
    target_f = open(ext_manga_data_file,'w',encoding="UTF-8")
    target_f.write(json.dumps(list(manga_data_per_id.values()),ensure_ascii=False))
    target_f.close()
    target_f = open(ext_manga_metadata_file,'w',encoding="UTF-8")
    target_f.write(json.dumps(list(manga_metadata_per_id.values()),ensure_ascii=False))
    target_f.close()

def save_cover_image_from_epub(t_metadata, book,lang,title):
    cover = None
    cover_img_id = None

    cover_entry = book.get_metadata('OPF', 'cover')
    if len(cover_entry)>0:
        cover_img_id = cover_entry[0][1]['content']
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

def save_chapter_pages(chapter_id, chapter_pages):
    if len(chapter_pages) == 0:
        return
    text = ''.join(chapter_pages)
    text = text.replace('<body>','<div class="page">')
    text = text.replace('</body>','</div>')
    ch_ipfs_path = target_ipfs_path + chapter_id
    if not os.path.exists(ch_ipfs_path):
        os.mkdir(ch_ipfs_path)
    item_f = open(ch_ipfs_path + '/' + "pages.html",'w',encoding="UTF-8")
    item_f.write(text)
    item_f.close()

def get_chapters_from_epub(book):
    chapter_titles = []
    item_list_per_chapter = []
    for toc_item in book.toc:

        if not isinstance(toc_item, ebooklib.epub.Link):
            toc_item = toc_item[0]
        href = toc_item.href
        ctitle = toc_item.title
        href = href.split('#')[0]
        item = book.get_item_with_href(href)

        if item is not None and ctitle is not None and ctitle[0] != '◆':
            #book_chapters.append(toc_item)
            title = toc_item.title
            while title in chapter_titles:
                title += ' -'  # to avoid collision of OIDs should there be duplicate chapter names
            chapter_titles.append(title)
            item_list_per_chapter.append([item])  # 1st file in the chapter

    heading_chapter_items = []
    active_chapter_idx = -1
    print("Chapter Heading:")
    for (item_id, _) in book.spine:
        item = book.get_item_with_id(item_id)
        if active_chapter_idx+1 < len(item_list_per_chapter) and item_id == item_list_per_chapter[active_chapter_idx+1][0].id:
            active_chapter_idx += 1
            print("Chapter: %s" % chapter_titles[active_chapter_idx])
        else:
            if active_chapter_idx == -1:
                heading_chapter_items.append(item)
            else:
                item_list_per_chapter[active_chapter_idx].append(item)
        print("\t(%s) %s" % (item_id,item.file_name))

    if len(heading_chapter_items)>0:
        chapter_titles = ['Heading'] + chapter_titles
        item_list_per_chapter = [heading_chapter_items] + item_list_per_chapter
    return chapter_titles, item_list_per_chapter


def get_virtual_page_count_from_characters(num_characters):

        # Norwegian woods - 298822 chars, 471-2p (268-2 + 260-2 = 532) ->  637/561
        #   Chap 6.  81549ch, 34p -> 
        #    Chap 8. 30503ch, 94-38+1=57 -> 535ch/p
        # 秋の牢獄  - 86344 chars, 217-2p -> 401.6 ch/p (Amz 224-2 -> 388ch/p)
        # イーロン・マスク - 527320 chars, 480-2 + 464-2 = 940 -> 560ch/p
        # コンビニ人間 , 72411 ch, 176-2p -> 416 ch/p
        # ニューロマンサー, 215779 ch, 464-2 -> 467 ch/p
        # underground: はじめに, 9711 ch, 16p -> 606 ch/p. 
    return int(num_characters/550) + 1

def get_virtual_page_count_from_words(num_words):
    return int(num_words/250) + 1

def convert_vertical_to_horizontal(lines):
    new_lines = []
    for line in lines:
        line = line.replace('︱','ー')
        line = line.replace('﹃','『')
        line = line.replace('﹄','』')
        line = line.replace('︻','【')
        line = line.replace('︼','】')
        line = line.replace('﹁','「')
        line = line.replace('﹂','」')
        line = line.replace('︶','）')
        line = line.replace('︵','（')
        line = line.replace('︿','〈')
        line = line.replace('﹀','〉')
        
        new_lines.append(line)
    return new_lines

def process_epub(t_data, title_id, book, lang, vol_id, vol_name, start_ch_idx):

    lang_data_field = lang + '_data'
    ch_name_field = 'ch_na' + lang
    ch_lang_h_field = 'ch_' + lang + 'h'
    ch_lang_field = 'ch_' + lang
    vol_lang_field = 'vol_' + lang

    print("Process vol/book %s [%s]" % (vol_name,vol_id))

    # TODO: HANDLE RUBY!!!

    items = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            items.append(item)

    chapter_titles, item_list_per_chapter = get_chapters_from_epub(book)

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

        for item in chapter_items:

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

            content = item.get_content()

            # extracts text from the HTML content
            soup = BeautifulSoup(content,features="html.parser")
            paragraphs = soup.find_all('p')

            if lang == 'jp':
                target_ocr_file_path = target_ocr_path + ch_id + '.json'
                for p in paragraphs:
                    if len(p.text)>0 and (has_cjk(p.text) or has_word_hiragana(p.text) or has_word_katakana(p.text)):

                        if 'は平安後期からの言葉でした' in p.text:
                            pass
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

                        if len(line)>0:
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


def scan(args):
    if verbose:
        print("Found titles: ",titles)
    for title_path in titles:

        if '.epub' in title_path:
            title = title_path[:-5]
            jp_volumes = [src_jp + title_path]
        else:
            title = title_path # directory name
            jp_volumes = [src_jp + title_path + '/' + f_name for f_name in os.listdir(src_jp + title_path) if '.epub' in f_name ]
            jp_volumes.sort()

        if args['keyword'] is not None and args['keyword'].lower() not in title.lower():
            if verbose:
                print("Skipping %s" % title)
            continue

        if args['simulate']:
            title_id = get_oid(title, create_new_if_not_found=False)
            if title_id is None:
                print("New title found: %s" % title)
            continue
                
        title_id = get_oid(title)

        if title_id in manga_metadata_per_id and title_id in manga_data_per_id and not args['force']:
            if verbose:
                print("Skipping already processed %s" % title)
            continue

        print("Processing title [%s]: %s " % (title_id, title))

        if os.path.exists(args['source_dir'] + 'en/' + title + '.epub'):
            en_book = epub.read_epub(args['source_dir'] + 'en/' + title + '.epub')
            en_vol_title,_ = en_book.get_metadata('DC', 'title')[0]
        else:
            en_book = None

        if title_id not in manga_data_per_id:
            t_data = dict()
            t_data['_id'] = dict()
            t_data['_id']['$oid'] = title_id
            if en_book is not None:
                t_data['syn_en'] = en_vol_title
            else:
                t_data['syn_en'] = PLACEHOLDER
            t_data['syn_jp'] = PLACEHOLDER
            t_data['en_data'] = dict()
            t_data['jp_data'] = dict()

            t_data['en_data']['ch_naen'] = []
            t_data['en_data']['ch_enh'] = []
            t_data['en_data']['vol_en'] = dict()
            t_data['en_data']['ch_en'] = dict()

            manga_data_per_id[title_id] = t_data 
        else:
            t_data = manga_data_per_id[title_id]

        if title_id not in manga_metadata_per_id:
            t_metadata = dict()
            if en_book is not None:
                t_metadata['entit'] = en_book.get_metadata('DC', 'title')
            else:
                t_metadata['entit'] = title

            t_metadata['jptit'] = PLACEHOLDER
            t_metadata['coveren'] = PLACEHOLDER
            t_metadata['coverjp'] = PLACEHOLDER
            t_metadata['genres'] = []
            t_metadata['Author'] = [PLACEHOLDER]
            t_metadata['Artist'] = [PLACEHOLDER]

            t_metadata['Release'] = PLACEHOLDER
            t_metadata['Status'] = PLACEHOLDER
            t_metadata['search'] = PLACEHOLDER
            t_metadata['enid'] = title_id
            t_metadata['fetched'] = False

            manga_metadata_per_id[title_id] = t_metadata 
        else:
            t_metadata = manga_metadata_per_id[title_id]
        t_metadata['verified_ocr'] = True
        t_metadata['is_book'] = True
        t_data['is_book'] = True


        #############  process english chapters
        if en_book is not None:

            t_data['en_data']['ch_naen'] = []
            t_data['en_data']['ch_enh'] = []
            t_data['en_data']['vol_en'] = dict()
            t_data['en_data']['ch_en'] = dict()

            vol_name = en_vol_title
            vol_id = get_oid(title_id + '/en/' + vol_name)
            vol_number = 1

            print("\tVolume EN [%s]: %s " % (vol_id, vol_name))

            vol_ipfs_path = target_ipfs_path + vol_id

            if not os.path.exists(vol_ipfs_path):
                os.mkdir(vol_ipfs_path)
 
            save_cover_image_from_epub(t_metadata, en_book, 'en',title)

            t_data['en_data']['virtual_chapter_page_count'] = []

            process_epub(t_data, title_id, en_book,'en', vol_id, en_vol_title, 0)


        #############  process jp volumes/chapters
        t_data['jp_data']['ch_najp'] = []
        t_data['jp_data']['ch_jph'] = []
        t_data['jp_data']['vol_jp']= dict()
        t_data['jp_data']['ch_jp'] = dict()
        t_data['jp_data']['virtual_chapter_page_count'] = []
        total_ch_count = 0

        for vol_idx, jp_volume_f in enumerate(jp_volumes):

            jp_book = epub.read_epub(jp_volume_f)
            jp_vol_title,_ = jp_book.get_metadata('DC', 'title')[0]
            vol_id = get_oid(title_id + '/jp/' + jp_vol_title)

            print("\tVolume JP [%s]: %s " % (vol_id, jp_vol_title))

            if vol_idx == 0:
                # get the metadata from the first volume
                t_data['syn_jp'] = jp_book.get_metadata('DC', 'description')

                # get rid of of the volume part in title
                jptitle = jp_vol_title.split(' 上 ')[0]
                jptitle = jptitle.split(' 中 ')[0]
                jptitle = jptitle.split(' 下 ')[0]

                t_metadata['jptit'] = jptitle
                creator, _ = jp_book.get_metadata('DC', 'creator')[0]
                t_metadata['Author'] = [creator]

                # get the cover image from the first volume also
                save_cover_image_from_epub(t_metadata, jp_book, 'jp',title)

            total_ch_count += process_epub(t_data, title_id, jp_book,'jp', vol_id, jp_vol_title, total_ch_count)


        save_metadata_files()

def remove(args):
    found = False
    for title, title_id in ext_object_ids.items():
        if args['title_id'] == title_id:

            if title_id in manga_metadata_per_id:
                found = True
                print("Deleting %s [%s]" % (title,title_id))
                del(manga_data_per_id[title_id])
                del(manga_metadata_per_id[title_id])
                save_metadata_files()

                if title_id in ext_mangaupdates:
                    del(ext_mangaupdates[title_id])
                    ext_mangaupdates[title_id] =  { "series_id":-1 }
                    print(" * Deleted also mangaupdates match")
                    f = open(ext_mangaupdates_file,"w",encoding="utf-8")
                    s = json.dumps(ext_mangaupdates)
                    f.write(s)
                    f.close()

    if not found:
        print("Title id %s not found!" % args['title_id'])


def set_en_vol(args):
    title_id = args['title_id']
    if title_id in manga_metadata_per_id:
        t_data = manga_data_per_id[title_id]
        t_metadata = manga_metadata_per_id[title_id]

        en_book = epub.read_epub(args['file'])
        en_vol_title,_ = en_book.get_metadata('DC', 'title')[0]

        t_metadata['entit'] = en_vol_title
        t_data['syn_en'] = en_book.get_metadata('DC', 'description')

        t_data['en_data']['ch_naen'] = []
        t_data['en_data']['ch_enh'] = []
        t_data['en_data']['vol_en'] = dict()
        t_data['en_data']['ch_en'] = dict()
        ch_idx = 1

        vol_name = en_vol_title
        vol_id = get_oid(title_id + '/en/' + vol_name)
        vol_number = 1

        print("\tVolume EN [%s]: %s " % (vol_id, vol_name))

        vol_ipfs_path = target_ipfs_path + vol_id

        if not os.path.exists(vol_ipfs_path):
            os.mkdir(vol_ipfs_path)

        save_cover_image_from_epub(t_metadata, en_book, 'en',en_vol_title)

        t_data['en_data']['virtual_chapter_page_count'] = []

        process_epub(t_data, title_id, en_book,'en', vol_id, en_vol_title, 0)

        save_metadata_files()

    else:
        print("Title id %s not found!" % args['title_id'])

def search(args):
    saved_oids = []
    for title, title_id in ext_object_ids.items():
        if args['keyword'].lower() in title.lower():
            print("[%s] %s" % (title_id,title))
            if verbose:
                saved_oids.append(title_id)
        if verbose:
            for oid in saved_oids:
                if oid in title:
                    print("[%s] -> [%s] %s" % (oid,title_id,title))

def show(args):
    for title_id, mdata in manga_metadata_per_id.items():
        for title, oid in ext_object_ids.items():
            if oid == title_id:
                entit = mdata['entit']
                mark = ' '
                if entit.lower() != title.lower():
                    mark = '*'
                print("%s [%s] %s\t%s" % (mark,title_id,title.ljust(20),mdata['entit']))


if cmd != None:
  locals()[cmd](args)
