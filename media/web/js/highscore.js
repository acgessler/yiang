// logic to obtain the latest highscores from the server

///////////////////////////////////////////////////////////////////////////////////
// (c) Alexander C. Gessler, 2010
// www.greentoken.de/yiang
// NO redistribution, reuse or change without written permission.
///////////////////////////////////////////////////////////////////////////////////

String.prototype.trim = function () {
    return this.replace(/^\s*/, "").replace(/\s*$/, "");
}

function cleanupPage() {
	// wipe the entire highscore table 
	$("#hs tr").not("#hs_head").remove();
}

function loadPage(index,itemcnt,byname,previous) {
	var index = index  || 0;
	var itemcnt = itemcnt || 30;

 
	// obtain the highscore list in JSON format using another AJAX request 
	$.getJSON("./php/highscore.php?itemcnt=" + itemcnt + "&page="+index+(byname ? ("&byname="+byname) : "" ),function(data) {			
		var cnt = data.pages, pselect = "<b>";
		
		if (byname) {
			if ($.isEmptyObject(data)) {
				return;
			}
			else {
				index = data.thispage;
				// crucial! need to unbind previous handler or more than one of them
				// is active (in nested closures -> hell is here)
				$("#search").unbind("keydown");
			}
		}
		
		function add(n) {
			pselect += (n==index ? "<i>"+(n+1)+"</i>" : "<a class=\"choosep\" id=\""+n+"\">" + (n+1) + "</a>" )+"&nbsp;";			
		};	
		var min = Math.min, max = Math.max;
		
		var pad = 1, end = 3;
		for (var a=0; a < min(end,cnt,index-pad); ++a) {
			add(a);
		}
		
		if (index > end) {
			pselect += "...&nbsp;"
		}
		for (var a = max(index - pad, 0); a < min(cnt,index + pad+1); ++a) {
			add(a);
		}
		
		if (cnt-end > index + pad) {
			pselect += "...&nbsp;"
			for (var a = max(cnt - end, 0); a < cnt; ++a) {
				add(a);
			}
		}
		
		pselect += "</b>"
		$("#highscore_pageselect").html(pselect);
		

		$("#search").keydown(function(e){
	         if ((e.which && e.which == 13) || (e.keyCode && e.keyCode == 13)) {
                 e.preventDefault();
                 
                 cleanupPage();
		 //data.items = [];
                 loadPage(index, itemcnt, $(this).val().trim());

	         }
	     });
		 
		 $(".choosep").click(function(){
	         cleanupPage();

		 // see note above. crucial as well.
	 	 $(".choosep").unbind("click");
	         loadPage(parseInt($(this).attr("id")));
	     });
		
		for (var e in data.items) {
			var entry = data.items[e];
			var open = null, close = null;
			
			switch (entry.rank) {
				case 0: 
					open = '<font color="#cdcd00"><b><u>';
					close = "</u></b></font>";
					break;
				case 1: 
					open = '<font color="#cdcdcd"><b>';
					break;
				case 2: 
					open = '<font color="#cd6020"><b>';
					break;
				default:
					close = "";
			}
			
			if (entry.player === byname) {
				open = '<font color="#ff0000"><b><u>';
				close = null;
			}
			
			if (close === null) {
				close = "</b></font>";
			}
			if (open === null) {
				open = "";
			}
			
			var app = "<tr><td>"+open+entry.rank+close
				+"</td><td>"+open+entry.player+close
				+"</td><td>"+open+entry.country+close
				+"</td><td>"+open+entry.score/100000+close+
			"</td></tr>";
				
			$("#hs").append(app);
		}
	});
}


$(document).ready(function(){
	//main(); // in main.js, fires the visual fx logic
	
	$(document).ajaxError(function(event, request, settings){
   		alert("<li>Error requesting page " + settings.url + "</li>");
 	});
	 
	loadPage();
})
