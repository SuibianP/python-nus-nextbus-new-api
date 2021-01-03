import requests
import dateutil.parser
import enum
import re

# FIGURE OUT THE AUTHENTICATION CREDENTIALS FROM THE API DOCUMENTATION REPOSITORY YOURSELF
auth_code = None # HAVE TO FILL THIS BEFORE USAGE
baseurl = 'https://nnextbus.nus.edu.sg'

class publicity_banner_type(enum.Enum):
    IMG = 0
    IMG_LINK = 1
    IMG_FORM = 2


def _http_get(endpoint, auth_obj=auth_code, params=None):
    response = requests.get(baseurl + endpoint, auth=auth_obj, params=params)
    response.raise_for_status() # raise exception if HTTP 4XX/5XX
    return response.json()

# the following private methods only do
# - fetch raw json data
# - simplification (remove unnecessary nesting, etc.)
# - convertion (to most suitable Python native data types)
# - deletion (of evidently useless data)
# They are not supposed to do
# - transformation
# - parameter validation

def _get_publicity():
    response_json = _http_get('/publicity')
    for item in response_json['banners']:
        item['begin'] = dateutil.parser.isoparse(item['begin'])
        item['end'] = dateutil.parser.isoparse(item['end'])
        item['type'] = publicity_banner_type[item['type']]
        if item['link_url'] == 'null':
            item['link_url'] = None
    return response_json

def _get_list_of_bus_stops():
    response_json = _http_get('/BusStops')
    return response_json['BusStopsResult']['busstops']

def _get_pickup_point(route_code):
    response_json = _http_get('/PickupPoint', params={'route_code': route_code})
    for item in response_json['PickupPointResult']['pickuppoint']:
        item['latitude'] = item.pop('lat')
        item['longitude'] = item.pop('lng')
        response_json['PickupPointResult']['routeid'] = item.pop('route_id') # FIXME: redundancy
    return response_json['PickupPointResult']

def _get_shuttle_service(busstopname):
    # parameter should be busstopcode from _get_list_of_busstops
    response_json = _http_get('/ShuttleService', params={'busstopname': busstopname})
    response_json['ShuttleServiceResult']['TimeStamp'] = dateutil.parser.isoparse(response_json['ShuttleServiceResult']['TimeStamp'])
    for item in response_json['ShuttleServiceResult']['shuttles']:
        # remove seemingly unused keys
        for key in {'passengers', 'nextPassengers'}:
            del item[key]
        for key in {'arrivalTime', 'nextArrivalTime'}:
            item[key] = None if item[key] == '-' else float(item[key])
    return response_json['ShuttleServiceResult']

def _get_active_bus(route_code):
    response_json = _http_get('/ActiveBus', params={'route_code': route_code})
    response_json['ActiveBusResult']['ActiveBusCount'] = float(response_json['ActiveBusResult']['ActiveBusCount'])
    response_json['ActiveBusResult']['TimeStamp'] = dateutil.parser.isoparse(response_json['ActiveBusResult']['TimeStamp']);
    for bus in response_json['ActiveBusResult']['activebus']:
        bus['latitude'] = bus.pop('lat')
        bus['longitude'] = bus.pop('lng')
    return response_json['ActiveBusResult']

def _get_bus_location(veh_plate):
    response_json = _http_get('/BusLocation', params={'veh_plate': veh_plate})
    response_json['BusLocationResult']['latitude'] = response_json['BusLocationResult'].pop('lat')
    response_json['BusLocationResult']['longitude'] = response_json['BusLocationResult'].pop('lng')
    response_json['BusLocationResult']['status'] = distutils.util.strtobool(response_json['BusLocationResult']['status'])
    return response_json['BusLocationResult']

def _get_route_min_max_time(route_code):
    response_json = _http_get('/RouteMinMaxTime', params={'route_code': route_code})
    for item in response_json['RouteMinMaxTimeResult']['RouteMinMaxTime']:
        item.DisplayOrder = int(item.DisplayOrder)
        item.FirstTime = dateutil.parser.parse(item.FirstTime)
        item.LastTime = dateutil.parser.parse(item.LastTime)
    return response_json['RouteMinMaxTimeResult']['RouteMinMaxTime']

def _get_service_description():
    response_json = _http_get('/ServiceDescription')
    return response_json['ServiceDescriptionResult']['ServiceDescription']

def _get_announcements():
    response_json = _http_get('/Announcements')
    for item in response_json['AnnouncementsResult']['Announcement']:
        item['Created_On'] = dateutil.parser.parse(item['Created_On'])
        item['ID'] = int(item['ID'])
        item['Priority'] = int(item['Priority'])
        item['Status'] = item['Status'] == 'Enabled'
        try:
            item['Affected_Service_Ids'] = item['Affected_Service_Ids'].split(',').remove('[]')
        except ValueError:
            pass
        # FIXME: not elegant
        return response_json['AnnouncementsResult']['Announcement']

def _get_ticker_tapes():
    response_json = _http_get('/TickerTapes')
    for item in response_json['TickerTapesResult']['TickerTape']:
        item['Affected_Service_Ids'] = re.split(r'\W+', response_json['Affected_Service_Ids'])
        item['Created_On'] = dateutil.parser.parse(item['Created_On'])
        item['Display_From'] = dateutil.parser.parse(item['Display_From'])
        item['Display_To'] = dateutil.parser.parse(item['Display_To'])
        item['ID'] = int(item['ID'])
        item['Status'] = item['Status'] == 'Enabled'
        return response_json['TickerTapesResult']

def _get_checkpoints(route_code):
    response_json = _http_get('/CheckPoint', params={'route_code': route_code})
    return response_json['CheckPointResult']['CheckPoint']
