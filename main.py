########## environment set up ##########

### import python modules
import time
import datetime
import pytz
import http.client
import json
import pandas as pd
import streamlit as st

### set web page config
st.set_page_config(page_title='Cod Tournament Builder', layout='wide')


########## back end ##########

### cache input so filters don't refresh
@st.cache()

### function to build leaderboard based on selection of inputs
def get_leaderboard(scoring,platform,gamemode,duration_hours,start_time,players):

    ### calculate end time
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
        match_list = next(iter(history_dict.values()))['matches']

        ### create empty list and append details for dataframe conversion
        d = []
        for match in match_list:
            d.append((
                username,
                match['attributes']['id'],
                datetime.datetime.strptime((match['metadata']['timestamp']), '%Y-%m-%dT%H:%M:%S%z'), # convert time to ISO 8601 timestamp
                match['metadata']['modeName'],
                1,
                match['segments'][0]['metadata']['placement'],
                match['segments'][0]['stats']['kills']['value']
            ))

        player_matches = pd.DataFrame(d, columns=('username', 'id', 'timestamp', 'gamemode','games_played','placement', 'kills'))
        all_matches = all_matches.append(player_matches)

    ### match details between tournament start and end times (copy() to get rid of SettingWithCopyWarning)
    tournament_matches = all_matches[(all_matches['gamemode'] == gamemode) & (all_matches['timestamp'] >= start_time) & (all_matches['timestamp'] < end_time)].copy()
    tournament_matches.reset_index(drop=True, inplace=True)

    ### calculate points based on game mode type
    if scoring == 'Standard':
        
        ### standard game mode - calculate points
        tournament_matches.loc[tournament_matches.placement <= 5, 'placement_points'] = 6 - tournament_matches.placement
        tournament_matches.loc[tournament_matches.placement > 5, 'placement_points'] = 0                                        
        tournament_matches['kill_points'] = tournament_matches['kills']

        ### standard game mode - aggregate to create leaderboard
        leaderboard = tournament_matches.groupby('username', as_index=False).sum() # stop usernames becoming indices
        leaderboard.drop(['placement','kills'], axis=1, inplace=True)
        leaderboard['total_points'] = leaderboard['placement_points'] + leaderboard['kill_points']
        leaderboard.sort_values(['total_points'], inplace=True, ascending=False)
        leaderboard.reset_index(inplace=True, drop=True)
        leaderboard.index += 1
        return leaderboard
    
    elif scoring == 'Kills Only':

        ### other game mode - aggregate to create leaderboard
        leaderboard = tournament_matches.groupby('username', as_index=False).sum() # stop usernames becoming indices
        leaderboard.drop(['placement'], axis=1, inplace=True)
        leaderboard.sort_values(['kills'], inplace=True, ascending=False)
        leaderboard.reset_index(inplace=True, drop=True)
        leaderboard.index += 1
        return leaderboard
    
    else:
        st.error('There has been an error selecting a scoring system')
    
    ### end of get_leaderboard function

    
########## front end ##########    

### sidebar form components to collect tournament details
with st.sidebar.form(key ='tournament-details'):
    scoring_input = st.selectbox('Scoring system:', ['Standard','Kills Only'])
#     platform_input = st.selectbox('Platform:', ['psn','xbl'])
    gamemode_input = st.selectbox('Game mode:', ['Resurgence Duos','Resurgence Trios','Resurgence Quads'])
    date_input = st.date_input('Start date:', value=datetime.date(2021,7,22))
    time_input = st.time_input('Start time:', value=datetime.time(20,0))
    duration_input = st.slider('Duration:', value=2, min_value = 1, max_value = 5)
    players_input = st.text_input('Usernames:', value='Dav-Jones, ws23100', max_chars = 100, help='Comma separated')
    st.markdown('####')
    submit_inputs = st.form_submit_button(label='Get Results!')

### convert tournament details into format suitable for get_leaderboard function
scoring = scoring_input
# platform = platform_input
platform = 'psn'
gamemode = gamemode_input
duration_hours = duration_input
start_time = datetime.datetime.combine(date_input, time_input).astimezone(pytz.timezone('Europe/London'))
players = players_input.replace(' ','').split(',')
    
### main page components
st.title('Cod Tournament Builder')
st.markdown('####')
st.write('''
    - playstation only - update the filters and click 'Get Results!'
    - if mid-tournament don't refresh, press R key or the filters will reset
        ''')
st.markdown('####')
with st.beta_expander('Scoring system breakdown', expanded=False):
    st.write('''
             - standard - kill = 1, placement = 1 - 5 from 5th to 1st
             - kills only - kill = 1
            ''')
st.markdown('____')
st.header('Leaderboard: ' + scoring + ' ' + gamemode)
st.markdown('####')
st.table(get_leaderboard(scoring,platform,gamemode,duration_hours,start_time,players))

st.write(start_time)