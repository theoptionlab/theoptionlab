import entries
from datetime import datetime



start = datetime.now().date()
end = datetime(2019, 1, 1).date()
    
entries = entries.getEntries(start, end, 65, True, False)


for entry in entries:
    
    print str(entry['entrydate']) + "\t " + str(entry['expiration'])
