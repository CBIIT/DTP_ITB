CREATE OR REPLACE procedure ZHOUY17.insert_oncoKB 
IS
    i_count              INTEGER;
    e_no_data_inserted   EXCEPTION;
BEGIN
    i_count := 0;
    
    -- to do!! how to keep data in versions or just replace for each load? 
    execute immediate 'truncate table ZHOUY17.Emily_ONCOKBGENEPANEL';
    
    INSERT INTO ZHOUY17.Emily_ONCOKBGENEPANEL (       --ONCOKBGENEPANELSEQNBR,
                                               CELLLINENAME,
                                               HUGOGENESYMBOLSEQNBR,
                                               CHROMOSOME,
                                               STARTPOSITION,
                                               ENDPOSITION,
                                               VARIANTCLASSSEQNBR,
                                               REFERENCEALLELE,
                                               ALTALLELE,
                                               HGVSCDNACHANGE,
                                               HGVSPROTEINCHANGE,
                                               EXISTINGVARIANT,
                                               TOTALREADS,
                                               VARIANTADELLEFREQ,
                                               SIFT,
                                               POLYPHEN,
                                               ONCOGENICITY,
                                               MUTATIONEFFECT,
                                               ONCOKBVERSION)
        SELECT distinct                       --2, -- seq
               DECODE (TRIM (REPLACE (org.Tumor_Sample_Barcode, '_', '-')),
                       'A549', 'A549/ATCC', -- or map to A549(ASC), A549-luc-C8, A549 (Alveolar)???
                       'COLO205', 'COLO 205',
                       'HS578T', 'HS 578T',
                       'LOXIMVI', 'LOX IMVI',
                       'NCI-ADR-RES', 'NCI/ADR-RES',
                       'RXF-393', 'RXF 393',
                       'T47D', 'T-47D',
                       'HL-60', 'HL-60(TB)',
                       'MDA-MB-231', 'MDA-MB-231/ATCC',
                       TRIM (REPLACE (org.Tumor_Sample_Barcode, '_', '-'))), -- may need additional change?
               -- Hugo_Symbol, -- decode of VHL, 396
               NVL (hs.HUGOGENESYMBOLSEQNBR, 0),
               'chr' || TRIM (Chromosome),
               TO_NUMBER (TRIM (Start_Position)),
               TO_NUMBER (TRIM (End_Position)),
               --Variant_Classification, -- decode of Frame_Shift_Del
               NVL (vc.VARIANTCLASSSEQNBR, 0),
               TRIM (Reference_Allele),
               TRIM (Tumor_Seq_Allele2),
               --Trim(HGVSc),  -- cut off anything before ":"
               TRIM (SUBSTR (HGVSc, 1 + INSTR (HGVSc, ':', -1))),
               TRIM (HGVSp_Short),
               TRIM (Existing_variation),
               TO_NUMBER (TRIM (T_DEPTH)),
               TO_NUMBER (
                   TRIM (SUBSTR (TUMOR_VAF, 1, LENGTH (tumor_vaf) - 1) / 100)),
               TRIM (SIFT),
               TRIM (PolyPhen),
               TRIM (ONCOGENIC),
               TRIM (MUTATION_EFFECT),
               TRIM (Version)
          FROM ZHOUY17.EMILY_ONKOKB_ORG  org,
               COMMON.HUGOGENESYMBOL            hs,
               COMMON.VARIANTCLASS              vc
         WHERE                                  --org.hugo_symbol = 'VHL' and
                   UPPER (TRIM (org.HUGO_SYMBOL)) =
                   UPPER (TRIM (hs.HUGOGENESYMBOLDESCRIPTION(+)))
               AND UPPER (
                       TRIM (
                           DECODE (org.VARIANT_CLASSIFICATION,
                                   'Splice_Region', 'Not Found', -- or 'Not Found'? Please confirm, also may add trim, case, etc.!!!
                                   'Translation_Start_Site', 'Not Found',
                                   org.VARIANT_CLASSIFICATION))) =
                   UPPER (TRIM (vc.VARIANTCLASSDESCRIPTION(+)));

    i_count := SQL%ROWCOUNT;

    IF i_count > 0
    THEN
        DBMS_OUTPUT.put_line ('Number of rows inserted: ' || i_count);
        COMMIT;
        
        -- to do!! how to keep data in versions or just replace for each load? 
        --execute immediate 'truncate table ZHOUY17.EMILY_ONKOKB_ORG';
    ELSE
        RAISE e_no_data_inserted;
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND
    THEN
        DBMS_OUTPUT.put_line ('No data has been found');
    WHEN e_no_data_inserted
    THEN
        DBMS_OUTPUT.put_line ('No data has been inserted, please check!!!');
    WHEN OTHERS
    THEN
        raise_application_error (
            -20002,
            'An error has occurred inserting an oncoKB record.');
END;
/