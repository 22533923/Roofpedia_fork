
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
    //postMapBounds(bounds);
    getRasterTiles(coords);
}


function applyBindings() {
    document.getElementById("valSelBut").addEventListener("click", getMapBounds);
    document.getElementById("rasterBut").addEventListener("click", getMapBounds);
}

applyBindings()


function postMapBounds(coords) { 
    $.ajax({
        type: "POST",
        url: "/validateSelection",
        data: coords,
        success: function(response){
            //window.location.href = response.redirect;
            console.log("success")
        }
   });
  }

  function getRasterTiles(coords){
    $.ajax({
        type: "POST",
        url: "/mapbox-raster-tiles",
        data: JSON.stringify(coords),
        dataType: "json",
        contentType: "application/json",
        success: function(response){
            console.log("success from FE")
        }
   });
//     accessToken = 'pk.eyJ1IjoibHVrYXN2ZG0iLCJhIjoiY2w2YnVlbXg0MWg3bTNpbzFnYmxubzd6NSJ9.RZBMIv2Wi-PsKYcHCI0suA';
//     $.ajax({
//         type: "GET",
//         url: "https://api.mapbox.com/styles/v1/lukasvdm/cl6bxq32t005715rua6cxmqys/tiles/256/19/91563/211676?"+
//         "access_token="+accessToken,
//         success: function(response){
//             console.log("success - tile fetched ")
//             console.log(response)
//         }
//    });
  }