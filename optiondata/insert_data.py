import zipfile
from os import listdir
from os.path import isfile, join
import pandas
import numpy as np
from sqlalchemy import create_engine
import os 
import MySQLdb
from private import settings


def insert(underlying):
    
    print "insert: " + str(underlying) 
    print 
    
    engine = create_engine("mysql+mysqldb://" + settings.db_username + ":" + settings.db_password + "@localhost/optiondata")
    table = 'optiondata'
    
    path_to_data_folder = settings.path_to_data_folder
    tempbasepath = settings.tempbasepath
    
    unzippedpath = "" 
    counter = 0 
    
    onlyfiles = [f for f in listdir(path_to_data_folder) if isfile(join(path_to_data_folder, f))]
    for datafile in onlyfiles: 

        if datafile.endswith(".zip"): 

            index = datafile.index('_') + 1
            datestring = datafile[index : (index + 10)]
            
            db = MySQLdb.connect(host="localhost", user=settings.db_username, passwd=settings.db_password, db="optiondata") 
            cur2 = db.cursor()
            query = "SELECT EXISTS(SELECT 1 FROM optiondata WHERE quote_date = '" + datestring + "' AND underlying_symbol = '" + underlying + "')"
            cur2.execute(query)
            row = cur2.fetchone()
            
            if (row[0] == 0):
                
                counter += 1
                print str(counter) + ": " + str(datafile) 
                  
                datafilepath = path_to_data_folder + datafile
                archive = zipfile.ZipFile(datafilepath)
          
                for ffile in archive.namelist():
                    archive.extract(ffile, tempbasepath)
                    unzippedpath = tempbasepath + ffile

                csv = pandas.read_csv(unzippedpath, header=0, dtype={"underlying_symbol": object, "quote_date": object, "root": object, "expiration": object, "strike": np.float64, "option_type": object, "open": np.float64, "high": np.float64, "low": np.float64, "close": np.float64, "trade_volume": np.int64, "bid_size_1545": np.int64, "bid_1545": np.float64, "ask_size_1545": np.int64, "ask_1545": np.float64, "underlying_bid_1545": np.float64, "underlying_ask_1545": np.float64, "bid_size_eod": np.int64, "bid_eod": np.float64, "ask_size_eod": np.int64, "ask_eod": np.float64, "underlying_bid_eod": np.float64, "underlying_ask_eod": np.float64, "vwap": object, "open_interest": np.float64, "ask_eod": np.float64, "delivery_code": object})                
                
                filtered = csv[(csv['underlying_symbol'] == underlying)]
                filtered.to_sql(table, engine, if_exists='append', index=False)
                db.commit()
        
                os.remove(unzippedpath)
            
            db.close()
      
    print "Done"
    print 
    
