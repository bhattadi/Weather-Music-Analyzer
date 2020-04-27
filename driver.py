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


#Using SQL joins to find corresponding genres for a particular date
#Using matplotlib to produce bar graphs and pie charts
# -------------- Visualization #1--------------------
def barGraph(cur, conn):
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
    plt.title('Music Genres vs Frequency')
    plt.ylabel('Frequency')
    plt.xlabel('Genres')
    plt.savefig('Genre vs Frequency Bar Graph')


# ------------------ Visualizations #2-#6 ----------------------        
def pieCharts(cur, conn):
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
        plt.title('Music Genres vs Frequency')
        plt.legend()
        plt.savefig('Genre vs Frequency Bar Graph ' + str(i))
        i += 1

# Plot weather vs genre
# Plot weather over time
# Plot time over genre

def main():

    cur, conn =  data_collection.setUpDatabase('final.db')
    barGraph(cur, conn)
    pieCharts(cur, conn)

    print("Joint Genres with Weather Dates")


if __name__ == "__main__":
    main()