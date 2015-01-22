<?php

if ($_POST['srcid']) {
    $srcid = $_POST['srcid'];
} else {
  print "POST parsing error";
};


##### MySQL init:
require_once "PEAR/MDB2.php";
## DSN constructed from parameters
$dsn = "mysql://wwwuser@192.168.1.25/object_test_db";
$mdb2 =& MDB2::connect($dsn);
if (PEAR::isError ($mdb2))
    die ("Cannot connect: " . $mdb2->getMessage () . "\n");


## Get the column names from table:
$select_str = "DESCRIBE source_test_db.caltech_classif_summary";
$result =& $mdb2->query($select_str);
if (PEAR::isError($result)) {
  $result =& $mdb2->query($select_str);
  die($result->getMessage() . '<br />' . $result->getDebugInfo());
}

$col_names = array();
$table_data = array();
while ($row_array = $result->fetchRow()) {
  $col_names[] = $row_array[0];
  $table_data[] = array();
}
$result->free();

### Get the table values:
$select_str = "SELECT * FROM source_test_db.caltech_classif_summary";
$result =& $mdb2->query($select_str);
if (PEAR::isError($result)) {
  $result =& $mdb2->query($select_str);
  die($result->getMessage() . '<br />' . $result->getDebugInfo());
}

while ($row_array = $result->fetchRow()) {
  $i_col = 0;
  for ($i=0; $i<count($row_array); $i++){      
    $table_data[$i][] = $row_array[$i];
    $i_col++;
  };
}
$result->free();

$output_array = array("table_data" => $table_data, "col_names" => $col_names);
echo json_encode($output_array);

?>
