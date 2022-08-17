function getMapBounds(){
    const bounds = map.getBounds();
    south_edge_lat = bounds.getSouthWest().lat
    west_edge_lng = bounds.getSouthWest().lng
    north_edge_lat = bounds.getNorthEast().lat
    east_edge_lng = bounds.getNorthEast().lng
    data = {
        'south_edge_lat': south_edge_lat,
        'west_edge_lng': west_edge_lng,
        'north_edge_lat': north_edge_lat,
        'east_edge_lng': east_edge_lng,
    };
    console.log("from map: ", data)
    request(data);
}

function applyBindings() {
    document.getElementById("valSelBut").addEventListener("click", getMapBounds);
}

applyBindings()

function request(data) { 
    $.ajax({
        type: "POST",
        url: "/validateSelection",
        data: data,
        success: function(response){
            //window.location.href = response.redirect;
            console.log("success")
        }
   });
  }