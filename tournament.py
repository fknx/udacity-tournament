#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import time
import psycopg2
from random import shuffle

def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")

def deleteMatches():
    """Remove all the match records from the database."""
    db = connect()
    c = db.cursor()

    c.execute("DELETE FROM matches")
    db.commit()
    db.close()

def deletePlayers():
    """Remove all the player records from the database."""
    deleteTournamentPlayers()

    db = connect()
    c = db.cursor()

    c.execute("DELETE FROM players;")
    db.commit()
    db.close()

def deleteTournamentPlayers():
    """Remove all the tournament player records from the database."""
    db = connect()
    c = db.cursor()

    c.execute("DELETE FROM tournament_players;")
    db.commit()
    db.close()

def deleteTournaments():
    """Remove all the tournaments from the database."""
    db = connect()
    c = db.cursor()

    c.execute("DELETE FROM tournaments;")
    db.commit()
    db.close()

def countPlayers():
    """Returns the number of players currently registered."""
    db = connect()
    c = db.cursor()

    c.execute("SELECT count(*) from players;")
    rows = c.fetchall()

    db.close()

    return int(rows[0][0])

def createTournament(name, tournamentID = None):
    """Creates a new tournament.

    Args:
      name: the tournament's name
      tournamentID: the tournament's id (optional)
    """
    db = connect()
    c = db.cursor()

    if tournamentID is None:
        c.execute("INSERT INTO tournaments VALUES (DEFAULT, %s);", (name, ))
    else:
        c.execute("INSERT INTO tournaments VALUES (%s, %s);", (tournamentID, name))

    db.commit()
    db.close()


def registerPlayer(name, tournamentID = 1):
    """Adds a player to the tournament database and optionally adds him to a tournament.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
      tournamentID: the id of the tournament the player shall be added to (optional)
    """
    db = connect()
    c = db.cursor()

    c.execute("INSERT INTO players VALUES (DEFAULT, %s);", (name, ))

    if tournamentID is not None:
        c.execute("SELECT currval(pg_get_serial_sequence('players', 'id'));")
        playerID = int(c.fetchall()[0][0])

        c.execute("INSERT INTO tournament_players VALUES (%s, %s, DEFAULT)", (tournamentID, playerID))

    db.commit()
    db.close()

def addPlayerToTournament(tournamentID, playerID):
    """Adds an existing player to a tournament.

    Args:
      tournamentID: the id of the tournament
      playerID: the id of the player to be added to the tournament
    """
    db = connect()
    c = db.cursor()

    c.execute("INSERT INTO tournament_players VALUES (%s, %s, DEFAULT)", (tournamentID, playerID))

    db.commit()
    db.close()

def playerStandings(tournamentID = 1):
    """Returns a list of the players and their win records, sorted by wins.

    In case there is a tie, the players are sorted by the number of wins of their opponents (omw).

    Args:
      tournamentID: the id of the tournament for that the player standings shall be returned

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    db = connect()
    c = db.cursor()

    c.execute("SELECT PlayerID, PlayerName, Wins, Games FROM player_stats WHERE TournamentID = %s" , (tournamentID, ))
    rows = c.fetchall()

    db.close()

    l = list()

    for row in rows:
        l.append((int(row[0]), row[1], int(row[2]), int(row[3])))
        
    return l

def playerStats(tournamentID = 1):
    """Returns a list containing tuples with the player stats.

    Args:
      tournamentID: the id of the tournament

    Returns:
      A list of tuples, each of which contains (PlayerID, PlayerName, Games, Wins, OMW)
        PlayerID: the id of the player
        PlayerName: the name of the player
        Games: the number of games (matches) the player has player
        Wins: the number of wins the player has achieved
        OMW: the number of wins the player's opponents have achieved
    """
    db = connect()
    c = db.cursor()

    c.execute("SELECT * FROM player_stats WHERE TournamentID = %s;", (tournamentID, ))
    rows = c.fetchall()

    db.close()

    return [(int(row[1]), row[2], int(row[3]), int(row[4]), int(row[5])) for row in rows]

def reportMatch(firstPlayer, secondPlayer, winner, tournamentID = 1):
    """Records the outcome of a single match between two players.

    Args:
      firstPlayer:   the id of the first player
      secondPlayer:  the id of the second player
      winner:        the id of the winner (or None in case of a draw)
      tournamentID:  the id of the matche's tournament
    """
    db = connect()
    c = db.cursor()

    c.execute("INSERT INTO matches VALUES (DEFAULT, %s, %s, %s, %s);", (tournamentID, firstPlayer, secondPlayer, winner))
    db.commit()
    db.close()

def swissPairings(tournamentID = 1):
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Args:
      tournamentID: the ID of the tournament the pairings shall be found for

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    standings = playerStandings(tournamentID)

    if len(standings) % 2 != 0:
        # there is an odd amount of players
        players = playersWithoutBye()
        shuffle(players)

        luckyPlayer = players.pop()
        setBye(luckyPlayer[0])

        # directly report the match and remove the lucky player from the standings
        reportMatch(luckyPlayer[0], None, luckyPlayer[0])
        standings = [player for player in standings if player[0] != luckyPlayer[0]]

    l = list()

    while len(standings) >= 2:
        firstPlayer = standings.pop(0)
        secondPlayer = standings.pop(0)

        l.append((firstPlayer[0], firstPlayer[1], secondPlayer[0], secondPlayer[1]))

    return l

def playersWithoutBye(tournamentID = 1):
    """Returns a list of player ids which did not have a bye in this tournament.

    Args:
      tournamentID: the id of the tournament
    """
    db = connect()
    c = db.cursor()

    c.execute("""SELECT PlayerID, Name FROM tournament_players
                 INNER JOIN players ON tournament_players.PlayerID = players.ID
                 WHERE HadBye = 0 AND TournamentID = %s;""", (tournamentID, ))
    rows = c.fetchall()

    db.close()

    return [(int(row[0]), row[1]) for row in rows]

def setBye(playerID, tournamentID = 1):
    """Sets HadBye to one for the given player.

    Args:
      playerID: the id of the player which just used a bye
      tournamentID: the id of the tournament
    """
    db = connect()
    c = db.cursor()

    c.execute("UPDATE tournament_players SET HadBye = 1 WHERE TournamentID = %s AND PlayerID = %s;", (tournamentID, playerID))
    db.commit()

    db.close()
