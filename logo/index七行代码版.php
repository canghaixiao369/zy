<?php
$dir = './images/';//图片文件夹
$files = glob($dir . '*.*');
$image = $files[array_rand($files)];

header("Location: {$image}");
exit;
?>
