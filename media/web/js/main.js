// A bit of fancy jquery magic paired up with a bit of AJAX to show the game background

///////////////////////////////////////////////////////////////////////////////////
// (c) Alexander C. Gessler, 2010
// www.greentoken.de/yiang
// NO redistribution, reuse or change without written permission.
///////////////////////////////////////////////////////////////////////////////////


// Global settings
tile_size_x = 5;
tile_size_y = 3;

tiles_x = 80;
tiles_y = 25;

cells_x = tiles_x * tile_size_x;
cells_y = tiles_y * tile_size_y;

current_plane = 1;
update_ms = 200;
cur_tick = 0;

show_stats = false;
// ---------------------------------------------------------
stats = { // debug statistics, can be shown with the 'D' key
	entities_total : 0,
	entities_visible : 0,
	seconds: 0,
	current_map: -1, // -1 means 'test map' or 'no map' 
	map_changes: 0,
	
	sentinel: 0  
}
// ---------------------------------------------------------

lines = [];
entities = [];
visible_entities = [];
map_cache = [];

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

// ---------------------------------------------------------
function AnimTile(lines,speed){
	//assert("lines",this);
	
    this.anim_lines = lines;
	this.speed = speed;
	this.num_frames = lines.length;
    return this;
}

AnimTile.prototype.instance = function() {
	return new AnimTileInstance(this);
};

// ---------------------------------------------------------
DIR_HORIZONTAL = 0, DIR_VERTICAL = 1;
function SmallTraverser(lines,speed,dir){
	//assert("lines",this);
	
    this.anim_lines = lines;
	this.speed = speed;
    return this;
}

SmallTraverser.prototype.instance = function() {
	return new SmallTraverserInstance(this);
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

TileInstance.prototype.isVisible = function(x0,y0,w,h) {
    return true;
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
	this.updateAnim();
}

AnimTileInstance.prototype.updateAnim = function(){
	this.cur_anim =  Math.floor(((update_ms/1000.0)*cur_tick / (this.outer.speed/this.outer.num_frames))) 
		% this.outer.anim_lines.length;
}

AnimTileInstance.prototype.getTextLines = function(x, y) {
    return this.outer.anim_lines[this.cur_anim];
}

// ---------------------------------------------------------
function SmallTraverserInstance(outer){
    this.outer = outer;
    this.cur_anim = 0;
	this.cur_tick = 0;
    
    return this;
}

SmallTraverserInstance.prototype = new AnimTileInstance();
SmallTraverserInstance.prototype.constructor =SmallTraverserInstance;
SmallTraverserInstance.prototype.update = function(){
	this.updateAnim();
}

SmallTraverserInstance.prototype.getTextLines = function(x, y) {
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
 * Get the size of the visible screen, in pixels, as a dict with 
 * 'width' and 'height' as keys. Return null if the information is not available.
 */
// -----------------------------------------------------------------------------------
function getViewportSize() {
	// http://www.geekdaily.net/2007/07/04/javascript-cross-browser-window-size-and-centering/
	var w = 0;
	var h = 0;

	//IE
	if(!window.innerWidth){
		//strict mode
		if(!(document.documentElement.clientWidth == 0))
		{
			w = document.documentElement.clientWidth;
			h = document.documentElement.clientHeight;
		}
		//quirks mode
		else
		{
			w = document.body.clientWidth;
			h = document.body.clientHeight;
		}
	} 
	// w3c
	else
	{
		w = window.innerWidth;
		h = window.innerHeight;
	}
	return {width:w,height:h};
}

// -----------------------------------------------------------------------------------
/**
 * Add a specific entity to the list of active entities. This operation may
 * be deferred when necessary.
 * @param {Object} entity
 */
// -----------------------------------------------------------------------------------
function addEntity(entity){
    entities.push(entity)
}

// -----------------------------------------------------------------------------------
/**
 * Remove a specific entity from the list of active entities. This operation may
 * be deferred when necessary.
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
 * @param {int} index original index of the map, may be left out.
 */
// -----------------------------------------------------------------------------------
function loadMap(map,index){
	index = index || -1;
	
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
    
	gatherVisibleEntities();
    updatePlayGround(false);
	
	// XXX
	$('div#game'+current_plane).animate({
        opacity: "show"
    }, 1000, function(){});
	
	stats.current_map = index;
	++stats.map_changes;
}

// -----------------------------------------------------------------------------------
/**
 * Load a map asychronously.
 * @param {Object} index Map index, same as for the offline game.
 */
// -----------------------------------------------------------------------------------
function loadMapFromServerAsync(index){
	// first check if we have this map already
	if (index in map_cache) {
		loadMap(map_cache[index],index);
		return;
	}
    var url = '/yiang/levels/' + index + ".txt";
    $.ajax({
        url: url,
        data: {},
        dataType: "text",
        
        success: function(data, status, xmlhttp){
            loadMap(data,index);
			map_cache[index] = data;
        },
        error: function(xhr, err, e){
            alert("Error: " + err);
        }
    });
}

// -----------------------------------------------------------------------------------
/**
 * Update the 'visible_entities' array with a up-to=date list of all visible
 * entities, that is entities that are presumably visible in the user's current
 * viewport. Of course, this depends on our ability to determine the current
 * screen size. If we can't find proper values, all entities are assumed visible.
 */
// -----------------------------------------------------------------------------------
function gatherVisibleEntities() {
	visible_entities = new Array();
	
	var screen = getViewportSize();
	if (screen == null || screen.width <= 0 || screen.height <= 0) {
		// we make a copy because we need to emulate the behaviour that
		// visible_entities is not necessarily up-to-date.
		visible_entities = entities.clone();
	}
	
	for (var entity in entities) {
		if (entities[entity].isVisible(0,0,screen.width,screen.height)) {
			visible_entities.push(entities[entity]);
		}
	}
}

// -----------------------------------------------------------------------------------
/**
 * Clear the drawing plane and call draw() on all entities.
 */
// -----------------------------------------------------------------------------------
function drawEntities(){
    clearPlayGround();
    for (var entity in visible_entities) {
        entities[entity].draw();
    }
}

// -----------------------------------------------------------------------------------
/** 
 * Call update() on all entities.
 */
// -----------------------------------------------------------------------------------
function updateEntities(){
	++cur_tick;
    for (var entity in visible_entities) {
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

	// update stats
	stats.entities_total = entities.length;
	stats.entities_visible = visible_entities.length;
	stats.seconds = update_ms*cur_tick/1000.0;
	if (show_stats) {
		$('div.stats').html("<b>***DEBUG***</b> ('D' to toggle)<br/>entities_total: "+stats.entities_total+"<br />"+
			"entities_visible: "+stats.entities_visible+"<br />"+
			"seconds_running: "+stats.seconds+"<br />"+
			"current_map: "+stats.current_map+"<br />"+
			"map_changes: "+stats.map_changes+"<br />");
	}

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

// -----------------------------------------------------------------------------------
/**
 * Check if a specific ASCII code matches a character. Ignore case
 * @param {Object} code ASCII code, 0..127
 * @param {Object} c Character to check for, may be either lower or upper case.
 */
// -----------------------------------------------------------------------------------
function matchCodeI(code,c) {
	var icode = parseInt(code); // manual version, might be faster than fromCharCode()
	assert(icode > 0 && icode < 128 && c.length, this);
	var ch = c.charCodeAt(0);
	
	if (icode >=  97 && icode <= 122) {
		icode -= 32;
	}
	if (ch >=  97 && ch <= 122) {
		ch -= 32;
	}
	return icode==ch;
}

// -----------------------------------------------------------------------------------
/**
 * Setup basic keyboard event handlers (i.e. debug gui).
 */
// -----------------------------------------------------------------------------------
function setupBasicKeyHandlers() {
	$(document).keydown(function(event) {
		if (matchCodeI(event.keyCode, "d" )) {
			$("div.stats").animate({
        		opacity: ( (show_stats = !show_stats) ? "show" : "hide" )
    		}, 1000, function(){
				// empty
			});
		}
	});
}

// -----------------------------------------------------------------------------------
// jQuery customization
// -----------------------------------------------------------------------------------
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
	
	// slowly fade the main info field in.
    $("div.main").hide().wait(1000).fadeIn(1000, function(){
		var old_opacity = parseFloat($(this).css("opacity"));
		assert(old_opacity > 0.0 && old_opacity <= 1.0, this);
		
		$(this).mouseenter(function() { // hover()
			$(this).animate({
				opacity: 1.0
			}, 500, function() {
				// empty
			});
		});		
		
		$(this).mouseleave(function() {
			$(this).animate({
				opacity: old_opacity
			}, 500, function() {
				// empty
			});
		});
		
		// register an additional timer to deactivate the main info field
		// automatically after a specific time interval.
		
		$(this).everyTime("15s",function() {
    		$(this).animate({
				opacity: old_opacity
			}, 500, function() {
				// empty
			});
    	});
    			
	});
	
	// scroll the header
    $('div.header').hide().animate({
        opacity: "show",
        top: '+=26px',
    }, 500, function(){
		// empty
    });
	
	$('div#game'+0).hide();
	current_plane = 1;
	
	// some levels are too short, don't bother displaying them
	var skip = {18:1,19:1,1:1,5:1,9:1,16:1};
    
	nxt = 17;
	max = 20;
	setupPlayGround(nxt++);
	$(document).everyTime("6500ms",function() {
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
	
	setupBasicKeyHandlers();
});





