from bdb import checkfuncname
from curses import newpad
from re import L
from tabnanny import check
from tkinter import NW
from webbrowser import get
import pandas as pd
import pickle
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
# from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from IPython.display import clear_output
# https://github.com/tasos-py/Search-Engines-Scraper
from search_engines import Google
from courlan import *

def getpage(url, dynamic=False, timetofetch=3):
    if not dynamic:
        page = requests.get(url)
        return BeautifulSoup(page.text, 'html.parser')
    else:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome('chromedriver', options=chrome_options)
        driver.get(url)
        time.sleep(timetofetch)
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        driver.close()
        return soup

class stack:
    def __init__(self):
        self.__index = []

    def __len__(self):
        return len(self.__index)

    def push(self,item):
        self.__index.insert(0,item)

    def peek(self):
        if len(self) == 0:
            raise Exception("peek() called on empty stack.")
        return self.__index[0]

    def pop(self):
        if len(self) == 0:
            raise Exception("pop() called on empty stack.")
        return self.__index.pop(0)

    def __str__(self):
        return str(self.__index)

def getgooglelinks(keyword, dynamic=False, timetofetch=3):

    url = f"https://www.google.com/search?q=what+is+{keyword}+blockchain"

    soup = getpage(url, dynamic=dynamic)
    anchorcontainers = soup.find_all('div')
    links = []
    for element in anchorcontainers:
        try:
            if element.h3 != None:
                links.append(element.a['href'])
        except:
            continue
    links = [element[element.find('/url?q=')+7:element.find('&sa=')] for element in links if element[0:7]=='/url?q=']
    clear_output(wait=True)
    return set(links)

def articlescraper(url, databaseid, dynamic=False, timetofetch=3):

    host = get_host_and_path(url)[0]
    url = urlcheck(url, host)

    headingdict = {'h1':1, 'h2':2, 'h3':3, 'h4':4, 'h5':5, 'h6':6}
    clear_output(wait=True)
    topic = False
    lastheadingid = 0
    lastheadingnumber = 0
    topicid = 0
    paragraphid = 0
    lasttext = ''
    insideheading = stack()

    newdocument = []
    newheadings = []
    newparagraphs = []

    try:
        soup = getpage(url, dynamic=dynamic, timetofetch=timetofetch)
    except Exception as e:
        print(e)
        return None

    for element in soup.body.descendants:
        try:

            if element.name == 'footer':
                break

            if topic==False:
                if str(element.name)=='h1':
                    if headingcheck(element):
                        continue
                    topic = True
                    lastheadingid = topicid
                    lastheadingnumber = 0
                    lasttext = element.text

                    if len(cleanbackslashnandt(element.text))==0:
                        continue
                    newheadings.append([databaseid, 'topic', cleanbackslashnandt(element.text), None, None, []])

                    continue
                else:
                    continue
            
            # multiple h1 in a row and at the beginning
            if lastheadingid==0:
                if str(element.name)=='h1':
                    if headingcheck(element):
                        continue
                    topic = True
                    lastheadingid = topicid
                    lastheadingnumber = 0
                    lasttext = element.text
                    if len(cleanbackslashnandt(element.text))==0:
                        continue
                    newheadings = []
                    newheadings.append([databaseid, 'topic', cleanbackslashnandt(element.text), None, None, []])
                    continue
                elif str(element.name)=='ul' or str(element.name)=='ol':
                    continue
                else:
                    pass


            if element.text==lasttext:
                continue

            if element.name in headingdict:

                if element.name == 'h1':
                    break

                if headingcheck(element):
                    continue

                headingid = lastheadingid+1

                headingnumber = headingdict[str(element.name)]
                lasttext = element.text

                if len(cleanbackslashnandt(element.text))==0:
                    continue
                newheadings.append([databaseid, element.name, cleanbackslashnandt(element.text), None, None, []])

                if lastheadingnumber==0:
                    insideheading.push([lastheadingnumber, lastheadingid])
                    newheadings[lastheadingid][3] = headingid
                elif headingnumber>lastheadingnumber:
                    insideheading.push([lastheadingnumber, lastheadingid])
                    newheadings[lastheadingid][3] = headingid
                elif headingnumber==lastheadingnumber:
                    newheadings[lastheadingid][4] = headingid
                else:
                    while True:
                        try:
                            poppedheading = insideheading.pop()
                            if poppedheading[0]>headingnumber:
                                continue
                            elif poppedheading[0]==headingnumber:
                                newheadings[poppedheading[1]][4] = headingid
                                break
                            else:
                                insideheading = stack()
                                newheadings[topicid][4] = headingid
                                break
                        except:
                            insideheading = stack()
                            break
                lastheadingid = headingid
                lastheadingnumber = headingnumber
            elif element.name=='p':
                if paracheck(element):
                    continue
                newparagraphs.append([databaseid, 'p', cleanbackslashnandt(element.text), getanchors(url, element)])
                newheadings[lastheadingid][5].append(paragraphid)
                lasttext = element.text
                paragraphid += 1
            elif element.name=='ol':
                for li in element.find_all('li'):
                    if paracheck(li):
                        continue
                    newparagraphs.append([databaseid, 'oli', cleanbackslashnandt(li.text), getanchors(url, li)])
                    newheadings[lastheadingid][5].append(paragraphid)
                    lasttext = li.text
                    paragraphid += 1
            elif element.name=='ul':
                for li in element.find_all('li'):
                    if paracheck(li):
                        continue
                    newparagraphs.append([databaseid, 'uli', cleanbackslashnandt(li.text), getanchors(url, li)])
                    newheadings[lastheadingid][5].append(paragraphid)
                    lasttext = li.text
                    paragraphid += 1
        except Exception as e:
            continue
    try:
        newdocument = [topicid, url, len(newheadings), len(newparagraphs)]
    except:
        pass
    return newdocument, newheadings, newparagraphs

def headingcheck(headingelement):
    return False

def paracheck(paragraphelement):
    if len(cleanbackslashnandt(paragraphelement.text))<2:
        return True
    return False

def cleanbackslashnandt(somestring):
    somestring = ''.join([somestring[i] for i in range(len(somestring)) if somestring[i:i+1]!='\n'])
    somestring = ''.join([somestring[i] for i in range(len(somestring)) if somestring[i:i+1]!='\t'])
    return cleanspaces(somestring)

def cleanspaces(somestring):
    return ' '.join([element.strip() for element in somestring.split(' ') if len(element)!=0])

def getanchors(url, element):
    host = get_host_and_path(url)[0]
    anchors = element.find_all('a')
    listtoreturn = []
    for anchor in anchors:
        if validate_url[0]:
            listtoreturn.append([urlcheck(anchor['href'], host), cleanbackslashnandt(anchor.text)])
    return listtoreturn

def urlcheck(url, host):
    url = normalize_url(url)
    if not is_not_crawlable(url):
        if not is_navigation_page(url):
            if validate_url(url)[0]:
                return url
            else:
                return urlcheck(fix_relative_urls(host, url), host)
        else:
            return None
    else:
        return None

def adddocument(headings, paragraphs):
    totalpragraphs = len(paragraphs)
    totalheadings = len(headings)
    if totalpragraphs==0:
        return False
    elif totalheadings==0:
        return False
    else:
        return True