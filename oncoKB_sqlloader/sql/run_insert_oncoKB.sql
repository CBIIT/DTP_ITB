column RunDateTime     new_value RunDateTime
column Global_Name new_value Global_Name

SET SERVEROUTPUT ON
select to_char(sysdate, 'YYYYMMDD_HHMI') RunDateTime, Global_Name from Host_Info;
spool C:\Temp\test_sqlldr\sqlloader-files\log\Insert_OncoKB_&Global_Name._&RunDateTime;
select 'zhouy17.EMILY_ONKOKB_ORG table count: ' || count(*) from zhouy17.EMILY_ONKOKB_ORG;
select 'ZHOUY17.EMILY_ONCOKBGENEPANEL table count: ' || count(*) from ZHOUY17.EMILY_ONCOKBGENEPANEL;
select 'minimum seq: ' || min(o.ONCOKBGENEPANELSEQNBR) from ZHOUY17.EMILY_ONCOKBGENEPANEL o;
select systimestamp from dual;
exec ZHOUY17.insert_oncoKB;
select systimestamp from dual;
select 'zhouy17.EMILY_ONKOKB_ORG table count: ' || count(*) from zhouy17.EMILY_ONKOKB_ORG;
select 'ZHOUY17.EMILY_ONCOKBGENEPANEL table count: ' || count(*) from ZHOUY17.EMILY_ONCOKBGENEPANEL;
select 'minimum seq: ' || min(o.ONCOKBGENEPANELSEQNBR) from ZHOUY17.EMILY_ONCOKBGENEPANEL o;
spool off;
/
