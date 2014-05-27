from datetime import datetime
import os

import config


root_dir = config.CONST['ROOT_LOG_DIR']

os.chdir(os.path.join(root_dir, 'Windows7'))
date_obj = datetime.today()
time_stamp = date_obj.strftime('%I_%M')
red_flags = open("red_flags"+time_stamp +".log", "w")

for folder, sub_folder, files in os.walk(os.getcwd()):
  for my_file in files:
    if my_file.startswith('diff_autorunsc') and os.stat(os.path.abspath(folder +'/'+my_file)).st_size > 0:
      prev_folder = folder.rpartition('/')[0]
      prev_folder = prev_folder.rpartition('/')[2]
      red_flags.write("autorunsc change in: " + prev_folder + '\n')
