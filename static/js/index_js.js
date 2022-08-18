
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
    //testReq(data);
    request(data);
}

function applyBindings() {
    document.getElementById("valSelBut").addEventListener("click", getMapBounds);
}

applyBindings()

// function testReq(data){
//     bound_box = String(data.south_edge_lat) + ',' + String(data.west_edge_lng) +
//      ',' + String(data.north_edge_lat) + ',' + String(data.east_edge_lng)
//     $.ajax({
//         url:
//             'https://www.overpass-api.de/api/interpreter?data=' + 
//             '[out:json][timeout:60];' + 
//             '(node["building"](' + bound_box + ');' +
//             'way["building"](' +  bound_box + ');' +
//             'relation["building"](' + bound_box + '););' +
//             '(._;>;);out body;',
//         dataType: 'json',
//         type: 'GET',
//         async: true,
//         crossDomain: true,
//         success: function(data){
//             console.log(data);
//         }
//     }).done(function() {
//         console.log( "second success" );
//     }).fail(function(error) {
//         console.log(error);
//         console.log( "error" );
//     }).always(function() {
//         console.log( "complete" );
//     });
// }

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