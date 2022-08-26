var intervalID
$(document).ready(function() {
    intervalID = setInterval(request, 10000);
});

function request() { 
    $.ajax({
     type: "GET",
     url: "/track",
     success: function(response){
       if(response.redirect === "running"){
       console.log(response);
     }else{
      console.log("FINISHED");
      clearInterval(intervalID);
      window.location.href = "/finished"
     }
    }
   });
  }

