import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import requests
import json
import sys
import math

HOST = '3.96.206.57'
#HOST = '127.0.0.1'
PORT = 12345

gamesPlayed = 0
playerList = {}

currentPlayers = [{'UserID': '-1', 'Rating': '0'}, {'UserID': '-1', 'Rating': '0'}, {'UserID': '-1', 'Rating': '0'}]

def ConnectionLoop(sock):
    global playerList
    global gamesPlayed
    while True:
        data, addr = sock.recvfrom(1024)
        data = str(data)
        data = data[2 : len(data) - 1]
        if 'playerList' in data:
            # Receive and update the player list
            message = json.loads(data)
            playerList = list(message['playerList'])
        if 'matchReady' in data:
            message = json.loads(data)
            gamesPlayed += 1
            print("\nGame ID: " + str(message['gameID']))
            
            for index in range(0, len(playerList)):
                if playerList[index]['UserID'] == message['playerIDs'][0]:
                    currentPlayers[0] = {'UserID': playerList[index]['UserID'], 'Rating': playerList[index]['Rating']}
                    print("Player " + currentPlayers[0]['UserID'] + " is ready!")
                elif playerList[index]['UserID'] == message['playerIDs'][1]:
                    currentPlayers[1] = {'UserID': playerList[index]['UserID'], 'Rating': playerList[index]['Rating']}
                    print("Player " + currentPlayers[1]['UserID'] + " is ready!")
                elif playerList[index]['UserID'] == message['playerIDs'][2]:
                    currentPlayers[2] = {'UserID': playerList[index]['UserID'], 'Rating': playerList[index]['Rating']}
                    print("Player " + currentPlayers[2]['UserID'] + " is ready!")

            winner = random.randint(0, 2)
            print("Winner is player " + currentPlayers[winner]['UserID'] + "\n")
            UpdatePlayer(sock, currentPlayers[winner]['UserID'], str(float(currentPlayers[winner]['Rating']) + 10))

            k = 20.0
            rA = float(currentPlayers[winner]['Rating'])
            rB1 = float(currentPlayers[(winner + 1) % 3]['Rating'])
            rB2 = float(currentPlayers[(winner + 2) % 3]['Rating'])

            expectedScoreAB1 = 1.0 / (1.0 + math.pow(10.0, (rB1-rA) / 400.0))
            expectedScoreB1A = 1.0 / (1.0 + math.pow(10.0, (rA-rB1) / 400.0))
            expectedScoreAB2 = 1.0 / (1.0 + math.pow(10.0, (rB2-rA) / 400.0))
            expectedScoreB2A = 1.0 / (1.0 + math.pow(10.0, (rA-rB2) / 400.0))

            # Winner: R'A = RA + K * (1 - EA)
            newRA = rA + k * (2 - expectedScoreAB1 - expectedScoreAB2)
            # Losers: R'B = RB + K * (0 - EB)
            newRB1 = rB1 - k * expectedScoreB1A
            newRB2 = rB2 - k * expectedScoreB2A

            # Update data on the client / server
            for index in range(0, len(playerList)):
                if playerList[index]['UserID'] == currentPlayers[winner]['UserID']:
                    playerList[index]['Rating'] = str(newRA) # Update data on the client
                    print("Player " + playerList[index]['UserID'] + "'s new rating: " + str(newRA) + " ( +" + str(newRA - rA) + " )")
                elif playerList[index]['UserID'] == currentPlayers[(winner + 1) % 3]['UserID']:
                    playerList[index]['Rating'] = str(newRB1)
                    print("Player " + playerList[index]['UserID'] + "'s new rating: " + str(newRB1) + " ( -" + str(rB1 - newRB1) + " )")
                elif playerList[index]['UserID'] == currentPlayers[(winner + 2) % 3]['UserID']:
                    playerList[index]['Rating'] = str(newRB2)
                    print("Player " + playerList[index]['UserID'] + "'s new rating: " + str(newRB2) + " ( -" + str(rB2 - newRB2) + " )")

                UpdatePlayer(sock, playerList[index]['UserID'], playerList[index]['Rating']) # Update data on the server

            print("Game " + str(message['gameID']) + " is over.\n")


def GameLoop(sock):
    global numberOfGames
    global gamesPlayed
    logFile = open('Log.txt', 'w')
    sys.stdout = logFile
    while gamesPlayed < numberOfGames:
        if len(playerList) > 0:
            # Send a message to the server to tell the server that a new player is requesting a game
            randomPlayerIndex = random.randint(0, len(playerList) - 1)
            message = {"cmd": 'matchRequest', "UserID": playerList[randomPlayerIndex]['UserID']}
            m = json.dumps(message)
            print("Player " + playerList[randomPlayerIndex]['UserID'] + " (Rating: " + playerList[randomPlayerIndex]['Rating'] + ") is waiting for a match.")
            sock.sendto(bytes(m,'utf8'), (HOST, PORT)) 
        time.sleep(0.5)
    logFile.close()
    sys.exit()


def RequestPlayerList(s):
    # Send a message to the server to request the player list
    message = {"cmd": 'playerList'}
    m = json.dumps(message)
    s.sendto(bytes(m,'utf8'), (HOST, PORT))

def UpdatePlayer(s, playerID, newRating):
    message = {"cmd":'updatePlayer', "UserID": playerID, "Rating": newRating}
    m = json.dumps(message)
    s.sendto(bytes(m,'utf8'), (HOST, PORT))

def main():
   global numberOfGames
   numGames = input("Please enter the number of games: ")
   numberOfGames = int(numGames)

   port = 12346
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(GameLoop, (s,))
   start_new_thread(ConnectionLoop, (s,))

   RequestPlayerList(s)

   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
