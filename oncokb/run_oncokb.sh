#!/bin/bash
###Update the path below###
working_dir="${PWD}/maf_file"
cnv_working_dir="${PWD}/cnv_file"
clinical_working_dir="${PWD}/clinical_file"
script_dir="${PWD}/script"
output_dir="${PWD}/nci-60_oncokb"
oncokb_package="${PWD}/oncokb-annotator"
sam="nci_60_samplelist"

#Oracle credentials
username=$1
pw=$2
host=$3
service=$4

#oncoKB Key
oncokb_key=$5
echo "$username $pw"
echo "$oncokb_key"
#Andrew Change -- Backup directory and/or make new output directory
if [ -d $output_dir ]
then
	backupdir="nci-60_oncokb_`date +%Y%m%d%H%M`"
	echo "Backing up existing oncoKB output directory to folder $backupdir"
	mv "nci-60_oncokb" $backupdir
	echo "Back up done."
	mkdir "nci-60_oncokb"
else
	mkdir "nci-60_oncokb"
fi

#Generate the readme file with version info
python $oncokb_package/GenerateReadMe.py -o $output_dir/readme

#oncokb_snv/indel
for sample in `cat $sam`;
do
	##
	echo -e "Working on $sample"
	samID=`echo $sample|cut -f1 -d,`
	histo=`echo $sample|cut -f2 -d,`

	echo -e "$samID, $histo"
	#add oncokb token after -b
	python $oncokb_package/MafAnnotator.py -i $working_dir/${samID}.variants.maf -o $output_dir/${samID}.maf -t $histo -b $oncokb_key
	echo "Done oncoKB annotation!"

	#Note -- For some reason TC's script here doesn't work right on Windows, I guess.
	#I have adapted all the filter logic into my script. except the file directory changes
	python $script_dir/filterMAF_oncoKB_050522.py -f $output_dir/${samID}.maf >$output_dir/${samID}.maf.tmp
	echo "Done filterMAF!"
	
	rm $output_dir/${samID}.maf
	mv -f $output_dir/${samID}.maf.tmp $output_dir/${samID}.maf
	echo "Done on $samID"

	#Add oncoKB version to maf file
	python $script_dir/add_oncoKB_version.py -f $output_dir/${samID}.maf -i $output_dir/readme > $output_dir/${samID}.oncoKB.txt

done

#Andrew Change move oncoKB annotated TSV files to "data" folder for my ETL script
if [ -d "${PWD}/data" ]
then
	rm -R "${PWD}/data"
	mkdir "data"
else
	mkdir "data"
fi
cp ./nci-60_oncokb/*.txt ./data

#Andrew Change Run
echo "Installing necessary Python Packages"
pip install pandas --user
pip install numpy --user
pip install oracledb --user
pip install sqlalchemy --user

echo "Beginning ETL of annotated Files..."
python oncokbETL.py $username $pw $host $service

#oncokb_cnv
#for i in `cat $sam`;
#do
#	samID=`echo $i|cut -f1 -d,`
#	histo=`echo $i|cut -f2 -d,`
#	
#	echo "Paste cnv.txt"
#	paste $script_dir/hugo_list $cnv_working_dir/${samID}.temp.cnv.txt |perl $script_dir/filterCNA.pl - $i > $cnv_working_dir/${samID}.tmp2.cnv.txt
#	echo "Working CNV oncoKB annotation!"
	#add oncokb token after -b
#	python $oncokb_package/CnaAnnotator.py -i $cnv_working_dir/${samID}.tmp2.cnv.txt -o $output_dir/${samID}.cnv -t $histo -b $5
	#rm $output_dir/*.cnv.txt
#done

#oncokb_summary_patient#
#for i in `cat $sam`;
#do
	#samID=`echo $i|cut -f1 -d,`
	#histo=`echo $i|cut -f2 -d,`
	#python $oncokb_package/ClinicalDataAnnotator.py -i $clinical_working_dir/${samID}.clinical.txt -o $output_dir/${samID}.oncoKB.clinical.txt -a $output_dir/${samID}.maf,$output_dir/${samID}.cnv
#done

echo "Done"
