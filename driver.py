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
import data_collection

frequency_of_genre = {}
genre_freq_by_condition = {'Cloudy' : {}, 
                            'Rainy' : {},
                            'Sunny' : {},
                            'Snow' : {},
                            'Hail' : {}}

#Using SQL joins to find corresponding genres for a particular date
#Using matplotlib to produce bar graphs and pie charts
# -------------- Visualization #1--------------------
# Input: The cur and conn connections to the final database
# Output: Bar Graphs for frequency of different genres
def barGraph(cur, conn):
    cur.execute('SELECT Genres.date, Genres.genre \
        FROM Genres \
        JOIN Weather_condition \
        ON Weather_condition.date = Genres.date')
    date_and_genre = cur.fetchall()
    
    for date, genre in date_and_genre:
        frequency_of_genre[genre] = frequency_of_genre.get(genre, 0) + 1

    x_axis = frequency_of_genre.keys()
    y_axis = frequency_of_genre.values()
    plt.bar(x_axis, y_axis)
    plt.title('Music Genres vs Frequency')
    plt.ylabel('Frequency')
    plt.xlabel('Genres')
    plt.savefig('Genre vs Frequency Bar Graph')


# ------------------ Visualizations #2-#4 ----------------------    
# Input: Database cursor and connection
# Output: Produces 5 pie charts corresponding to each type of weather condition 
# and the frequency of genres on that type of day    
def pieCharts(cur, conn):
    cur.execute('SELECT Weather_condition.condition, Genres.genre \
        FROM Genres \
        JOIN Weather_condition \
        ON Weather_condition.date = Genres.date')
    condition_and_genre = cur.fetchall()

    for state, genre in condition_and_genre:
        genre_freq_by_condition[state][genre] = genre_freq_by_condition[state].get(genre, 0) + 1
    
    i = 0
    for item in genre_freq_by_condition.items():
        #we need to map each weather state into a pie chart where the percentages are determined by the frequency of the genre
        labels = item[1].keys()
        percentages = item[1].values()
        fig1, ax1 = plt.subplots()
        ax1.pie(percentages, labels=labels, shadow=True, startangle=90, autopct='%1.1f%%')
        ax1.axis('equal')
        plt.title(item[0] + ' Day: Music Genres vs Frequency')
        plt.legend()
        plt.savefig('Genre vs Frequency Pie Chart ' + str(i))
        i += 1

def yearsAnalysisOfGenre(cur, conn):
    


# Input: None
# Output: Written file with calculations for all visualizations
def writeToFile():
    f = open("Final_calculations.txt", "a")
    f.write("Frequency of Music Genre\n\n")
    f.write(json.dumps(frequency_of_genre))
    f.write('\n\n----------------------------------------------------------------------------------------------------------------------------\n\n')
    f.write("Calculations for Pie Chart of Genre frequencies at a given weather state\n\n")
    for key, value in genre_freq_by_condition.items():
        f.write("Weather State: " + key + " | Frequencies of Genre: " + str(json.dumps(value)))
        f.write('\n')
    f.close()

def main():

    cur, conn =  data_collection.setUpDatabase('final.db')
    barGraph(cur, conn)
    pieCharts(cur, conn)
    writeToFile()

    print("Joint Genres with Weather Dates")


if __name__ == "__main__":
    main()