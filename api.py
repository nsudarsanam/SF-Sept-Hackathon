from flask import Flask, render_template, request
import calendar
from datetime import datetime
import json
import csv
import string
import io
import math
from flask import jsonify
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
import urllib
from flask import Response

## globals
SF_LOCATIONS_URL='https://data.sfgov.org/resource/vbiu-2p9h.json'
RATING = 3.0
SF_LAT = 37.775 
SF_LON = -122.419
WGS84_a = 6378137.0  # Major semiaxis [m]
WGS84_b = 6356752.3  # Minor semiaxis [m]

#end globals

app = Flask(__name__)

class RestaurantData:
    def __init__(self, name,timeslot,interest):
        self.name = name
        self.timeslot = timeslot
        self.numOfTourists = 0
        self.numOfLocals = 0
        self.interest = interest
    
    def addTourist(self):
        self.numOfTourists = self.numOfTourists + 1
    
    def addLocal(self):
        self.numOfLocals = self.numOfLocals + 1
    
    def getOtherCount(self,userType):
        if userType == 0:
            return self.numOfLocals
        elif userType == 1:
            return self.numOfTourists

    def addCount(self, userType):
        if userType == 0: # 0 = tourist, 1 = local
            self.addTourist()
            print self.numOfTourists, self.numOfLocals
        elif userType == 1:
            self.addLocal()
            print self.numOfTourists, self.numOfLocals
        return self.getOtherCount(userType)
    
_allData = dict()

@app.route("/results", methods=['GET'])
def get_results():
    return getResults(request.args['interest'], request.args['time'],request.args['location'],request.args['distance'])

@app.route("/touristResults", methods=['GET'])
def get_touristResults():
    return getTouristResults(request.args['interest'], request.args['time'],request.args['location'],request.args['distance'])

@app.route('/update', methods = ['GET'])
def post_update():
    return postUpdate(request.args['name'],request.args['interest'], request.args['time'],request.args['userType'])

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
  return response

def deg2rad(degrees):
    return math.pi*degrees/180.0
# radians to degrees
def rad2deg(radians):
    return 180.0*radians/math.pi

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

def getResults(interest,time,location,distance):
    splitLoc = location.split(",")
    lat = float(splitLoc[0])
    lon = float(splitLoc[1])
    with io.open('config_secret.json') as cred:
        creds = json.load(cred)
        auth = Oauth1Authenticator(**creds)
        client = Client(auth)
        bounds = boundingBox( lat, lon, float(distance) * 1.0 )
        print bounds

        params = {
        'term': interest,
        'sort':2
        }

        searchResponse = client.search_by_bounding_box(
            bounds[0],
            bounds[1],
            bounds[2],
            bounds[3],
            **params
        )

        foundBusiness = [ ({'name':business.name,'count':tryGetKey(business.name,time,0)}) for business in searchResponse.businesses  if business.rating > RATING]
        return Response(json.dumps(foundBusiness),mimetype='application/json')

def getTouristResults(interest=None,time=None,location=None,distance=None):
    keys=('name','interest','time','numberOfLocals','distance')
    allBusinesses =  [({'name': value.name,'interest':value.interest,'time':value.timeslot,'numberOfLocals':value.numOfLocals,'distance':'1'}) for key,value in _allData.iteritems() ]
    return Response(json.dumps(allBusinesses),mimetype='application/json')


def tryGetKey(name,time,userType):
    key = getDataKey(name,time)
    if key in _allData:
        return getOtherCount( _allData[key], userType )
    return 1

def postUpdate(name, interest, time, userType):
    key = getDataKey(name,time)
    count = 0
    if key in _allData:
        count = _allData[key].addCount(int(userType))
    else:
        _allData[key] = RestaurantData(name,time,interest)
        count = _allData[key].addCount(int(userType))   
    
    for key,data in _allData.iteritems():
        print data.name, data.interest, data.timeslot, data.numOfTourists, data.numOfLocals 

    return Response(str(count),mimetype='application/json')

def getDataKey(name, time):
    return name + ',' + time   

if __name__ == "__main__":
    app.run()

