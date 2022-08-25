from ast import Return
from asyncio import current_task
from audioop import add
from crypt import methods
from fileinput import filename
from glob import glob
import json
import os
import shutil
from this import d
from urllib import response
from xml.etree.ElementTree import tostring
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
from flask import Flask, render_template, url_for, request, redirect, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
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
#mapbox_access_token = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2YnVlbXg0MWg3bTNpbzFnYmxubzd6NSJ9.RZBMIv2Wi-PsKYcHCI0suA'
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
        coords.append(list(gdf.centroid[i].coords))
        (lon,lat) = coords[i][0]
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






app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))#pathname of app.py
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')#specify the database you want to establish a connection with
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)#database object
class Feature(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    coord = db.Column(db.String(100),nullable=False)
    address = db.Column(db.String(100000),nullable=False)
    area = db.Column(db.Float(100),nullable=False)

    def __repr__(self):
        return f'<Feature {self.id}>'


def getResultsFile():#fetch results stored in Results04 geojson
    extractPolygonAreas(extent,"Solar")#convert areas in geojson in Result04 to square meters
    coords,addresses = extract_features(extent,"Solar")#extract coords and addresses from geojson in 04Results
    path = os.path.abspath("results/04Results/"+extent+"_Solar.geojson")
    f = open(path,"r")
    geojson_data = json.load(f)
    f.close()
    return geojson_data

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



@app.route("/validateSelection",methods=['POST','GET'])
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

@app.route("/finished",methods=['POST','GET'])
def finished():
    global extent
    #args = request.args
    #extent = args["extent"]
    extent = "MAP" #REMVOVE WHEN DONE TESTING
    extractPolygonAreas(extent,"Solar")#convert areas in geojson in Result04 to square meters
    coords,addresses = extract_features(extent,"Solar")#extract coords and addresses from geojson in 04Results
    #get geojson results file to pass to finished.html
    geojson_data = getResultsFile()
    # print("CHECK1: ",addresses)
    # if request.method == "POST":
    #     feature_index = request.form["index"]
    #     features_dict = { i : geojson_data["features"][i] for i in range(0, len(geojson_data["features"]) ) }
    #     new_coords = []
    #     new_add = []
    #     new_feat = []
    #     for key in features_dict:
    #         feature = features_dict[key]
    #         if str(key) != str(feature_index):
    #             new_feat.append(feature)
    #             new_coords.append(coords[key])
    #             new_add.append(addresses[key])
    #     addresses = new_add
    #     coords = new_coords
    #     geojson_data["features"] = new_feat
    #     print("CHECK2: ",addresses)
    #     #return jsonify({'redirect': url_for('finished'),'extent': extent})
    #     return render_template("finished.html",coords = coords,addresses = addresses,geojson_data = geojson_data)
    # else:
        #Following code removes all features that aren't polygons
    features_dict = { i : geojson_data["features"][i] for i in range(0, len(geojson_data["features"]) ) }
    filtered_coords = []
    filtered_add = []
    filtered_feat = []
    for key in features_dict:
        feature = features_dict[key]
        if features_dict[key]["geometry"]["type"] == "Polygon":
            filtered_feat.append(feature)
            filtered_coords.append(coords[key])
            filtered_add.append(addresses[key])
    addresses = filtered_add
    coords = filtered_coords
    geojson_data["features"] = filtered_feat
    return render_template("finished.html",coords = coords,addresses = addresses,geojson_data = geojson_data)


@app.route("/running",methods=['POST','GET'])
def running():
    #global running, model_thread_name, extent
    global extent
    extent = request.form['extent']
    if not model_thread_name:
        #string empty
        model_thread = threading.Thread(target=run_model,args=(extent,)).start()
        #running = True
    return render_template("running.html")


@app.route("/track", methods=["GET"])
def track():
    global complete
    if complete: # model has finished running, set complete False
        complete = False
        #load features, coords and addresses to database
        geojson_data = getResultsFile()
        features = geojson_data["features"]
        coords,addresses = extract_features(extent,"Solar")#extract coords and addresses from geojson in 04Results
        for i in range(len(features)):
            area = features[i]["properties"]["area"]
            coord = str(coords[i])
            address = str(addresses[i])
            new_feature = Feature(coord = coord, address = address,area = area)
            print("Feature: ",coord,"   ",address,"   ",area)
            try:
                db.session.add(new_feature)
                db.session.commit()
            except:
                print('failed to add feature')
        return jsonify({'redirect': url_for('finished'),'extent': extent})
    return jsonify({'redirect': "running"}), 200 # give the client SOMETHING so the request doesn't timeout and error

if __name__ == "__main__":
    app.run(debug=True)
    #app.config["TEMPLATES_AUTO_RELOAD"] = True




