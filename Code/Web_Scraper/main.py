import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import sys
import csv
import pandas as pd # type: ignore
import numpy as np # type: ignore
import os
import Functions as f
import cache as c
import re
def PageGather():
    #makes a list of all the athlete pages 
    listing_urls = []
    for i in range(1, 73):   # starts at 1, ends at 72
        url = f'https://www.onefc.com/athletes/page/{i}/'
        listing_urls.append(url)
    #this essentially goes into each of the athlete pages and gets the html content 
    pages = c.fetch_many_cached(listing_urls, max_workers=8)
    # process in order for stability like goes from athlete page 0 to 72 in that order kind of 
    for url in sorted(pages.keys()):
        html = pages[url]
        listing_soup = BeautifulSoup(html, 'html.parser')
        AthleteScraper(listing_soup=listing_soup)  # pass soup instead of index


def AthleteScraper(listing_soup=None, i=None):
    # If listing_soup not provided, fall back to old behavior (still cached)
    if listing_soup is None:
        assert i is not None, "Provide either listing_soup or page index i"
        url = f'https://www.onefc.com/athletes/page/{i}/'
        html = c.fetch_cached(url)
        listing_soup = BeautifulSoup(html, 'html.parser')

    sys.stdout.reconfigure(encoding='utf-8')

    # files + columns
    stats_file  = 'athlete_stats.csv'
    fights_file = 'fight_records.csv'

    stats_cols = [
        'Name', 'Weight (kg)', 'Height (cm)', 'Country', 'Age', 'Team', 'Sport', 'Gender', 'Weight Class',
        'WIN', 'LOSS', 'DRAW', 'W TKO', 'W Submission', 'W Disqualification', 'W Unanimous Decision',
        'W Split Decision', 'L TKO', 'L Submission', 'L Disqualification', 'L Unanimous Decision',
        'L Split Decision', 'Total Fights'
    ]
    fights_cols = ['Fighter', 'Opponent', 'Result', 'Method', 'Date']

    page_stats_rows = []
    page_fights_dfs = []

    AllLinks = listing_soup.find_all("a", class_='title text-center')

    for link in AllLinks:
        href = link.get("href")
        try:
            # fetch profile once (cached)
            html = c.fetch_cached(href)
            profile_soup = BeautifulSoup(html, 'html.parser')

            # use the SAME soup for both functions (no duplicate requests/parsing)
            matchups = Matchup(link=href, soup=profile_soup)
            if not matchups.empty:
                matchups = matchups.reindex(columns=fights_cols)
                page_fights_dfs.append(matchups)

            WIN  = (matchups['Result'] == 'WIN').sum()      if not matchups.empty else 0
            LOSS = (matchups['Result'] == 'LOSS').sum()     if not matchups.empty else 0
            DRAW = (matchups['Result'] == 'Unknown').sum()  if not matchups.empty else 0

            w_tko  = ((matchups['Result'] == 'WIN')  & (matchups['Method'] == 'TKO')).sum()                if not matchups.empty else 0
            w_sub  = ((matchups['Result'] == 'WIN')  & (matchups['Method'] == 'Submission')).sum()         if not matchups.empty else 0
            w_dq   = ((matchups['Result'] == 'WIN')  & (matchups['Method'] == 'Disqualification')).sum()   if not matchups.empty else 0
            w_ud   = ((matchups['Result'] == 'WIN')  & (matchups['Method'] == 'Unanimous Decision')).sum() if not matchups.empty else 0
            w_sd   = ((matchups['Result'] == 'WIN')  & (matchups['Method'] == 'Split Decision')).sum()     if not matchups.empty else 0

            l_tko  = ((matchups['Result'] == 'LOSS') & (matchups['Method'] == 'TKO')).sum()                if not matchups.empty else 0
            l_sub  = ((matchups['Result'] == 'LOSS') & (matchups['Method'] == 'Submission')).sum()         if not matchups.empty else 0
            l_dq   = ((matchups['Result'] == 'LOSS') & (matchups['Method'] == 'Disqualification')).sum()   if not matchups.empty else 0
            l_ud   = ((matchups['Result'] == 'LOSS') & (matchups['Method'] == 'Unanimous Decision')).sum() if not matchups.empty else 0
            l_sd   = ((matchups['Result'] == 'LOSS') & (matchups['Method'] == 'Split Decision')).sum()     if not matchups.empty else 0

            total = 0 if matchups.empty else len(matchups)

            
            stat_data = StatScraper(link=href, soup=profile_soup)  # <-- only signature change

            if not isinstance(stat_data, list) or len(stat_data) < 9:
                name = stat_data[0] if isinstance(stat_data, list) and len(stat_data) > 0 else 'Unknown'
                stat_data = [name, -1, -1, -1, -1, -1, -1, "NA", "Out of range"]

            row = stat_data + [WIN, LOSS, DRAW, w_tko, w_sub, w_dq, w_ud, w_sd, l_tko, l_sub, l_dq, l_ud, l_sd, total]
            page_stats_rows.append(row)

        except Exception as e:
            print(f"Error scraping {href}: {e}")

    # write once per listing page (append; header only if file doesn't exist)
    if page_fights_dfs:
        fights_df = pd.concat(page_fights_dfs, ignore_index=True)
        write_header = not os.path.isfile(fights_file)
        fights_df.to_csv(fights_file, mode='a', header=write_header, index=False)

    if page_stats_rows:
        stats_df = pd.DataFrame(page_stats_rows, columns=stats_cols)
        write_header = not os.path.isfile(stats_file)
        stats_df.to_csv(stats_file, mode='a', header=write_header, index=False)


def StatScraper(link, soup=None):
    url = link
    if soup is None:
        # fetch from cache if soup not provided
        html = c.fetch_cached(url)
        soup = BeautifulSoup(html, 'html.parser')

    sys.stdout.reconfigure(encoding='utf-8')
    visted_links = {link}

    # Athlete name
    athlete_name = soup.find('h1', class_='use-letter-spacing-hint my-4')
    if athlete_name:
        athlete_name = athlete_name.text.strip()

    # defaults
    weight, height, team, country, age, sport = -1, -1, -1, -1, -1, -1
    gender = "NA"
    j = 0

    # attributes
    attributes = soup.find_all('div', class_='value')
    if len(attributes) >= 4:
        # weight
        weight = attributes[j].text.strip()
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
                    if weight[1] == '1':
                        weight = weight[1:4]
                    else:
                        weight = weight[2:4]
            j += 1
        else:
            fightevent = soup.find_all("td", class_='event d-none d-sm-table-cell')
            if fightevent:
                fightlink = fightevent[0].find("a", class_='is-link is-distinct')
                if fightlink:
                    fightlink_url = fightlink.get("href")
                    weight = f.InsideFightNight(fightlink_url, link)
            # else: leave weight as -1

        visted_links.clear()
        visted_links.add(url)

        # height
        height = attributes[j].text.strip()
        try:
            index = height.index("CM")
        except ValueError:
            index = -1
        if index != -1:
            height = height[index - 4:index-1]
            j += 1
            height = float(height)
        else:
            height = -1

        # country
        country = attributes[j].text.strip()
        j += 1

        # age
        age = attributes[j].text.strip()[0:2]
        if not age.isdigit():
            age = -1
        else:
            age = int(age)
            j += 1

        # team
        team = attributes[j].text.strip()
        j += 1

        # sport
        sport = soup.find('td', class_='sport d-none d-md-table-cell').text.strip()

    # Gender detection
    paragraphs = soup.find_all('p')
    for paragraph in paragraphs:
        text = paragraph.text.lower()
        if ' she ' in text or ' her ' in text:
            gender = "Female"
            break
        elif ' he ' in text or ' his ' in text:
            gender = "Male"
            break
    if gender == "NA":
        athletes = soup.find_all("a", class_='is-link is-distinct')
        if athletes:
            for athlete in athletes:
                gender = f.OpponentGender(athlete.get("href"), visted_links)
                if gender != "NA":
                    break

    # Convert weight to float for weight class
    try:
        weight = float(weight)
    except (ValueError, TypeError):
        weight = -1

    if weight >= 102.058:
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

    return [athlete_name, weight, height, country, age, team, sport, gender, weight_class]

def Matchup(link=None, soup=None):
    results = []
    if soup is None:
        html = c.fetch_cached(link)
        soup = BeautifulSoup(html, 'html.parser')

    sys.stdout.reconfigure(encoding='utf-8')

    # athlete name
    name_tag = soup.find('h1', class_='use-letter-spacing-hint my-4')
    athlete_name = name_tag.text.strip() if name_tag else "Unknown"

    load_more = soup.find('a', class_='load-more action-button is-desktop-one-line mt-4')

    if not load_more:  # single page of matchups
        matchups = soup.find_all('tr', class_='is-data-row')
        for row in matchups:
            try:
                opponent_tag = row.find('h5', class_='fs-100 m-0')
                opponent_name = opponent_tag.text.strip() if opponent_tag else "Unknown"

                date_tag = row.find('td', class_='date d-none d-xxl-table-cell')
                if date_tag:
                    timestamp = date_tag.get('data-timestamp')
                    if timestamp:
                        date = pd.to_datetime(int(timestamp), unit='s').strftime('%b %d, %Y')
                    else:
                        date = date_tag.get_text(strip=True)
                else:
                    date = None

                result_tag = row.find('div', class_="is-distinct is-positive") or \
                             row.find('div', class_="is-distinct is-negative")
                result = result_tag.text.strip() if result_tag else "Unknown"

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

                results.append([athlete_name, opponent_name, result, MethodOf, date])
            except Exception as e:
                print(f"Error processing opponent: {e}")

    else:  # multiple pages of matchups
        base_url = load_more.get("href")
        base_url = base_url[0:base_url.index("2/")]
        page = 1
        while True:
            url = base_url + str(page) + "/"
            html = c.fetch_cached(url)
            soup = BeautifulSoup(html, 'html.parser')

            if soup.title and "404" in soup.title.text:
                break

            matchups = soup.find_all('tr', class_='is-data-row')
            for row in matchups:
                try:
                    opponent_tag = row.find('h5', class_='fs-100 m-0')
                    opponent_name = opponent_tag.text.strip() if opponent_tag else "Unknown"

                    result_tag = row.find('div', class_="is-distinct is-positive") or \
                                 row.find('div', class_="is-distinct is-negative")
                    result = result_tag.text.strip() if result_tag else "Unknown"

                    date_tag = row.find('td', class_='date d-none d-xxl-table-cell')
                    if date_tag:
                        timestamp = date_tag.get('data-timestamp')
                        if timestamp:
                            date = pd.to_datetime(int(timestamp), unit='s').strftime('%b %d, %Y')
                        else:
                            date = date_tag.get_text(strip=True)
                    else:
                        date = None

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

                    results.append([athlete_name, opponent_name, result, MethodOf, date])
                except Exception as e:
                    print(f"Error processing opponent: {e}")

            page += 1

    results = pd.DataFrame(results, columns=['Fighter', 'Opponent', 'Result', 'Method', 'Date'])
    return results

if __name__ == "__main__":
    # if os.path.exists("athlete_stats.csv"):
    #     os.remove("athlete_stats.csv")
    #     print("Old CSV deleted. Starting fresh.")
    # else:
    #     print("No old CSV found. You're good.")
    # if os.path.exists("fight_records.csv"):
    #     os.remove("fight_records.csv")
    #     print("Old CSV deleted. Starting fresh.")
    # else:
    #     print("No old CSV found. You're good.")
    tag = 'https://www.onefc.com/athletes/kana/'
    # Matchup(tag)
    # AthleteScraper(tag)
    StatScraper(tag)
    # PageGather()
