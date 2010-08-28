// logic to obtain the latest highscores from the server

///////////////////////////////////////////////////////////////////////////////////
// (c) Alexander C. Gessler, 2010
// www.greentoken.de/yiang
// NO redistribution, reuse or change without written permission.
///////////////////////////////////////////////////////////////////////////////////


function loadPage(index,itemcnt) {
	index = index  || 0;
	itemcnt = itemcnt || 30;

	 $(document).ajaxError(function(event, request, settings){
   		alert("<li>Error requesting page " + settings.url + "</li>");
 	});
 
	// obtain the highscore list in JSON format using another AJAX request 
	$.getJSON("./php/highscore.php?itemcnt=" + itemcnt + "&page="+index,function(data) {
		var cnt = data.pages, pselect = "<b>";
		
		function add(n) {
			pselect += (n==index ? "<b>"+(n+1)+"<b>" : "<a class=\"choosep\" id=\""+n+"\">" + (n+1) + "</a>" )+"&nbsp;";			
		};	
		var min = Math.min, max = Math.max;
		
		var pad = 1, end = 3;
		for (a=0; a < min(end,cnt,index-pad); ++a) {
			add(a);
		}
		
		if (index > end) {
			pselect += "...&nbsp;"
		}
		for (a = max(index - pad, 0); a < min(cnt,index + pad+1); ++a) {
			add(a);
		}
		
		if (cnt-end > index + pad) {
			pselect += "...&nbsp;"
			for (a = max(cnt - end, 0); a < cnt; ++a) {
				add(a);
			}
		}
		
		pselect += "</>"
		$("#highscore_pageselect").html(pselect);
		$(".choosep").click(function() {
			$("#hs tr").not("#hs_head").remove();
			loadPage( parseInt( $(this).attr("id") ) );
		})
		
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
	
	loadPage();
})
