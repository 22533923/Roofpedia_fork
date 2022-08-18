mapboxgl.accessToken = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2YnVlbXg0MWg3bTNpbzFnYmxubzd6NSJ9.RZBMIv2Wi-PsKYcHCI0suA';

const map = new mapboxgl.Map({
container: 'map', // container ID
style: 'mapbox://styles/lukasvdm/cl6uoz4za002815lb59bemga9', // style URL
center: [-115.5, 35], // starting position [lng, lat]
zoom: 4, // starting zoom
projection: 'equirectangular' // display the map as a 3D globe
});


map.on('click',function(e){
// Find all features in one source layer in a vector source
    const bounds = map.getBounds();//return lngLatBounds
    //lngLatBounds -> southwest and northeast points in longitude and latitude
    south_edge_lat = bounds.getSouthWest().lat
    west_edge_lng = bounds.getSouthWest().lng
    north_edge_lat = bounds.getNorthEast().lat
    east_edge_lng = bounds.getNorthEast().lng
    })

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