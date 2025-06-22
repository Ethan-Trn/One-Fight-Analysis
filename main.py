import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import sys
import csv
import pandas as pd # type: ignore
import numpy as np # type: ignore
import os
import Functions as f
import re
def PageGather():
    for i in range(68):
        AthleteScraper(i+1)

def AthleteScraper(i):
    #Goes into the One Championship Athlete Page #
    print(f"Scraping page {i}")
    url = f'https://www.onefc.com/athletes/page/{i}/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    sys.stdout.reconfigure(encoding='utf-8')
    #This gets all the links to the athletes for that specific page
    AllLinks = soup.find_all("a", class_='title text-center')
    
    #Looks For the athlete_stats.csv and fight_record and create if it isn't there
    stats_file = 'athlete_stats.csv'
    fights_file = 'fight_records.csv'
    stats_exists = os.path.isfile(stats_file)
    fights_exists = os.path.isfile(fights_file)

    with open(stats_file, mode='a', newline='', encoding='utf-8') as s_file, \
         open(fights_file, mode='a', newline='', encoding='utf-8') as f_file:

        stats_writer = csv.writer(s_file)
        fights_writer = csv.writer(f_file)

        if not stats_exists:
            stats_writer.writerow(['Name', 'Weight (kg)', 'Height (cm)', 'Country', 'Age', 'Team', 'Sport', 'Gender','Weight Class'
                                   'WIN', 'LOSS', 'DRAW','W TKO', 'W Submission', 'W Disqualification', 'W Unanimous Decision',
                                   'W Split Decision', 'L TKO', 'L Submission', 'L Disqualification', 'L Unanimous Decision',
                                   'L Split Decision','Total Fights'])

        if not fights_exists:
            fights_writer.writerow(['Fighter', 'Opponent', 'Result', 'Method','Date'])
        #This is for going inside the link
        for link in AllLinks:
            href = link.get("href")
            try:
                matchups = Matchup(href)
                if matchups.empty:
                    print(f"No matchups found for {href}")
                    continue

                # Write matchups to the Fight_Record
                fights_writer.writerows(matchups.values.tolist())

                # Calculate statistics
                WIN = matchups[matchups['Result'] == 'WIN'].shape[0]
                LOSS = matchups[matchups['Result'] == 'LOSS'].shape[0]
                DRAW = matchups[matchups['Result'] == 'Unknown'].shape[0]
                w_tko = matchups[(matchups['Result'] == 'WIN') & (matchups['Method'] == 'TKO')].shape[0]
                w_submission = matchups[(matchups['Result'] == 'WIN') & (matchups['Method'] == 'Submission')].shape[0]
                w_disqualification = matchups[(matchups['Result'] == 'WIN') & (matchups['Method'] == 'Disqualification')].shape[0]
                w_unanimous_decision = matchups[(matchups['Result'] == 'WIN') & (matchups['Method'] == 'Unanimous Decision')].shape[0]
                w_split_decision = matchups[(matchups['Result'] == 'WIN') & (matchups['Method'] == 'Split Decision')].shape[0]
                l_tko = matchups[(matchups['Result'] == 'LOSS') & (matchups['Method'] == 'TKO')].shape[0]
                l_submission = matchups[(matchups['Result'] == 'LOSS') & (matchups['Method'] == 'Submission')].shape[0]
                l_disqualification = matchups[(matchups['Result'] == 'LOSS') & (matchups['Method'] == 'Disqualification')].shape[0]
                l_unanimous_decision = matchups[(matchups['Result'] == 'LOSS') & (matchups['Method'] == 'Unanimous Decision')].shape[0]
                l_split_decision = matchups[(matchups['Result'] == 'LOSS') & (matchups['Method'] == 'Split Decision')].shape[0]
                Total_Fights = len(matchups)

                # Get athlete stats and write to stats file
                stat_data = StatScraper(href)
                stats_writer.writerow(stat_data + [WIN, LOSS, DRAW,w_tko, w_submission, w_disqualification, w_unanimous_decision,
                                                   w_split_decision, l_tko, l_submission, l_disqualification,
                                                   l_unanimous_decision, l_split_decision,Total_Fights])
                print(f"Scraped {href} successfully.")
            except Exception as e:
                print(f"Error scraping {href}: {e}")

def StatScraper(link):
    url = link  # Replace with the target URL
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    sys.stdout.reconfigure(encoding='utf-8')
    #Creating Dictionary For Both Gender and Weight Recursion
    visted_links = {link}
    #get the athlete name
    athlete_name = soup.find('h1',class_ = 'use-letter-spacing-hint my-4')
    if athlete_name:
        #get the value of the whatever is in that thing
        athlete_name = (athlete_name.text.strip())
        # print(athlete_name)
    else:
        print("Athlete name not found")
    # print(soup.prettify())
    #Let's get the athlete's attribute
    weight = -1
    height = -1
    team = -1
    Country = -1 
    age = -1
    sport = -1
    gender = "NA"
    j = 0
    attributes = soup.find_all('div', class_ = 'value')
    # print(attributes.__len__())
    if attributes.__len__() >= 4:
        #tries to look for theweight
        weight = attributes[j].text.strip()
        try:
            index = weight.index("KG")
        except ValueError:
            index = -1
        if index != -1:
            #if he weights >- 100kg with decimal
            if weight[index - 6] == '1':
                weight = weight[index - 6:index-1]
            #lighterman skill or a > 100kg without decimal
            else:
                weight = weight[index - 5:index-1]
                if not weight[0].isdigit():
                    if weight[1] ==  '1':
                        weight = weight[1:4]
                    else:
                        weight = weight[2:4]
            j+=1
        #if weight isn't identified look for the opponent's weight
        else:
            #Look at the Opponent Weight
            athletes = soup.find_all("a", class_ = 'opponent')
            if athletes:
                for athlete in athletes:
                    athlete_link = soup.find("a", class_ = 'is-link is-distinct')
                    weight = f.OpponentWeight(athlete.get("href"),visted_links)
                    if weight != -1:
                        break
            else:
                #Look at the text if it says anything about the weight class they fight in 
                paragraphs = soup.find_all('p')
                for paragraph in paragraphs:
                    text = paragraph.text.lower()
                    if 'heavyweight' in text:
                        weight = 102.06
                        break
                    elif 'light heavyweight' in text:
                        weight = 92.99
                        break
                    elif 'middleweight' in text:
                        weight = 83.91
                        break
                    elif 'welterweight' in text:
                        weight = 77.11
                        break
                    elif 'lightweight' in text:
                        weight = 70.31
                        break
                    elif 'featherweight' in text:
                        weight = 65.77
                        break
                    elif 'bantamweight' in text:
                        weight = 61.23
                        break
                    elif 'flyweight' in text:
                        weight = 56.70
                        break
                    elif 'strawweight' in text:
                        weight = 52.16
                        break
                    elif 'atomweight' in text:
                        weight = 47.63
                        break
        visted_links.clear()
        visted_links.add(url)
        # print(weight)
        #height
        height = attributes[j].text.strip()
        try:
            index = height.index("CM")
        except ValueError:
            index = -1
        if index != -1:
            height = height[index - 4:index-1]
            j+=1
            # print (height)
        else:
            height = -1
            # print(height)
        height = float(height)
        #country 
        country = attributes[j].text.strip()
        j+=1
        # print (country)
        #age
        age = attributes[j].text.strip()
        age = age[0:2]
        if not age.isdigit():
            age = -1
        else:
            age = int(age)
            j+=1
        # print (age)
        #Team
        #if they have a 1 one it means they have no team
        team = attributes[j].text.strip()
        j+=1
        # print (team)
        #Sport
        sport = soup.find('td',class_ = 'sport d-none d-md-table-cell').text.strip()
        
    # Determine gender based on pronouns in <p> tags
    paragraphs = soup.find_all('p')
    for paragraph in paragraphs:
        text = paragraph.text.lower()
        if ' she ' in text or ' her ' in text:
            gender = "Female"
            break
        elif ' he ' in text or ' his ':
            gender = "Male"
            break
    if gender == "NA":
         #Look at the Opponent Gender
        athletes = soup.find_all("a", class_ = 'is-link is-distinct')
        if athletes:
            for athlete in athletes:
                gender = f.OpponentGender(athlete.get("href"),visted_links)
                if gender != "NA":
                    break
    #Getting the weight class
    try:
        weight = float(weight)
    except (ValueError, TypeError):
        weight = -1

    if weight >= 102.06 and weight <= 120.20:
        weight_class = "Heavyweight"
    elif weight >= 92.99:
        weight_class = "Light Heavyweight"
    elif weight >= 83.91:
        weight_class = "Middleweight"
    elif weight >= 77.11:
        weight_class = "Welterweight"
    elif weight >= 70.31:
        weight_class = "Lightweight"
    elif weight >= 65.77:
        weight_class = "Featherweight"
    elif weight >= 61.23:
        weight_class = "Bantamweight"
    elif weight >= 56.70:
        weight_class = "Flyweight"
    elif weight >= 52.16:
        weight_class = "Strawweight"
    elif weight >= 47.63:
        weight_class = "Atomweight"
    else:
        weight_class = "Out of range"


    print(f"Name: {athlete_name}, Gender: {gender}, Weight: {weight}, Height: {height}, Country: {country}, Age: {age}, Team: {team}, Sport: {sport}, Weight Class: {weight_class}")
    return [athlete_name, weight, height, country, age, team, sport, gender,weight_class]

    # else:
        # print ("------------")
        # nfigure(encoding='utf-8')          
def Matchup(link):
    results = []
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    sys.stdout.reconfigure(encoding='utf-8')
    
    #At
    name_tag = soup.find('h1', class_='use-letter-spacing-hint my-4')
    athlete_name = name_tag.text.strip() if name_tag else "Unknown"

    #what is this doing
    #getting the page of each match up
    load_more = soup.find('a', class_='load-more action-button is-desktop-one-line mt-4')
    #Checks how many fighter are there 
    #This is the case if there is only one page
    if not load_more:
        print ("Only One page")
        #This grabs all the matchups the athlete has fought
        matchups = soup.find_all('tr', class_='is-data-row')
        for row in matchups:
                try:
                    opponent_tag = row.find('h5', class_='fs-100 m-0')
                    opponent_name = opponent_tag.text.strip() if opponent_tag else "Unknown"
                    date_tag = row.find('td', class_='date d-none d-xxl-table-cell')
                    date = date_tag.text.strip() if date_tag else None
                    #write this later for it to be your own
                    result_tag = row.find('div', class_="is-distinct is-positive") or \
                                row.find('div', class_="is-distinct is-negative")
                    result = result_tag.text.strip() if result_tag else "Unknown"
                    # print("Result of " + opponent_name + " is " + result)
                    MethodOf = row.find('td', class_="method d-none d-lg-table-cell").text.strip()
                    if "TKO" in MethodOf:
                        MethodOf = "TKO"
                    elif "Submission" in MethodOf:
                        MethodOf = "Submission"
                    elif "Disqualification" in MethodOf:
                        MethodOf = "Disqualification"
                    elif "Unanimous Decision" in MethodOf:
                        MethodOf = "Unanimous Decision"
                    elif "Split Decision" in MethodOf:
                        MethodOf = "Split Decision"
                    elif "Majority Decision" in MethodOf:
                        MethodOf = "Majority Decision"
                    elif "Knockout" in MethodOf:
                        MethodOf = "Knockout"
                    else:
                        MethodOf = "Unknown"
                    results.append([athlete_name, opponent_name, result, MethodOf,date])
                except Exception as e:
                    print(f"Error processing opponent: {e}")
#if there are multiple pages that needed to be loaded
    else:
        #will look smth like this: 'https://www.onefc.com/athletes/anatoly-malykhin/matchups/page/' 
        #will become with page # to get each page
        base_url = load_more.get("href")
        base_url = base_url[0:base_url.index("2/")]
        page = 1
        while True:
            url = base_url + str(page) +"/"
            # print (f"Scraping page {page}...")
            #signal 404 is like no can find
            response = requests.get(url)
            if response.status_code >= 400:
                print(f"Page {page} not found. Stopping.")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            #this grabs each row or matchup
            matchups = soup.find_all('tr', class_='is-data-row')

            for row in matchups:
                try:
                    opponent_tag = row.find('h5', class_='fs-100 m-0')
                    opponent_name = opponent_tag.text.strip() if opponent_tag else "Unknown"
                    #write this later for it to be your own
                    result_tag = row.find('div', class_="is-distinct is-positive") or \
                                row.find('div', class_="is-distinct is-negative")
                    result = result_tag.text.strip() if result_tag else "Unknown"
                    date_tag = row.find('td', class_='date d-none d-xxl-table-cell')
                    date = date_tag.text.strip() if date_tag else None
                    MethodOf = row.find('td', class_="method d-none d-lg-table-cell").text.strip()
                    if "TKO" in MethodOf:
                        MethodOf = "TKO"
                    elif "Submission" in MethodOf:
                        MethodOf = "Submission"
                    elif "Disqualification" in MethodOf:
                        MethodOf = "Disqualification"
                    elif "Unanimous Decision" in MethodOf:
                        MethodOf = "Unanimous Decision"
                    elif "Split Decision" in MethodOf:
                        MethodOf = "Split Decision"
                    elif"Majority Decision" in MethodOf:
                        MethodOf = "Majority Decision"
                    elif "Knockout" in MethodOf:
                        MethodOf = "Knockout"
                    else:
                        MethodOf = "Unknown"
                    results.append([athlete_name, opponent_name, result, MethodOf,date])
                except Exception as e:
                    print(f"Error processing opponent: {e}")
            page += 1
    results = np.array(results)
    results = pd.DataFrame(results, columns=['Fighter', 'Opponent', 'Result', 'Method', 'Date'])
    #print out all the wins
    # print(results[results['Result'] == 'WIN'].shape[0])
    #print out all the losses
    # print(results[results['Result'] == 'LOSS'].shape[0])
    #print out all Win from TKO
    # print(results[(results['Result'] == 'WIN') & (results['Method'] == 'TKO')].shape[0])
    # print(results[["Opponent", "Result", "Method"]])
    return results
            
if __name__ == "__main__":
    if os.path.exists("athlete_stats.csv"):
        os.remove("athlete_stats.csv")
        print("Old CSV deleted. Starting fresh.")
    else:
        print("No old CSV found. You're good.")
    if os.path.exists("fight_records.csv"):
        os.remove("fight_records.csv")
        print("Old CSV deleted. Starting fresh.")
    else:
        print("No old CSV found. You're good.")
    # tag = 'https://www.onefc.com/athletes/anton-petrov/'
    # Matchup(tag)
    # PrintScraper('https://www.onefc.com/athletes/adilet-alimbek-uulu/')
    PageGather()
    # StatScraper(tag)
    # StatScraper('https://www.onefc.com/athletes/roman-kryklia/')
    # OpponentWeight('https://www.onefc.com/athletes/demetrious-johnson/')
    # f.AthleteScraper2(1)