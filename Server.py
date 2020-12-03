import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import requests
import json

urlGetAllPlayers = "https://7ohqc3qz5h.execute-api.ca-central-1.amazonaws.com/default/GetAllPlayers"
queryParams = {"UserID": "0", "Rating": "1000"}

response = requests.get(urlGetAllPlayers)

gameID = 0

waitingPlayerIDs = []
matchList = {}

def connectionLoop(sock):
    while True:
        global gameID
        data, addr = sock.recvfrom(1024)
        data = str(data)
        data = data[2 : len(data) - 1]
        data = json.loads(data)
        if 'playerList' in data['cmd']:
            allPlayers = GetAllPlayers()
            message = {"cmd":'playerList', "playerList": allPlayers}
            m = json.dumps(message)
            sock.sendto(bytes(m,'utf8'), (addr[0],addr[1])) # Send the player list to the requesting client
        if 'updatePlayer' in data['cmd']:
            UpdatePlayer(data['UserID'], data['Rating'])
        if 'matchRequest' in data['cmd']:
            playerAlreadyInList = False
            # Check if the requesting player is already in the list
            for x in range(0, len(waitingPlayerIDs)):
                if waitingPlayerIDs[x] == data['UserID']:
                    playerAlreadyInList = True
            if playerAlreadyInList == False:
                waitingPlayerIDs.append(data['UserID']) # Add the player to the waiting list
                if (len(waitingPlayerIDs) >= 3) :
                    gameID += 1
                    # Send the message saying that a match is found
                    message = {"cmd": 'matchReady', "gameID": gameID, "playerIDs": [str(waitingPlayerIDs[0]), str(waitingPlayerIDs[1]), str(waitingPlayerIDs[2])]}
                    m = json.dumps(message)
                    sock.sendto(bytes(m, 'utf8'), (addr[0], addr[1]))
                    waitingPlayerIDs.remove(waitingPlayerIDs[2])
                    waitingPlayerIDs.remove(waitingPlayerIDs[1])
                    waitingPlayerIDs.remove(waitingPlayerIDs[0])

def GetPlayerRating(playerid)->str:
    urlGetPlayer = "https://w7lk0raq6l.execute-api.ca-central-1.amazonaws.com/default/GetPlayer"
    queryParams = "?UserID=" + str(playerid)
    response = requests.get(urlGetPlayer + queryParams)
    body = json.loads(response.content)
    rating = body['Rating']
    return rating

def GetAllPlayers()->list:
    response = requests.get(urlGetAllPlayers)
    body = json.loads(response.content)
    return body

def UpdatePlayer(playerID, rating):
    urlUpdatePlayer = "https://867dis29il.execute-api.ca-central-1.amazonaws.com/default/UpdatePlayer"
    queryParams = "?UserID=" + str(playerID) + "&Rating=" + str(rating)
    response = requests.post(urlUpdatePlayer + queryParams)
    body = json.loads(response.content)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(connectionLoop, (s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
