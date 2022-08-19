
function getMapBounds(){
    const bounds = map.getBounds();
    nw_coords = bounds.getNorthWest();
    ne_coords = bounds.getNorthEast();
    sw_coords = bounds.getSouthWest();
    se_coords = bounds.getSouthEast();
    coords = {
        'south_edge_lat': sw_coords.lat,
        'west_edge_lng': sw_coords.lng,
        'north_edge_lat': ne_coords.lat,
        'east_edge_lng': ne_coords.lng,
        'nw_coords': {'lat':nw_coords.lat, 'lng': nw_coords.lng},
        'ne_coords': {'lat':ne_coords.lat, 'lng': ne_coords.lng},
        'sw_coords': {'lat':sw_coords.lat, 'lng': sw_coords.lng},
        'se_coords': {'lat':se_coords.lat, 'lng': se_coords.lng},
    };
    return coords
}


function applyBindings() {
    document.getElementById("valSelBut").addEventListener("click", postMapBounds);
    document.getElementById("rasterBut").addEventListener("click", getRasterTiles);
}

applyBindings()


function postMapBounds() { 
    coords = getMapBounds()
    $.ajax({
        type: "POST",
        url: "/validateSelection",
        data: JSON.stringify(coords),
        dataType: "json",
        contentType: "application/json",
        success: function(response){
            console.log("Success - roof polygons geojson")
        }
   });
  }

  function getRasterTiles(){
    coords = getMapBounds()
    $.ajax({
        type: "POST",
        url: "/mapbox-raster-tiles",
        data: JSON.stringify(coords),
        dataType: "json",
        contentType: "application/json",
        success: function(response){
            console.log("Success - Raster tiles")
        }
   });
  }