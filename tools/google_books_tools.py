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
from br_mongo import *
from helper import get_metadata_by_title_id, get_jp_title_names, get_jp_title_by_id, get_authors, get_publisher, get_data_by_title_id, is_book, get_title_id

QUOTA_EXCEEDED = "quota_exceeded"
NOT_FOUND = "not_found"
quota_exceeded_timeout_counter = -1

base_dir = "./"

search_url = "https://www.googleapis.com/books/v1/volumes?q="
get_volume_url = "https://www.googleapis.com/books/v1/volumes/"
headers = {'Content-Type': 'application/json'}

def get_google_books_entry(title_id):
    entry = database[BR_GOOGLE_BOOKS].find_one({'_id':title_id})
    if entry is not None and (entry['google_book_id'] == QUOTA_EXCEEDED or entry['google_book_id'] == NOT_FOUND):
        return None
    return entry

def get_title_name(title_id):
    t = get_metadata_by_title_id(title_id)
    return t['jptit']

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

def show(args):
    i = 0
    for title_id, title_name in get_jp_title_names().items():
        if is_book(title_id):
            i += 1
            c = get_google_books_entry(title_id)
            if c is None:
                print("MISSING: [%s] %s " % (title_id, title_name))
            else:
                if c['id'] == -1:
                    print("OMITTED: [%s] " % (title_id))
                else:
                    t = c['volumeInfo']['title']
                    star = '* ' if t.lower() != title_name.lower() else '  '
                    cat = ' '
                    print("%s %s %d [%s] %s : %s" % (star, cat, i, title_id, title_name,t ))


def search_records_and_select_one(title_id, search_metadata, index, manual_confirmation=False):

    global quota_exceeded_timeout_counter

    if quota_exceeded_timeout_counter >= 0:
        print("[%s]: Google Books quota exceeded for the day. Retrying after %d queries" % (title_id, quota_exceeded_timeout_counter))
        j = {'google_book_id' : QUOTA_EXCEEDED}
        database[BR_GOOGLE_BOOKS].update_one({'_id':title_id},{'$set':j},upsert=True)
        quota_exceeded_timeout_counter -= 1
        return None

    tried_metadata = []
    entry = database[BR_GOOGLE_BOOKS].find_one({'_id':title_id})
    if entry is not None and entry['google_book_id'] == NOT_FOUND:
        tried_metadata = entry['tried_metadata']
        for metadata in entry['tried_metadata']:
            if metadata == search_metadata:
                # search has already failed with this metadata
                return None
    tried_metadata.append(search_metadata)

    keyword = search_metadata['title']
    author = search_metadata.get('author')
    translator = search_metadata.get('translator')
    publisher = search_metadata.get('publisher')

    keyword = ud.normalize('NFKC', keyword)
    keyword_candidates = set()
    keyword_candidates.update([keyword])
    keyword_candidates.update([keyword.replace('ッ','')])
    keyword_candidates.update([keyword.replace(' ','')])
    keyword_candidates.update([keyword.replace('_','')])

    url = search_url + keyword
    if author is not None:
        url += '+inauthor:' + author
    url = urllib.parse.quote(url, safe='+/:?=', encoding=None, errors=None)
    response = requests.get(url, headers=headers, verify=False)
    r = response.json()
    if r is not None and 'totalItems' in r:
        quota_exceeded_timeout_counter = -1
        hits = r['totalItems']
        if hits>0:
            if index != -1:
                j = r['items'][index]
                # for some reason the search result doesn't contain always all the information
                #  (author or description. Try to fetch these with a separate query)
                url = j['selfLink']
                response = requests.get(url, headers=headers, verify=False)
                j = response.json()
                return save_record(title_id,j)
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
                        title_candidates.update([title.replace(' ','')])
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
                        authors = []
                        detected_translator = ''
                        if 'authors' in vi:
                            for author in vi['authors']:
                                if '／' in author:
                                    auth_tr = author.split('／')
                                    if '訳' == auth_tr[1][-1]:
                                        detected_translator = auth_tr[1][:-1]
                                        authors.append(auth_tr[0])
                                    else:
                                        authors.append(auth_tr[0])
                                        authors.append(auth_tr[1])
                                else:
                                    authors.append(author)
                        vi['authors'] = authors
                        if 'description' in vi and vi['language'] == 'ja':
                            if author is None or len(authors)>0:
                                if translator is None or translator == detected_translator:
                                    print("[match #%d]" % (index+1))
                                    ok = True
                                    if manual_confirmation:
                                        translate_metadata(j)
                                        print("Title: ",vi['title'])
                                        print("Authors: ",vi['authors'])
                                        print("Authors (en): ",j['en_authors_deepl'])
                                        if detected_translator != '':
                                            print("Detected translator:",detected_translator)
                                        if translator is not None:
                                            print("Translator:",translator)
                                        if publisher is not None:
                                            print("Publisher:",publisher)
                                        print("Description: ",vi['description'])
                                        print("Description (en): ",j['en_synopsis_deepl'])
                                        print("Publisher: ",vi['publisher'])
                                        ans = input("Is this ok? ")
                                        if ans != 'y':
                                            ok = False
                                    if ok:
                                        return save_record(title_id,j)
                                    else:
                                        print("Skipped")
                                        return None
                    index += 1
    elif 'error' in r:
        if r['error']['code'] == 429:
            print("[%s] %s: Google Books quota exceeded for the day. Retry later" % (title_id, keyword))
            j = {'google_book_id' : QUOTA_EXCEEDED}
            database[BR_GOOGLE_BOOKS].update_one({'_id':title_id},{'$set':j},upsert=True)
            quota_exceeded_timeout_counter = 50
            return None
        else:
            print("[%s] %s: Error %s" % (title_id, keyword, str(r)))
    else:
        print("Unknown response %s" % str(r))

    j = {'google_book_id' : NOT_FOUND, 'tried_metadata':tried_metadata}
    database[BR_GOOGLE_BOOKS].update_one({'_id':title_id},{'$set':j},upsert=True)
    print("\t",get_jp_title_by_id(title_id) + " with keyword " + keyword+ " not found")
    return None

    
def clean_google_books_title(title):
    vols = ['上','中','下']
    for vol in vols:
        if title[-1] == vol:
            if title[-2] == '\u3000':
                title = title[:-2]
    return title

def translate_metadata(j):
    title = j['volumeInfo']['title']
    title = clean_google_books_title(title)

    j['en_title_deepl'] = deepl_translate(title)
    if 'description' in j['volumeInfo']:
        j['en_synopsis_deepl'] = deepl_translate(j['volumeInfo']['description'])
    else:
        j['en_synopsis_deepl'] = 'NA'
    j['en_authors_deepl'] = []
    if 'authors' in j['volumeInfo']:
        for jp_author in j['volumeInfo']['authors']:
            j['en_authors_deepl'].append(deepl_translate(jp_author))


def save_record(title_id,j):

    j['google_book_id'] = j['id']
    del(j['id'])
    metadata = get_metadata_by_title_id(title_id)
    data = get_data_by_title_id(title_id)
    vi = j['volumeInfo']

    if 'authors' in vi:
        authors = vi['authors']
    else:
        authors = "NA"
    print("\t%s [%s] : MU name: %s (%s)" % (
            get_jp_title_by_id(title_id), metadata['Release'], 
            vi['title'], authors)
    )

    if 'description' in vi:
        vi['description'] = cleanhtml(vi['description'])
    else:
        vi['description'] = 'NA'

    print("BM synopsis: %s" % (data['syn_jp']))
    print("MU synopsis: %s" % (vi['description']))
    print("")

    del(j['saleInfo'])
    del(j['accessInfo'])

    if 'en_title_deepl' not in j:
        translate_metadata(j)

    j['last_refreshed_timestamp'] = int(time.time())

    database[BR_GOOGLE_BOOKS].update_one({'_id':title_id},{'$set':j},upsert=True)
    return database[BR_GOOGLE_BOOKS].find_one({'_id':title_id})


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
    search_metadata = { 'title' : args['keyword'] }
    search_records_and_select_one(title_id, search_metadata, args['index']-1)

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
        return None
    j = response.json()
    if 'authors' not in j['volumeInfo']:
        print("Warning! No author included in response!")
    return save_record(title_id,j)


def is_title_ignored_for_google_books(title_id):
    j = database[BR_GOOGLE_BOOKS].find_one({'_id':title_id})
    if j is None:
        return False
    else:
        return j['google_book_id'] == -1

def was_google_books_quota_exceeded_for_title(title_id):
    j = database[BR_GOOGLE_BOOKS].find_one({'_id':title_id})
    if j is None:
        return False
    else:
        return j['google_book_id'] == QUOTA_EXCEEDED

def ignore_google_book_matching_for_title(title_id):
    j = dict()
    j['google_book_id'] = -1
    j['_id'] = title_id
    database[BR_GOOGLE_BOOKS].update_one({'_id':title_id},{'$set':j},upsert=True)
    return database[BR_GOOGLE_BOOKS].find_one({'_id':title_id})

def refresh(args):

    i = 0
    for title_id, title_name in get_jp_title_names().items():
        i += 1

        if args['keyword'] is not None and args['keyword'].lower() not in get_jp_title_by_id(title_id).lower():
            continue

        j = get_google_books_entry(title_id)

        updated = False
        timestamp = int(time.time())
        if 'last_refreshed_timestamp' not in j or (j['last_refreshed_timestamp'] < timestamp - 24*60*60) or args['keyword'] is not None:

            print("Updating %d : %s" % (i,get_jp_title_by_id(title_id)))
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

        if ('en_authors_deepl' not in j) or (j['en_authors_deepl'] == ''):
            j['en_authors_deepl'] = deepl_translate(j['volumeInfo']['authors'])
            updated = True

        if updated:
            database[BR_GOOGLE_BOOKS].update_one({'_id':title_id},j,upsert=True)


def match_all(args):
    no_matches = []
    for title_id, title_name in get_jp_title_names().items():
        j = get_google_books_entry(title_id)
        if j is None:

            title_name = title_name.replace('.TXT','')
            title_name = title_name.replace('.txt','')

            if title_name == 'Placeholder':
                print("Skipping",title_id)
                continue

            print("Searching %s:%s" % (title_id,title_name))
            queries = []
            keyword = title_name
            queries.append((keyword,None))

            for author in get_authors(title_id):
                if author != 'Placeholder':
                    queries.insert(0,(keyword,author))

            publisher = get_publisher(title_id)
            if publisher != '' and publisher != 'Placeholder':
                keyword += ' ' + publisher
                queries.insert(0,(keyword,None))

            i = 0
            res = False
            while i<len(queries) and res==False:
                keyword, author = queries[i]
                search_metadata = {
                    'title' : keyword,
                    'author'  : author,
                }
                res = search_records_and_select_one(title_id,search_metadata, -1, args['manual_confirmation'])
                time.sleep(1)
                i += 1

            if res == False:
                print("\t","!! No matches for %s [%s]" % (title_name,title_id))
                no_matches.append(title_id)
    if len(no_matches)>0:
        print("\nNo matches for these titles! Match manually with:")
        for title_id in no_matches:
            print("\t%s:\tpython3 tools/google_books_tools.py %s https://www.google.com/books/edition/_/" % (get_jp_title_by_id(title_id),title_id))


def remove(args):
    title_id = get_title_id(args['title'])

    entry = database[BR_GOOGLE_BOOKS].find_one({'_id':title_id})

    if entry is not None:
        if entry['id'] == -1:
            print("Already removed!")
            return
        
        entry =  { "id":-1 }
        print("Removed match for %s [%s]" % (get_jp_title_by_id(title_id),title_id))
        database[BR_GOOGLE_BOOKS].update_one({'_id':title_id},j,upsert=True)
    else:
        print("Match not found!")


if __name__ == '__MAIN__':
    parser = argparse.ArgumentParser(
        prog="google_books_tools",
        description="Bilingual Manga DB <-> Google Books match and update tool",
        
    )
    subparsers = parser.add_subparsers(help='', dest='command')

    parser_match_all = subparsers.add_parser('match_all', help='Match all the book titles with Google Maps')
    parser_match_all.add_argument('--manual_confirmation', '-mc', action='store_true', help='Ask confirmation before matching')

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

    if cmd != None:
        locals()[cmd](args)
