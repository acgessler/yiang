

<?php

/* 

--------------------------------------------------------------------------------
API:
--------------------------------------------------------------------------------

Parameters (HTTP GET)
==========

itemcnt=n

  Specify number of items per page. Must be a valid positive integer.


page=n

  Specify zero-based page index. Must be a valid and positive integer. 
  Empty or non-existent pages yield an empty result set, too.

byname=<name>

  If present, specifies the user-name to look for and returns the
  site which it can be found on. The page parameters is ignored then.
  If the user is not found in the database, an empty json object
  is returned.


Return (JSON)
======

... sample:
{ "pages":5000, "thispage":0, "items": [
  { "rank": 0, "player": "U1fq-ppZeiE", "score": 99985222, "country": "GB", "date": "1861-03-10 15:09:14" },
  { "rank": 1, "player": "ymZrAcGf", "score": 99985128, "country": "AU", "date": "1939-12-11 02:06:56" }
]}

thispage   echoes the given or assumed value for `page`
pages      is the number of highscore pages for this itemcnt
items      is the result set, or an empty set of the requested page does not exist

  score      is specified in 1/100000 USD
  country    is an iso country code
  date       is an iso date plus time
  rank       is zero-based
  player     is maximally 32 characters long, nonempty, alphanumerics plus innocuous special characters


Errors
======

In case of failure, normal PHP errors are printed out. In such cases JSON 
parsing is doomed to fail too, so this is the best sign.


*/
include 'config.php';
include 'opendb.php';


function dbfail($occasion) {
	die("Failure to query database: #$occasion");
}


$itemcnt = $_GET["itemcnt"];
if (!$itemcnt ) {
	$itemcnt = 20;	
}

if ($itemcnt > 1000) {
	die("itemcnt over 1000 not supported");
}

$byname = $_GET["byname"];

$page = $_GET["page"];
if ($page === null) {
	$page = 0;
}

// Debugging, comment later
$myFile = "log1.txt";
$fh = fopen($myFile, 'a') or die("can't open file");
fwrite($fh, "GET page=$page itemcnt=$itemcnt byname=$byname\n");
fclose($fh);


$query = "SELECT COUNT(*) FROM entries;"; 
$result = mysql_query($query) or dbfail(1);
$pages = (int) ( mysql_result($result, 0) / $itemcnt );

if ($byname) {
	$byname = mysql_real_escape_string( $byname );
	$query = "SELECT player,score FROM entries WHERE player='$byname'";
	$result = mysql_query($query) or dbfail(3);
	
	$row = mysql_fetch_array($result,MYSQL_ASSOC);
	if (!$row) {
		echo "{}";
		return;
	}

	$query = "SELECT count(*) FROM entries WHERE score > {$row['score']}";
	$result = mysql_query($query) or dbfail(6);
	$page = (int) ( mysql_result($result, 0) / $itemcnt );
}

$minrank = $itemcnt*$page;
$query = "SELECT player,score,country,date FROM entries ORDER BY score DESC LIMIT $itemcnt OFFSET $minrank;";
$result = mysql_query($query) or dbfail(2);

$json = "{ \"pages\":$pages, \"thispage\":$page, \"items\": [\n";
$have = 0;
while ($row = mysql_fetch_array($result,MYSQL_ASSOC)) {
	$rank = $have + $minrank;
	$json .= "{ \"rank\": {$rank}, \"player\": \"{$row['player']}\", \"score\": {$row['score']}, \"country\": \"{$row['country']}\", \"date\": \"{$row['date']}\" },\n";

	++$have;
}

if ($have > 0) { 
	$json = substr($json, 0,-2);
}
$json .= ']}'; 

echo $json;
include 'closedb.php';
?>
