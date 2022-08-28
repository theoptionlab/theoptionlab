* Data (theoptionlab uses EOD data from the CBOE).

* Python (currently version 3, for version 2 see [previous release](https://github.com/theoptionlab/theoptionlab/releases/tag/v1.0)

* Install postgres and configure user: 
`brew install postgresql`

* Install dependencies: `pip3 install -r requirements.txt`

* Clone the repository and change directory: 
`git clone https://github.com/theoptionlab/theoptionlab.git && cd theoptionlab`

* create postgres database optiondata - only if it does not exist yet:
`psql -tc "SELECT 1 FROM pg_database WHERE datname = 'optiondata'" | grep -q 1 || psql -c "CREATE DATABASE optiondata"`

* Create database and tables with script:
`psql -d optiondata -f optiondata/db/create_db.sql`

* Adapt `private/settings_template.py` with your own settings and rename the file into settings.py

* Run `insert_fullday.py` and `free_money_scanner.py` in the free_money_scanner directory

* Insert all the data and precompute the greeks (takes a while), with or without the risk free rate (takes an even longer while)

* Once the data is in place, run your first backtest with `call_backtests.py`
