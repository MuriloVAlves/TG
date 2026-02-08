import requests as r

class SatTLE:
    def __init__(self):
        self.headers = {
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
                        }

        self.list_tles_links =['https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle']
        self.satellite_list = {}

    def load_sats_data(self):
        for link in self.list_tles_links:
            base_response = r.get(link)#,headers=headers)
            counter = 0
            sat_info = ''
            for sat in base_response.text.split('\r\n'):
                if counter == 0:
                    sat_info = sat.strip()
                    self.satellite_list[sat_info] = {}
                    counter += 1
                elif counter == 1:
                    self.satellite_list[sat_info]['TLE1'] = sat
                    counter += 1
                elif counter == 2:
                    self.satellite_list[sat_info]['TLE2'] = sat
                    counter = 0

if __name__ == '__main__':
    tle = SatTLE()
    tle.load_sats_data()
    print(tle.satellite_list.keys())