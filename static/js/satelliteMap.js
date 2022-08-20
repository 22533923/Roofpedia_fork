mapboxgl.accessToken = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2YnVlbXg0MWg3bTNpbzFnYmxubzd6NSJ9.RZBMIv2Wi-PsKYcHCI0suA';

const map = new mapboxgl.Map({
container: 'satellite-map', // container ID
style: 'mapbox://styles/mapbox/satellite-v9', // style URL
center: [137.9150899566626, 36.25956997955441], // starting position [lng, lat]
zoom: 9 // starting zoom
});

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