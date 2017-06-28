<?php

function search($file) {
    if (is_file($file) && strpos($file, "01.md")) {
		print("FILE: ".$file."\n");
		$handle = fopen($file, "r");
		$new_list = true;
		$level_inds = array();
		$inds_level = array();
		$level_bullets = array();
		$level = 0;
		$content = "";
		$num = 0;
		$last_line_was_bullet = false;
		if ($handle) {
			while (! feof($handle)) {
				++$num;
				$line = fgets($handle);
				print("LINE: ".$line."\n");
				preg_match('/^( *)(-|\*|[0-9]+\.)\s+(.*)$/', $line, $matches);
				if($matches) {
					$ind = strlen($matches[1]);
					$bullet = $matches[2];
					$text = $matches[3];
					if($ind < $level_inds[0]){
						print("STARTING OVER WITHIN A LIST!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
						$new_list = true;
						$level_inds = array();
						$inds_level = array();
						$level_bullets = array();
						$level = 0;
					}
					if(! $new_list ){
						if($ind > $level_inds[$level]) {
							if($last_line_was_bullet && preg_match('/^[0-9]+\./', $level_bullets[$level])){
								$content .= "\n";
							}
							++$level;
							$level_inds[$level] = $ind;
							$inds_level[$ind] = $level;
							$level_bullets[$level] = $bullet;
							print("LEVEL NOW ".$level." (IND ".$ind.")\n");
						}
						else if(isset($inds_level[$ind])){
							$level = $inds_level[$ind];
							print("LEVEL NOW ".$level." (IND ".$ind.")\n");
						}
						else {
							print("FOUND A BAD BULLET!!! ".$file."\n");
							print("LINE ".$num.": ".$line."\n");
							print("LEVEL ${level}, IND ${ind}");
							print_r($level_inds);
							print_r($inds_level);
							exit(1);
						}
					} else {
						$new_list = false;
						$level_inds[$level] = $ind;
						$inds_level[$ind] = $level;
						$level_bullets[$level] = $bullet;
						print("START NEW LIST\nLEVEL NOW ".$level." (IND ".$ind.")\n");
					}
					$content .= str_repeat("    ", $level).$bullet.' '.$text."\n";
					$last_line_was_bullet = true;
				}
				else if(trim($line)){
					print("STARTING OVER!\n");
					$new_list = true;
					$level_inds = array();
					$inds_level = array();
					$level_bullets = array();
					$level = 0;
					if($last_line_was_bullet){
						$content .= "\n";
					}
					$last_line_was_bullet = false;
					$content .= $line;
				}
				else {
					$content .= "\n";
					$last_line_was_bullet = false;
				}
			}
			print("==============================\n");
//			print($content);
			fclose($handle);
			file_put_contents($file, $content);
		} else {
			print("ERROR OPENING FILE: ".$file."\n");
		}
    } else if (is_dir($file)) {
        // file is a directory
        $base_dir = $file;
        $dh = opendir($base_dir);
        while (($file = readdir($dh))) {
            if (($file != '.') && ($file != '..')) {
                // call search() on the found file/directory
                search($base_dir . '/' . $file);
            }
        }
        closedir($dh);
    }
}

$dir = $argv[1];
print($dir."\n");
$found = array();
search($dir);

