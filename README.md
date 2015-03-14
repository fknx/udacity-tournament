# udacity-tournament

To run this project you must create an PostgreSQL database called **tournament**. In this database, you need to create the tables and views as specified in the **tournament.sql** file.

You can test the project by running the tests defined in **tournament_test.py** file. The tests have been slightly modified to support draw games. Additionally, three more tests have been added to test odd pairings, draw games and the correct ordering of the standings (two or more players with the same amount of wins are ordered accordings to their opponents' wins (OMW)).

The functions in the **tournament.py** file have been adopted to support multiple tournaments. Most of the function now have a **tournamentID** parameter which defaults to one, so that no adjustments had to be made to the tests. This is also the reason why a tournamentID may be passed to the **createTournament** function although the Tournament-Table  uses an auto-incrementing primary key. This way, always a tournament with id *one* can be created before the tests are run.

New players can optionally be added directly to a tournament by specifying the **tournamentID** parameter. Existing players can be added to a tournament by calling the **addPlayerToTournament** function and passing the tournament's and the player's id as parameters.

In case of a bye the lucky player will not be included in the pairings. Instead, the match will be reported directly.