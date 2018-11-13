"""
Shows basic usage of the Sheets API. Prints values from a Google Spreadsheet.
"""
# @author: Catherine Hu, James Zhu, Carolyn Wang (for add_users)
from apiclient.discovery import build
from oauth2client import file, client, tools

import httplib2
import os
import random
import string

import argparse
flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/admin-directory_v1-python-quickstart.json
SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.group.member',
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/admin.directory.group'
]
CLIENT_SECRET_FILE = 'client_secret.json'
CREDENTIALS_FILE = 'cred.json'
APPLICATION_NAME = 'hknweb'

# Elections spreadsheet
SPREADSHEET_ID = '1wnZfinKlVUsdXaz-W0ACnb_G7HFfDVlpudUSGpA1GrM'
OFFICER_SHEET_ID = '682750401'
MEMBER_SHEET_ID = '2002556869'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.getcwd()
    credential_path = os.path.join(credential_dir, CREDENTIALS_FILE)

    store = file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    print("ran get_credentials")
    return credentials


def get_election_data(credentials, range):
    # Setup the Sheets API
    http = credentials.authorize(httplib2.Http())
    service = build('sheets', 'v4', http=http)

    # Call the Sheets API
    result = service.spreadsheets().values() \
        .get(spreadsheetId=SPREADSHEET_ID, range=range) \
        .execute()
    print("ran get_election_data")
    return result.get('values', [])


# def get_users(credentials):
#     """Gets the first 10 users in the domain, by email."""
#     http = credentials.authorize(httplib2.Http())
#     service = build('admin', 'directory_v1', http=http)

#     print('Getting the first 10 users in the domain')
#     results = service.users() \
#         .list(customer='my_customer', maxResults=10, orderBy='email') \
#         .execute()
#     print("ran get_users")
#     return results.get('users', [])

def add_users(credentials, election_data):
    #create new account for users, by Carolyn Wang, modified by Catherine Hu
    http = credentials.authorize(httplib2.Http())
    service = build('admin', 'directory_v1', http=http)
    if election_data:
        for row in election_data:
            firstName = row[1].strip().capitalize()
            lastName = row[2].strip().capitalize()
            randomPass = ''.join(random.choice(string.ascii_letters) for m in range(8)) + '1!'
            print(randomPass)
            email = row[3] + '@hkn.eecs.berkeley.edu'
            #TODO: get rid of spaces, capitalize names, error catching
            body = {'name': {'familyName': lastName, 'givenName': firstName}, 'password': randomPass, 'primaryEmail': email, 'changePasswordAtNextLogin': True}
            if service.users().get(userKey=email):
                continue
            result = service.users().insert(body=body).execute()
            print(result)
    print("ran add_users")
    return

def add_user_to_group(credentials, user, groupKey):
    #add USER to a mail list GROUP
    http = credentials.authorize(httplib2.Http())
    service = build('admin', 'directory_v1', http=http)

    print("ran add_user_to_group")
    body = {
        'email': user + '@hkn.eecs.berkeley.edu',
        'role': 'MEMBER',
    }
    print(body['email'])
    if service.members().hasMember(groupKey=groupKey, memberKey=body.get('email')):
        return 
    return service.members().insert(groupKey=groupKey + '@hkn.eecs.berkeley.edu', body=body).execute()

def add_officers_to_committes(credentials):
    # add all officers to committees, read from spreadsheet column F
    election_data = get_election_data(credentials, "A2:H5")
    # users = get_users(credentials)
    user_committee = []

    print(election_data)
    if election_data:
        for i in range(0, len(election_data)):
            if len(election_data[i]) < 6:
                continue
            committee = election_data[i][5][:-1]
            user_committee.append((election_data[i][3], committee))
            #user_committee[users[i]] = committee

    for user, committee in user_committee:
        result = add_user_to_group(credentials, user, committee+'-officers')
        print(result)

    print("ran add_officers_to_committes")

def add_members_to_committes(credentials):
    # add all members to committes, read from spreadsheet column G
    election_data = get_election_data(credentials, "A2:H5")
    #users = get_users(credentials)
    mailing_lists = []

    if election_data:
        for i in range(0, len(election_data)):
            if len(election_data[i]) < 7:
                continue
            row = election_data[i]
            mailing = row[6][:-1].split('@, ')
            mailing_lists.append((election_data[i][3], mailing))
            #mailing_lists[users[i]] = mailing_list

    for user, mailing_list in mailing_lists:
        for committee in mailing_list:
            add_user_to_group(credentials, user, committee)
            print('added ' + user + ' to ' + committee)
    print("ran add_members_to_committes")

def add_all_to_committes():
    # add all users to their committees and groups
    credentials = get_credentials()
    add_officers_to_committes(credentials)
    add_members_to_committes(credentials)
    print("ran add_all_to_committes")

credentials = get_credentials()
election_data = get_election_data(credentials, "A2:H5")
add_users(credentials, election_data)
add_all_to_committes()

"""
def main():
    Shows basic usage of the Google Admin SDK Directory API.

    Creates a Google Admin SDK API service object and outputs a list of first
    10 users in the domain.
    
    credentials = get_credentials()
    election_data = get_election_data(credentials)
    users = get_users(credentials)

    print('Position, Officers')
    if election_data:
        for row in election_data:
            # Print columns A and E, which correspond to indices 0 and 4.
            print('{}, {}'.format(row[0], row[1:]))

    print('Users:')
    for user in users:
        print(user['primaryEmail'].split('@')[0])
        # print('{0} ({1})'.format(user['primaryEmail'], user['name']['fullName']))


if __name__ == '__main__':
    main()
"""