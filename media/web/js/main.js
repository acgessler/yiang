// A bit of fancy jquery magic paired up with a bit of AJAX to show the game background

///////////////////////////////////////////////////////////////////////////////////
// (c) Alexander C. Gessler, 2010
// www.greentoken.de/yiang
// NO redistribution, reuse or change without written permission.
///////////////////////////////////////////////////////////////////////////////////

tile_size_x = 5;
tile_size_y = 3;

tiles_x = 80;
tiles_y = 25;

cells_x = tiles_x * tile_size_x;
cells_y = tiles_y * tile_size_y;

current_plane = 1;
update_ms = 200;

lines = new Array();
entities = new Array();


// -----------------------------------------------------------------------------------
// Each class serves as factory class for a specific entity class, i.e.
// Tile.instance() yields an object of type TileInstance() which can then
// be placed on the game area using TileInstance.setPosition() and addEntity().
// -----------------------------------------------------------------------------------
function Tile(lines){
    this.lines = lines;
    return this;
}

Tile.prototype.instance = function() {
	return new TileInstance(this);
};

function AnimTile(lines,speed){
    this.anim_lines = lines;
	this.speed = speed;
    return this;
}

AnimTile.prototype.instance = function() {
	return new AnimTileInstance(this);
};

// ---------------------------------------------------------
function TileInstance(outer) {
	this.outer = outer;
}

TileInstance.prototype.setPosition = function(x,y) {
	this.x = x;
	this.y = y;
}

TileInstance.prototype.setColor = function(color) {
	this.color = color;
}

TileInstance.prototype.draw = function() {

	var tlines = this.getTextLines();
    for (var yy = this.y * tile_size_y; yy < this.y * tile_size_y + tlines.length; ++yy) {
        line = tlines[yy - this.y * tile_size_y];
        for (var xx = this.x * tile_size_x; xx < this.x * tile_size_x + line.length; ++xx) {
            lines[yy][xx] = [line[xx - this.x * tile_size_x], this.color];
        }
    }
}
TileInstance.prototype.update = function() {
	// the default update does actually nothing.
}

TileInstance.prototype.getTextLines = function() {
	return this.outer.lines;
}

// ---------------------------------------------------------
function AnimTileInstance(outer){
    this.outer = outer;
    this.cur_anim = 0;
	this.cur_tick = 0;
    
    return this;
}

AnimTileInstance.prototype = new TileInstance();
AnimTileInstance.prototype.constructor = AnimTileInstance;
AnimTileInstance.prototype.update = function(){
    ++this.cur_tick;
	this.updateAnim();
}

AnimTileInstance.prototype.updateAnim = function(){
	this.cur_anim =  Math.floor(((update_ms/1000.0)*this.cur_tick / (this.outer.speed/this.outer.anim_lines.length))) 
		% this.outer.anim_lines.length;
}

AnimTileInstance.prototype.getTextLines = function(x, y) {
    return this.outer.anim_lines[this.cur_anim];
}

// ***********************************************************************************
// These are the actual entity definitions. Most are simple Tiles, only few
// are animated (AnimTile) and probably even interactive (i.e. Enemy, Player).
// ***********************************************************************************

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
]],3.0);

entity_showcase["S0"] = new AnimTile([[
"/...\\",
".0,1.",
"\\.../"
],[
"/- -\\",
".0,1.",
"\\.../"
],[
"/...\\",
".0,1|",
"\\.../"
],[
"/...\\",
".0,1.",
"\\- -/"
],[
"/...\\",
"|0,1.",
"\\.../"
]],3.0);

entity_showcase["S1"] = new AnimTile([[
"[(.)]",
"[   ]"
],[
"[(')]",
"[   ]"
],[
"[(\")]",
"[   ]"
],[
"((.))",
"[   ]"
],[
"[(\")]",
"[   ]"
],[
"[(')]",
"[   ]"
],[
"[(.)]",
"[   ]"
]],2.0);

entity_showcase["B0"] = new Tile([
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

// -----------------------------------------------------------------------------------
/**
 * Add a specific entity to the list of active entities. This operation may
 * be deferred if this is necessary.
 * @param {Object} entity
 */
// -----------------------------------------------------------------------------------
function addEntity(entity){
    entities.push(entity)
}

// -----------------------------------------------------------------------------------
/**
 * Remove a specific entity from the list of active entities. This operation may
 * be deferred if this is necessary.
 * @param {Object} entity
 */
// -----------------------------------------------------------------------------------
function removeEntity(entity){
    entities.splice(entities.indexOf(entity), 1)
}

// -----------------------------------------------------------------------------------
/** Load a given map, specified as simple ascii text
 *
 * @param {String} map A simple string describing the map in the usual syntax, as for
 *   the offline game. This include a 'shebang' python line, which is skipped
 *   and is required to be present (i.e. '<out> = new Tile()');
 */
// -----------------------------------------------------------------------------------
function loadMap(map){
	entities = new Array();
    clearPlayGround();
    
    var maplines = map.split("\n");
    for (var x = 1; x < Math.min(tiles_y, maplines.length); ++x) {
        curline = maplines[x];
        
        for (var y = 0; y < Math.min(tiles_x * 3, curline.length); y += 3) {
            ccode = curline.charAt(y);
            tcode = curline.charAt(y + 1) + curline.charAt(y + 2);
            
            if (ccode == "." || ccode == "") {
                continue;
            }
            
            
            ccode = cdict[ccode];
            if (ccode == undefined) {
                ccode = "#ffffff";
            }
            
            
            tcode = entity_showcase[tcode];
            if (tcode == undefined) {
                continue;
            }
            
            tcode = tcode.instance();
            tcode.setPosition(y / 3, x - 1);
            tcode.setColor(ccode);
            
            addEntity(tcode);
        }
    }
    
    updatePlayGround(false);
	
	// XXX
	$('div#game'+current_plane).animate({
        opacity: "show"
    }, 1000, function(){});
}

// -----------------------------------------------------------------------------------
/**
 * Load a map asychronously.
 * @param {Object} index Map index, same as for the offline game.
 */
// -----------------------------------------------------------------------------------
function loadMapFromServerAsync(index){
    var url = '/yiang/levels/' + index + ".txt";
    $.ajax({
        url: url,
        data: {},
        dataType: "text",
        
        success: function(data, status, xmlhttp){
            loadMap(data);
        },
        error: function(xhr, err, e){
            alert("Error: " + err);
        }
    });
}

// -----------------------------------------------------------------------------------
/**
 * Clear the drawing plane and call draw() on all entities.
 */
// -----------------------------------------------------------------------------------
function drawEntities(){
    clearPlayGround();
    for (var entity in entities) {
        entities[entity].draw();
    }
}

// -----------------------------------------------------------------------------------
/** 
 * Call update() on all entities.
 */
// -----------------------------------------------------------------------------------
function updateEntities(){
    for (var entity in entities) {
        entities[entity].update();
    }
}

// -----------------------------------------------------------------------------------
/**
 * Update the game area - this includes calling drawEntities() and updateEntities()
 * unless explicitly disabled by parameters. Afterwards, the
 * actual HTML code for the drawing plane is re-generated and comitted to the DOM.
 * @param {Object} update
 * @param {Object} draw
 */
// -----------------------------------------------------------------------------------
function updatePlayGround(update, draw){
    update = (update == undefined ? true : update);
    draw = (draw == undefined ? true : draw);
    
    if (update) {
        updateEntities();
    }
    
    if (draw) {
        drawEntities();
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
            
            if (elem[1] != cur_color) {
                text += "</span><span class=\"tile_" + elem[1] + "\">";
                cur_color = elem[1];
            }
            text += elem[0];
        }
        text += "</span> <br />";
    }
    
    text += "</pre>";
    $('div#game'+current_plane).html(text);
}

// -----------------------------------------------------------------------------------
/**
 * Clear the whole game area (represented by the global lines array).
 */
// -----------------------------------------------------------------------------------
function clearPlayGround(){
    for (var i = 0; i < cells_y; ++i) {
        lines[i] = new Array();
        for (var x = 0; x < cells_x; ++x) {
            lines[i][x] = [" ", "white"];
        }
    }
}

// -----------------------------------------------------------------------------------
/** 
 * Load a specific map and setup the timer to update it regularly.
 * @param index Index of the map to be loaded, alternatively the map as string.
 */
// -----------------------------------------------------------------------------------
function setupPlayGround(index){
	//$(document).everyTime("1000ms","update"); // stop existing timers
    clearPlayGround();
    
    if (typeof(index) == "string") {
        loadMap(testMap1);
    }
    else {
        loadMapFromServerAsync(index);
    }
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


// -----------------------------------------------------------------------------------
// jQuery startup
// -----------------------------------------------------------------------------------
$(document).ready(function(){

    $("div.main").hide().wait(1000).fadeIn(1000, function(){});
    $('div.header').hide().animate({
        opacity: "show",
        top: '+=26px',
    }, 500, function(){
    });
	
	$('div#game'+0).hide();
	current_plane = 1;
	
	// some levels are too short, don't bother displaying them
	var skip = {18:1,19:1,1:1,5:1,9:1};
    
	nxt = 17;
	max = 20;
	setupPlayGround(nxt++);
	$(document).everyTime("4500ms",function() {
		$('div#game'+current_plane).animate({
        	opacity: "hide"
    	}, 1000, function(){
		});
		
		current_plane = 1-current_plane;
		
		while (nxt in skip)++nxt;
		if (nxt==max) {
			nxt=1;
		}
		while (nxt in skip)++nxt;
    	setupPlayGround(nxt++);
    });
	
	$(document).everyTime(update_ms+"ms",function() {
    	updatePlayGround(true);	
    });
});





