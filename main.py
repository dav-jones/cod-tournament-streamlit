########## environment set up ##########

### import python modules
import time
import datetime
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

            d_data=[]
            d_data.append(username)
            d_data.append(match['attributes']['id'])
            d_data.append(datetime.datetime.strptime((match['metadata']['timestamp']),'%Y-%m-%dT%H:%M:%S%z') + datetime.timedelta(hours=1)) # convert time to ISO 8601 timestamp, temporary fix for 1 hour bug on deployment
            d_data.append(match['metadata']['modeName'])
            d_data.append(1)
            d_data.append(match['segments'][0]['metadata']['placement'])
            d_data.append(match['segments'][0]['stats']['kills']['value'])
            d_data.append(match['segments'][0]['stats']['deaths']['value'])
            d_data.append(match['segments'][0]['stats']['executions']['value'])

            # deal with KeyError on these data points    
            try:
                d_data.append(match['segments'][0]['stats']['objectiveBrMissionPickupTablet']['value'])
            except KeyError:
                d_data.append(0)
            try:
                d_data.append(match['segments'][0]['stats']['objectiveBrKioskBuy']['value'])
            except KeyError:
                d_data.append(0)
            try:
                d_data.append(match['segments'][0]['stats']['objectiveBrCacheOpen']['value'])
            except KeyError:
                d_data.append(0)

            # final list of list of lists with data points
            d.append(d_data)

        player_matches = pd.DataFrame(d, columns=('username','id','timestamp','gamemode','games_played','placement','kills'
                                                  ,'deaths','executions','contracts_started','shop_purchases','boxes_opened'))
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
        leaderboard.drop(['placement','kills','deaths','executions','contracts_started','shop_purchases','boxes_opened']
                         , axis=1, inplace=True)
        leaderboard['total_points'] = leaderboard['placement_points'] + leaderboard['kill_points']
        leaderboard.sort_values(['total_points'], inplace=True, ascending=False)
        leaderboard.reset_index(inplace=True, drop=True)
        leaderboard.index += 1
        return leaderboard
    
    elif scoring == 'Kills Only':

        ### other game mode - aggregate to create leaderboard
        leaderboard = tournament_matches.groupby('username', as_index=False).sum() # stop usernames becoming indices
        leaderboard.drop(['placement','deaths','executions','contracts_started','shop_purchases','boxes_opened']
                         , axis=1, inplace=True)
        leaderboard.sort_values(['kills'], inplace=True, ascending=False)
        leaderboard.reset_index(inplace=True, drop=True)
        leaderboard.index += 1
        return leaderboard
    
    elif scoring == 'Test Mode 1':

        ### other game mode - aggregate to create leaderboard
        leaderboard = tournament_matches.groupby('username', as_index=False).sum() # stop usernames becoming indices
        leaderboard.drop(['placement','kills','executions']
                         , axis=1, inplace=True)
        leaderboard['total_points'] = (leaderboard['contracts_started'] * 3) + leaderboard['shop_purchases'] + leaderboard['boxes_opened'] - (leaderboard['deaths'] * 5)
        leaderboard.sort_values(['total_points'], inplace=True, ascending=False)
        leaderboard.reset_index(inplace=True, drop=True)
        leaderboard.index += 1
        return leaderboard
   
    elif scoring == 'Test Mode 2':

        ### other game mode - aggregate to create leaderboard
        leaderboard = tournament_matches.groupby('username', as_index=False).sum() # stop usernames becoming indices
        leaderboard.drop(['placement','contracts_started','shop_purchases','boxes_opened']
                         , axis=1, inplace=True)
        leaderboard['total_points'] = (leaderboard['kills'] * 2) - leaderboard['deaths'] + (leaderboard['executions'] * 6)
        leaderboard.sort_values(['total_points'], inplace=True, ascending=False)
        leaderboard.reset_index(inplace=True, drop=True)
        leaderboard.index += 1
        return leaderboard

    else:
        st.error('There has been an error selecting a scoring system')
    
    ### end of get_leaderboard function

    
########## front end ##########    

### sidebar form components to collect tournament details
with st.sidebar.form(key ='tournament-details'):
    scoring_input = st.selectbox('Scoring system:', ['Standard','Kills Only','Test Mode 1','Test Mode 2'])
#     platform_input = st.selectbox('Platform:', ['psn','xbl'])
    gamemode_input = st.selectbox('Game mode:', ['Resurgence Duos','Resurgence Trios','Resurgence Quads'])
    date_input = st.date_input('Start date:') #, value=datetime.date(2021,7,22))
    time_input = st.time_input('Start time:') #, value=datetime.time(20,0))
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
start_time = datetime.datetime.combine(date_input, time_input).astimezone()
players = players_input.replace(' ','').split(',')
    
### main page components
st.title('Cod Tournament Builder')
st.markdown('####')
st.write('''
    - playstation and uk only - update the filters and click 'Get Results!'
    - if mid-tournament don't refresh, press R key or the filters will reset
        ''')
st.markdown('####')
with st.beta_expander('Scoring system breakdown', expanded=False):
    st.write('''
             - standard - kill = +1, placement = +5 to +1 from 1st to 5th
             - kills only - kill = +1
             - test mode 1 - death = -5, contract = +3, shop purchase = +1, box open = +1
             - test mode 2 - death = -1, kill = +2, execution = +6
            ''')
st.markdown('____')
st.header('Leaderboard: ' + scoring + ' ' + gamemode)
st.markdown('####')
st.table(get_leaderboard(scoring,platform,gamemode,duration_hours,start_time,players))