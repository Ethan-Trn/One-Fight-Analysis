import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import sys
import csv
import pandas as pd # type: ignore
import numpy as np # type: ignore
import os
import main as M # type: ignore

def OpponentWeight(link):
    url = link  # Replace with the target URL
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    sys.stdout.reconfigure(encoding='utf-8')
    #get the athlete weight
    #grab the first element and check to see if has weight 
    weight = soup.find('h5',class_ = 'title')
    
    if weight and weight.text.strip() == "Weight Limit":
        weight = soup.find('div', class_ = 'value').text.strip()
        try:
            index = weight.index("KG")
        except ValueError:
            index = -1
        if weight[index - 6] == '1':
            weight = weight[index - 6:index-1]
        else:
            weight = weight[index - 5:index-1]
            if not weight[0].isdigit():
                weight = weight[2:4]
    else:
        print("No Worked")
        return -1
def FindWeightText(link):
    url = link
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    sys.stdout.reconfigure(encoding='utf-8')
    #Look For It By reading their description
    paragraphs = soup.find_all('p')
    for paragraph in paragraphs:
        text = paragraph.text.lower()
        if '' in text or 'him' in text:
            gender = "Male"
            break
        elif 'she' in text or 'her' in text:
            gender = "Female"
            break
#Basically the same as AthleteScrapper but instead of getting a csv it just displays all the info
def AthleteScraper2(i):
    print(f"Scraping page {i}")
    url = f'https://www.onefc.com/athletes/page/{i}/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    sys.stdout.reconfigure(encoding='utf-8')
    AllLinks = soup.find_all("a", class_='title text-center')
    print ("Found", len(AllLinks), "links")
    print("------------------------------")
    for link in AllLinks:
        href = link.get("href")
        print("href", href)
        try:
            matchups = M.Matchup(href)
            # matchups.head(5)
            #get the stats I need and put it to Stat_data
            #Get the amount of WINs and LOSSes
            #Get the amount of WINs and LOSSes by TKO, Submission, Disqualification, Unanimous Decision, Split Decision
            #Get the amount of LOSSes by TKO, Submission, Disqualification, Unanimous Decision, Split Decision
            #put them into stat_data
            WIN = matchups[matchups['Result'] == 'WIN'].shape[0]
            LOSS = matchups[matchups['Result'] == 'LOSS'].shape[0]
            w_tko = matchups[(matchups['Result'] == 'WIN') & (matchups['Method'] == 'TKO')].shape[0]
            # w_submission = matchups[matchups['Result'] == 'WIN']&[matchups['Method'] == 'Submission'].shape[0]
            # w_disqualification = matchups[matchups['Result'] == 'WIN']&[matchups['Method'] == 'Disqualification'].shape[0]
            # w_unanimous_decision = matchups[matchups['Result'] == 'WIN']&[matchups['Method'] == 'Unanimous Decision'].shape[0]
            # w_split_decision = matchups[matchups['Result'] == 'WIN']&[matchups['Method'] == 'Split Decision'].shape[0]
            # l_tko = matchups[matchups['Result'] == 'LOSS']&[matchups['Method'] == 'TKO'].shape[0]
            # l_submission = matchups[matchups['Result'] == 'LOSS']&[matchups['Method'] == 'Submission'].shape[0]
            # l_disqualification = matchups[matchups['Result'] == 'LOSS']&[matchups['Method'] == 'Disqualification'].shape[0]
            # l_unanimous_decision = matchups[matchups['Result'] == 'LOSS']&[matchups['Method'] == 'Unanimous Decision'].shape[0]
            # l_split_decision = matchups[matchups['Result'] == 'LOSS']&[matchups['Method'] == 'Split Decision'].shape[0]
            stat_data = M.StatScraper(href) 
            #make a dataframe with the data I need
            for i in range(len(stat_data)):
                print(stat_data[i])
            
            print("Win:" + str(WIN))
            print("Loss:" + str(LOSS))
            print("Win by TKO:" + str(w_tko))
            print(f"Scraped {href} successfully.")
            print("------------------------------")
        except Exception as e:
            print(f"Error scraping {href}: {e}")
        print("------------------------------")
