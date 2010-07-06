// Tiny assert() remake.

///////////////////////////////////////////////////////////////////////////////////
// (c) Alexander C. Gessler, 2010
// www.greentoken.de/yiang
// NO redistribution, reuse or change without written permission.
///////////////////////////////////////////////////////////////////////////////////

function Assertion(notice) {
	this.msg = notice;
}

Assertion.prototype.toString = function() {
	return "ASSERT: " + this.msg;
}

function assert(cond, thisobj) {
	try { 
		if (new Function("return false == !!(" + cond + ");").apply(thisobj)) {
			throw new Assertion(cond);
		}
	}
	catch (e) {
		var str = e.toString();
		if (str != null && str.length > 6 && str.substring(0,6)=="ASSERT") {
			throw e;
		} 
		throw new Error("ASSERT '"+cond+"' caused exception: "+str);
	}
}

// Comment this to enable assertions
//function assert() {}
