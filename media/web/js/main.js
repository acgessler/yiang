// A bit of fancy jquery magic paired up with a bit of AJAX to show the game background

// (c) Alexander C. Gessler, 2010
// www.greentoken.de/yiang
// NO redistribution, reuse or change without written permission.

tile_size_x = 5;
tile_size_y = 3;

tiles_x = 80;
tiles_y = 25;

cells_x = tiles_x * tile_size_x;
cells_y = tiles_y * tile_size_y;

lines = new Array();



function Tile(lines){
    this.lines = lines;
	this.getTextLines = function() {
		return this.lines;
	}
	
	this.update = function() {
		
	}
    return this;
}

function AnimTile(lines,speed){
    this.anim_lines = lines;
	this.lines = lines[0];
	this.speed = speed;
	this.cur_anim = 0;
	
	this.getTextLines = function(x,y) {
		return this.anim_lines[this.cur_anim % this.anim_lines.length];
	}
	
	this.update = function(tick) {
		this.cur_anim += 1;
	}
    return this;
}


entity_showcase = {};
entity_showcase["PL"] = new Tile([
"  ____", 
"o|'O.O|o", 
" |___-|", 
"  /  \\ ", 
" o____o ", 
" _|  |_"
]);

entity_showcase["A0"] = new Tile([
"*****", 
"\\\\-\\\\", 
"99999"
]);

entity_showcase["A1"] = new Tile([
"/====",
"\\\\\\\\\\",
"====="
]);

entity_showcase["A2"] = new Tile([
"===\\",
"\\\\\\\\\\",
"====="
]);

entity_showcase["A3"] = new Tile([
"/===\\",
"\\\\\\\\\\",
"====="
]);

entity_showcase["A4"] = new Tile([
"/===\\",
"\\\\\\\\\\",
"\\===/"
]);

entity_showcase["A5"] = new Tile([
"|===|",
"\\\\\\\\\\",
"|===|"
]);

entity_showcase["A6"] = new Tile([
"=====",
"\\\\\\\\\\",
"\===/"
]);

entity_showcase["A8"] = new Tile([
" ___",
"/   \\",
"\\___/"
]);

entity_showcase["A9"] = new Tile([
" ___", 
"[___]", 
"[___]", 
"[___]"
]);

entity_showcase["DA"] = new AnimTile([[
"|Dan|", 
"|ger|", 
"|   |"
],[
"|   |", 
"|Dan|", 
"|ger|"
],[
"|   |", 
"|Dan|", 
"|   |"
],[
"|   |", 
"|   |", 
"|   |"
],[
"|Dan|", 
"|   |", 
"|ger|"
],[
"|Dan|", 
"|   |", 
"|   |"
]]);

entity_showcase["S1"] = new Tile([
"[(.)]",
"[   ]"
]);

entity_showcase["S1"] = new Tile([
"AAAAA",
"AAAAA",
"AAAAA"
]);

cdict = {
    "r": "red",
    "g": "green",
    "b": "blue",
    "y": "yellow",
    "p": "pink",
    "w": "white",
    "_": "white"
};


testMap1 = 
"<python stub>\n"+
"                                                                  _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"                                                                  _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"                                                                  _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"   gPL                                                            _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"                                                                  _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"            gPL                                                   _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"                                                                  _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"                                                                  _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"                                                                  _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"                                             rE2               rFI_DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"                                 _A1_A0_A0_A0_A2                  _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+
"            _S0               _A1_B0_B0_B0_A5                  rFI_DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+                                                                                                                      
"            _A1            _A1_B0_B0_B0_B0_A5                     _DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n"+                                                                                                                                         
"_A0_A0_A0_A0_A0_A0_A0_A0_A0_B0_B0_B0_B0_B0_B0_A0_A0_A0_A0_A0_A0_A0_DA_DA_DA_DA_DA_DA_DA_DA_DA_DA\n";       

function placeTile(tile, x, y, color){
	var tlines = tile.getTextLines();
    for (var yy = y * tile_size_y; yy < y * tile_size_y + tlines.length; ++yy) {
        line = tlines[yy - y * tile_size_y];
        for (var xx = x * tile_size_x; xx < x * tile_size_x + line.length; ++xx) {
            lines[yy][xx] = [line[xx - x * tile_size_x], color, (tile ? tile : null)];
			tile = undefined;
        }
    }
}

function loadMap(map){
    clearPlayGround();
    
    var maplines = map.split("\n");
    for (var x = 1; x < Math.min(tiles_y,maplines.length); ++x) {
        curline = maplines[x];
        
        for (var y = 0; y < Math.min(tiles_x*3, curline.length); y += 3) {
            ccode = curline.charAt(y);
            tcode = curline.charAt(y + 1) + curline.charAt(y + 2);
            
            if (ccode == "." || ccode == "") {
                continue;
            }
                   
     
            ccode = cdict[ccode];
            if (ccode == undefined ) {
            	ccode = "#ffffff";
            }             
			
	
			tcode = entity_showcase[tcode];			
			if (tcode == undefined ) {
				continue;
			}
			
			placeTile(tcode,y/3,x-1,ccode);     
        }
    }

    updatePlayGround(false);
}

function loadMapFromServerAsync(index){
	var url = '/yiang/levels/' + index + ".txt";
    $.ajax({
      	url:url,
      	data:{},
      	dataType:"text",
	  
      	success: function(data, status, xmlhttp)	{ 
	  		loadMap(data);
	  	},
      	error: function(xhr,err,e)	{ 
	  		alert( "Error: " + err ); 
		}
	});
}

function updatePlayGround(update){
	
	if (update==undefined) {
		update = false;
	}
	
    var text = "<pre>";
    for (var i = 0; i < lines.length; ++i) {
        var cur_color = "white";
        text += "<span class=\"tile_white\">";
        for (var x = 0; x < lines[i].length; ++x) {
            var elem = lines[i][x];
            if (!elem) {
                continue;
                
            }        
			if (update && elem.length>2 && elem[2] != null) {
				elem[2].update();
				//placeTile(elem[2],x,i);
			}
			
			if (elem[1] != cur_color) {
                text += "</span><span class=\"tile_" + elem[1] + "\">";
				cur_color = elem[1];
            }			
            text += elem[0];
        }
        text += "</span> <br />";
    }
    
    text += "</pre>";
    $('div.game').html(text);
}

function clearPlayGround(){
    for (var i = 0; i < cells_y; ++i) {
        lines[i] = new Array();
        for (var x = 0; x < cells_x; ++x) {
            lines[i][x] = [" ", "white",null];
        }
    }
}

function setupPlayGround(){

    clearPlayGround();
    //loadMapFromServerAsync(1);
	
	loadMap(testMap1);
	
	$(document).everyTime("1000ms",function() {
		updatePlayGround(true);	
	});
}

$.fn.wait = function(time, type){
    // http://docs.jquery.com/Cookbook/wait
    time = time || 1000;
    type = type || "fx";
    return this.queue(type, function(){
        var self = this;
        setTimeout(function(){
            $(self).dequeue();
        }, time);
    });
};

$(document).ready(function(){

    $("div.main").hide().wait(1000).fadeIn(1000, function(){
    });
    
    $('div.header').hide().animate({
        opacity: "show",
        top: '+=30px',
    }, 500, function(){
    });
    
    setupPlayGround();
});

