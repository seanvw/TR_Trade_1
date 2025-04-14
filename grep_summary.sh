#/bin/bash
# This script is used to extract specific lines from the summary files generated 
 egrep '^Total Return on Investment \(ROI\) \[before tax and' my_sharedeal_reports/*.txt | perl -ne '$foo=$.%2; print "$_" if $foo == 0' -

