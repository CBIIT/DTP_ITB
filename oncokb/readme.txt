--You will need to download the OncoKB Annotator from Github
	and place it in a folder called
	"oncokb-annotator" within this directory.

	https://github.com/oncokb/oncokb-annotator

	Some of the requirements for imports in other packages within the annotator don't work.
	You should not need anything out of the ordinary.  Try to follow directions for most of the imports for the annotator.
	If it doesn't work, try running the MAF annotator anyways as it should be pretty basic.

--To run the end-to-end script:
	./run_oncokb.sh <OracleUsername> <OraclePassword> <host> <service> <oncokb_key>

	Caveat-- if your Password has a $ or something, you need to escape it with a \
	example:  Pa$$word -->  Pa\$\$word

-- maf_file_maker.py is used if we need to recreate new maf files from cBioportal, which might be necessary when we do update our data.
	for that, run it against the large data_mutations.txt file from the sample set download at cBioportal
	https://cbioportal-datahub.s3.amazonaws.com/cellline_nci60.tar.gz

	It is within cellline_nci60/data_mutations.txt  In the future can fully automate these processes.

