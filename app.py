from ast import Return
from asyncio import current_task
from audioop import add
from fileinput import filename
from glob import glob
import os
import torch
import toml
import threading
import geopandas as gpd
import geocoder

from src.predict import predict
from src.extract import intersection
from flask import Flask, render_template, url_for, request, redirect, jsonify, url_for
from shapely.geometry import Point
from geopy.geocoders import Nominatim

class Predict_and_extract:
    #Code to run Roofpedia model on sample data

    def pred_and_ext(self,city):

        config = toml.load('config/predict-config.toml')

        # city_name = args.city
        # target_type = args.type
        city_name = city
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
complete = False
running = False
absolute_path = os.path.dirname(__file__)
model_thread_name = ""
#mapbox_access_token = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2YnVlbXg0MWg3bTNpbzFnYmxubzd6NSJ9.RZBMIv2Wi-PsKYcHCI0suA'
#methods

def run_model(city):
    #start a thread to run the model as a background task
    global complete,model_thread_name
    model_thread_name = threading.current_thread().name
    print("Starting thread: ",model_thread_name)
    new_class = Predict_and_extract()
    new_class.pred_and_ext(city)
    complete = True
    model_thread_name = ""

def extract_features(city,type):
    #extract rooftop features identified by Roofpedia model
    global absolute_path
    geolocator = Nominatim(user_agent="my_app")
    coords = []
    addresses = []
    gdf = gpd.read_file(os.path.join(absolute_path,'results/04Results/'+city+'_'+type+'.geojson'))#path to results
    gdf['centroid'] = gdf.centroid
    for i in range(gdf.shape[0]):
        coords.append(list(gdf.centroid[i].coords))
        (lon,lat) = coords[i][0]
        c_string = str(lat) + ', ' + str(lon)
        addresses.append(geolocator.reverse(c_string))
    return coords, addresses



app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/finished")
def finished():
    coords,addresses = extract_features("SD","Solar")
    return render_template("finished.html",addresses = addresses)


@app.route("/running",methods=['POST','GET'])
def running():
    global running, model_thread_name
    city = request.form['city']
    if not model_thread_name:
        #string empty
        model_thread = threading.Thread(target=run_model,args=(city,)).start()
        running = True
    return render_template("running.html")

@app.route("/track", methods=["GET"])
def track():
    global complete # regrab the value of complete every iteration
    print(complete)
    if complete: # model has finished running, complete set to True
        complete = True
        return jsonify({'redirect': url_for('finished')})
    return jsonify({'redirect': "running"}), 200 # give the client SOMETHING so the request doesn't timeout and error

if __name__ == "__main__":
    app.run(debug=True)




