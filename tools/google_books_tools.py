import json
import argparse
import time
import os
import requests
import json
import re
from datetime import date
import logging
from bs4 import BeautifulSoup
logging.captureWarnings(True) # repress HTML certificate verification warnings
from deepl_helper import deepl_translate
import unicodedata as ud
import urllib

parser = argparse.ArgumentParser(
    prog="google_books_tools",
    description="Bilingual Manga DB <-> Google Books match and update tool",
     
)
subparsers = parser.add_subparsers(help='', dest='command')

parser_match_all = subparsers.add_parser('match_all', help='Search data for all the book titles and select the first match')

parser_update = subparsers.add_parser('refresh', help='Refresh entries')
parser_update.add_argument('keyword', type=str, help='search keyword (e.g: Meitantei)')

parser_list = subparsers.add_parser('show', help='Show matched titles')

parser_search = subparsers.add_parser('search', help='Search book titles from Google Books')
parser_search.add_argument('keyword', type=str, help='search keyword (e.g: Meitantei)')

parser_match_url = subparsers.add_parser('match_url', help='Match book titles via Google Books URL')
parser_match_url.add_argument('title', type=str, help='Book title')
parser_match_url.add_argument('url', type=str, help='Google Books URL')

parser_match_url = subparsers.add_parser('match_googleid', help='Match book titles via Google Books ID')
parser_match_url.add_argument('title', type=str, help='Book title')
parser_match_url.add_argument('googleid', type=str, help='Google Books ID')

parser_select = subparsers.add_parser('match', help='Select book title from search results')
parser_select.add_argument('title', type=str, help='Book title')
parser_select.add_argument('keyword', type=str, help='search keyword (e.g: Meitantei)')
parser_select.add_argument('index', type=int, help='search result index number')

parser_remove = subparsers.add_parser('remove', help='Remove book title match')
parser_remove.add_argument('title', type=str, help='book title')

args = vars(parser.parse_args())
cmd = args.pop('command')

base_dir = "./"

ext_manga_data_file = base_dir + "json/ext.manga_data.json"
ext_manga_metadata_file = base_dir + "json/ext.manga_metadata.json"
google_books_file = base_dir + "json/google_books.json"
ext_oid_file = 'json/ext.oids.json'

search_url = "https://www.googleapis.com/books/v1/volumes?q="
get_volume_url = "https://www.googleapis.com/books/v1/volumes/"
headers = {'Content-Type': 'application/json'}

title_name_to_id = dict()
title_names = dict()
title_years = dict()
synopsis = dict()
authors = dict()
publishers = dict()

all_entries = dict()
ext_object_ids = dict()

try:
    with open(google_books_file,"r",encoding="utf-8") as f:
        data = f.read()
        entries = json.loads(data)
        for id,item in entries.items():
            all_entries[id] = item
except:
    print("Existing google_books.json not found")

if os.path.exists(ext_oid_file):
    with open(ext_oid_file,'r',encoding="UTF-8") as oid_f:
        ext_object_ids = json.loads(oid_f.read())


with open(ext_manga_metadata_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_titles = json.loads(data)
    for t in manga_titles:
        if 'is_book' in t and t['is_book']:
            title_id = t['enid']
            title_name = t['jptit']
            title_years[title_id] = t['Release']
            title_names[title_id] = title_name
            authors[title_id] = t['Author']
            if 'Publisher' in t and t['Publisher'] != 'Placeholder':
                publishers[title_id] = t['Publisher']
                
            title_name_to_id[title_name.lower()] = title_id


with open(ext_manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_data = json.loads(data)
    for m in manga_data:
        title_id = m['_id']['$oid']
        if title_id in title_names:
            synopsis[title_id] = m['syn_en']
            pages = m['jp_data']['ch_jp']

def clean_text(title):
    title = title.replace('&#039;',"'")
    title = title.replace('&quot;','"')
    title = title.replace('&amp;',"&")
    return title

CLEANR = re.compile('<.*?>') 
def cleanhtml(raw_html):
  if raw_html is None:
      return None
  cleantext = re.sub(CLEANR, '', raw_html)
  cleantext = clean_text(cleantext)
  return cleantext

def get_title_id(item):
    item = item.lower()
    if item in title_name_to_id.keys():
        return title_name_to_id[item]
    if item in title_names.keys():
        # the item is in fact the title id
        return item
    raise Exception("unknown book title/id %s" % str(item))

def show(args):
    i = 0
    for title_id, title_name in title_names.items():
        i += 1
        if title_id not in all_entries:
            print("MISSING: [%s] %s " % (title_id, title_name))
        else:
            c = all_entries[title_id]
            if c['id'] == -1:
                print("OMITTED: [%s] " % (title_id))
            else:
                t = c['volumeInfo']['title']
                star = '* ' if t.lower() != title_name.lower() else '  '
                cat = ' '
                print("%s %s %d [%s] %s : %s" % (star, cat, i, title_id, title_name,t ))


def search_records_and_select_one(title_id, keyword, author, index):

    keyword = ud.normalize('NFKC', keyword)
    keyword_candidates = set()
    keyword_candidates.update([keyword])
    keyword_candidates.update([keyword.replace('ッ','')])
    keyword_candidates.update([keyword.replace(' ','')])

    url = search_url + keyword
    if author is not None:
        url += '+inauthor:' + author
    url = urllib.parse.quote(url, safe='+/:?=', encoding=None, errors=None)
    response = requests.get(url, headers=headers, verify=False)
    r = response.json()
    hits = r['totalItems']
    if hits>0:
        if index != -1:
            j = r['items'][index]
            # for some reason the search result doesn't contain always all the information
            #  (author or description. Try to fetch these with a separate query)
            url = j['selfLink']
            response = requests.get(url, headers=headers, verify=False)
            j = response.json()
            save_record(title_id,j)
            return True
        else:
            index = 0
            while index <len(r['items']):
                j = r['items'][index]
                vi = j['volumeInfo']
                title_candidates = set()
                if 'title' in vi:
                    title = ud.normalize('NFKC',vi['title'])
                    title_candidates.update([title])
                    title_candidates.update([title.replace('（上）','')])
                    title_candidates.update([title.replace('(上)','')])
                found = False
                for keyword_candidate in keyword_candidates:
                    for title_candidate in title_candidates:
                        if title_candidate in keyword_candidate:
                            found = True
                        if keyword_candidate in title_candidate:
                            found = True
                if found:
                    # for some reason the search result doesn't contain always all the information (author or description. Try to fetch these with a separate query)
                    url = j['selfLink']
                    response = requests.get(url, headers=headers, verify=False)
                    j = response.json()
                    vi = j['volumeInfo']                    
                    if 'description' in vi:
                        if author is None or 'authors' in vi:
                            print("[match #%d]" % (index+1))
                            save_record(title_id,j)
                            return True
                index += 1

    print("\t",title_names[title_id] + " with keyword " + keyword+ " not found")
    return False
    


def save_record(title_id,j):

    vi = j['volumeInfo']

    if 'authors' in vi:
        authors = vi['authors']
    else:
        authors = "NA"
    print("\t%s [%s] : MU name: %s (%s)" % (
            title_names[title_id], title_years[title_id], 
            vi['title'], authors)
    )

    vi['description'] = cleanhtml(vi['description'])

    print("BM synopsis: %s" % (synopsis[title_id]))
    print("MU synopsis: %s" % (vi['description']))
    print("")

    del(j['saleInfo'])
    del(j['accessInfo'])

    j['en_title_deepl'] = deepl_translate(j['volumeInfo']['title'])
    j['en_synopsis_deepl'] = deepl_translate(j['volumeInfo']['description'])

    j['last_refreshed_timestamp'] = int(time.time())

    all_entries[title_id] = j

    f = open(google_books_file,"w",encoding="utf-8")
    s = json.dumps(all_entries, ensure_ascii=False)
    f.write(s)
    f.close()
    return True


def search(args):

    url = search_url + '%s' % args['keyword']
    url = urllib.parse.quote(url, safe='+/:?=', encoding=None, errors=None)
    response = requests.get(url, headers=headers, verify=False)
    r_json = response.json()
    if r_json['totalItems'] == 0:
        print("No results!")
        return
    i = 1
    for r in r_json['items']:
        vj = r['volumeInfo']
        authors = []
        if 'authors' in vj:
            authors = vj['authors']
        print("%d: %s (authors %s)" % (i, vj['title'], authors))
        print("%s" % r['selfLink'])
        if 'description' in vj and 'publishedDate' in vj:
            print("\t(%s) %s" % (vj['publishedDate'], vj['description']))
        else:
            print("\t NO DESCRIPTION OR PUBLISHED DATE")
        print("")
        i += 1


def match(args):
    title_id = get_title_id(args['title'])
    search_records_and_select_one(title_id, args['keyword'], False, args['index']-1)

def match_url(args):
    title_id = get_title_id(args['title'])

    if '/books/edition/_/' in args['url']:
        splitter = '/books/edition/_/'
    else:
        print("Unknown url: %s" % args['url'])
        return

    id_attempt = args['url'].split(splitter)
    if len(id_attempt)==2:
        id = id_attempt[1].split('/')[0]
        url = get_volume_url + id
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200:
            print("Error:", response.reason)
            return
        j = response.json()
        save_record(title_id,j)
        #print(j)
    else:
        print("Invalid url: %s" % args['url'])
    
def match_googleid(args):
    title_id = get_title_id(args['title'])

    url = get_volume_url + args['googleid']
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code != 200:
        print("Error:", response.reason)
        return
    j = response.json()
    save_record(title_id,j)

def refresh(args):

    i = 0
    for title_id, j in all_entries.items():
        i += 1

        if args['keyword'] is not None and args['keyword'].lower() not in title_names[title_id].lower():
            continue

        updated = False
        timestamp = int(time.time())
        if 'last_refreshed_timestamp' not in j or (j['last_refreshed_timestamp'] < timestamp - 24*60*60) or args['keyword'] is not None:

            print("Updating %d : %s" % (i,title_names[title_id]))
            j['last_refreshed_timestamp'] = int(time.time())

            url = j['selfLink']
            response = requests.get(url, headers=headers, verify=False)
            new_j = response.json()
            j['volumeInfo'] = new_j['volumeInfo']

            j['volumeInfo']['description'] = cleanhtml(j['volumeInfo']['description'])
            updated = True


        if ('en_title_deepl' not in j) or (j['en_title_deepl'] == ''):
            j['en_title_deepl'] = deepl_translate(j['volumeInfo']['title'])
            updated = True

        if ('en_synopsis_deepl' not in j) or (j['en_synopsis_deepl'] == ''):
            j['en_synopsis_deepl'] = deepl_translate(j['volumeInfo']['description'])
            updated = True

        if updated:
            all_entries[title_id] = j

            f = open(google_books_file,"w",encoding="utf-8")
            s = json.dumps(all_entries, ensure_ascii=False)
            f.write(s)
            f.close()


def match_all(args):
    no_matches = []
    for title_id, title_name in title_names.items():
        if not title_id in all_entries:

            title_name = title_name.replace('.TXT','')
            title_name = title_name.replace('.txt','')

            if title_name == 'Placeholder':
                print("Skipping",title_id)
                continue

            print("Searching %s:%s" % (title_id,title_name))
            queries = []
            keyword = title_name
            queries.append((keyword,None))

            for author in authors[title_id]:
                if author != 'Placeholder':
                    queries.insert(0,(keyword,author))

            if title_id in publishers:
                keyword += ' ' + publishers[title_id]
                queries.insert(0,(keyword,None))

            i = 0
            res = False
            while i<len(queries) and res==False:
                keyword, author = queries[i]
                res = search_records_and_select_one(title_id,keyword,author,-1)
                time.sleep(1)
                i += 1

            if res == False:
                print("\t","!! No matches for %s [%s]" % (title_name,title_id))
                no_matches.append(title_id)
    if len(no_matches)>0:
        print("\nNo matches for these titles! Match manually with:")
        for title_id in no_matches:
            print("\t%s:\tpython3 tools/google_books_tools.py %s https://www.google.com/books/edition/_/" % (title_names[title_id],title_id))


def remove(args):
    title_id = get_title_id(args['title'])
    if title_id in all_entries:
        if all_entries[title_id]['id'] == -1:
            print("Already removed!")
            return
        
        del(all_entries[title_id])
        all_entries[title_id] =  { "id":-1 }
        f = open(google_books_file,"w",encoding="utf-8")
        f.write(json.dumps(all_entries))
        f.close()
        print("Removed match for %s [%s]" % (title_names[title_id],title_id))

    else:
        print("Match not found!")

if cmd != None:
  locals()[cmd](args)
