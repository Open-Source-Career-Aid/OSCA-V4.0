from re import L
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

def getlinks(url, domainname, registereddomains, timetofetch=3):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome('chromedriver', options=chrome_options)
    driver.get(url)
    time.sleep(timetofetch)
    page = driver.page_source
    soup = BeautifulSoup(page, 'html.parser')
    if registereddomains[domainname]['getlinks']['attrs']==None:
        anchorcontainers = soup.find_all(registereddomains[domainname]['getlinks']['tag'])
    else:
        anchorcontainers = soup.find_all(registereddomains[domainname]['getlinks']['tag'], registereddomains[domainname]['getlinks']['attrs'])
    links = []
    for element in anchorcontainers:
        anchors = element.find_all('a')
        for anchor in anchors:
            links.append(anchor['href'])
    driver.close()
    clear_output(wait=True)
    return links

def articlescraper(url, domainname, database, headings, paragraphs, registereddomains, dynamic=False, timetofetch=3):
    headingdict = {'h1':1, 'h2':2, 'h3':3, 'h4':4, 'h5':5, 'h6':6}
    clear_output(wait=True)
    topic = False
    lastheadingid = 0
    lastheadingnumber = 0
    lastparagraphid = 0
    totalsubheadings = 0
    totalparagraphs = 0
    insideheading = stack()
    try:
        soup = getpage(url, dynamic=dynamic, timetofetch=timetofetch)
        if registereddomains[domainname]['articlecontainer']['attrs']==None:
            main = soup.find(registereddomains[domainname]['articlecontainer']['tag'])
        else:
            main = soup.find(registereddomains[domainname]['articlecontainer']['tag'], registereddomains[domainname]['articlecontainer']['attrs'])
        descendants = main.descendants
    except Exception as e:
        print(e)
        return None
    for element in descendants:
        try:
            if topic==False:
                if str(element.name)=='h1':
                    docid = len(database.index)
                    topicid = len(headings.index)
                    headings.loc[topicid] = ['topic', element.text, None, None, []]
                    topic = True
                    lastheadingid = topicid
                    lastheadingnumber = 0
                    continue
                else:
                    continue

            if element.name in headingdict:
                if element.parent.name==registereddomains[domainname]['articlecontainer']['datacontainer']:
                    totalsubheadings+=1

                    headingid = len(headings.index)

                    headingnumber = headingdict[str(element.name)]
                    headings.loc[headingid] = [element.name, element.text, None, None, []]

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
            elif element.name=='p' and element.parent.name==registereddomains[domainname]['articlecontainer']['datacontainer']:

                if len(element.text)==0:
                    continue
                totalparagraphs+=1
                paragraphid = len(paragraphs.index)
                paragraphs.loc[paragraphid] = ['p', element.text]
                headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
                lastparagraphid = paragraphid
            elif element.name=='ol' and element.parent.name==registereddomains[domainname]['articlecontainer']['datacontainer']:

                totalparagraphs+=1

                for li in element.find_all('li'):
                    if len(li.text)==0:
                        continue
                    paragraphid = len(paragraphs.index)
                    paragraphs.loc[paragraphid] = ['oli', li.text]
                    headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
            elif element.name=='ul' and element.parent.name==registereddomains[domainname]['articlecontainer']['datacontainer']:

                totalparagraphs+=1

                for li in element.find_all('li'):
                    if len(li.text)==0:
                        continue
                    paragraphid = len(paragraphs.index)
                    paragraphs.loc[paragraphid] = ['uli', li.text]
                    headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
            elif element.name=='footer':
                break
        except Exception as e:
            print(url)
            print(element, e)
            break
    try:
        database.loc[docid] = [topicid, url, totalsubheadings, totalparagraphs]
    except:
        pass
    return database, headings, paragraphs, descendants