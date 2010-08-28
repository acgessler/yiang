<?php

$conn = mysql_connect($dbhost, $dbuser, $dbpass) or die ('Error connecting to mysql, db not accessible');
mysql_select_db($dbname);
?>