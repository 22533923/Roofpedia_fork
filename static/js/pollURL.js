$(document).ready(function() {
    setInterval(request, 10000);
});

function request() { 
    $.ajax({
     type: "GET",
     url: "/track",
     success: function(response){
       if(response.redirect === "running"){
       console.log(response);
     }else{
        window.location.href = response.redirect+'?extent='+response.extent;
     }
    }
   });
  }