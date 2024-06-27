"""
 Bilingual Manga DB <-> MangaUpdates.com id match and ratings update tool

 USAGE: 

* To match Bilingual Manga DB series ID with the corresponding Mangaupdates.com series ID:

            python3 mangaupdates.py match_all

        For every manga title in admin_manga_metadata.json a search query will be done. 
        The search keyword is the BM manga title. The script will automatically select
        the first (best) search result and print the data. 
        Make sure to check that name and release year matches and synopsis suggests it's the same manga

            python3 mangaupdates.py show

        This will show manga id and title in BM database and the corresponding manga title in Mangaupdates.com
        Titles differ from mangaupdates title name are highlighted with * marking.

        For example if there's an error (mismatch) like below:

            *  787 [667809ff5346850879afe0bf] I''s :  I''s dj - Fuwafuwarin (JP: I''s dj - Fuwafuwarin)

        Then start correcting it with following sequence:
            python3 mangaupdates.py search <keyword>

        For example in this case "I''s" has a mismatch, use command:
            python3 mangaupdates.py search "I''s"
            .
            .
            .
        However this didn't result in proper searches because the title contains
        quotation marks instead of apostrophes. Let's try again:
            python3 mangaupdates.py search 'I"s'
        
                1: I"s (JP: I"s)
                https://www.mangaupdates.com/series/vih2i09/i-quot-s
                    (1997) From VIZ:Shy Ichitaka has a crush on his high-school classmate Iori, but ever since she posed for semi-provocative swimsuit photos in a magazine, she's had a lot of sleazy guys hitting on her. Ichitaka's afraid to make his feelings known for fear Iori will think he's just another creep.                1: I&quot;s (JP: I&quot;s)

        .. and note the search result number of the correct manga (in this case it's 1)

        Then match the manga with the right search result:
            python3 mangaupdates.py match <title_name> <search_keyword> <search_result_index>
        or 
            python3 mangaupdates.py match <title_id> <search_keyword> <search_result_index>

        In this case it's better to use title_id because the title name contains apostrophes 
        and it's hard to escape:

            python3 mangaupdates.py match 667809ff5346850879afe0bf 'I"s' 1

        Alternatively you can do the matching using corresponding the mangaupdates entry URL:
            python3 mangaupdates.py match_url 667809ff5346850879afe0bf 'I"s' https://www.mangaupdates.com/series/vih2i09/i-quot-s


* To refresh votes and ratings for each matched manga title:

        python3 mangaupdates.py refresh

"""
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
#from urllib.parse import unquote

parser = argparse.ArgumentParser(
    prog="mangaupdates",
    description="Bilingual Manga DB <-> MangaUpdates.com match and update tool",
     
)
subparsers = parser.add_subparsers(help='', dest='command')

parser_download = subparsers.add_parser('match_all', help='Search data for all the manga titles and select the first match')

parser_update = subparsers.add_parser('refresh', help='Refresh ratings')

parser_list = subparsers.add_parser('show', help='Show matched titles')

parser_search = subparsers.add_parser('search', help='Search manga titles from mangaupdates.com')
parser_search.add_argument('keyword', type=str, help='search keyword (e.g: Meitantei)')

parser_match_url = subparsers.add_parser('match_url', help='Search manga titles from mangaupdates.com')
parser_match_url.add_argument('manga', type=str, help='Manga title')
parser_match_url.add_argument('url', type=str, help='Mangaupdates.com title URL')

parser_select = subparsers.add_parser('match', help='Select manga title from search results')
parser_select.add_argument('manga', type=str, help='Manga title')
parser_select.add_argument('keyword', type=str, help='search keyword (e.g: Meitantei)')
parser_select.add_argument('index', type=int, help='search result index number')

parser_remove = subparsers.add_parser('remove', help='Remove manga title match')
parser_remove.add_argument('manga', type=str, help='Manga title')

parser_dup = subparsers.add_parser('duplicates', help='Search duplicate matches')

args = vars(parser.parse_args())
cmd = args.pop('command')

base_dir = "./"

manga_data_file = base_dir + "json/BM_data.manga_data.json"
manga_metadata_file = base_dir + "json/BM_data.manga_metadata.json"
ext_manga_data_file = base_dir + "json/ext.manga_data.json"
ext_manga_metadata_file = base_dir + "json/ext.manga_metadata.json"
ratings_file = base_dir + "json/ratings.json"
ext_ratings_file = base_dir + "json/ext_ratings.json"
ext_oid_file = 'json/ext.oids.json'

search_url = "http://api.mangaupdates.com/v1/series/search"
get_series_url = "http://api.mangaupdates.com/v1/series/"
headers = {'Content-Type': 'application/json'}

title_name_to_id = dict()
title_names = dict()
title_years = dict()
synopsis = dict()

ratings = dict()
ext_ratings = dict()
all_ratings = dict()
ext_object_ids = dict()

try:
    with open(ratings_file,"r",encoding="utf-8") as f:
        data = f.read()
        ratings = json.loads(data)
        for id,item in ratings.items():
            all_ratings[id] = item
except:
    print("Existing ratings.json not found")


try:
    with open(ext_ratings_file,"r",encoding="utf-8") as f:
        data = f.read()
        ext_ratings = json.loads(data)
        for id,item in ext_ratings.items():
            #if item['series_id'] != -1:
            all_ratings[id] = item
except:
    print("Existing ext_ratings.json not found")

if os.path.exists(ext_oid_file):
    with open(ext_oid_file,'r',encoding="UTF-8") as oid_f:
        ext_object_ids = json.loads(oid_f.read())



with open(manga_metadata_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_metadata = json.loads(data)
    manga_titles = manga_metadata[0]['manga_titles']
    for t in manga_titles:
        title_id = t['enid']
        title_name = t['entit']
        title_years[title_id] = t['Release']
        title_names[title_id] = title_name
        title_name_to_id[title_name.lower()] = title_id

with open(ext_manga_metadata_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_titles = json.loads(data)
    for t in manga_titles:
        title_id = t['enid']
        title_name = t['entit']
        title_years[title_id] = t['Release']
        title_names[title_id] = title_name
        title_name_to_id[title_name.lower()] = title_id


with open(manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_data = json.loads(data)
    for m in manga_data:
        title_id = m['_id']['$oid']
        synopsis[title_id] = m['syn_en']
        pages = m['jp_data']['ch_jp']

with open(ext_manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_data = json.loads(data)
    for m in manga_data:
        title_id = m['_id']['$oid']
        synopsis[title_id] = m['syn_en']
        pages = m['jp_data']['ch_jp']

def get_title_id(item):
    item = item.lower()
    if item in title_name_to_id.keys():
        return title_name_to_id[item]
    if item in title_names.keys():
        # the item is in fact the title id
        return item
    raise Exception("unknown manga title/id %s" % str(item))

def is_external_title(title_id):
    for _,oid in ext_object_ids.items():
        if oid == title_id:
            return True
    return False

CLEANR = re.compile('<.*?>') 
def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  cleantext = clean_title(cleantext)
  return cleantext

def clean_title(title):
    title = title.replace('&#039;',"'")
    title = title.replace('&quot;','"')
    title = title.replace('&amp;',"&")
    return title

def show(args):
    i = 0
    for title_id, title_name in title_names.items():
        i += 1
        if title_id not in all_ratings:
            print("MISSING: [%s] %s " % (title_id, title_name))
        else:
            c = all_ratings[title_id]
            if c['series_id'] == -1:
                print("OMITTED: [%s] " % (title_id))
            else:
                t = c['title_name']
                t = t.replace("&#039;","'")
                t = t.replace("&amp;","&")
                t = t.replace("&quot;",'"')
                star = '* ' if t.lower() != title_name.lower() else '  '
                print("%s %d [%s] %s : %s" % (star, i, title_id, title_name,t ))

def copy_record(c,r):
    c['url'] = r['url']
    c['rating'] = r['bayesian_rating']
    c['votes'] = r['rating_votes']
    c['last_updated'] = r['last_updated']['as_string']
    c['last_refreshed'] = str(date.today())
    c['last_refreshed_timestamp'] = int(time.time())

    categories = []
    for cat in r['categories']:
        if cat['series_id'] == c['series_id']:
            del(cat['series_id'])
            if 'added_by' in cat:
                del(cat['added_by'])
            categories.append(cat)
    c['categories'] = categories
    c['recommendations'] = r['recommendations']
    c['category_recommendations'] = r['category_recommendations']


def search_records_and_select_one(title_id, keyword, index):
        
    body = json.dumps({"search" :keyword})
    #Making http post request
    response = requests.post(search_url, headers=headers, data=body, verify=False)
    r = response.json()
    hits = r['total_hits']
    if hits>0:
        j = r['results'][index]
        print("[match #%d] %s [%s] : MU name: %s [%s] (%s)" % 
            (index+1,
                title_names[title_id], title_years[title_id], 
                j['hit_title'], j['record']['year'], j['record']['title'])
        )
        print("BM synopsis: %s" % (synopsis[title_id]))
        print("MU synopsis: %s" % (clean_title(j['record']['description'])))
        print("")

        c = dict()

        c['title_name'] = j['hit_title']
        c['series_id'] = j['record']['series_id']

        # another query to fetch the whole record (including categories)
        response = requests.get(get_series_url + str(c['series_id']), headers=headers, verify=False)
        r = response.json()

        copy_record(c,r)

        if is_external_title(title_id):
            ext_ratings[title_id] = c

            f = open(ext_ratings_file,"w",encoding="utf-8")
            s = json.dumps(ext_ratings)
            f.write(s)
            f.close()
        else:
            ratings[title_id] = c

            f = open(ratings_file,"w",encoding="utf-8")
            s = json.dumps(ratings)
            f.write(s)
            f.close()
    else:
        print(title_names[title_id] + " not found")


def search(args):
    body = json.dumps({"search" :args['keyword']})

    response = requests.post(search_url, headers=headers, data=body, verify=False)
    r_json = response.json()
    i = 1
    for r in r_json['results']:
        print("%d: %s (JP: %s)" % (i, clean_title(r['hit_title']), clean_title(r['record']['title'])))
        print("%s" % r['record']['url'])
        print("\t(%s) %s" % ( r['record']['year'], cleanhtml(r['record']['description'])))
        print("")
        i += 1


def match(args):
    title_id = get_title_id(args['manga'])
    search_records_and_select_one(title_id, args['keyword'], args['index']-1)

def match_url(args):
    title_id = get_title_id(args['manga'])

    c = dict()
    response = requests.get(args['url'], headers=headers, verify=False)

    soup = BeautifulSoup(response.text, 'html.parser')
    al = soup.find_all('a')
    series_id = None
    for a in al:
        href = a.get('href')
        # extract the series is from the first a href 
        if 'https://api.mangaupdates.com/v1/series/' in href:
            series_id = href.split('/')[5]
            break
    if series_id is None:
        raise Exception("Could not extract series id!")
    
    response = requests.get(get_series_url + series_id, headers=headers, verify=False)
    r = response.json()

    print("BM synopsis: %s" % (synopsis[title_id]))
    print("MU synopsis: %s" % (cleanhtml(r['description'])))
    print("")

    c['series_id'] = series_id
    c['title_name'] = clean_title(r['title'])
    copy_record(c,r)

    if is_external_title(title_id):
        ext_ratings[title_id] = c

        f = open(ext_ratings_file,"w",encoding="utf-8")
        s = json.dumps(ext_ratings)
        f.write(s)
        f.close()
    else:
        ratings[title_id] = c

        f = open(ratings_file,"w",encoding="utf-8")
        s = json.dumps(ratings)
        f.write(s)
        f.close()

def refresh(args):

    i = 0
    for title_id, c in all_ratings.items():
        i += 1

        if title_id not in title_names:
            print("!! Removing deprecated item %s [%s]" % (c['title_name'],title_id))
            if is_external_title(title_id):
                del(ext_ratings[title_id])
                f = open(ext_ratings_file,"w",encoding="utf-8")
                s = json.dumps(ext_ratings)
                f.write(s)
                f.close()
            else:
                del(ratings[title_id])
                f = open(ratings_file,"w",encoding="utf-8")
                s = json.dumps(ratings)
                f.write(s)
                f.close()
            continue

        timestamp = int(time.time())
        if 'last_refreshed_timestamp' not in c or (c['last_refreshed_timestamp'] < timestamp - 24*60*60):

            print("Updating %d : %s" % (i,title_names[title_id]))

            response = requests.get(get_series_url + str(c['series_id']), headers=headers, verify=False)
            r = response.json()

            rating = r['bayesian_rating']
            votes = r['rating_votes']

            if rating != c['rating']:
                print("  - Updating Rating %f -> %f" % 
                    (c['rating'], rating)
                )
            if votes != c['votes']:
                print("  - Updating votes %d -> %d" % 
                    (c['votes'],votes)
                )

            copy_record(c,r)
            
            if is_external_title(title_id):
                ext_ratings[title_id] = c
            else:
                ratings[title_id] = c
            #time.sleep(0.1)

            f = open(ratings_file,"w",encoding="utf-8")
            f.write(json.dumps(ratings))
            f.close()

            f = open(ext_ratings_file,"w",encoding="utf-8")
            f.write(json.dumps(ext_ratings))
            f.close()

def match_all(args):
    for title_id, title_name in title_names.items():
        if not title_id in all_ratings:
            search_records_and_select_one(title_id,title_name,0)
            time.sleep(1)

def remove(args):
    title_id = get_title_id(args['manga'])
    if title_id in all_ratings:
        if all_ratings['series_id'] == -1:
            print("Already removed!")
            return
        
        if is_external_title(title_id):
            del(ext_ratings[title_id])
            ext_ratings[title_id] =  { "series_id":-1 }
            f = open(ext_ratings_file,"w",encoding="utf-8")
            f.write(json.dumps(ext_ratings))
            f.close()
        else:
            del(ratings[title_id])
            ratings[title_id] =  { "series_id":-1 }
            f = open(ratings_file,"w",encoding="utf-8")
            f.write(json.dumps(ratings))
            f.close()
        print("Removed match for %s [%s]" % (title_names[title_id],title_id))

    else:
        print("Match not found!")

def duplicates(args):
    title_by_series = dict()
    for title_id, title_name in title_names.items():
        if not title_id in all_ratings:
            print("%s [%s] missing!" % (title_name,title_id))
        else:
            sid = all_ratings[title_id]['series_id']
            if sid != -1:
                if sid not in title_by_series:
                    title_by_series[sid] = title_id
                else:
                    existing_title_id = title_by_series[sid]
                    print("%s [%s] already exists as %s [%s]" % (title_id,title_name,existing_title_id,title_names[existing_title_id]))

if cmd != None:
  locals()[cmd](args)
