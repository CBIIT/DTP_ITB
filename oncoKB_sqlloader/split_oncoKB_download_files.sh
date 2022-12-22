#!/bin/bash
working_dir="${PWD}/download_org"

# run example: ./split_oncoKB_download_files.sh data_mutations.txt 17 maf_file
# download_dir="/c/Users/zhouy17/Downloads/cellline_nci60.tar/cellline_nci60/cellline_nci60"
download_dir="C/Temp/test_sqlldr/sqlloader-files/cellline_nci60.tar/cellline_nci60/cellline_nci60"
filename="${download_dir}/data_mutations.txt"
splitcolumn=17
target_dir="${download_dir}/maf_file"

#filename="${download_dir}/$1"
#splitcolumn=$2  
#target_dir="${download_dir}/$3"

echo "$download_dir $filename $splitcolumn $target_dir"

uni_values=` awk -F'\t' -v sc=$splitcolumn '{print $sc}' $filename|sort -u` 

echo ${uni_values}

current_time=$(date "+%Y.%m.%d-%H.%M.%S")

echo "Starting processing $filename at $current_time"

if [[ ! -e $target_dir ]]; then
	mkdir $target_dir
fi

echo ${target_dir}

for maf_id in ${uni_values}
do
    echo ${maf_id}
	head -2 $filename > $target_dir/${maf_id}.variants.maf
	#egrep $maf_id $filename >> $target_dir/${maf_id}.variants.maf
	awk -F'\t' -v sc=$splitcolumn -v mid=$maf_id '{if ($sc == mid) print $0}' $filename >> $target_dir/${maf_id}.variants.maf
	echo "${maf_id}.variants.maf is generated"
done

current_time=$(date "+%Y.%m.%d-%H.%M.%S")

echo "Done processing $filename at $current_time"
mv $filename $filename_$current_time
mv $target_dir ${target_dir}_${current_time}


