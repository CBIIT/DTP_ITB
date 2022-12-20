import os
from dotenv import load_dotenv
import oracledb
import sys
oracledb.version = "8.3.0"
sys.modules["cx_Oracle"] = oracledb
from sqlalchemy import create_engine
import pymongo
import pandas as pd
import plotly.graph_objects as go

class DataService:

    def __init__(self):
        load_dotenv()
        CONN_STRING = os.getenv('CONN_STRING')
        PANEL_NAME_MAP = {"REN":"Renal Cancer","MEL":"Melanoma","PRO":"Prostate Cancer","CNS":"CNS Cancer","LEU":"Leukemia","OVA":"Ovarian Cancer","COL":"Colon Cancer","BRE":"Breast Cancer","LNS":"Non-Small Cell Lung Cancer"}
        # Mongo
        self.CLIENT = pymongo.MongoClient(CONN_STRING,connect=True)
        self.DB = self.CLIENT.get_database('NCIDCTD')
        self.COLL = self.DB.get_collection('fivedose_panel')

        #Oracle
        USERNAME = os.getenv('USERNAME')
        PW = os.getenv('PW')
        self.engine = create_engine(f'oracle://{USERNAME}:{PW}@',
                            connect_args={
                                "host": os.getenv('HOST'),
                                "port": 1521,
                                "service_name": os.getenv('SERVICE')
                            }
                )

        # NCI 60 Reference
        NCI60_SQL = 'SELECT CELLNAME, PANELCDE FROM COMMON.cellline WHERE COMPARE > 0'
        self.DF_NCI60 = pd.read_sql(NCI60_SQL, self.engine)
        self.DF_NCI60['panel'] = [self.join_panel(x,PANEL_NAME_MAP) for x in self.DF_NCI60.panelcde]

        #exprIds
        self.load_exp_ids()
    
    def __del__(self):
        self.engine.dispose(close=True)
        self.CLIENT.close()
    
    def load_exp_ids(self):
        '''
        Returns a list of documents, {expid: 'string', fivedose_nsc: number}
        The expid field is repeated as there are many NSCs in each experiment
        '''
        ids = [ d for d in 
                            (self.COLL.aggregate(
                                [
                                    {
                                        '$limit':100
                                    },{
                                        '$project':{
                                                    'expid':1,
                                                    'fivedose_nsc':1,
                                                    '_id':0
                                                    }
                                    }
                                ]
                            ))
                        ]
        uniques = []
        nsc_dict = {}
        for x in ids:
            uniques.append(x['expid'])
            nsc_dict[x['expid']] = x['fivedose_nsc']
        self.EXPIDS = uniques
        self.NSC_DICT = nsc_dict
        

    def get_df_by_nsc(self,nsc,exp_id):
        data =  [d for d in 
                            (self.COLL.aggregate(
                                [                            
                                    {
                                        '$match': {
                                            'expid': exp_id,
                                        }
                                    }, {
                                        '$project': {
                                            'paneldetails_1': 1, 
                                            'paneldetails_2': 1, 
                                            'paneldetails_3': 1, 
                                            'paneldetails_4': 1, 
                                            'paneldetails_5': 1, 
                                            '_id': 0
                                        }
                                    }

                                ])
                            )
                        ]
        dfs = []
        for item in data:
            for stuff in item:
                for cols in item[stuff]:
                    dfs.append(pd.Series(cols))
        df = pd.DataFrame(dfs)
        nsc_df = df.query(f"nsc == {nsc}").sort_values(by="conc")
        nsc_df = nsc_df.drop(['plandate','testseq','prefix','nsc','hiconc'],axis=1)
        nsc_df.columns = [x.upper().replace('  ',' ').replace('MDA-N','HS 578T') for x in nsc_df.columns]
        nsc_df = nsc_df.set_index('CONC')
        nsc_df = nsc_df.dropna(axis=1) # remove cell lines that were not tested fully or at all
        return nsc_df

    def join_panel(self,val,panel_map):
        for key in panel_map.keys():
            if val == key:
                return panel_map[key]
        return 'not found'

    def create_grouped_data_dict(self,df):
        print('IN CREATE_GROUPED_DATA_DICT')
        data_dict = dict()
        for panel in self.DF_NCI60['panel'].unique():
            data_dict[panel] = pd.DataFrame(index=df.index)
        
        for col in df.columns: # Column is cell line
            panel_name = self.DF_NCI60[self.DF_NCI60['cellname'] == col]['panel'].iloc[0]
            data_dict[panel_name] = pd.concat([data_dict[panel_name],df[col]],axis=1).dropna(axis=1)
        return data_dict
    
    def get_conc_resp_graph(self,nsc_df,nsc):
        conc_resp_fig = go.Figure()
        for cell in nsc_df.columns:
            conc_resp_fig.add_trace(
                go.Scatter(
                    x=nsc_df[cell].index,
                    y=nsc_df[cell].values,
                    mode='lines+markers',
                    name=f'{cell}',
                    line_shape='spline',
                ))
        conc_resp_fig.update_xaxes(type='log',dtick='log', exponentformat='E',title='Concentration (mol)')
        conc_resp_fig.update_yaxes(title='Growth Inhibition Pct (GI%)')
        conc_resp_fig.update_layout(height=700,title=f'NSC-{nsc} 5-Concentration Response',title_x=.44, legend_title_text='Cell Lines',)
        return conc_resp_fig

    def get_conc_resp_graph_by_panel(self,nsc_df,nsc,panel):
        print(f'IN GET_CONC_RESP_GRAPH_BY_PANEL | nsc:{nsc}, panel:{panel}')
        conc_resp_fig = go.Figure()
        for cell in nsc_df.columns:
            conc_resp_fig.add_trace(
                go.Scatter(
                    x=nsc_df[cell].index,
                    y=nsc_df[cell].values,
                    mode='lines+markers',
                    name=f'{cell}',
                    line_shape='spline',
                ))
        conc_resp_fig.update_xaxes(type='log',dtick='log', exponentformat='E',title='Concentration (mol)')
        conc_resp_fig.update_yaxes(title='Growth Inhibition Pct (GI%)')
        conc_resp_fig.update_layout(title=f'{panel} Response',title_x=.48, legend_title_text='Cell Lines',)
        return conc_resp_fig
    
    def get_nscs_by_expid(self,expid):
        nsc_list =self.COLL.aggregate([
                            {
                                '$match': {
                                    'expid': expid
                                }
                            }, {
                                '$project': {
                                    '_id': 0, 
                                    'fivedose_nsc': 1
                                }
                            }, {
                                '$unwind': {
                                    'path': '$fivedose_nsc'
                                }
                            }
                        ])
        return [x['fivedose_nsc'] for x in nsc_list]
    
    def get_mean_graph(self,nsc,expid):
        coll = self.DB.get_collection('new_onedose')
        data = coll.aggregate([
            {
                '$match': {
                    'expid': expid
                }
            }, {
                '$project': {
                    '_id': 0, 
                    'tline': 1
                }
            }, {
                '$unwind': {
                    'path': '$tline', 
                    'preserveNullAndEmptyArrays': False
                }
            }
        ])
        exp_df = pd.DataFrame([d['tline'] for d in data])
        exp_df.GrowthPercent = exp_df.GrowthPercent.apply(lambda x: x['Average'])
        exp_df = exp_df.sort_values('GrowthPercent',ascending=False,ignore_index=True)