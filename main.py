### import python modules
import time
import datetime
import http.client
import json
import pandas as pd
import streamlit as st

### set page config and title
st.set_page_config(page_title='Cod Tournament')
st.title('Cod Tournament')
st.info('Make your selection and then click start to begin a tournament')
st.error('There has been an error, refresh the page to start again')
st.success('Done!')

### create selection sidebar
platform = st.sidebar.selectbox('Platform:', ['psn','xbl'])
gamemode = st.sidebar.selectbox('Game mode:', ['Resurgence Duos','Resurgence Trios','Resurgence Quads'])
date = st.sidebar.date_input('Tournament date')
start_time = st.sidebar.time_input('Start time')
end_time= st.sidebar.time_input('End time')
players = st.sidebar.text_input('Usernames (comma separated)')
st.sidebar.button('Start')

### input variables to build leaderboard
platform = 'psn'
players = ['Dav-Jones','ws23100']
gamemode = 'Resurgence Trios'
duration_hours = 2
start_time = datetime.datetime.strptime('2021-07-22 20:00:00+00:00', '%Y-%m-%d %H:%M:%S%z')

### calculate tournament end time
end_time = start_time + datetime.timedelta(hours = duration_hours)

### dataframe that collects match data for all usernames in players
all_matches = pd.DataFrame()
for username in players:

    ### get tracker.gg json object using api
    conn = http.client.HTTPSConnection('api.tracker.gg')
    payload = ''
    conn.request('GET', '/api/v2/warzone/standard/matches/' + platform + '/' + username + '?type=wz', payload)
    res = conn.getresponse()
    history_dict = json.loads(res.read())

    ### parse only the match details
    match_list = history_dict['data']['matches']

    ### create empty list and append details for dataframe conversion
    d = []
    for match in match_list:
        d.append((
            username,
            match['attributes']['id'],
            ### convert time to ISO 8601 timestamp
            datetime.datetime.strptime((match['metadata']['timestamp']), '%Y-%m-%dT%H:%M:%S%z'),
            match['metadata']['modeName'],
            match['segments'][0]['metadata']['placement'],
            match['segments'][0]['stats']['kills']['value']
        ))

    player_matches = pd.DataFrame(d, columns=('username', 'id', 'timestamp', 'gamemode', 'placement', 'kills'))
    all_matches = all_matches.append(player_matches)
    
### match details between tournament start and end times (copy() to get rid of SettingWithCopyWarning)
tournament_matches = all_matches[(all_matches['gamemode'] == gamemode) & (all_matches['timestamp'] >= start_time) & (all_matches['timestamp'] < end_time)].copy()

### calculate points based on placement and kills for each match
tournament_matches.loc[tournament_matches.placement <= 5, 'placement_points'] = 6 - tournament_matches.placement
tournament_matches.loc[tournament_matches.placement > 5, 'placement_points'] = 0                                        
tournament_matches['kill_points'] = tournament_matches['kills']

### aggregate points and rank usernames - ranking not working
leaderboard = tournament_matches.groupby('username').sum()
leaderboard.drop(['placement','kills'], axis=1, inplace=True)
leaderboard['total_points'] = leaderboard['placement_points'] + leaderboard['kill_points']
leaderboard.sort_values('total_points', ascending = True)
leaderboard.reset_index(inplace=True)
leaderboard.insert(1, 'rank', leaderboard.index.values + 1)

st.table(leaderboard)