1) Data (theoptionlab uses EOD data from the CBOE).

2) Python (currently version 3, for version 2 see previous release: https://github.com/theoptionlab/theoptionlab/releases/tag/v1.0)

3) Install dependencies: pip3 install -r requirements.txt 

4) postgres database

5) database and tables with script in create_db.sql
psql -h host -d optiondata -U user -f /path/to/create.sql

6) adapt private/settings_template.py with your own settings and rename the file into settings.py

7) try to run insert_fullday.py and free_money_scanner.py 

8) And then you are ready to insert all the data and precompute the greeks (takes a while), with or without the risk free rate (takes an even longer while)! 

9) Once the data is in place, run your first backtest with call_backtests.py 
