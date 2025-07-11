# geoip_database.py
import geoip2.database
import argparse
from geoip2.errors import AddressNotFoundError
from collections import defaultdict

# Load the GeoLite2-City database once
reader = geoip2.database.Reader("GeoLite2-Country.mmdb")

def get_iso_country(ip: str) -> str:
    try:
        #print("ip:", ip.split('/')[0].replace('.0','.10'))
        #response = reader.country(ip.split('/')[0].replace('.0','.10'))
        response = reader.country(ip)
        # print(response)
        return response.country.iso_code or "NA"
    except Exception:
        return "NA"

def main():
    parser = argparse.ArgumentParser(description="Look up ip-address's physical location -- geoip2-country")
    parser.add_argument("--ip", required=True, help="")

    args = parser.parse_args()

    ip = args.ip

    get_iso_country(ip)

if __name__ == '__main__':
    main()