// logic to obtain the latest highscores from the server

///////////////////////////////////////////////////////////////////////////////////
// (c) Alexander C. Gessler, 2010
// www.greentoken.de/yiang
// NO redistribution, reuse or change without written permission.
///////////////////////////////////////////////////////////////////////////////////


function loadPage(index) {
	index = index  || 0;

	 $(document).ajaxError(function(event, request, settings){
   		alert("<li>Error requesting page " + settings.url + "</li>");
 	});
 
	// obtain the highscore list in JSON format using another AJAX request 
	$.getJSON("./php/highscore.php",function(data) {
		
		$("#highscore_pageselect").html("<b>"+data.pages+"</b>");
		
		for (var e in data.items) {
			var entry = data.items[e];
			$("#hs").append("<tr><td>"+entry.rank
				+"</td><td>"+entry.player
				+"</td><td>"+entry.country
				+"</td><td>"+entry.score+"</td></tr>"
			);
		}
	});
}


$(document).ready(function(){
	//main(); // in main.js, fires the visual fx logic
	
	loadPage();
})
