from re import L
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
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from IPython.display import clear_output

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

def articlescraper(url, database, headings, paragraphs, dynamic=False, timetofetch=3):
    headingdict = {'h1':1, 'h2':2, 'h3':3, 'h4':4, 'h5':5, 'h6':6}
    clear_output(wait=True)
    topic = False
    lastheadingid = 0
    lastheadingnumber = 0
    lastparagraphid = 0
    totalsubheadings = 0
    totalparagraphs = 0
    lasttext = ''
    insideheading = stack()
    try:
        soup = getpage(url, dynamic=dynamic, timetofetch=timetofetch)
        # if registereddomains[domainname]['articlecontainer']['attrs']==None:
        #     main = soup.find(registereddomains[domainname]['articlecontainer']['tag'])
        # else:
        #     main = soup.find(registereddomains[domainname]['articlecontainer']['tag'], registereddomains[domainname]['articlecontainer']['attrs'])
        # descendants = main.descendants
    except Exception as e:
        print(e)
        return None
    for element in soup.descendants:
        try:
            if topic==False:
                if str(element.name)[0]=='h':
                    docid = len(database.index)
                    topicid = len(headings.index)
                    headings.loc[topicid] = ['topic', element.text, None, None, []]
                    topic = True
                    lastheadingid = topicid
                    lastheadingnumber = 0
                    lasttext = element.text
                    continue
                else:
                    continue
            
            # so that the nested elements don't make the same text count twice
            if element.text==lasttext:
                continue

            if element.name in headingdict:
                totalsubheadings+=1

                headingid = len(headings.index)

                headingnumber = headingdict[str(element.name)]
                headings.loc[headingid] = [element.name, element.text, None, None, []]
                lasttext = element.text

                if lastheadingnumber==0:
                    insideheading.push([lastheadingnumber, lastheadingid])
                    headings.iloc[lastheadingid]['subheading'] = headingid
                elif headingnumber>lastheadingnumber:
                    insideheading.push([lastheadingnumber, lastheadingid])
                    headings.iloc[lastheadingid]['subheading'] = headingid
                elif headingnumber==lastheadingnumber:
                    headings.iloc[lastheadingid]['nextheading'] = headingid
                else:
                    while True:
                        try:
                            poppedheading = insideheading.pop()
                            if poppedheading[0]>headingnumber:
                                continue
                            elif poppedheading[0]==headingnumber:
                                headings.iloc[poppedheading[1]]['nextheading'] = headingid
                                break
                            else:
                                insideheading = stack()
                                headings.iloc[topicid]['subheading'] = headingid
                                break
                        except:
                            insideheading = stack()
                            break
                lastheadingid = headingid
                lastheadingnumber = headingnumber
            elif element.name=='p':

                if len(element.text)==0:
                    continue
                totalparagraphs+=1
                paragraphid = len(paragraphs.index)
                paragraphs.loc[paragraphid] = ['p', element.text]
                headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
                lastparagraphid = paragraphid
                lasttext = element.text
            elif element.name=='ol':

                totalparagraphs+=1

                for li in element.find_all('li'):
                    if len(li.text)==0:
                        continue
                    paragraphid = len(paragraphs.index)
                    paragraphs.loc[paragraphid] = ['oli', li.text]
                    headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
                    lasttext = element.text
            elif element.name=='ul':

                totalparagraphs+=1

                for li in element.find_all('li'):
                    if len(li.text)==0:
                        continue
                    paragraphid = len(paragraphs.index)
                    paragraphs.loc[paragraphid] = ['uli', li.text]
                    headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
                    lasttext = element.text
        except Exception as e:
            # print(url)
            # print(element, e)
            # break
            continue
    try:
        database.loc[docid] = [topicid, url, totalsubheadings, totalparagraphs]
    except:
        pass
    return database, headings, paragraphs