from yelp.client import Client
import io
import json
import math
from yelp.oauth1_authenticator import Oauth1Authenticator
import urllib

def deg2rad(degrees):
    return math.pi*degrees/180.0
# radians to degrees
def rad2deg(radians):
    return 180.0*radians/math.pi

# Semi-axes of WGS-84 geoidal reference
WGS84_a = 6378137.0  # Major semiaxis [m]
WGS84_b = 6356752.3  # Minor semiaxis [m]

SF_LOCATIONS_URL='https://data.sfgov.org/resource/vbiu-2p9h.json'

RATING = 3.0
SF_APP_TOKEN='c256AYOZ4Msabyeqb8R8vXj53'

# Earth radius at a given latitude, according to the WGS-84 ellipsoid [m]
def WGS84EarthRadius(lat):
    # http://en.wikipedia.org/wiki/Earth_radius
    An = WGS84_a*WGS84_a * math.cos(lat)
    Bn = WGS84_b*WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt( (An*An + Bn*Bn)/(Ad*Ad + Bd*Bd) )

# Bounding box surrounding the point at given coordinates,
# assuming local approximation of Earth surface as a sphere
# of radius given by WGS84
def boundingBox(latitudeInDegrees, longitudeInDegrees, halfSideInMiles):
    lat = deg2rad(latitudeInDegrees)
    lon = deg2rad(longitudeInDegrees)
    halfSide = 1000*halfSideInMiles*1.61

    # Radius of Earth at given latitude
    radius = WGS84EarthRadius(lat)
    # Radius of the parallel at given latitude
    pradius = radius*math.cos(lat)

    latMin = lat - halfSide/radius
    latMax = lat + halfSide/radius
    lonMin = lon - halfSide/pradius
    lonMax = lon + halfSide/pradius

    return (rad2deg(latMin), rad2deg(lonMin), rad2deg(latMax), rad2deg(lonMax))

def buildSfApiUrl(foundBusiness):
    url = SF_LOCATIONS_URL +'?'

    titles = '$$app_token=' + SF_APP_TOKEN +'&$WHERE=dba_name IN ('
    titles = titles + ''.join('\'' + business.upper() + '\',' for business in foundBusiness)
    titles = titles + ')'
    titles = titles + '&$order=location_start_date ASC'
    arg = urllib.quote(titles.encode('utf-8'))
    url = url + arg
    print url

SF_LAT = 37.775 
SF_LON = -122.419

with io.open('config_secret.json') as cred:
    creds = json.load(cred)
    auth = Oauth1Authenticator(**creds)
    client = Client(auth)
    bounds = boundingBox( SF_LAT, SF_LON, 0.3 )
    print bounds

    params = {
    'term': 'food',
    'sort':2
    }

    searchResponse = client.search_by_bounding_box(
        bounds[0],
        bounds[1],
        bounds[2],
        bounds[3],
        **params
    )

    foundBusiness = [ business.name for business in searchResponse.businesses  if business.rating > RATING]
  
    for business in foundBusiness:
        print business

    sfApiUrl = buildSfApiUrl(foundBusiness)