### import python modules
import time
import datetime
import http.client
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Cod Tournament Builder', layout='wide')

##### CACHED EXAMPLE #####

# @st.cache
# def test(num):
#     return num * 2
    
# num = st.sidebar.slider('Tournament duration:',min_value = 1, max_value = 5)

# st.write(test(num))


##### DYNAMIC AND CACHED #####

@st.cache
### function to build leaderboard based on selection of inputs
def get_leaderboard(platform,gamemode,duration_hours,start_time,players):

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
    tournament_matches.reset_index(drop=True, inplace=True)

    ### standard game mode - add more columns (headshots, wallbangs, guns, etc) to create other game modes
    tournament_matches.loc[tournament_matches.placement <= 5, 'placement_points'] = 6 - tournament_matches.placement
    tournament_matches.loc[tournament_matches.placement > 5, 'placement_points'] = 0                                        
    tournament_matches['kill_points'] = tournament_matches['kills']

    ### standard game mode - aggregate to create leaderboard
    leaderboard = tournament_matches.groupby('username', as_index=False).sum() # stop usernames becoming indices
    leaderboard.drop(['placement','kills'], axis=1, inplace=True)
    leaderboard['total_points'] = leaderboard['placement_points'] + leaderboard['kill_points']
    leaderboard.sort_values(['total_points'], inplace=True, ascending=False)
    return leaderboard

### sidebar form components to collect tournament details
with st.sidebar.form(key ='tournament-details'):
#     platform_input = st.selectbox('Platform:', ['psn','xbl'])
    gamemode_input = st.selectbox('Game mode:', ['Resurgence Duos','Resurgence Trios','Resurgence Quads'])
    date_input = st.date_input('Tournament start date:')
    time_input = st.time_input('Tournament start time:')
    duration_input = st.slider('Tournament duration:',min_value = 1, max_value = 5)
    players_input = st.text_input('Usernames (comma separated no spaces):', 'Dav-Jones,ws23100', max_chars = 50)
    submit_inputs = st.form_submit_button(label = 'Get Results!')

### convert tournament details into format suitable for get_leaderboard function
# platform = platform_input
platform = 'psn'
gamemode = gamemode_input
duration_hours = duration_input
start_time = datetime.datetime.combine(date_input, time_input).astimezone()
players = players_input.split(',')
    
### main page components
st.title('Cod Tournament Builder')
st.markdown('####')
st.write('''
    - playstation only - update the filters and click 'Get Results!'
    - if mid-tournament don't refresh, press R key, or the filters will reset
    - points - kill = 1, placement = 1-5 from 5th to 1st
''')
st.markdown('____')
st.header('Leaderboard')
st.markdown('####')
st.table(get_leaderboard(platform,gamemode,duration_hours,start_time,players))


##### FIXED AND NON-CACHED - DATA ERROR CHECK #####

# ### import python modules
# import time
# import datetime
# import http.client
# import json
# import pandas as pd
# import streamlit as st

# ### input variables to build leaderboard - fixed
# platform = 'psn'
# gamemode = 'Resurgence Trios'
# duration_hours = 2
# start_time = datetime.datetime.strptime('2021-07-22 20:00:00+00:00', '%Y-%m-%d %H:%M:%S%z')
# players = ['Dav-Jones','ws23100']

# ### calculate end time
# end_time = start_time + datetime.timedelta(hours = duration_hours)

# ### dataframe that collects match data for all usernames in players
# all_matches = pd.DataFrame()
# for username in players:
    
#     ### get tracker.gg json object using api
#     conn = http.client.HTTPSConnection('api.tracker.gg')
#     payload = ''
#     conn.request('GET', '/api/v2/warzone/standard/matches/' + platform + '/' + username + '?type=wz', payload)
#     res = conn.getresponse()
#     history_dict = json.loads(res.read())

#     ### parse only the match details
#     match_list = history_dict['data']['matches']

#     ### create empty list and append details for dataframe conversion
#     d = []
#     for match in match_list:
#         d.append((
#             username,
#             match['attributes']['id'],
#             ### convert time to ISO 8601 timestamp
#             datetime.datetime.strptime((match['metadata']['timestamp']), '%Y-%m-%dT%H:%M:%S%z'),
#             match['metadata']['modeName'],
#             match['segments'][0]['metadata']['placement'],
#             match['segments'][0]['stats']['kills']['value']
#         ))

#     player_matches = pd.DataFrame(d, columns=('username', 'id', 'timestamp', 'gamemode', 'placement', 'kills'))
#     all_matches = all_matches.append(player_matches)
    
# ### match details between tournament start and end times (copy() to get rid of SettingWithCopyWarning)
# tournament_matches = all_matches[(all_matches['gamemode'] == gamemode) & (all_matches['timestamp'] >= start_time) & (all_matches['timestamp'] < end_time)].copy()
# tournament_matches.reset_index(drop=True, inplace=True)

# ### standard game mode - add more columns (headshots, wallbangs, guns, etc) to create other game modes
# tournament_matches.loc[tournament_matches.placement <= 5, 'placement_points'] = 6 - tournament_matches.placement
# tournament_matches.loc[tournament_matches.placement > 5, 'placement_points'] = 0                                        
# tournament_matches['kill_points'] = tournament_matches['kills']

# ### standard game mode - aggregate to create leaderboard
# leaderboard = tournament_matches.groupby('username', as_index=False).sum() # stop usernames becoming indices
# leaderboard.drop(['placement','kills'], axis=1, inplace=True)
# leaderboard['total_points'] = leaderboard['placement_points'] + leaderboard['kill_points']
# leaderboard.sort_values(['total_points'], inplace=True, ascending=False)

# st.table(leaderboard)