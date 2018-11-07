from collections import defaultdict
import requests
from lxml import html
from datetime import datetime
import re
from multiprocessing import Pool
import dill
import pandas as pd
import time
import sys

def collect_fics(url):
	page = requests.get(url.strip())
	tree = html.fromstring(page.content)
	fics = tree.xpath('//li[@class="work blurb group"]')
	entries = []
	for fic in fics:
		entry = read_fic(fic)
		entries.append(entry)
	df_fics = pd.concat(entries, axis=0, sort=False)
	return df_fics

def read_fic(fic):
    fid = fic.attrib['id'][5:]
    header = fic.find('div')
    tags = fic.find('ul')
    stats = fic.find('dl')
    #header
    title,by,author = header.find('h4').text_content().replace('\n','').partition(' by ')
    title = title.strip()
    author = author.strip()
    date = datetime.strptime(header.find('p').text_content(),"%d %b %Y")
    fandomlist = [node.text_content() for node in header.find('h5').findall('a')]
    diamond = header.find('ul').text_content().split('\n')
    rating,warnings,slashtype,finished = diamond[1:-1]
    rating = rating.strip()
    warnings = warnings.split(',')
    warnings = [s.strip() for s in warnings]
    slashtype = slashtype.split(',')
    slashtype = [s.strip() for s in slashtype]
    finished = finished.strip()
	#tag
    relationships = [node.text_content() for node in tags.xpath("li[@class='relationships']")]
    characters = [node.text_content() for node in tags.xpath("li[@class='characters']")]
    othertags = [node.text_content() for node in tags.xpath("li[@class='freeforms']")]
    #stats
    stats = stats.text_content().replace('\n','').split()
    dict_stats = defaultdict(int)
    for i in range(len(stats)):
        if stats[i] == 'Language:' or stats[i] == 'Chapters:':
            dict_stats[stats[i][:-1]]=stats[i+1]
        elif stats[i] == 'Words:'or stats[i] == 'Comments:'or stats[i] == 'Kudos:'or stats[i] == 'Hits:'or stats[i] == 'Bookmarks:':
            dict_stats[stats[i][:-1]]=int(stats[i+1].replace(',',''))
    #language,wordcnt,chaptercnt,commentcnt,kudoscnt,bookmarkcnt,hits = stats[1::2]
    #print(dict_stats.items())
    new_entry = pd.DataFrame.from_dict({str(fid):[fid,title,author,date,rating,warnings,slashtype,finished,
                                                  fandomlist,relationships,characters,othertags,
                                                  dict_stats['Language'],dict_stats['Words'],
                                                  dict_stats['Chapters'],dict_stats['Comments'],dict_stats['Kudos'],
                                                  dict_stats['Bookmarks'],dict_stats['Hits']]},orient='index',
                                       columns=['workid','title','author','date','rating','warnings','slashtype',
                                                'finished','fandomlist','relationships','characters','tags',
                                                'language','wordcnt','chaptercnt','commentcnt','kudoscnt',
                                                'bookmarkcnt','hits'])

    return new_entry





if __name__ == '__main__':
	pool = Pool(processes=4)
	start = time.time()
	urllist = open(sys.argv[1]).readlines()
	urllist = [url[:-1] for url in urllist]
	#print(urllist)
	#for url in urllist:
	#	print(url)
	#	print(collect_fics(url))
	df_fics = pd.concat(pool.map(collect_fics,urllist))
	df_fics = df_fics.dropna()
	dill.dump(df_fics,open('fics_info.pkd', 'wb'))
	end = time.time()
	print('Finished in '+str(end - start)+' s.')



