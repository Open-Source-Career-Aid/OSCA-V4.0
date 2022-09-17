from curses import newpad
from re import L
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

def articlescraper(url, dynamic=False, timetofetch=3):
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
                    newheadings.append(['topic', cleanbackslashnandt(element.text), None, None, []])

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
                    newheadings.append(['topic', cleanbackslashnandt(element.text), None, None, []])
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
                newheadings.append([element.name, cleanbackslashnandt(element.text), None, None, []])

                if lastheadingnumber==0:
                    insideheading.push([lastheadingnumber, lastheadingid])
                    newheadings[lastheadingid][2] = headingid
                elif headingnumber>lastheadingnumber:
                    insideheading.push([lastheadingnumber, lastheadingid])
                    newheadings[lastheadingid][2] = headingid
                elif headingnumber==lastheadingnumber:
                    newheadings[lastheadingid][3] = headingid
                else:
                    while True:
                        try:
                            poppedheading = insideheading.pop()
                            if poppedheading[0]>headingnumber:
                                continue
                            elif poppedheading[0]==headingnumber:
                                newheadings[poppedheading[1]][3] = headingid
                                break
                            else:
                                insideheading = stack()
                                newheadings[topicid][3] = headingid
                                break
                        except:
                            insideheading = stack()
                            break
                lastheadingid = headingid
                lastheadingnumber = headingnumber
            elif element.name=='p':
                if len(cleanbackslashnandt(element.text))==0:
                    continue
                newparagraphs.append(['p', cleanbackslashnandt(element.text)])
                newheadings[lastheadingid][4].append(paragraphid)
                lasttext = element.text
                paragraphid += 1
            elif element.name=='ol':
                for li in element.find_all('li'):
                    if len(cleanbackslashnandt(element.text))==0:
                        continue
                    newparagraphs.append(['oli', cleanbackslashnandt(li.text)])
                    newheadings[lastheadingid][4].append(paragraphid)
                    lasttext = element.text
                    paragraphid += 1
            elif element.name=='ul':
                for li in element.find_all('li'):
                    if len(cleanbackslashnandt(element.text))==0:
                        continue
                    newparagraphs.append(['uli', cleanbackslashnandt(li.text)])
                    newheadings[lastheadingid][4].append(paragraphid)
                    lasttext = element.text
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

def cleanbackslashnandt(somestring):
    somestring = ''.join([somestring[i] for i in range(len(somestring)) if somestring[i:i+1]!='\n'])
    somestring = ''.join([somestring[i] for i in range(len(somestring)) if somestring[i:i+1]!='\t'])
    return cleanspaces(somestring)

def cleanspaces(somestring):
    return ' '.join([element.strip() for element in somestring.split(' ') if len(element)!=0])

    # def articlescraper(url, dynamic=False, timetofetch=3):
    # headingdict = {'h1':1, 'h2':2, 'h3':3, 'h4':4, 'h5':5, 'h6':6}
    # clear_output(wait=True)
    # topic = False
    # lastheadingid = 0
    # lastheadingnumber = 0
    # # lastparagraphid = 0
    # # totalsubheadings = 0
    # # totalparagraphs = 0
    # topicid = 0
    # paragraphid = 0
    # lasttext = ''
    # insideheading = stack()

    # newdocument = []
    # newheadings = []
    # newparagraphs = []

    # try:
    #     soup = getpage(url, dynamic=dynamic, timetofetch=timetofetch)
    #     # if registereddomains[domainname]['articlecontainer']['attrs']==None:
    #     #     main = soup.find(registereddomains[domainname]['articlecontainer']['tag'])
    #     # else:
    #     #     main = soup.find(registereddomains[domainname]['articlecontainer']['tag'], registereddomains[domainname]['articlecontainer']['attrs'])
    #     # descendants = main.descendants
    # except Exception as e:
    #     print(e)
    #     return None

    # for element in soup.descendants:
    #     try:
    #         if topic==False:
    #             if str(element.name)[0]=='h':
    #                 # docid = len(database.index)
    #                 # topicid = len(headings.index)
    #                 # headings.loc[topicid] = ['topic', element.text, None, None, []]
    #                 topic = True
    #                 lastheadingid = topicid
    #                 lastheadingnumber = 0
    #                 lasttext = element.text

    #                 newheadings.append(['topic', element.text, None, None, []])

    #                 continue
    #             else:
    #                 continue
            
    #         # so that the nested elements don't make the same text count twice
    #         if element.text==lasttext:
    #             continue

    #         if element.name in headingdict:
    #             # totalsubheadings+=1

    #             headingid = lastheadingid+1

    #             headingnumber = headingdict[str(element.name)]
    #             # headings.loc[headingid] = [element.name, element.text, None, None, []]
    #             lasttext = element.text

    #             newheadings.append([element.name, element.text, None, None, []])

    #             if lastheadingnumber==0:
    #                 insideheading.push([lastheadingnumber, lastheadingid])
    #                 # headings.iloc[lastheadingid]['subheading'] = headingid
    #                 newheadings[lastheadingid][2] = headingid
    #             elif headingnumber>lastheadingnumber:
    #                 insideheading.push([lastheadingnumber, lastheadingid])
    #                 # headings.iloc[lastheadingid]['subheading'] = headingid
    #                 newheadings[lastheadingid][2] = headingid
    #             elif headingnumber==lastheadingnumber:
    #                 # headings.iloc[lastheadingid]['nextheading'] = headingid
    #                 newheadings[lastheadingid][3] = headingid
    #             else:
    #                 while True:

    #                     try:
    #                         poppedheading = insideheading.pop()
    #                         if poppedheading[0]>headingnumber:
    #                             continue
    #                         elif poppedheading[0]==headingnumber:
    #                             # headings.iloc[poppedheading[1]]['nextheading'] = headingid
    #                             newheadings[poppedheading[1]][3] = headingid
    #                             break
    #                         else:
    #                             insideheading = stack()
    #                             # headings.iloc[topicid]['subheading'] = headingid
    #                             newheadings[topicid][3] = headingid
    #                             break
    #                     except:
    #                         insideheading = stack()
    #                         break
    #             lastheadingid = headingid
    #             lastheadingnumber = headingnumber
    #         elif element.name=='p':
    #             if len(element.text)==0:
    #                 continue
    #             # totalparagraphs+=1
    #             # paragraphid = len(paragraphs.index)
    #             # paragraphs.loc[paragraphid] = ['p', element.text]
    #             newparagraphs.append(['p', element.text])
    #             # headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
    #             newheadings[lastheadingid][4].append(paragraphid)
    #             # lastparagraphid = paragraphid
    #             lasttext = element.text
    #             paragraphid += 1
    #         elif element.name=='ol':
    #             # totalparagraphs+=1
    #             for li in element.find_all('li'):
    #                 if len(li.text)==0:
    #                     continue
    #                 # paragraphid = len(paragraphs.index)
    #                 # paragraphs.loc[paragraphid] = ['oli', li.text]
    #                 newparagraphs.append(['oli', li.text])
    #                 # headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
    #                 newheadings[lastheadingid][4].append(paragraphid)
    #                 lasttext = element.text
    #                 paragraphid += 1
    #         elif element.name=='ul':
    #             # totalparagraphs+=1
    #             for li in element.find_all('li'):
    #                 if len(li.text)==0:
    #                     continue
    #                 # paragraphid = len(paragraphs.index)
    #                 # paragraphs.loc[paragraphid] = ['uli', li.text]
    #                 newparagraphs.append(['uli', li.text])
    #                 # headings.iloc[lastheadingid]['paragraphs'].append(paragraphid)
    #                 newheadings[lastheadingid][4].append(paragraphid)
    #                 lasttext = element.text
    #                 paragraphid += 1
    #     except Exception as e:
    #         # print(url)
    #         # print(element, e)
    #         # break
    #         continue
    # try:
    #     # database.loc[docid] = [topicid, url, totalsubheadings, totalparagraphs]
    #     newdocument = [topicid, url, len(newheadings), len(newparagraphs)]
    # except:
    #     pass
    # return newdocument, newheadings, newparagraphs