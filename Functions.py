import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import sys
import csv
import pandas as pd # type: ignore
import numpy as np # type: ignore
import os
import main as M # type: ignore

def OpponentWeight(link, visted_links):
    print("need Opponent Weight")
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    sys.stdout.reconfigure(encoding='utf-8')
    visted_links.add(link)

    # Try to get the athlete's weight directly
    weight = soup.find('h5', class_='title')
    if weight and weight.text.strip() == "Weight Limit":
        weight = soup.find('div', class_='value').text.strip()
        try:
            index = weight.index("KG")
        except ValueError:
            index = -1
        if index != -1:
            if weight[index - 6] == '1':
                weight = weight[index - 6:index-1]
            else:
                weight = weight[index - 5:index-1]
                if not weight[0].isdigit():
                    weight = weight[2:4]
            return weight
        else:
            print("Finding Weight: No Worked")
            return -1
    else:
        # Recursively look for opponent weights
        athletes = soup.find_all("a", class_ = 'opponent')
        if athletes:
            for athlete in athletes:
                athlete_link = soup.find("a", class_ = 'is-link is-distinct')
                opponent_tag = athlete.get("href")
                if opponent_tag in visted_links:  
                    print("Already In")
                else:
                    weight = OpponentWeight(opponent_tag, visted_links)
                    if weight != -1:
                        print("Got Weight From: " + opponent_tag)
                        return weight
        else:
            # Infer weight from text in <p> tags
            paragraphs = soup.find_all('p')
            for paragraph in paragraphs:
                text = paragraph.text.lower()
                if 'heavyweight' in text:
                    return 102.06
                elif 'light heavyweight' in text:
                    return 92.99
                elif 'middleweight' in text:
                    return 83.91
                elif 'welterweight' in text:
                    return 77.11
                elif 'lightweight' in text:
                    return 70.31
                elif 'featherweight' in text:
                    return 65.77
                elif 'bantamweight' in text:
                    return 61.23
                elif 'flyweight' in text:
                    return 56.70
                elif 'strawweight' in text:
                    return 52.16
                elif 'atomweight' in text:
                    return 47.63
        print("Finding Weight: No Worked")
        return -1
def OpponentGender(link,visted_links):
    url = link
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    sys.stdout.reconfigure(encoding='utf-8')
    visted_links.add(link)
    gender = "NA"
    paragraphs = soup.find_all('p')
    for paragraph in paragraphs:
        text = paragraph.text.lower()
        if 'he' in text or 'him' in text:
            return "Male"
        elif 'she' in text or 'her' in text:
            return "Female"
    if gender == "NA":
        #Look at the Opponent Gender
        athletes = soup.find_all("a", class_ = 'is-link is-distinct')
        if athletes:
            for athlete in athletes:
                opponent_link = athlete.get("href")
                if opponent_link in visted_links:
                    print("Already Used")
                else:
                    gender = OpponentGender(opponent_link, visted_links)
                if gender != "NA":
                    return gender
    return "NA"


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

