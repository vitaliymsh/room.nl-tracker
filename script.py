import urllib.request, json
from time import sleep

url = 'https://studentenplatformapi.hexia.io/api/v1/actueel-aanbod?limit=50&locale=en_GB&page=0&sort=-reactionData.publicationDate'



def main():
    while True:

        with urllib.request.urlopen(url) as page:
            data = json.loads(page.read().decode())
            for item in data['data']:
                print(item['city'], item['publicationDate'])
        sleep(10)

