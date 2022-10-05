#from ast import Return
#from asyncio import current_task
#from audioop import add
#from crypt import methods
#from fileinput import filename
#from glob import glob
#import re
#from xml.etree.ElementTree import tostring
#from urllib import response
#from this import d
import json
from operator import le
import os
from pyexpat import features
import shutil
import torch
import toml
import threading
import geopandas as gpd
import overpass
import osm2geojson
import requests
import io
import math

from geojson import dump
from src.predict import predict
from src.extract import intersection
from flask import Flask, render_template, url_for, request, redirect, jsonify, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from geopy.geocoders import Nominatim
from PIL import Image
from io import BytesIO

class Predict_and_extract:
    #Code to run Roofpedia model on sample data

    def pred_and_ext(self,extent):

        config = toml.load('config/predict-config.toml')


        city_name = extent
        target_type = "Solar"

        tiles_dir = os.path.join("results", '02Images', city_name)
        mask_dir = os.path.join("results", "03Masks", target_type, city_name)
        tile_size =  config["img_size"]

        # load checkpoints
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if target_type == "Solar":
            checkpoint_path = config["checkpoint_path"]
            checkpoint_name = config["solar_checkpoint"]
            chkpt = torch.load(os.path.join(checkpoint_path, checkpoint_name), map_location=device)

        elif target_type == "Green":
            checkpoint_path = config["checkpoint_path"]
            checkpoint_name = config["green_checkpoint"]
            chkpt = torch.load(os.path.join(checkpoint_path, checkpoint_name), map_location=device)

        predict(tiles_dir, mask_dir, tile_size, device, chkpt)

        intersection(target_type, city_name, mask_dir)
        return True

#global identifier
global complete
global running
global absolute_path
global model_thread_name
global extent
complete = False
running = False
absolute_path = os.path.dirname(__file__)
model_thread_name = ""
extent = ""
#methods

def run_model(extent):
    #start a thread to run the model as a background task
    global complete,model_thread_name
    model_thread_name = threading.current_thread().name
    print("Starting thread: ",model_thread_name)
    new_class = Predict_and_extract()
    new_class.pred_and_ext(extent)
    complete = True
    model_thread_name = ""


def query_rooftop_polygons(latSouthEdge,lngWestEdge,latNorthEdge,lngEastEdge):
    #TODO make name of geojson file dynamic. Currently hardcoded to "MAP"
    #global absolute_path
    latSouthEdge = str(latSouthEdge)
    lngWestEdge = str(lngWestEdge)
    latNorthEdge = str(latNorthEdge)
    lngEastEdge = str(lngEastEdge)
    QUERY = '[out:json] [timeout:25];(node["building"]('+latSouthEdge+','+lngWestEdge+','+latNorthEdge+','+lngEastEdge+');way["building"]('+latSouthEdge+','+lngWestEdge+','+latNorthEdge+','+lngEastEdge+');relation["building"]('+latSouthEdge+','+lngWestEdge+','+latNorthEdge+','+lngEastEdge+'););(._;>;);out body;'
    api = overpass.API()
    print("OVERPASS QUERY:\n",QUERY)
    res = api.get(QUERY,build=False)
    res_geojson = osm2geojson.json2geojson(res, filter_used_refs=False, log_level='INFO')
    completePath = os.path.join(absolute_path, 'results/01City/')
    with open(completePath+'MAP.geojson', 'w') as f:
        dump(res_geojson, f)


def extract_features(extent,type):
    #extract rooftop features identified by Roofpedia model
    #global absolute_path
    geolocator = Nominatim(user_agent="my_app")
    coords = []
    addresses = []
    gdf = gpd.read_file(os.path.join(absolute_path,'results/04Results/'+extent+'_'+type+'.geojson'))#path to results
    gdf['centroid'] = gdf.centroid
    for i in range(gdf.shape[0]):
        (lon,lat) = (gdf.centroid[i].coords[0])
        coordsList = [lon,lat]
        coords.append(coordsList)
        c_string = str(lat) + ', ' + str(lon)
        addresses.append(geolocator.reverse(c_string))
    return coords, addresses

def extractPolygonAreas(extent,type):
    gdf = gpd.read_file(os.path.join(absolute_path,'results/04Results/'+extent+'_'+type+'.geojson'))#path to results
    tost = gdf.copy()
    tost= tost.to_crs({'init': 'epsg:3857'})#change from projection with unit of degree to cartesian projection with unit m 
    tost["area"] = tost['geometry'].area

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def numRowsCols(nw_coords,sw_coords,ne_coords):
    #get number of rows in x,y,z raster grid of map bounds at zoom level 19
    #number of rows
    start_tile_x_r, start_tile_y_r = deg2num(nw_coords["lat"],nw_coords["lng"],19)
    end_tile_x_r, end_tile_y_r = deg2num(sw_coords["lat"],sw_coords["lng"],19)
    n_rows = abs(start_tile_y_r - end_tile_y_r)
    #number of cols
    start_tile_x_c, start_tile_y_c = deg2num(nw_coords["lat"],nw_coords["lng"],19)
    end_tile_x_c, end_tile_y_c = deg2num(ne_coords["lat"],ne_coords["lng"],19)
    n_cols = abs(start_tile_x_c - end_tile_x_c)
    return n_rows,n_cols

def startEndTilesXY(nw_coords,se_coords):
    start_tile_x, start_tile_y = deg2num(nw_coords["lat"],nw_coords["lng"],19)
    end_tile_x, end_tile_y = deg2num(se_coords["lat"],se_coords["lng"],19)
    start_tile_xy = {
        'x': start_tile_x,
        'y': start_tile_y,
    }
    end_tile_xy = {
        'x': end_tile_x,
        'y': end_tile_y,
    }
    return start_tile_xy, end_tile_xy

def getResultsFile(extent):#fetch results stored in Results04 geojson
    extractPolygonAreas(extent,"Solar")#convert areas in geojson in Result04 to square meters
    #coords,addresses = extract_features(extent,"Solar")#extract coords and addresses from geojson in 04Results
    path = os.path.abspath("results/04Results/"+extent+"_Solar.geojson")
    f = open(path,"r")
    geojson_data = json.load(f)
    f.close()
    return geojson_data

def filterForFeature(geojson_data,id):
    """
    search for a specific feature based on its ID and filter the geojson such that it
    only contains that one feature.
    """
    features_dict = { i : geojson_data["features"][i] for i in range(0, len(geojson_data["features"])) }
    filtered_feat = []
    for key in features_dict:
        if key+1 == id:
            feature = features_dict[key]
            filtered_feat.append(feature)
    geojson_data["features"] = filtered_feat
    return geojson_data

def filterGeoJSON(geojson_data,extent,type,coords_to_delete):
    """
    -filter out the rooftop to be deleted from results geojson
    """
    #get coords of all features in results geojson
    coords = []
    gdf = gpd.read_file(os.path.join(absolute_path,'results/04Results/'+extent+'_'+type+'.geojson'))#path to results
    gdf['centroid'] = gdf.centroid
    for i in range(gdf.shape[0]):
        (lon,lat) = (gdf.centroid[i].coords[0])
        coordsList = [lon,lat]
        coords.append(coordsList)

    features_dict = { i : geojson_data["features"][i] for i in range(0, len(geojson_data["features"]) ) }
    filtered_feat = []
    i=0
    for key in features_dict:
        feature = features_dict[key]
        if not float(gdf.centroid[i].coords[0][0]) == float(coords_to_delete[0][0]):
            filtered_feat.append(feature)
        i=i+1
    geojson_data["features"] = filtered_feat

    #update geojson file in 04Results with filtered features
    completePath = os.path.join(absolute_path, 'results/04Results/')
    filename = extent + '_Solar.geojson'
    with open(completePath+filename, 'w') as f:
        dump(geojson_data, f)

def filterFeatures(geojson_data, coords, addresses,extent):
    """
    -filter out all features in geojson_data object that aren't polygons
    -update MAP_Solar.geojson file in 04Results with filtered features
    -write feature representations to db. Each feature represented by unique index, coord, address and area
    """
    features_dict = { i : geojson_data["features"][i] for i in range(0, len(geojson_data["features"]) ) }
    #filtered_coords = []
    filtered_feat = []
    for key in features_dict:
        feature = features_dict[key]
        if features_dict[key]["geometry"]["type"] == "Polygon":#feature is of type polygon, therefore keep it
            filtered_feat.append(feature)
    geojson_data["features"] = filtered_feat

    #update geojson file in 04Results with filtered features
    completePath = os.path.join(absolute_path, 'results/04Results/')
    filename = extent + '_Solar.geojson'
    with open(completePath+filename, 'w') as f:
        dump(geojson_data, f)

    #load features, coords and addresses to database
    features = geojson_data["features"]
    coords,addresses = extract_features(extent,"Solar")#extract coords and addresses from geojson in 04Results
    db.drop_all()#not ideal, but prevents same features from being readded to db if finished.html gets refreshed. Also takes care of primary key issue
    db.create_all()#Features table is therefore cleared and repopulated every time finished.html refreshes
    for i in range(len(features)):
        area = features[i]["properties"]["area"]
        #coord = str(coords[i][0])
        #coord = str(coords[i])
        lng = coords[i][0]
        lat = coords[i][1]
        address = str(addresses[i])
        new_feature = Feature(lng = lng,lat = lat, address = address,area = area)
        try:
            db.session.add(new_feature)
            db.session.commit()
            print('feature representations saved to db')
        except:
            print('failed to add feature')
    return geojson_data

def areaToPower(area):
    """
    assume typical residential setup looks as follows:
    -array of 1m x 1.6m, 60 cell panels
    -typical power rating of 300-330W per 60 cell panel -> assume 315W
    -power/m^2 surface area -> 196.875W/m^2
    """
    power = float(area)*196.875
    return power



app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
basedir = os.path.abspath(os.path.dirname(__file__))#pathname of app.py
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')#specify the database you want to establish a connection with
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)#database object

class Feature(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    lng = db.Column(db.Float,nullable=False)
    lat = db.Column(db.Float,nullable=False)
    address = db.Column(db.String(100000),nullable=False)
    area = db.Column(db.Float(100),nullable=False)

    def __repr__(self):
        return f'<Feature {self.id}>'


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/mapbox-raster-tiles",methods=['POST','GET'])
def getTiles():
    #fetch raster tiles and save to local based on map extent and zoom level 19
    request_data = request.get_json()
    nw_coords = request_data['nw_coords']
    ne_coords = request_data['ne_coords']
    sw_coords = request_data['sw_coords']
    se_coords = request_data['se_coords']
    n_rows, n_cols = numRowsCols(nw_coords,sw_coords,ne_coords)
    accessToken = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2YnVlbXg0MWg3bTNpbzFnYmxubzd6NSJ9.RZBMIv2Wi-PsKYcHCI0suA'
    url_base = "https://api.mapbox.com/styles/v1/lukasvdm/cl6bxq32t005715rua6cxmqys/tiles/256/19/" 
    if os.path.isdir(os.path.join(absolute_path, 'results/02Images/MAP/19/')):
        shutil.rmtree(os.path.join(absolute_path, 'results/02Images/MAP/19/'))#remove directory
        path = os.path.join(absolute_path, 'results/02Images/MAP/19/')
    else:
        path = os.path.join(absolute_path, 'results/02Images/MAP/19/')
    start_tile_xy, end_tile_xy = startEndTilesXY(nw_coords, se_coords)
    for c in range(n_cols):
        x = int(start_tile_xy["x"])+c
        path_with_col = os.path.join(path,str(x)+"/")#col number
        os.makedirs(path_with_col)
        for r in range(n_rows):
            y = int(start_tile_xy["y"])+r
            url_complete = url_base+str(x)+"/"+str(y)+"?"+"access_token="+accessToken
            req = requests.get(url_complete)
            with BytesIO(req.content ) as f:
                file_data = f.read()
                image = Image.open(io.BytesIO(file_data))
                completeName = os.path.join(path_with_col,str(y)+'.jpeg')
                image.save(completeName,'JPEG')
    return {},200



@app.route("/rooftop-polygons",methods=['POST','GET'])
def check():
    #TODO: check that co-ordinates have valid zoom level
    #TODO: change from request.form to json data -> complete?
    request_data = request.get_json()
    latSouthEdge = request_data['south_edge_lat']
    lngWestEdge = request_data['west_edge_lng']
    latNorthEdge = request_data['north_edge_lat']
    lngEastEdge = request_data['east_edge_lng']
    query_rooftop_polygons(latSouthEdge,lngWestEdge,latNorthEdge,lngEastEdge);
    return {},200

@app.route("/running",methods=['POST','GET'])
def running():
    #global running, model_thread_name, extent
    global extent
    extent = request.form['extent'] #TODO: remove this & fix in front end
    if not model_thread_name:
        #string empty
        model_thread = threading.Thread(target=run_model,args=(extent,)).start()
        #running = True
    return render_template("running.html")

@app.route("/track", methods=["GET"])
def track():
    """
    called every 10s to check if model has finished running. Once model is finished: 
    -results saved in geojson in 04Results
    -representation of each feature in results geojson stored in DB. All features will
    be of type polygon. In the db, each feature represented
    by a unique id, the coordinates of the centroid, address of the centroid and
    the polygon area.
    -once db is populated, redirects to finished.html
    """
    global complete
    if complete: # model has finished running, set complete False
        complete = False
        extractPolygonAreas(extent,"Solar")#convert areas in geojson in Result04 to square meters
        return redirect(url_for('temp'))
    return jsonify({'redirect': "running"}), 200 # give the client SOMETHING so the request doesn't timeout and error

@app.route("/temp")
def temp():
    global extent
    #args = request.args
    #extent = args["extent"]
    extent = "MAP" #REMVOVE WHEN DONE TESTING
    coords,addresses = extract_features(extent,"Solar")#extract coords and addresses from geojson in 04Results
    #get geojson results file to pass to finished.html
    geojson_data = getResultsFile(extent)
    geojson_data = filterFeatures(geojson_data, coords, addresses,extent)
    features = Feature.query.all()
    session['geojson_data'] = geojson_data
    session['features'] = features
    return redirect(url_for('finished'))

@app.route("/finished",methods=['POST','GET'])
def finished():
    global extent
    #args = request.args
    #extent = args["extent"]
    # extent = "MAP" #REMVOVE WHEN DONE TESTING
    features = Feature.query.all()
    geojson_data = session['geojson_data']
    area = 0
    total_power=0
    for i in range(len(features)):
        area = area + features[i].area

    if not len(features) == 0:
        api_key = "YYhHCjfb0KfwJPwQWmDvDLoN4l2hqhWb5l6t9Bpr"
        lng = str(features[0].lng)
        lat = str(features[0].lat)
        area = str(area)
        module_type = str(0)
        array_type = str(1)
        losses = str(14.48)
        tilt = str(20)
        azimuth = str(180)
        dc_ac_ratio = str(1.2)
        inv_eff = str(96)
        gcr = str(0.4)
        system_capacity = str(areaToPower(area)/1000.0)
        url = "https://developer.nrel.gov/api/pvwatts/v6.json?api_key="+api_key+"&lat="+lat+"&lon="+lng+"&system_capacity="+system_capacity+"&module_type="+module_type+"&losses="+losses+"&array_type="+array_type+"&tilt="+tilt+"&azimuth="+azimuth+"&dc_ac_ratio="+dc_ac_ratio+"&gcr="+gcr+"&inv_eff="+inv_eff
        try:
            response_json = requests.get(url).json()
            total_power = response_json['outputs']['ac_annual']
        except:
            return "failed to get request"

    return render_template("finished.html",features = features,geojson_data = geojson_data,total_power = total_power)
    #return render_template("finished.html",coords = coords,addresses = addresses,geojson_data = geojson_data)


@app.route("/delete/<int:id>",methods = ["GET","POST"])
def delete(id):
    feature_to_delete = Feature.query.get_or_404(id)
    lng_to_delete = feature_to_delete.lng
    lat_to_delete = feature_to_delete.lat
    coords_to_delete = [(lng_to_delete,lat_to_delete)]
    print("COORDS TO DELETE: ",coords_to_delete)
    try:
        db.session.delete(feature_to_delete)
        db.session.commit()
        #features = Feature.query.all()
        geojson_data = session["geojson_data"]
        extent = "MAP"#TODO: change this when done 
        type = "Solar"
        print("START FILTERING GEOJSON")
        filterGeoJSON(geojson_data,extent,type,coords_to_delete)
        print("SUCCESSFUL!")
        return redirect(url_for('finished'))
        #return render_template("finished.html",features = features,geojson_data = geojson_data)
    except:
        return 'failed'

@app.route("/details/<int:id>",methods = ["GET","POST"])
def details(id):
    geojson_data = session['geojson_data']
    power = 0
    try:
        feature = Feature.query.get(id)
        power = areaToPower(feature.area)
    except:
        return "feature not found"
    return render_template("details.html",feature = feature,geojson_data = geojson_data,power = power)

@app.route("/power",methods=["GET","POST"])
def power():
    api_key = "YYhHCjfb0KfwJPwQWmDvDLoN4l2hqhWb5l6t9Bpr"
    lat = str(request.form["lat"])
    lng = str(request.form["lng"])
    area = request.form["area"]
    new_area = request.form["new_area"]
    module_type = str(request.form["module_type"])
    array_type = str(request.form["array_type"])
    losses = str(request.form["system_loss"])
    tilt = str(request.form["tilt"])
    azimuth = str(request.form["azimuth"])
    dc_ac_ratio = str(request.form["dc_ac_ratio"])
    inv_eff = str(request.form["inverter_eff"])
    gcr = str(request.form["ground_coverage"])
    if not new_area == "":
        system_capacity = str(areaToPower(new_area)/1000.0)
    else:
        system_capacity = str(areaToPower(area)/1000.0)
    url = "https://developer.nrel.gov/api/pvwatts/v6.json?api_key="+api_key+"&lat="+lat+"&lon="+lng+"&system_capacity="+system_capacity+"&module_type="+module_type+"&losses="+losses+"&array_type="+array_type+"&tilt="+tilt+"&azimuth="+azimuth+"&dc_ac_ratio="+dc_ac_ratio+"&gcr="+gcr+"&inv_eff="+inv_eff
    try:
        response = requests.get(url)
        response_json = response.json()
    except:
        return "failed to get request"

    return render_template("estimate.html",response=response_json),200


if __name__ == "__main__":
    app.run(debug=True)




