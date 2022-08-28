mapboxgl.accessToken = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2YnVlbXg0MWg3bTNpbzFnYmxubzd6NSJ9.RZBMIv2Wi-PsKYcHCI0suA';
var geo_data = JSON.parse(document.getElementById("geo_data_div").dataset.geojson_data);
console.log(geo_data)

function jumpToPlace(button_id){
    var place_lng = document.getElementById(button_id).dataset.lng;
    var place_lat = document.getElementById(button_id).dataset.lat;
    map.jumpTo({
        center: [place_lng,place_lat],
        zoom: 18,
        });
}

function removePlace(button_id){
    
}

function applyBindings() {
    document.getElementById("wrapper").addEventListener('click', (event) => {
        const isButton = event.target.nodeName === 'BUTTON';
        if (!isButton) {
          return;
        }
        if(String(event.target.id).includes("view")){
            jumpToPlace(event.target.id);
        }else{
            removePlace(event.target.id);
        };
    })
}
applyBindings()

const map = new mapboxgl.Map({
container: 'satellite-map', // container ID
style: 'mapbox://styles/mapbox/satellite-v9', // style URL
center: [137.9150899566626, 36.25956997955441], // starting position [lng, lat]
zoom: 9 // starting zoom
});

//CODE TO ADD POLYGONS TO MAP
map.on('load', () => {
    // Add a data source containing GeoJSON data.
    map.addSource('polygons', {
    'type': 'geojson',
    'data': geo_data
    });
     
    // Add a new layer to visualize the polygon.
    map.addLayer({
    'id': 'polygons',
    'type': 'fill',
    'source': 'polygons', // reference the data source
    'layout': {},
    'paint': {
    'fill-color': '#0080ff', // blue color fill
    'fill-opacity': 0.4
    }
    });
    // Add a black outline around the polygon.
    map.addLayer({
    'id': 'outline',
    'type': 'line',
    'source': 'polygons',
    'layout': {},
    'paint': {
    'line-color': '#000',
    'line-width': 3
    }
    });
    });
//CODE TO ADD POLYGONS TO MAP


const nav = new mapboxgl.NavigationControl({
    visualizePitch: true
});

map.addControl(nav, 'bottom-right');

map.addControl(new mapboxgl.GeolocateControl({
    positionOptions: {
        enableHighAccuracy: true
    },
    trackUserLocation: true,
    showUserHeading: true
}));

map.addControl(
    new MapboxGeocoder({
    accessToken: mapboxgl.accessToken,
    mapboxgl: mapboxgl
    })
    );