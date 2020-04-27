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
from collections import OrderedDict

numDays = 25
startYear = 2013

#Set up Spotify Authentication keys
cid = '47c048a48eb241eb87f5303a87519107'
secret = '342431872a43454fa85c8b35d0fb8a46'

#Used spotipy documentation as an example
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

# Initial database set up function to allow the program to be able to find the file in the OS
# Input: database name (string)
# Output: cur and conn (database cursor and connection)
def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


# Creates the weather temperature table, weather conditions table, the top Billboards table, and Genres table
# Input: database cursor and connection
# Output: none; creates database tables
def setUpTables(cur, conn):
    cur.execute("CREATE TABLE IF NOT EXISTS 'Weather_temp' ('date' TEXT, 'temperature' REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS 'Weather_condition' ('date' TEXT, 'condition' TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS 'Billboards' ('date' TEXT, 'name' TEXT, 'number' INTEGER, 'genre' TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS 'Genres' ('date' TEXT, 'genre' TEXT)")
    conn.commit()

# Call the weather API
# Create a table with dates and weather data
# Input: database cursor and connection
# Output: Sets up weather tables with temperature/condition by date
def setUpWeather(cur, conn):

    #Create assignments of general weather states
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

    #Establish a start date and the incrementer for how many days to skip during each iteration
    count = 0
    start_date = datetime.date(startYear, 6, 1)
    delta = datetime.timedelta(days=10)

    #Only access 20 items at a time from the API
    while count < 20:
        
        # Run execute to fetch data
        cur.execute('SELECT temperature FROM Weather_temp WHERE date=?', (str(start_date),))

        #If the data is already in the datatable, then skip this iteration
        if(cur.fetchone() != None):
            start_date += delta
            continue
        else:
            pass

        #Update thecounter and call the API to retrieve information from New York City weather
        count += 1
        date = str(start_date)
        date = date.replace('-', '/', 2)
        url = 'https://www.metaweather.com/api/location/2459115/' + str(date) + '/'
        data = requests.get(url).json()
        temperature_in = 0.0
        common_condition = {}
        
        #For each weather log for that particular date
        #Find the average temperature using a dictionary
        for item in data:
            condition = weather_dict[item['weather_state_name']]
            common_condition[condition] = common_condition.get(condition, 0) + 1
            if item['the_temp'] is not None:
                temperature_in += item['the_temp']
            else:
                temperature_in += 0

        #Take the average of the temperature and convert to fahrenheit
        temperature_in /= len(data)
        temperature_in = ((9/5) * temperature_in) + 32
        condition_in = max(common_condition.items(), key=operator.itemgetter(1))[0]  

        #Write this data into the database
        cur.execute('''INSERT INTO Weather_temp (date, temperature) VALUES (?,?)''', (start_date, temperature_in))
        cur.execute('''INSERT INTO Weather_condition (date, condition) VALUES (?,?)''', (start_date, condition_in))
        conn.commit()
        start_date += delta

    print("Retrieved 20 dates, restart to retrieve more dates")
    return

# Call the bill boards API
# Create a table with dates and top hits
# Input: The cur and conn connections to the final database
# Output: Table filled with information about top number of songs on a given range of dates
def setUpBillBoards(cur, conn):

    # genre setup
    
    master_genres = OrderedDict()

    master_genres = {'modern rock': 'rock',
                'pop rock': 'rock',
                'rock' : 'rock',
                'r&b': 'r&b',
                'edm': 'edm',
                'electro house' : 'edm',
                'tropical house' : 'edm',
                'country': 'country',
                'contemporary country': 'country',
                'hip hop': 'rap',
                'trap': 'rap',
                'rap': 'rap',
                'dance' : 'edm',
                'post-teen pop' : 'teen pop',
                'teen pop' : 'teen pop',
                'pop' : 'pop',
                'pop punk': 'pop'}


    reg_exp = r'^\S+'
                
    start_date = datetime.date(startYear, 6, 1)
    delta = datetime.timedelta(days=numDays)

    counter = 0
    while counter < 20:
        chart = billboard.ChartData(name='hot-100', date=str(start_date), timeout=50)
        cur.execute('SELECT name FROM Billboards WHERE date=?', (str(start_date),))

        if(cur.fetchone() != None):
            start_date += delta
            continue
        else:
            pass

        chart = chart[:20]
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
            for pair in master_genres.items():
                if pair[0] in genre_result:
                    final_genre = pair[1]
                    break
            
            if final_genre == "":
                final_genre = 'Other'

            cur.execute('''INSERT INTO Billboards (date, name, number, genre) VALUES (?,?,?,?)''', (str(start_date), item.title, item.rank, final_genre))
            conn.commit()

        counter += 1
        start_date += delta


# Find corresponding Genres for the songs
# Input: The cur and conn connections to the final database
# Output: Table filled with information about what the top genre of the day is for a range of dates
def setUpGenres(cur, conn):
        
    count = 0
    start_date = datetime.date(startYear, 6, 1)
    delta = datetime.timedelta(days=numDays)

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

# Input: none
# Calling all setup functions to collect all data in counts of 20
def main():
    cur, conn = setUpDatabase('final.db')
    print("Set up the Database")

    setUpTables(cur, conn)
    print("Set up the Tables")

    setUpWeather(cur, conn)
    print("Set up the weather")

    setUpBillBoards(cur, conn)
    print("Set up the Billboards")

    setUpGenres(cur, conn)
    print("Set up the Genres")



if __name__ == "__main__":
    main() 
