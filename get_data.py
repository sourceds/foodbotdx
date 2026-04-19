import requests
import dotenv
import dotenv
import os

def from_source_url() -> int:
    dotenv.load_dotenv() 
    source_url = os.getenv('SOURCE')
    dest_file = os.getenv('DATA')

    source_file = requests.get(source_url)

    if (source_file.status_code == 200):
        try:
            with open(dest_file, 'wb') as file:

                try:
                    file.write(source_file.content)
                    return 0
                
                except (IOError, OSError):
                    return 3 #Error: File Write Error
                
        except (FileNotFoundError, PermissionError, OSError):
            return 2 #Error: File Access Error
        
    else:
        return 1 #Error : Invalid HTTP response