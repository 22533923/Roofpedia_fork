mapboxgl.accessToken = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2Ynh3cm9yMG1zdTNjcWx1aDh4N2ZrcCJ9.v8cr-6oDTE4Lw7UML51-gA';
const map = new mapboxgl.Map({
container: 'map', // container ID
style: 'mapbox://styles/mapbox/streets-v11', // style URL
center: [-74.5, 40], // starting position [lng, lat]
zoom: 15, // starting zoom
projection: 'equirectangular' // display the map as a 3D globe
});