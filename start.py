#!/usr/bin/env python3
import threading 
import pickle
import time
from datetime import datetime
import urllib.request
from bs4 import BeautifulSoup
import re
from time import gmtime, strftime
import string
import datetime
import pymongo
import codecs
import subprocess;
from pymongo import MongoClient
import sys

starte = time.time()
list_app = []
saved = []
moya = []
moyapen = []
last_app = []

client = MongoClient('localhost', 27017)
db = client.itunes
collection = db.itunes_data

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def PagetoSoup(url): # Mise en beauté de la page
	try:
		response = urllib.request.urlopen( url )
	except urllib.error.HTTPError as e:
		print("HTTPError with: ", url, " as ", e)
		return None
	return BeautifulSoup(response.read())


def getApps(categoryUrl, id_itera, debugAlpha): #Récupère les applications de la page (cat/lettre)
    before = []
    num_page = 1  # gestion de toutes les pages
    moy = 0.0
    ta = time.clock()
    waittime = 1
    while(True):
        waittime+=1
        if waittime == 25:
            time.sleep(5)
            waittime=1
        url = categoryUrl + "&page=" + str(num_page)
        cat = PagetoSoup(url) # mise en forme de la page (balises etc ...)
        linkss = [link.get('href') for link in cat.findAll('a', href = re.compile('^https://itunes.apple.com/us/app'))]
        if linkss == before: 
            break
        list_app.extend([tmp for tmp in linkss if tmp not in list_app])
        before = linkss
        num_page += 1
        if id_itera == 5:
            tb = time.clock()
            moy = tb-ta
            id_itera = 0
            moyapen.append(moy)
            ta = time.clock()
        id_itera+=1
  


def Progress():
    threading.Timer(5, Progress).start()
    global moy
    #subprocess.call(["printf", "'\033c"]);
    print(bcolors.FAIL+"   ____ _____ _____   ___ _____ _   _ _   _ _____ ____    ____ ___ _____ ____ _   _ ")
    print("  / ___| ____|_   _| |_ _|_   _| | | | \ | | ____/ ___|  | __ |_ _|_   _/ ___| | | |")
    print(" | |  _|  _|   | |    | |  | | | | | |  \| |  _| \___ \  |  _ \| |  | || |   | |_| |")
    print(" | |_| | |___  | |    | |  | | | |_| | |\  | |___ ___) | | |_) | |  | || |___|  _  |")
    print("  \____|_____| |_|   |___| |_|  \___/|_| \_|_____|____/  |____|___| |_| \____|_| |_|"+ bcolors.ENDC)
    print("")
    print("                 ------------------------------------------------------")
    tactua = datetime.datetime.fromtimestamp(starte)
    print(tactua.strftime(bcolors.OKGREEN+"                 - Lancé le %Y-%m-%d %H:%M:%S"))
    tactua = datetime.datetime.fromtimestamp(time.time())
    print(tactua.strftime("                 - Nous somme le le %Y-%m-%d %H:%M:%S"))
    tactua = datetime.datetime.fromtimestamp(time.time()-starte-3600)
    print(tactua.strftime("                 - Actif depuis %H heure(s) %M minute(s) et %S seconde(s)"))
    print("                 - Total: "+str(len(list_app)+len(saved)))
    print("                 - Save: "+ str(len(saved)))
    print("                 - Pending: "+ str(len(list_app)))

    moyenne = 0.0
    iterations = 0
    for i in moya:
        moyenne = (iterations*moyenne + i)/ (iterations + 1)
        iterations += 1

    moyenne_pen = 0.0
    iterations = 0
    for i in moyapen:
        moyenne_pen = (iterations*moyenne_pen + i)/ (iterations + 1)
        iterations += 1

    print("                 - Moyenne de save: "+ str(float(moyenne))+ " secondes/100")
    print("                 - Moyenne de pending: "+ str(float(moyenne_pen))+ " secondes/5pages"+bcolors.ENDC)
    print("                 ------------------------------------------------------")

def getListApp(FinalArrayCate):
    id_itera = 0
    for category, alphabet in [(tmp_cat, tmp_alh) for tmp_cat in FinalArrayCate for tmp_alh in string.ascii_uppercase]:
        getApps(category + '&letter=' + alphabet, id_itera, None)


def insertOrNot(t):
    if t != None:
        document = None
        posts = db.posts
        for a in posts.find({'title': t['title']}):
            document = 1

        if document == None:
            post = {"app_url": t['app_url'],
                "title": t['title'],
                "developer": t['developer'],
                "price": t['price'],
                "category": t['category'],
                "lastRelease": t['lastRelease'],
                "langue": t['langue'],
                "compatibility": t['compatibility'],
                "desc": t['desc'],
                "rating": t['rating'],
                "rating_reason": t['rating_reason'],
                "developer_wesite": t['developer_wesite']}
            posts = db.posts
            post_id = posts.insert(post)




def getAppsDetails():
    moy = 0.0
    id_itera = 0
    waittime = 1;

    while(True):
        waittime+=1
        if waittime == 50:
            time.sleep(5)
            waittime=1
        ta = time.clock()
        for app in list_app:
            t = getInfosApps(app)
            insertOrNot(t)
            if id_itera == 100:
                tb = time.clock()
                moy = tb-ta
                id_itera = 0
                moya.append(moy)
                ta = time.clock()
            id_itera+=1

def getInfosApps(appUrl):
    if appUrl in saved: return None
    page = PagetoSoup(appUrl)
    if not page: return None

    pTitleDiv = page.find( 'p', {'class' : 'title'} )
    if pTitleDiv and pTitleDiv.getText() == 'One Moment Please.': return None

    apps = {}
    apps['app_url'] = appUrl

    title = page.find('div', {'id' : 'title'})
    apps['title'] = title.find('h1').getText()
    apps['developer'] = title.find('h2').getText()

    allDetails = page.find('div', {'id' : 'left-stack'})
    if not allDetails: return None 

    # Price Category Updated   Language  Compatibility 
    price = allDetails.find('div', {'class' : 'price'})
    if price: apps['price'] = price.getText()
    else: apps['price'] = ""

    category = allDetails.find('li', {'class' : 'genre'})
    if category: apps['category'] = category.find('a').getText()
    else: apps['category'] = ""

    lastRelease = allDetails.find('li', {'class' : 'release-date'})
    if lastRelease: apps['lastRelease'] = lastRelease.getText()
    else: apps['lastRelease'] = ""

    langue = allDetails.find('li', {'class' : 'language'})
    if langue: apps['langue'] = langue.getText().split()
    else: apps['langue'] = ""

    compa = allDetails.find('p')
    if compa: apps['compatibility'] = compa.getText()
    else: apps['compatibility'] = ""


    description = allDetails.find('div', {'metrics-loc' : 'Titledbox_Description'})
    if description: apps['desc'] = description.getText()
    else: apps['desc'] = ""

    rating = allDetails.find('div', {'class' : 'app-rating'})
    if rating: apps['rating'] = rating.getText()
    else: apps['rating'] = ""

    rating_reason = allDetails.find('ul', {'class' : 'list app-rating-reasons'})
    if rating_reason: apps['rating_reason'] = [li.getText() for li in rating_reason.findAll('li')]
    else: apps['rating_reason'] = ""

    # Thanks anuvrat for this  -> https://github.com/anuvrat/
    appLinksDiv = page.find('div', {'class' : 'app-links'})
    if appLinksDiv:
        for link in appLinksDiv.findAll( 'a', {'class' : 'see-all'} ):
            text = link.getText()
            href = link.get('href')
            if text.endswith('Web Site'): apps['developer_wesite'] = href
            elif not text.endswith('Web Site'): apps['developer_wesite'] = ""
    else:
        apps['developer_wesite'] = ""

    saved.append(appUrl)
    list_app.remove(appUrl)

    return apps

if __name__ == '__main__':
    Progress()

    ## Page de référencement ##
    allAppLinks = []
    mainPage = PagetoSoup('https://itunes.apple.com/us/genre/ios/id36?mt=8')

    ArrayCate = []
    FinalArrayCate = []

    # <div class="grid3-column">
    # id="genre-nav"
    # for column in ['grid3-column', 'column-']: 
    for x in ['list column first', 'list column', 'list column last']: # Enumeration. Page séparée en 3 column
        colContent = mainPage.find('ul', {'class' : x})
        ArrayCate.extend(lik.get('href') for lik in colContent.findAll('a', href = re.compile('^https://itunes.apple.com/us/genre')))

    for cat in ArrayCate:
        i = 0
        if cat.find('photo') != -1 or cat.find('business') != -1 or cat.find('games-') != -1 or cat.find('newsstand-') != -1:
            i+=1
        else:
            FinalArrayCate.append(cat)

    # Recherche apps links
    a = threading.Thread(None, getAppsDetails, None) 
    a.start()

    # Sauvegarde
    getListApp(FinalArrayCate)
