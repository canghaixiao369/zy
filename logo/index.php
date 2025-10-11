<?php
// 1. 定义图片存放的文件夹路径（根据实际位置修改，确保正确）
$imageDir = './images/'; 
// 允许的图片格式（可按需添加，如gif、svg）
$allowTypes = ['jpg', 'jpeg', 'png', 'webp'];

// 2. 读取文件夹内所有符合条件的图片，生成路径列表
$imagePaths = [];
if (is_dir($imageDir) && $handle = opendir($imageDir)) {
    while (false !== ($file = readdir($handle))) {
        // 排除系统默认的 "." 和 ".." 目录
        if ($file != '.' && $file != '..') {
            // 获取文件后缀并转小写，判断是否为允许的图片格式
            $fileExt = strtolower(pathinfo($file, PATHINFO_EXTENSION));
            if (in_array($fileExt, $allowTypes)) {
                // 拼接图片的完整URL路径（关键：确保是浏览器可访问的地址）
                $imagePaths[] = $imageDir . $file;
            }
        }
    }
    closedir($handle);
}

// 3. 处理异常：若文件夹无图片，显示提示
if (empty($imagePaths)) {
    die("错误：{$imageDir} 文件夹中未找到符合格式的图片，请检查路径和文件");
}

// 4. 随机选择一张图片的路径
$randomImgPath = $imagePaths[array_rand($imagePaths)];

// 5. 关键：临时跳转直接访问图片地址
header("Location: {$randomImgPath}");
exit; // 跳转后终止脚本，避免后续代码执行
?>
