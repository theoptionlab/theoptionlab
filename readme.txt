1) Data. We use EOD data from the CBOE. 

2) Python. We use version 3. 

3) Install dependencies: pip install -r requirements.txt 

4) postgres database 

5) database and tables with script in create_db_postresql.sql
$ psql -h host -d optiondata -U user -f /path/to/create_db_postresql.sql

6) adapt private/settings_template.py with your own settings and rename the file into settings.py

7) try to run insert_fullday.py and then free_money_scanner.py 

8) And then you are ready to insert all the data and precompute the greeks! 

9) Once the data is in place, run your first backtest with call_backtests.py 
