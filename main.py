from flask import Flask, request

import time
import datetime
import http.client
import json
import pandas as pd

app = Flask(__name__)

### example time flask function
@app.route('/time')
def get_current_time():
    return {'time': datetime.datetime.now().astimezone().replace(microsecond=0)}

@app.route('/api/query', methods = ['POST'])
def get_query_from_react():
    ### get data from request body, set variables
    data = request.get_json()

    players = ['Dav-Jones','MonsieurOmlette','connarm23']
    gamemode = 'Resurgence Quads'
    duration_hours = 2
    start_time = datetime.datetime.strptime('2021-03-20 00:00:00+00:00', '%Y-%m-%d %H:%M:%S%z')

    platform = data['platform']
    # players = data['players']
    # gamemode = data['gamemode']
    # duration_hours = data['duration_hours']
    # start_time = data['start_time']

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

    ### aggregate points and rank usernames
    leaderboard = tournament_matches.groupby('username').sum()
    leaderboard.drop(['placement','kills'], axis=1, inplace=True)
    leaderboard['total_points'] = leaderboard['placement_points'] + leaderboard['kill_points']
    leaderboard.sort_values(by=['total_points','kill_points'])
    leaderboard.reset_index(inplace=True)
    leaderboard.insert(1, 'rank', leaderboard.index.values + 1)

    ### convert to json
    json_leaderboard = json.dumps(json.loads(leaderboard.to_json(orient='records')), indent=4)

    return json_leaderboard