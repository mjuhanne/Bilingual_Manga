# These functions enable importing books in .txt format from Aozora repository 
# which have specific aozora [# ... ] formatting tags
# (explained https://www.aozora.gr.jp/aozora-manual/index-input.html

from book2bm_helper import *
import os
import re
from helper import *


text_regex = [
    # (一般小説) [藤沢周平] よろずや平四郎活人剣（上） (青空文庫対応txt 表紙付)(校正08-11-04).txt
    ["\(一般小説\)+\s+\[([^\]]+)\]\s+([^（\(\s\)]+)（(.{1})）",['author','title','vol_name']],
    ["\(一般小説\)+\s+\[([^\]]+)\]\s+([^（\(\s\)]+)",['author','title']],

    # 施耐庵／駒田信二訳-水滸伝（七）.txt
    ["([^／]+)／[^訳]+訳-([^\s(\d（上中下]*)（([^）]+){1}",['author','title','vol_name']],

    # 村上春樹-世界の終りとハードボイルド・ワンダーランド 1
    #["([^-]+)-(?:[^訳]+訳-)*([^\s(\d上中下]*)\s(\d+)",3]

    # ロレンス／吉田健一訳-息子と恋人 下巻 (青空文庫対応txt)(校正08-12-20).txt
    #["([^／]*)／([^訳]*)訳-([^\(]*) (.)巻 \(青空",['author','translator','title','vol_name']],

    # オーウェル／佐山栄太郎訳-動物農場 (青空文庫対応txt)(校正08-12-13).txt
    ["([^／]*)／([^訳]*)訳-([^\(]*)(.*) \(青空",['author','translator','title','vol_name']],

    # ドイル／延原謙訳-(新潮社版) シャーロック・ホームズの事件簿 (青空文庫対応txt)(校正09-11-10).txt
    ["([^／]*)／([^訳]*)訳-\(新潮社版\) ([^\(]*)(.*) \(青空",['author','translator','title','vol_name']],

    # ディック／朝倉久志訳-アンドロイドは電気羊の夢をみるか.txt
    ["([^／]*)／([^訳]*)訳-([^\(]*).txt",['author','translator','title']],

    # Ｅ・Ｅ・スミス／川口正吉訳-ヴァレロンのスカイラーク (青空文庫対応txt)(校正09-06-06).txt
    #["([^／]+)／[^訳]+訳-([^\s(\d上中下]*)",2],

    # 村上春樹-世界の終りとハードボイルド・ワンダーランド (上).txt
    ["([^-]*)-([^\(]*) \((.)\)",['author','title','vol_name']],

]


def get_info_from_txt_file_name(root_path,source_item, og_title, og_author):
    vol_name = None

    for reg in text_regex:
        res = re.search(reg[0],source_item)
        if res is not None:
            gr = res.groups()
            vol_name = ''
            translator = ''
            title = og_title
            author = og_author
            for field, value in zip(reg[1], res.groups()):
                if author is None and field == 'author':
                    author = value
                if title is None and field == 'title':
                    title = value
                if field == 'vol_name':
                    vol_name = value
                if field == 'translator':
                    translator = '(%s訳)' % value

            if vol_name == '':
                if '（上）' in source_item:
                    vol_name = '上'
                elif '（下）' in source_item:
                    vol_name = '下'
                elif '（中）' in source_item:
                    vol_name = '中'
                else:
                    vol_name = title
            if translator != '':
                vol_name += ' ' + translator

            if title != '' and author != '':
                return title, {'type':'txt','author':author,'volume_name':vol_name,'path':root_path,'filename': source_item}

    return None, None


wide_numbers = {'０':'0','１':'1','２':'2','３':'3','４':'4','５':'5','６':'6','７':'7','８':'8','９':'9'}
def wide_numbers_to_int(txt):
    new_txt = ''
    for ch in txt:
        if ch in wide_numbers.keys():
            new_txt += wide_numbers[ch]
        else:
            raise Exception("Invalid number" % txt)
    return int(new_txt)

def process_note(line,note,note2,rice,txt_line):
    if 'unicode' in note:
        try:
            uc = '0x'+ note.split('unicode')[1]
            uc_int = int(uc,0)
            uc_char = chr(uc_int)
            line += uc_char
        except:
            print("Error in unicode note [%s]" % note)
    elif '地付き' in note:
        # TODO: in vertical writing put the following text inferiorily
        # or in horizontal writing more it to the right side
        # 地付き or ここから地付き
        pass
    elif '表紙' in note:
        # TODO: refer cover image
        pass
    elif '字下げ' in note:
        if 'ここ' in note:
            # TODO: in vertical writing move the text between 
            # ここからx字下げ and 'ここで字下げ終わり'  inferiorily
            # or in horizontal writing more it to the right
            pass
        elif 'この行' in note:
            # TODO
            pass
        else:
            num_chars_str = note[0:note.find('字下げ')]
            num_chars = wide_numbers_to_int(num_chars_str)
            line += '\u3000' * num_chars
    elif len(note) == 1 and is_katakana_word(note):
        # TODO: # add small okurigana (訓点送り仮名 in https://www.aozora.gr.jp/annotation/kunten.html)
        pass
    elif 'に傍点' in note:
        # TODO: add emphasis marks
        pass
    elif note == '画像終わり':
        # TODO
        pass
    elif '段階大きい文字' in note:
        # TODO: ２段階大きい文字
        pass
    elif 'はゴシック体' in note:
        # TODO: gothic style
        pass
    elif '挿絵' in note:
        # TODO: include image
        pass
    elif '＋' in note:
        # TODO: how to combine components into kanji? For now just output the raw note
        line += note
    elif '／' in note:
        # TODO: '「凹／儿」'
        # Is this an alternative? For now just output the raw note
        line += note
    else:
        print("NOTICE! Unhandled note [%s] in line [%s]" % (note,txt_line))
        pass
    return line


def get_chapters_from_txt_file(path):
    txt_lines = []
    encodings = ['utf-8','shift_jis','utf_16','utf_32','shift_jis_2004','shift_jisx0213','euc_jp','cp932','euc_jis_2004','euc_jisx0213','iso2022_jp','iso2022_jp_1','iso2022_jp_2','iso2022_jp_2004',',iso2022_jp_3','iso2022_jp_ext',]
    for encod in encodings:
        if len(txt_lines) == 0:
            try:
                with open(path,"r",encoding=encod) as f:
                    d = f.read()
                    txt_lines = d.split('\n')
            except:
                pass

    ocr_dict = dict()
    chapter_paragraphs = []
    #chapter_pages = []
    num_sentences = 0
    num_characters = 0

    chapters = []

    chapter_name = 'Heading'
    page_breaks = []

    for txt_line in txt_lines:

        lines = []
        p_dict = dict()
        p_ruby_items = []
        p_len = 0
        line = ''
        rice = False

        i = 0
        while i<len(txt_line):

            if txt_line[i] == '※':
                rice = True
                i += 1
            elif txt_line[i] == '［':
                # note/annotation/formatting
                if i+1 < len(txt_line) and txt_line[i+1] == '＃':
                    i += 2
                    remainder = txt_line[i:]
                    if '］' in remainder:
                        note = remainder[0 : remainder.find('］')]
                        i += len(note) + 1
                        note2 = None
                        if i < len(txt_line) and txt_line[i] == '→':
                            i += 1
                            if i < len(txt_line) and txt_line[i] == '［':
                                remainder = txt_line[i:]
                                if '］' in remainder:
                                    note2 = remainder[0 : remainder.find('］')]
                                    i += len(note2)
                                else:
                                    print("Unexpected end of note2 [%s] at %d" % (txt_line,i))
                                    line += txt_line[i:]
                                    i = len(txt_line)
                            else:
                                print("Unexpected end of note2 [%s] at %d" % (txt_line,i))
                                line += txt_line[i:]
                                i = len(txt_line)
                        if note == '改ページ':
                            page_breaks.append(len(chapter_paragraphs))
                        else:
                            line = process_note(line,note,note2,rice,txt_line)

                    else:
                        print("Unexpected end of note [%s] at %d" % (txt_line,i))
                        line += txt_line[i:]
                        i = len(txt_line)
                else:
                    line += txt_line[i]
                    i += 1
            elif txt_line[i] == '《':
                # ruby
                i += 1
                remainder = txt_line[i:]
                if '》' in remainder:
                    ruby = remainder[0 : remainder.find('》')]
                    j = i-2
                    ruby_start_characters = ['｜','\u3000','。、？']
                    while j>=0 and txt_line[j] not in ruby_start_characters and is_cjk(txt_line[j]):
                        j -= 1
                    ruby_len = i-2-j
                    p_ruby_items.append({'s':p_len + len(line) - ruby_len,'l':ruby_len,'rt':ruby})
                    i += len(ruby) + 1
            elif txt_line[i] == '｜':
                i += 1
            elif txt_line[i] == '。':
                line += txt_line[i]
                i += 1
                p_len += len(line)
                lines.append(line)
                line = ''
                num_sentences += 1
            else:
                line += txt_line[i]
                i += 1

        line = cleanhtml(line)

        if len(line.strip())>0:
            if len(lines)==0 and len(line)<10 and len(p_ruby_items) == 0:
                # get rid of spaces in table of contents and sub titles
                line = line.replace('\u3000','')
                line = line.replace(' ','')
            if '-------' in line:
                page_breaks.append(len(chapter_paragraphs))
            else:
                lines.append(line)
                num_sentences += 1

        p_dict['lines'] = lines
        if len(p_ruby_items)>0:
            p_dict['ruby'] = p_ruby_items

        if len(lines)==0:
            if txt_line == '':
                chapter_paragraphs.append(p_dict)
        else:
            num_characters += len(''.join(lines))
            chapter_paragraphs.append(p_dict)

    chapters.append({
        'paragraphs' : chapter_paragraphs,
        'name' : chapter_name,
        'page_breaks' : page_breaks,
        'num_characters' : num_characters,
        'num_sentences' : num_sentences,
        'num_pages' : get_virtual_page_count_from_characters(num_characters)
    })


    if len(chapters) == 1:
        # divide into chapters by page breaks
        chapters = divide_chapters(chapters, 'isolated_scroll_reference')

    if len(chapters) == 1:
        # divide into chapters by page breaks
        chapters = divide_chapters(chapters, 'page_break')

    if len(chapters) < 2:
        chapters = divide_chapters(chapters, 'isolated_double_line_with_number')

    if len(chapters) < 2:
        chapters = divide_chapters(chapters, 'isolated_line')

    return chapters

def divide_chapters(chapters, divide_type):
    if len(chapters) == 0:
        return []
    chapter = chapters[0]
    existing_chapter_names = [ch['name'] for ch in chapters]
    chapters = []

    chapter_name = chapter['name']
    page_breaks = chapter['page_breaks']
    paragraphs = chapter['paragraphs']
    p_break_idx = 0
    p_i = 0

    def is_chapter_break():
        nonlocal p_break_idx
        nonlocal page_breaks
        nonlocal paragraphs
        nonlocal p_i
        if p_i > len(paragraphs) - 10:
            # don't start a new chapter near the end of the book
            return False
        if divide_type == 'isolated_scroll_reference':
            if p_i < len(paragraphs) - 2:
                line_lengths = [len(''.join(paragraphs[p_i+i]['lines'])) for i in range(3)]
                if line_lengths[0] == 0 and line_lengths[2] == 0:
                    lines = paragraphs[p_i+1]['lines']
                    if len(lines)>0:
                        if lines[0][0] == '巻' and '註' not in lines[0]:
                            return True
                        if lines[0][0] == '第' and lines[0][-1] == '回':
                            return True

        if divide_type == 'isolated_double_line_with_number':
            if p_i < len(paragraphs) - 4:
                ll = [len(''.join(paragraphs[p_i+i]['lines'])) for i in range(4)]
                if ll[0]==0 and ll[1]>0 and ll[2]>0 and ll[3]==0:
                    lines = paragraphs[p_i+1]['lines']
                    if len(lines)>0:
                        line = lines[0].replace('\u3000','')
                        if line[0] in wide_numbers.keys() or line[0].isdigit():
                            return True

        if divide_type == 'page_break':
            if p_break_idx < len(page_breaks) and p_i == page_breaks[p_break_idx]:
                p_break_idx += 1
                return True
        if divide_type == 'isolated_line':
            if p_i < len(paragraphs) - 2:
                line_lengths = [len(''.join(paragraphs[p_i+i]['lines'])) for i in range(3)]
                if line_lengths[0] == 0 and line_lengths[1] > 0 and line_lengths[2] == 0:
                    return True
        return False

    new_chapter = {
        'paragraphs' : [],
        'name' : chapter_name,
        'num_characters' : 0,
        'num_sentences' : 0,
        'page_breaks' : [],
    }
    while p_i < len(paragraphs):
        if is_chapter_break():
            new_chapter['num_pages'] = get_virtual_page_count_from_characters(new_chapter['num_characters'])
            if len(new_chapter['paragraphs']) < 5:
                # don't start a new chapter if the current is too short
                pass
            else:
                chapters.append(new_chapter)
                new_chapter = None
            while p_i < len(paragraphs) and len(''.join(paragraphs[p_i]['lines']))==0:
                # find the first sentence in the new chapter
                p_i += 1

            if p_i < len(paragraphs):
                # first sentence in the new chapter is the chapter name
                chapter_name = paragraphs[p_i]['lines'][0]
                chapter_name = chapter_name.replace('\u3000','')
                chapter_name = chapter_name.replace(' ','')

                while chapter_name in existing_chapter_names:
                    chapter_name += ' -'  # to avoid collision of OIDs should there be duplicate chapter names
                existing_chapter_names.append(chapter_name)
                
                if new_chapter is None:
                    new_chapter = {
                        'paragraphs' : [],
                        'name' : chapter_name, 
                        'num_characters' : 0,
                        'num_sentences' : 0,
                        'page_breaks' : [],
                    }
                else:
                    # replace the current chapter name
                    new_chapter['name'] = chapter_name
        else:
            new_chapter['paragraphs'].append(paragraphs[p_i])
            lines = paragraphs[p_i]['lines']
            new_chapter['num_sentences'] += len(lines)
            new_chapter['num_characters'] += len(''.join(lines))
            if divide_type != 'page_break':
                if p_break_idx < len(page_breaks) and p_i == page_breaks[p_break_idx]:
                    new_chapter['page_breaks'].append(len(new_chapter['paragraphs']))
                    p_break_idx += 1
            p_i += 1
    if len(new_chapter['paragraphs'])>0:
        new_chapter['num_pages'] = get_virtual_page_count_from_characters(new_chapter['num_characters'])
        chapters.append(new_chapter)
    return chapters




def process_txt_file(t_data, title_id, filepath, lang, vol_id, vol_name, start_ch_idx, ask_confirmation_for_new_chapters ):

    lang_data_field = lang + '_data'
    ch_name_field = 'ch_na' + lang
    ch_lang_h_field = 'ch_' + lang + 'h'
    ch_lang_field = 'ch_' + lang
    vol_lang_field = 'vol_' + lang

    print("Process vol/book %s [%s]" % (vol_name,vol_id))

    chapters = get_chapters_from_txt_file(filepath)

    t_data[lang_data_field][vol_lang_field][vol_name] = {'id':vol_id,'s':start_ch_idx,'e':start_ch_idx + len(chapters)-1}

    target_ocr_file_path = None
    target_page_file_path = None
    chapter_paragraphs = []
    chapter_pages = []
    total_num_characters = 0

    for ch_idx, chapter in enumerate(chapters):

        ch_name = chapter['name']

        ch_id = get_oid(title_id + '/' + lang + '/' + vol_id + '/' + ch_name, ask_confirmation=ask_confirmation_for_new_chapters)
        ch_ipfs_path = target_ipfs_path + ch_id
        t_data[lang_data_field][ch_name_field].append(ch_name)
        t_data[lang_data_field][ch_lang_h_field].append(ch_id + '/%@rep@%')
        t_data[lang_data_field][ch_lang_field][start_ch_idx+ch_idx+1] = ['pages.html']
        print("Chapter %s [%s]: %s " % (lang, ch_id, ch_name))

        target_ocr_file_path = target_ocr_path + ch_id + '.json'
        ocr_dict = dict()
        chapter_paragraphs = []
        chapter_pages = []

        ch_html = '<div>'
        for p_dict in chapter['paragraphs']:

            lines_str = ''.join(p_dict['lines'])
            if len(lines_str)>0:
                if lang == 'jp':
                    ch_html += '<p block_id=%s>' % len(chapter_paragraphs)
                else:
                    ch_html += '<p en_block_id=%s>' % len(chapter_paragraphs)           

                ch_html += lines_str
                ch_html += '</p>'
                chapter_paragraphs.append(p_dict)

        ch_html += '</div>'
        chapter_pages.append(ch_html)


        if lang == 'jp':
            t_data[lang_data_field]['virtual_chapter_page_count'].append(get_virtual_page_count_from_characters(chapter['num_characters']))
        else:
            t_data[lang_data_field]['virtual_chapter_page_count'].append(get_virtual_page_count_from_words(chapter['num_words']))

        print("\t.. with %s pages / %d paragraphs / %d sentences / %d characters" % (
            t_data[lang_data_field]['virtual_chapter_page_count'][-1],
            len(chapter_paragraphs),chapter['num_sentences'],chapter['num_characters']))

        if lang == 'jp':
            if len(chapter_paragraphs)>0:
                print("\t\tWriting OCR file %s" % target_ocr_file_path)
                ocr_dict['0'] = chapter_paragraphs
                target_ocr_f = open(target_ocr_file_path,'w',encoding="UTF-8")
                target_ocr_f.write(json.dumps(ocr_dict))
                target_ocr_f.close()

        save_chapter_pages(ch_id, chapter_pages)
        total_num_characters += chapter['num_characters']

    print("** Total %d characters" % (total_num_characters))
    return len(chapters)


