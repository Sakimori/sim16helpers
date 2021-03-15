import json, os
import onomancer as ono
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

data_dir = "data"
creds_filename = os.path.join(data_dir, "credentials.json")
token_filename = os.path.join(data_dir, "sheets_token.json")

class perennial(object):
    pitcher_max = 3
    batter_max = 12

    def __init__(self, channel, teams_dic, teams, rounds):
        self.channel = channel
        self.teams_dic = teams_dic
        self.teams_order = teams
        self.counter = 0
        self.rounds = rounds
        self.sheets = None
        self.sheet_id = None

    def current_drafter(self):
        """
        returns team, user
        """
        if self.counter < len(self.teams_order) * self.rounds:
            team = self.teams_order[self.counter % len(self.teams_order)]
            return team, self.teams_dic[team]
        else:
            return False, None

    def connect(self, sheet_id):
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = None

        if os.path.exists(token_filename):
            creds = Credentials.from_authorized_user_file(token_filename, scope)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_filename, scope)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_filename, 'w') as token:
                token.write(creds.to_json())

        service = build("sheets", "v4", credentials=creds)
        self.sheets = service.spreadsheets()
        self.sheet_id = sheet_id


    def check_for_name(self, search_name, s_range="Sheet1!A2:F"):
        if self.sheets is None:
            return False

        result = self.sheets.values().get(spreadsheetId=self.sheet_id, range=s_range).execute()
        names_rows = result.get("values", [])
        if not names_rows:
            return False
        
        for i in range(0, len(names_rows)):
            try:
                if names_rows[i][0] == search_name:
                    return True
            except IndexError:
                break
        return False

    def find_name(self, search_name, s_range="Sheet1!A2:F"): #also finds names already taken
        if self.sheets is None:
            return False, None

        result = self.sheets.values().get(spreadsheetId=self.sheet_id, range=s_range).execute()
        names_rows = result.get("values", [])
        if not names_rows:
            return False, None
        
        for i in range(0, len(names_rows)):
            try:
                if names_rows[i][0] == search_name:
                    return names_rows[i], i+2
            except IndexError:
                True
        return False, None

    def available_names_index(self, range="Sheet1!A2:F"):
        if self.sheets is None:
            return -1

        result = self.sheets.values().get(spreadsheetId=self.sheet_id, range=range).execute()
        names_rows = result.get("values", [])
        if not names_rows:
            return -1
        index = 0
        for name in names_rows:
            try:
                if name[0] is not None:
                    index += 1
            except IndexError:
                break
        return index + 2

    def end_name_index(self, range="Sheet1!A2:F"):
        if self.sheets is None:
            return -1

        result = self.sheets.values().get(spreadsheetId=self.sheet_id, range=range).execute()
        names_rows = result.get("values", [])
        if not names_rows:
            return -1
        index = 0
        removed = False
        for name in names_rows:
            try:
                if name[0] is not None:
                    index += 1
            except IndexError:
                if removed:
                    break
                else:
                    removed = not removed
        return index + 2

    def add_available(self, add_name, range="Sheet1!A"):
        player_row, row_number = self.find_name(add_name)
        if player_row:
            self.remove_taken(add_name)
        else:
            player_row = self.player_row(ono.get_stats(add_name))
        old_index_start = self.available_names_index() 
        self.slide_sheet(old_index_start+1, 1)

        new_name_row = range + str(old_index_start) + ":F" + str(old_index_start)
        new_body = {
            "range": new_name_row,
            "values": [player_row]}
        self.sheets.values().update(spreadsheetId=self.sheet_id, range=new_name_row, valueInputOption="RAW", body=new_body).execute()
        return True

    def remove_available(self, remove_name, range="Sheet1!A"):
        player_row, row_number = self.find_name(remove_name)
        if not player_row or not self.check_for_name(remove_name):
            return False

        self.sheets.values().clear(spreadsheetId=self.sheet_id, range=(range+str(row_number)+":F"+str(row_number))).execute()
        self.slide_sheet(row_number+1, -1)

        self.add_taken(player_row, name_is_row = True)
        

    def add_taken(self, add_name, range="Sheet1!A", name_is_row = False):
        end_index = self.end_name_index()
        end_range = range + str(end_index+1) + ":F"
        append_body = {"range": end_range}
        if name_is_row:
            append_body["values"] = [add_name]
        else:
            append_body["values"] = [self.player_row(ono.get_stats(add_name))]

        self.sheets.values().update(spreadsheetId=self.sheet_id, range=end_range, valueInputOption="RAW", body=append_body).execute()

    def remove_taken(self, remove_name, range="Sheet1!A"):
        player_row, row_number = self.find_name(remove_name)

        self.sheets.values().clear(spreadsheetId=self.sheet_id, range=(range+str(row_number)+":F"+str(row_number))).execute()
        self.slide_sheet(row_number+1, -1)

    def next_team(self):
        self.counter += 1
        try:
            return self.teams_dic[self.teams_order[self.counter-1]]
        except:
            return False

    def player_row(self, player_stats):
        statsum = player_stats["batting_stars"] + player_stats["pitching_stars"] + player_stats["baserunning_stars"] + player_stats["defense_stars"]
        return [player_stats["name"], player_stats["batting_stars"], player_stats["pitching_stars"], player_stats["baserunning_stars"], player_stats["defense_stars"], statsum]

    def slide_sheet(self, rownum, slide_offset, range="Sheet1!A"):
        old_range = range + str(rownum)+":F"
        result = self.sheets.values().get(spreadsheetId=self.sheet_id, range=old_range).execute()
        old_names_rows = result.get("values", [])
        self.sheets.values().clear(spreadsheetId=self.sheet_id, range=old_range).execute()

        old_range = range + str(rownum+slide_offset)+":F"
        old_body = {"range": old_range,
                    "values": old_names_rows
                   }
        self.sheets.values().update(spreadsheetId=self.sheet_id, range=old_range, valueInputOption="RAW", body=old_body).execute()

    def drafted(self, user_id, drafted_player, outgoing_player = None):
        return None