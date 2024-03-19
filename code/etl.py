import os
import glob
import psycopg2
import pandas as pd 
from sql_queries import *

def process_song_data(cur, filepath):
    #read song file
    df = pd.read_json(filepath, lines=True)
    
    #insert data into song table
    song_data = df[["song_id", "title", "artist_id", "year", "duration"]].values[0]
    cur.execute(song_table_insert, song_data)
    
    #insert data into artist table
    artist_data = df[["artist_id", "artist_name", "artist_location", "artist_latitude", "artist_longitude"]].values[0]
    cur.execute(artist_table_insert, artist_data)   

def process_log_data(cur, filepath):
    #read log file
    df = pd.read_json(filepath, lines=True)
    
    #filter data by NextSong action
    df = df[df['page'] == 'NextSong']
    
    #convert datatype of timestampt column to time
    t = pd.to_datetime(df['ts'], unit='ms')
    
    #insert data into time table
    time_data = (t, t.dt.hour, t.dt.day, t.dt.isocalendar().week, t.dt.month, t.dt.year, t.dt.weekday)
    column_labels = ('timestamp', 'hour', 'day', 'week of year', 'month',' year', 'weekday')
    time_dict = dict(zip(column_labels, time_data))
    time_df = pd.DataFrame.from_dict(time_dict) 
    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))
    
    #insert data into user table
    user_df = df[['userId', 'firstName', 'lastName', 'gender', 'level']]
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)
    
    #get and insert data into songplay table
    for index, row in df.iterrows():
        
        #get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None
        
        #insert data into songplay table
        songplay_data = (time_df.timestamp[index], row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)

def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))

def main():
    conn = psycopg2.connect("host=localhost dbname=sparkifydb user=postgres password=hoanguyen204")
    cur = conn.cursor()
    
    process_data(cur, conn, filepath='data/song_data', func=process_song_data)
    process_data(cur, conn, filepath='data/log_data', func=process_log_data)

    conn.close()

if __name__ == "__main__":
    main()

