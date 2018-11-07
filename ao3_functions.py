import requests
from lxml import html
import dill
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter,defaultdict
import re

#Scraping utilities
def gen_pagelist(url):
    page = requests.get(url.strip())
    tree = html.fromstring(page.content)
    pages = tree.xpath('//ol[@class="pagination actions"]')[0].findall('li')
    max_p = int(pages[-2].text_content())
    f = open('scraping_input.txt','w')
    for i in range(1,min(max_p,50)):
        f.write(url+'?page='+str(i)+'\n')
    f.close()
    return


def read_lead(url):
    fid = re.findall('[0-9]+',url)[0]
    title = ''
    author = ''
    date = ''
    
    page = requests.get(url.strip())
    tree = html.fromstring(page.content)
    meta = tree.xpath('//dl[@class="work meta group"]')[0]
    
    rating = meta.xpath('//dd[@class="rating tags"]')[0].text_content().strip()
    
    warnings = meta.xpath('//dd[@class="warning tags"]')[0].find('ul').findall('li')
    warnings = [s.text_content().strip() for s in warnings]
    
    slashtype = meta.xpath('//dd[@class="category tags"]')[0].find('ul').findall('li')
    slashtype = [s.text_content().strip() for s in slashtype]
    
    if len(meta.xpath('//dd[@class="fandom tags"]'))==0:
        fandomlist = []
    else:
        fandomlist = meta.xpath('//dd[@class="fandom tags"]')[0].find('ul').findall('li')
        fandomlist = [s.text_content().strip() for s in fandomlist]
    
    if len(meta.xpath('//dd[@class="relationship tags"]'))==0:
        relationships = []
    else:
        relationships = meta.xpath('//dd[@class="relationship tags"]')[0].find('ul').findall('li')
        relationships = [s.text_content() for s in relationships]
    
    if len(meta.xpath('//dd[@class="character tags"]'))==0:
        characters = []
    else:
        characters = meta.xpath('//dd[@class="character tags"]')[0].find('ul').findall('li')
        characters = [s.text_content() for s in characters]
    
    if len(meta.xpath('//dd[@class="freeform tags"]'))==0:
        othertags = []
    else:
        othertags = meta.xpath('//dd[@class="freeform tags"]')[0].find('ul').findall('li')
        othertags = [s.text_content() for s in othertags]
    
    language = meta.xpath('//dd[@class="language"]')[0].text_content().strip()
    
    stats = meta.xpath('//dd[@class="stats"]')[0].find('dl')
    dict_stats = defaultdict(int)
    stats_list = [s.text_content() for s in stats.getchildren()]
    for i in range(int(len(stats_list)/2)):
        dict_stats[stats_list[2*i][:-1]] = stats_list[2*i+1]
    dict_stats['Published'] = datetime.strptime(dict_stats['Published'],"%Y-%m-%d")
    if dict_stats['Completed'] !=0:
        finished = True
    else:
        finished = False
    for key in dict_stats.keys():
        if key != 'Published' and key != 'Completed' and key != 'Chapters':
            dict_stats[key] = int(dict_stats[key])
    
    new_entry = pd.DataFrame.from_dict({str(fid):[fid,title,author,dict_stats['Published'],rating,warnings,slashtype,finished,
                                                  fandomlist,relationships,characters,othertags,
                                                  language,dict_stats['Words'],
                                                  dict_stats['Chapters'],dict_stats['Comments'],dict_stats['Kudos'],
                                                  dict_stats['Bookmarks'],dict_stats['Hits']]},orient='index',
                                       columns=['workid','title','author','date','rating','warnings','slashtype',
                                                'finished','fandomlist','relationships','characters','tags',
                                                'language','wordcnt','chaptercnt','commentcnt','kudoscnt',
                                                'bookmarkcnt','hits'])
    return new_entry
    


    
#Data clean-up and processing
def vectorizer(d,l):#vectorize list according to a dictionary
    v = np.zeros(len(d))
    #print(l)
    for i in range(len(d)):
        if list(d.keys())[i] in l:
            v[i] = d[list(d.keys())[i]]
        else:
            v[i] = 0
    return v

#find out how similar two fics are and return a score
def score_match(fic1,fic2,weight=[0.16, 0.38, 0.55, 0.38,
                                  0.19, 0.19,0.54, 0.10]):#both input pd series
    score = np.zeros(8)
    #Rating,slashtype,warning,fandom match,realationships,characters,other tags,length
    
    #Ratings: General Audiences, Teen And Up Audiences, Mature, Explicit
    d_ratings = {'General Audiences':0, 'Teen And Up Audiences':1, 'Mature':2, 'Explicit':3, 'Not Rated':1.5}
    score[0] = 3-abs(d_ratings[fic1['rating']]-d_ratings[fic2['rating']])
    
    #Slashtype: F/F, F/M, M/M, Multi, Gen, Other, No category    
    d_slashtype = {'F/F':1, 'F/M':1, 'M/M':1, 'Multi':1, 'Gen':1, 'Other':1, 'No category':0}
    v1 = vectorizer(d_slashtype,fic1['slashtype'])
    v2 = vectorizer(d_slashtype,fic2['slashtype'])
    score[1] = np.dot(v1,v2)/max(len(fic1['slashtype']),len(fic2['slashtype']))
    
    #Warnings:No Archive Warnings Apply, Graphic Depictions of Violence, 
    #Major Character Death, Rape/Non-Con, Underage Sex, Choose Not To Use Archive Warnings
    d_warnings = {'No Archive Warnings Apply':0,
                  'Graphic Depictions Of Violence':1,
                  'Major Character Death':1,
                  'Rape/Non-Con':1,
                  'Underage':1,
                  'Choose Not To Use Archive Warnings':0}
    v1 = vectorizer(d_warnings,fic1['warnings'])
    v2 = vectorizer(d_warnings,fic2['warnings'])
    score[2] = np.dot(v1,v2)
        
    #Fandom list: all kinds
    for f in fic1['fandomlist']:
        if f in fic2['fandomlist']: score[3]+=1.
    score[3] = score[3]/max(len(fic1['fandomlist']),len(fic2['fandomlist']))
    
    #Ships! This is important
    for t in fic1['relationships']:
        if t in fic2['relationships']: 
            if '/' in t: 
                score[4]+=2.
            elif '&' in t:
                score[4]+=1.
    
    #Characters. Dont normalize
    for t in fic1['characters']:
        if t in fic2['characters']: score[5]+=1.
    
    #Other tags. Dont normalize
    for t in fic1['tags']:
        if t in fic2['tags']: score[6]+=1.

    
    #Length. One-shot or long-ass fic
    if fic1['wordcnt'] <=10000 and fic2['wordcnt'] <=10000:
        score[7]+=5.
    elif fic1['wordcnt'] >10000 and fic2['wordcnt'] >10000:
        score[7]+=5.
    else:
        score[7]=0.
    
    return np.sum(score*weight)/np.linalg.norm(weight)

#A fic's popularity score based on kudos/hits, weighted by chaptercnt
def score_popularity(fic):
    nchp,_,_ = fic['chaptercnt'].partition("/")
    nchp = float(nchp)
    #return fic['kudoscnt']/(fic['hits']/nchp*3.)
    if fic['hits'] == 0: return 0
    return (fic['kudoscnt']/fic['hits']-(np.log(nchp)*-0.013+0.10))/(np.log(nchp)*-0.006+0.037)
    #return fic['kudoscnt']/fic['hits']

    
def find_rec(lead_url,df_fics):#input fic is a DataFrame entry
    lead_id = re.findall('[0-9]+',url)
    if type(lead_id) == list:
        lead_id = lead_id[0]
    if lead_id in df_fics['workid'].values:
        lead = df_fics.iloc[[lead_id]]
    else:
        lead = read_lead(lead_url).squeeze()
    recs = []
    for index, row in df_fics.iterrows():
        if row['title'] == lead['title']: continue
        if row['language'] != lead['language']:continue
        rec = pd.DataFrame.from_dict({'workid':[row['workid']],
                                      'popularity':[score_popularity(row)],
                                      'match':[score_match(lead,row)],
                                      'title':[row['title']]})
        if len(recs) == 0:
            recs = rec
        else:
            recs = recs.append(rec)
    recs = recs.sort_values(by='match',ascending=False).head(10)
    recs = recs.sort_values(by='popularity',ascending=False)
    print('You may also enjoy:')
    for ind,rec in recs.head(5).iterrows():
        print(rec['title']+': archiveofourown.org/works/'+str(rec['workid']))
    return #recs



#Fandometrics

import matplotlib

font = {'family' : 'normal','weight' : 'normal','size'   : 20}

def plot_ratings(df_fics,ax):
    rating_cnt = dict(df_fics['rating'].value_counts())
    labels = rating_cnt.keys()
    sizes = rating_cnt.values()

    ax.pie(sizes, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title('How NSFW your fandom is?')
    return

def plot_slashtype(df_fics,ax):
    types = sum(list(dict(df_fics['slashtype']).values()),[])
    type_cnt = Counter()
    for s in types:
        type_cnt[s] += 1
    del type_cnt['Other']
    del type_cnt['No category']
    labels = list(type_cnt.keys())
    sizes = list(type_cnt.values())

    ax.pie(sizes, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title('What kind of ships does your fandom have?')
    return 

def popular_char(df_fics,ax):
    list_char = sum(df_fics['characters'].values,[])
    dict_char = Counter()
    for c in list_char:
        dict_char[c] +=1
    sort_list = sorted(dict_char.items(),key=lambda v: v[1],reverse=True)[:4]
    #print(sort_list)
    chars = [v[0] for v in sort_list]
    cnts = [v[1] for v in sort_list]
    ax.bar(chars,cnts,width=0.35)
    ax.set_title("Who's the most popular?")
    ax.set_ylabel('# Featured')
    return 



def plot_unfinished(df_fics,ax):
    finished = Counter()
    pits = Counter()
    for ind,row in df_fics.iterrows():
        y = row['date'].year
        #y = datetime(year=y,month=1,day=1)
        nchp = int(row['chaptercnt'].partition('/')[0])
        if nchp > 1:
            if row['finished'] == 'Work in Progress':
                pits[y] +=1
            else:
                finished[y] +=1
    
    width = 0.35       # the width of the bars: can also be len(x) sequence
    p1 = ax.bar(finished.keys(),finished.values(), width,label='Finished multi-chapter works')
    p2 = ax.bar(pits.keys(),pits.values(), width, bottom=list(finished.values()),
                label='Works created that were never finished')
    ax.legend('best')
    ax.set_xlabel('Year created')
    ax.set_xticks(list(pits.keys()))
    ax.set_title('How likely are authors to finish their work in this fandom?')
    return


    