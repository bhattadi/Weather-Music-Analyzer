# SI 206 Final Project
# Aditya Bhatt, Ashka Pujara, Anirudh Lagisetty

#Barbara11$

# THE IMPORTS
import sqlite3
import json
import os
import requests
import datetime
import operator
import billboard
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
import matplotlib.pyplot as plt
import numpy as np

#Set up Spotify Authentication keys
cid = '47c048a48eb241eb87f5303a87519107'
secret = '342431872a43454fa85c8b35d0fb8a46'

#Used spotipy documentation as an example
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

#Initial database set up function to allow the program to be able to find the file in the OS
def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

# Creates the weather temperature table, weather conditions table, the top Billboards table, and Genres table
def setUpTables(cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS 'Weather_temp' ('date' TEXT, 'temperature' REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS 'Weather_condition' ('date' TEXT, 'condition' TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS 'Billboards' ('date' TEXT, 'name' TEXT, 'number' INTEGER, 'genre' TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS 'Genres' ('date' TEXT, 'genre' TEXT)")
    conn.commit()

# Call the weather API
# Create a table with dates and weather data
def setUpWeather(cur, conn):

    weather_dict = {'Snow':'Snow',
                    'Sleet': 'Hail',
                    'Hail': 'Hail',
                    'Thunder': 'Rainy',
                    'Thunderstorm': 'Rainy',
                    'Heavy Rain': 'Rainy',
                    'Light Rain': 'Rainy',
                    'Showers': 'Rainy',
                    'Heavy Cloud': 'Cloudy',
                    'Light Cloud': 'Sunny',
                    'Clear': 'Sunny'}

    count = 0

    start_date = datetime.date(2014, 1, 1)
    #end_date = datetime.date(2020, 4, 24)
    delta = datetime.timedelta(days=10)

    while count < 20:
        
        # Run execute to fetch data
        cur.execute('SELECT temperature FROM Weather_temp WHERE date=?', (str(start_date),))

        if(cur.fetchone() != None):
            start_date += delta
            continue
        else:
            pass

        count += 1

        date = str(start_date)

        date = date.replace('-', '/', 2)
        url = 'https://www.metaweather.com/api/location/2459115/' + str(date) + '/'
        data = requests.get(url).json()
        temperature_in = 0.0
        common_condition = {}
        
        for item in data:
            condition = weather_dict[item['weather_state_name']]
            common_condition[condition] = common_condition.get(condition, 0) + 1
            if item['the_temp'] is not None:
                temperature_in += item['the_temp']
            else:
                temperature_in += 0

        temperature_in /= len(data)
        temperature_in = ((9/5) * temperature_in) + 32

        condition_in = max(common_condition.items(), key=operator.itemgetter(1))[0]  


        cur.execute('''INSERT INTO Weather_temp (date, temperature) VALUES (?,?)''', (start_date, temperature_in))
        cur.execute('''INSERT INTO Weather_condition (date, condition) VALUES (?,?)''', (start_date, condition_in))
        conn.commit()
        start_date += delta

    print("Retrieved 20 dates, restart to retrieve more dates")
    return

# Call the bill boards API
# Create a table with dates and top hits

def setUpBillBoards(cur, conn):

    # genre setup
    genres = {'dance pop':'pop',
                'dance' : 'edm',
                'modern rock': 'rock',
                'pop rock': 'rock',
                'rock' : 'rock',
                'r&b': 'r&b',
                'edm': 'edm',
                'electro house' : 'edm',
                'tropical house' : 'edm',
                'pop' : 'pop',
                'pop punk': 'pop',
                'post-teen pop' : 'pop',
                'teen pop' : 'pop',
                'country': 'country',
                'contemporary country': 'country',
                'hip hop': 'rap',
                'trap': 'rap',
                'rap': 'rap'}
    reg_exp = r'^\S+'
                
    start_date = datetime.date(2014, 1, 1)
    #end_date = datetime.date(2020, 4, 24)
    delta = datetime.timedelta(days=10)

    counter = 0
    while counter < 20:
        chart = billboard.ChartData(name='hot-100', date=str(start_date))
        cur.execute('SELECT name FROM Billboards WHERE date=?', (str(start_date),))

        if(cur.fetchone() != None):
            start_date += delta
            continue
        else:
            pass

        chart = chart[:5]
        for item in chart:
            #Data Cleaning and Preprocessing for genre
            artist = item.artist.replace('by', '')
            artist = artist.replace('The ', '')
            artist = re.findall(reg_exp, artist)[0]   
            # print(item.title)
            # print(artist)
            val = sp.search(q=(item.title + " " + artist), limit=1, type='track')
            id = val['tracks']['items'][0]['artists'][0]['id']

            final_genre = ""
            genre_result = sp.artist(id)['genres']
            for genre in genre_result:
                if genres.get(genre) != None:
                    final_genre = genres[genre]
                    break
            
            if final_genre == "":
                final_genre = 'Other'

            cur.execute('''INSERT INTO Billboards (date, name, number, genre) VALUES (?,?,?,?)''', (str(start_date), item.title, item.rank, final_genre))
            conn.commit()

        counter += 1
        start_date += delta


# Find corresponding Genres for the songs
def setUpGenres(cur, conn):
        
    count = 0
    start_date = datetime.date(2014, 1, 1)
    delta = datetime.timedelta(days=10)

    while count < 20:
        
        # Run execute to fetch data
        cur.execute('SELECT genre FROM Genres WHERE date=?', (str(start_date),))

        if(cur.fetchone() != None):
            start_date += delta
            continue
        else:
            pass

        count += 1

        cur.execute('SELECT genre FROM Billboards WHERE date=?', (str(start_date),))
        results = cur.fetchall()

        daily_genres = {}
        for item in results:
            daily_genres[item[0]] = daily_genres.get(item[0], 0) + 1
        
        common_genre = max(daily_genres.items(), key=operator.itemgetter(1))[0] 

        cur.execute('INSERT INTO Genres (date, genre) VALUES (?,?)', (str(start_date), common_genre)) 
        conn.commit()

        start_date += delta    

    

#   ------------------------------------------NEW FILE BEGINS HERE--------------------------------------------

# Join 2 weather tables together
# Join Genre table with weather table to find matching data

def joinTables(cur, conn):

    # -------- Visualization #1--------------------
    cur.execute('SELECT Genres.date, Genres.genre \
        FROM Genres \
        JOIN Weather_condition \
        ON Weather_condition.date = Genres.date')
    date_and_genre = cur.fetchall()
    
    frequency_of_genre = {}
    for date, genre in date_and_genre:
        frequency_of_genre[genre] = frequency_of_genre.get(genre, 0) + 1

    x_axis = frequency_of_genre.keys()
    y_axis = frequency_of_genre.values()
    plt.bar(x_axis, y_axis)
    plt.title('Genres vs Frequency')
    plt.ylabel('Frequency')
    plt.xlabel('Genres')
    plt.savefig('Genre vs Frequency Bar Graph')

    # ------------ Visualization #2 ----------------------        
    cur.execute('SELECT Weather_condition.condition, Genres.genre \
        FROM Genres \
        JOIN Weather_condition \
        ON Weather_condition.date = Genres.date')
    condition_and_genre = cur.fetchall()
    print(condition_and_genre)

    genre_freq_by_condition = {'Cloudy' : {}, 
                                    'Rainy' : {},
                                    'Sunny' : {},
                                    'Snow' : {},
                                    'Hail' : {}}

    for state, genre in condition_and_genre:
        genre_freq_by_condition[state][genre] = genre_freq_by_condition[state].get('genre', 0) + 1

    i = 0
    for item in genre_freq_by_condition.items():
        #we need to map each weather state into a pie chart where the percentages are determined by the frequency of the genre
        labels = item[1].keys()
        percentages = item[1].values()
        print(labels)
        print(percentages)
        fig1, ax1 = plt.subplots()
        ax1.pie(percentages, labels=labels, shadow=True, startangle=90, autopct='%1.1f%%')
        ax1.axis('equal')
        plt.title('Genres vs Frequency')
        plt.legend()
        plt.savefig('Genre vs Frequency Bar Graph ' + str(i))
        i += 1


    cur.execute('SELECT Weather_temp.temperature, Genres.genre \
        FROM Genres \
        JOIN Weather_temp \
        ON Weather_temp.date = Genres.date')
    temperature_and_genre = cur.fetchall()

    



    # cur.execute('''UPDATE Weather_temp 
    #                 SET Weather_temp.condition = Weather_condition.condition 
    #                 FROM Weather_temp
    #                 INNER JOIN Weather_condition 
    #                 ON date = Weather_condition.date''')
    conn.commit()


# Plot weather vs genre
# Plot weather over time
# Plot time over genre

def main():
    cur, conn = setUpDatabase('final.db')
    print("Set up the Database")

    setUpTables(cur, conn)
    print("Set up the Tables")

    # setUpWeather(cur, conn)
    # print("Set up the weather")

    # setUpBillBoards(cur, conn)
    # print("Set up the Billboards")

    # setUpGenres(cur, conn)
    # print("Set up the Genres")

    joinTables(cur, conn)
    print("Joint Genres with Weather Dates")


if __name__ == "__main__":
    main()