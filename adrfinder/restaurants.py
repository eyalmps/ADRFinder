import json
import http.client
import urllib.parse
import datetime
from collections import OrderedDict


class Restaurants(object):

    def __init__(self):
        self.header = self.get_auth_cookie()

    def get_auth_cookie(self):
        """
        Get the authorization cookie
        """
        payload = "{}"
        headers = {}

        connection = http.client.HTTPSConnection("disneyworld.disney.go.com")

        try:
            connection.request("POST", "/finder/api/v1/authz/public", payload, headers)
        except Exception as e:
            connection.close()
            print(">> Request failed, Unable to get AUTH cookie: {}".format(e))
            raise SystemExit(e)

        response = connection.getresponse()

        if response.status == 302:
            # Try redirect for geolocation
            connection.close()
            print(">> Request failed, 302 received getting AUTH cookie: {}".format(response.status))
            location_header = response.getheader('location')
            location_data = urllib.parse.urlparse(location_header)
            print(">> Trying redirected location: {}".format(location_data.hostname))
            connection = http.client.HTTPSConnection(location_data.hostname)

            try:
                connection.request("POST", "/finder/api/v1/authz/public", payload, headers)
            except Exception as e:
                connection.close()
                print(">> Request failed, Unable to get AUTH cookie: {}".format(e))
                raise Exception("Request failed, Unable to get AUTH cookie: {}".format(e))

            response = connection.getresponse()

        if response.status != 200:
            connection.close()
            print(">> Request failed, Non-200 received getting AUTH cookie: {}".format(response.status))
            raise SystemExit(response.status)

        response.read()
        connection.close()
        headers['Cookie'] = response.getheader('set-cookie')

        return headers

    def get_dining_data(self):
        """
        Get the dining info for WDW
        """
        if hasattr(self, 'dining_data'):
            return self.dining_data

        yyyymmdd = datetime.datetime.today().strftime('%Y-%m-%d')

        connection = http.client.HTTPSConnection("disneyworld.disney.go.com")

        try:
            connection.request("GET", "/finder/api/v1/explorer-service/list-ancestor-entities/wdw/80007798;entityType=destination/" + yyyymmdd + "/dining", headers=self.header)
        except Exception as e:
            connection.close()
            print(">> Request failed, Unable to get Dining Data: {}".format(e))
            raise SystemExit(e)

        response = connection.getresponse()

        if response.status == 302:
            # Try redirect for geolocation
            connection.close()
            print(">> Request failed, 302 received getting Dining Data: {}".format(response.status))
            location_header = response.getheader('location')
            location_data = urllib.parse.urlparse(location_header)
            print(">> Trying redirected location: {}".format(location_data.hostname))
            connection = http.client.HTTPSConnection(location_data.hostname)

            try:
                connection.request("GET", "/finder/api/v1/explorer-service/list-ancestor-entities/wdw/80007798;entityType=destination/" + yyyymmdd + "/dining", headers=self.header)
            except Exception as e:
                connection.close()
                print(">> Request failed, Unable to get Dining Data: {}".format(e))
                raise Exception("Request failed, Unable to get Dining Data: {}".format(e))

            response = connection.getresponse()
        
        if response.status != 200:
            connection.close()
            print(">> Request failed, Non-200 received getting Dining Data: {}".format(response.status))
            raise SystemExit(response.status)

        data = response.read()
        connection.close()

        self.dining_data = json.loads(data.decode("utf-8"))
        return self.dining_data

    def get_restaurants(self):
        """
        Find all the restaurants at WDW
        Filter the ones that accept reservations

        return: dict { restaurant_name: restaurant_id;type }

        """

        dining_data = self.get_dining_data()

        restaurant_results = {}

        for result in dining_data['results']:
            accepts_reservations = False

            for facet in result['facets']:
                for flag in result['facets'][facet]:
                    if 'reservations-accepted' == flag:
                        accepts_reservations = True

            if accepts_reservations is True:
                restaurant_results[result['id']] = result['name']

        return restaurant_results

# replace get_search_times() body with a safer version
    def get_search_times(self):
        """
        Get the valid search times => values from disney dining page
        """
        dining_data = self.get_dining_data()
        search_times = OrderedDict()

        filters = dining_data.get('filters') or {}

    # try multiple likely keys; Disney may have renamed this block
    df = (
        filters.get('diningFormFilter') or
        filters.get('diningReservationFormFilter') or
        filters.get('reservationFormFilter') or
        {}
    )

    # Try both old/new field names; default to empty list to avoid KeyError
    for mp in (df.get('mealPeriods') or df.get('mealPeriodsV2') or []):
        # items might be dicts with key/value, or already strings — guard both
        k = mp.get('key') if isinstance(mp, dict) else str(mp)
        v = mp.get('value') if isinstance(mp, dict) else str(mp)
        if k is not None and v is not None:
            search_times[k] = v

    for t in (df.get('times') or df.get('timesV2') or []):
        k = t.get('key') if isinstance(t, dict) else str(t)
        v = t.get('value') if isinstance(t, dict) else str(t)
        if k is not None and v is not None:
            search_times[k] = v

    return search_times

    def get_party_size(self):
        """
        Hardcode max party
        """

        search_info = OrderedDict()
        for n in range(1, 51):
            search_info[n] = n

        return search_info
