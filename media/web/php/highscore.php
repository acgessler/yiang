

<?php

/* API:

itemcnt=n

Specify number of items per page. Must be a valid positive integer.


page=n

Specify zero-based page index. Must be a valid and positive integer. 
Empty or non-existent pages yield an empty result set, too.



*/
include 'config.php';
include 'opendb.php';

$itemcnt = $_GET["itemcnt"];
if (!$itemcnt ) {
	$itemcnt = 20;	
}

if ($itemcnt > 1000) {
	die("itemcnt over 1000 not supported");
}

$page = $_GET["page"];
if ($page === null) {
	$page = 0;
}

// Debugging, comment later
$myFile = "log1.txt";
$fh = fopen($myFile, 'a') or die("can't open file");
fwrite($fh, "GET page=$page itemcnt=$itemcnt\n");
fclose($fh);


$query = "SELECT COUNT(*) FROM entries;"; 
$result = mysql_query($query) or die ("Querying the database fails #1");
$pages = (int) ( mysql_result($result, 0) / $itemcnt );

$minrank = $itemcnt*$page;
$query = "SELECT player,score,country,date FROM entries ORDER BY score DESC LIMIT $itemcnt OFFSET $minrank;";
$result = mysql_query($query) or die ("Querying the database fails #2");

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
