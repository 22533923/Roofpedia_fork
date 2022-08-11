import os
import torch
import toml
import argparse
import threading

from src.predict import predict
from src.extract import intersection
from flask import Flask, render_template, url_for, request, redirect

# parser = argparse.ArgumentParser()
# parser.add_argument("city", help="City to be predicted, must be the same as the name of the dataset")
# parser.add_argument("type", help="Roof Typology, Green for Greenroof, Solar for PV Roof")
# args = parser.parse_args()

class Predict_and_extract:

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

def run_model(city):
    #run as backround task via threading
    print("Starting thread: ",threading.current_thread().name)
    new_class = Predict_and_extract()
    new_class.pred_and_ext(city)
    print("Thread completed!")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/running",methods=['POST','GET'])
def running():
    city = request.form['city']
    threading.Thread(target=run_model,args=(city,)).start()
    return render_template("running.html")

if __name__ == "__main__":
    app.run(debug=True)




