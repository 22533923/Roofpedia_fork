mapboxgl.accessToken = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2YnVlbXg0MWg3bTNpbzFnYmxubzd6NSJ9.RZBMIv2Wi-PsKYcHCI0suA';

var geo_data = JSON.parse(document.getElementById("geo_data_div").dataset.geojson_data);
var coords = JSON.parse(document.getElementById("coords_data_div").dataset.coords);
console.log(geo_data)
console.log(coords)

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
    'fill-opacity': 0.5
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

//CODE TO ADD DRAWING FUNCTIONALITY
const draw = new MapboxDraw({
    displayControlsDefault: false,
    // Select which mapbox-gl-draw control buttons to add to the map.
    controls: {
    polygon: true,
    trash: true
    },
    // Set mapbox-gl-draw to draw by default.
    // The user does not have to click the polygon control button first.
    defaultMode: 'draw_polygon'
    });
    map.addControl(draw);
     
    map.on('draw.create', updateArea);
    map.on('draw.delete', updateArea);
    map.on('draw.update', updateArea);
     
    function updateArea(e) {
    const data = draw.getAll();
    const answer = document.getElementById('calculated-area');
    if (data.features.length > 0) {
    const area = turf.area(data);
    // Restrict the area to 2 decimal points.
    const rounded_area = Math.round(area * 100) / 100;
    answer.innerHTML = `<p><strong>${rounded_area}</strong></p><p>square meters</p>`;
    } else {
    answer.innerHTML = '';
    if (e.type !== 'draw.delete')
    alert('Click the map to draw a polygon.');
    }
    }
//CODE TO ADD DRAWING FUNCTIONALITY


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