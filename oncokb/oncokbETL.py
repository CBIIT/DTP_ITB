"""
Loads TSV oncokb annotated MAF files, performs transformations,
and inserts into COMMON.ONCOKBGENEPANEL oracle table.

Author: A. Gruenberger
v1.0.10122222
"""
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import os
import oracledb
import sys
oracledb.version = "8.3.0"
sys.modules["cx_Oracle"] = oracledb


# ========== START: Initializing Static Variables ==========

# OncoKB NCI-60 Cell Line Names to NCI's CellLineNames in Common.Cellline
cell_name_map = {
                'A549': 'A549/ATCC', 'HL_60': 'HL-60(TB)',
                'HS578T': 'HS 578T',
                'LOXIMVI': 'LOX IMVI',
                'MDA_MB_231': 'MDA-MB-231/ATCC',
                'NCI_ADR_RES': 'NCI/ADR-RES',
                'RXF_393': 'RXF 393',
                'T47D': 'T-47D'
                }

# Blacklist of Hugo_Symbol and HGVSp_Short delimited by a $ from TC Script
blacklist = [
            'TGFBR2$p.K153Sfs*35',
            'LZTR1$p.X217_splice',
            'KMT2C$p.C391*',
            'ATXN2$p.Q174Afs*75',
            'ATXN2$p.Q174Hfs*32',
            'SDHA$p.L649Efs*4',
            'HLA-A$p.L180Q',
            'FANCD2$p.X426_splice',
            'PMS2$p.L729Qfs*6'
            ]

# Columns that we will be using from the dataframe
keep_cols = [
        'Tumor_Sample_Barcode', 'Hugo_Symbol', 'Chromosome',
        'Start_Position', 'End_Position', 'Variant_Classification',
        'Reference_Allele', 'Tumor_Seq_Allele2', 'HGVSc', 'HGVSp_Short',
        'Existing_variation', 't_depth', 'tumor_vaf', 'SIFT', 'PolyPhen',
        'ONCOGENIC', 'MUTATION_EFFECT', 'Version'
        ]

# Database Table column names corresponding to our kept columns
db_cols = [
        'CELLLINENAME', 'HUGOGENESYMBOLSEQNBR', 'CHROMOSOME', 'STARTPOSITION',
        'ENDPOSITION', 'VARIANTCLASSSEQNBR', 'REFERENCEALLELE', 'ALTALLELE',
        'HGVSCDNACHANGE', 'HGVSPROTEINCHANGE', 'EXISTINGVARIANT', 'TOTALREADS',
        'VARIANTADELLEFREQ', 'SIFT', 'POLYPHEN', 'ONCOGENICITY',
        'MUTATIONEFFECT', 'ONCOKBVERSION'
        ]

# SQL to load Variants Class Description data from lookup table
variants_sql = 'SELECT variantclassdescription FROM COMMON.VARIANTCLASS'
# SQL to load HugoGeneSymbol data from lookup table
hugo_sql = 'SELECT * FROM COMMON.HUGOGENESYMBOL'


# ========== END: Initializing Variables and Database Connections ==========

# ========== START: Define Utility Functions ==========


def dna_change(dna):
    """Remove Transcript ID from DNA Change"""
    return dna.split(':')[1]


def vaf_type_change(vaf):
    """
    Perform a data type conversion after removing % from
    the string.  The VAF comes in as a percentage in
    string format, so we need to convert it to decimal.
    """
    return float(vaf.replace('%', ''))/100


def chr_change(ch):
    """Per PDMR system, we are adding chr for chromosome"""
    return 'chr{}'.format(str(ch))


def read_data(f):
    """
    Reads the TSV files in the data directory.
    Some columns are given data type definitions.
    """
    return pd.read_csv(
                        'data/{}'.format(f),
                        delimiter='\t',
                        dtype={
                            'Chromosome': str,
                            'Start_Position': np.int64,
                            'End_Position': np.int64,
                            't_depth': int,
                            'HGVSc': str
                        },
                        engine='python'
                    )


def cell_line_changes(cl):
    """
    Perform special cell line name Mapping if there
    is an alternative name in the Cell Line table versus
    what is in the OncoKB/cBioportal maf files.  After,
    that it converts all underscores to dashes.
    """
    if (cl in cell_name_map):
        cl = cell_name_map.get(cl)
    cl = cl.replace('_', '-')
    return cl


def blacklist_filter(row):
    """
    Ensures the combination is not in the blacklist given a
    row of OncoKB data.  Returns True if it is not blacklisted.
    """
    hugo_aa = str(row['Hugo_Symbol']) + '$' + str(row['HGVSp_Short'])
    if hugo_aa in blacklist:
        return False
    else:
        return True

# ========== END: Define Utility Functions ==========


def extract():
    '''
    Extracts the data from the OncoKB Annotator output files
    into a dataframe.  All input files are located in a co-located
    folder called data.

    Returns DataFrame with all data amalgamated.
    '''
    # Collect all file paths for files in data directory
    filepaths = [f for f in os.listdir("data/")]

    # Sequentially concatenate data from each file into one DF
    df = pd.concat(map(read_data, filepaths))

    return df


def transform(df, engine):
    '''
    Transforms loaded data into final format of data to represent
    what will be inserted into Oracle or whatever db.

    Returns DataFrame after necessary transformations.
    '''

    # DataFrame of the variants data
    df_variants = pd.read_sql(variants_sql, engine)
    # DataFrame of the HugoGene data
    df_hugo = pd.read_sql(hugo_sql, engine)

    var_dict = dict()  # Initialize dictionary for variants mapping
    hugo_dict = dict()  # Initialize dictionary for hugo symbol mapping

    # Create the corresponding map to apply to our data for Vars and Hugo
    for i in range(0, df_variants.size):
        var_dict[df_variants.iloc[i, 0]] = i
    for i in df_hugo.index:
        hugo_dict[df_hugo['hugogenesymboldescription'][i]] = \
            df_hugo['hugogenesymbolseqnbr'][i]

    # Trying to adapt TC code to dataFrame here
    # These two should reflect his whole Script
    df = df[(~df['MUTATION_EFFECT'].str.contains('Unknown') |
             ~df['ONCOGENIC'].str.contains('Unknown')) |
            ((df['HIGHEST_LEVEL'].str.len() > 0) |
             (df['MUTATION_EFFECT_CITATIONS'].str.len() > 0))].copy()
    df = df[df.apply(blacklist_filter, axis=1)].copy()

    # Specify the index to be sequential serialized
    # instead of serial number from sub dataframe loads
    df.index = range(0, df.index.size)

    # Select only the columns we need, discard others
    df = df[keep_cols]

    # Perform mapping as well as reformatting for columns and column data
    df['HGVSc'] = df['HGVSc'].apply(dna_change).copy()
    df['tumor_vaf'] = df['tumor_vaf'].apply(vaf_type_change).copy()
    df['Chromosome'] = df['Chromosome'].apply(chr_change).copy()
    df.columns = db_cols
    df['CELLLINENAME'] = df['CELLLINENAME'].apply(cell_line_changes).copy()
    df['HUGOGENESYMBOLSEQNBR'] = df['HUGOGENESYMBOLSEQNBR'].map(hugo_dict)

    # For this column, 0, should be in place of any null or NaN values
    df['VARIANTCLASSSEQNBR'] = df['VARIANTCLASSSEQNBR'].map(var_dict).fillna(0)

    return df


def load(df, engine):
    '''
    Loads data from Dataframe into database.  For now, that is Oracle.
    We use Pandas to_sql Function to insert to the table.  We do not want it
    to use index of the dataframe for the database table index.  Still not
    certain if we need to append new data every time we run OncoKB Annotator.
    That is to say-- are we looking for differences every time?  I assume data
    will be mostly the same each time unless a new 'hit' is identified in
    OncoKB, and would appear here ultimately.
    '''
    df.to_sql(name='oncokbgenepanel', con=engine, schema='COMMON',
              if_exists='append', index=False)
    print('Data Loaded to Oracle.')


# Driver section.  Checks and sets input args.
if __name__ == '__main__':
    if len(sys.argv) == 5:
        # There are 2 args, allegedly username and password
        print('Initializing ETL Connections')
        host = sys.argv[3]  # Staging Database
        service = sys.argv[4]  # Staging Database Service
        port = 1521  # Staging Database port
        username = sys.argv[1]
        pw = sys.argv[2]

        # SQL Alchemy Engine creation for Oracle Databases
        engine = create_engine(f'oracle://{username}:{pw}@',
                               connect_args={
                                'host': host,
                                'port': port,
                                'service_name': service
                                })
        print('Starting Extraction...')
        df = extract()
        print('...done.')
        print('Starting Transformations...')
        df = transform(df, engine)
        print('...done.')
        print('Starting load of data into Oracle...')
        load(df, engine)  # Comment out for testing
        print('...data Loaded to database.')
        engine.dispose()
        print('ETL complete, connections closed.')
    else:
        print(
            '''
            Unable to run without necessary arguments.
            You need to pass in username, password, host, and service:

            python oncokbETL.py usernameHere passwordHere host service

            Note: if your password has special characters
            then you will need to escape them using a backslash
            such as \$ or \\"
            '''
            )
