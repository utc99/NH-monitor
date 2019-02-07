# NH-monitor
# Task for final project

Nicehash.com is a mining platform, while users are mining cryptocurrency, stats are being displayed
more or less in real time on their webpage.
The problem I had is that it only displays current workers(mining pc's),and if some stops mining, you have to remember
how many you had, and search for it in site, double check if it's missing, and only then you know which one needs to be fixed.
I created an app that uses NH api's to collect data, show it in the page, and keep history of it. So when one of the miners are
missing, you can clearly see it.

Initial test user: tester1 - tester1

Use cases:
*Register an new account
*Login
*Switch between wallets
*Edit user settings
*Add wallet addresses
*Change user email
*Change displayed currency
*Change password
*View workers, stats, worker activity(green - active, red - inactive up to 10 min, grey - inactive more than 10 min)
*Remove inactive workers

Known bugs:

*If the user has a miner, which mines more than one algorythm of the same type (eg. Cryptonight), and names both workers
the same(eg. Machine1), only one will be displayed. NH API do not give data that would let server to distinguish between those two
for history keeping, while we need to know which one is which if we track the history

*For some reason after a while, this application works slower and slower, first rounds takes 3-6 secs, starts overloading after 20 minutes and bumps up to 300+ secs over 24hrs.
Memmory size do not increase, all CPU gets used up, maybe it's an Cloud 9 IDE trying to save a working power, or some kind of cpu leak,
didn't found solutions for that at the momment.

Future improvements:

*IF a worker is lost for a certain amount of time, send an email notification.
(Did a testings with gmail email sending, works good, if i'll continue to use NH, I'm going to implament it later)

*Minor fixes


