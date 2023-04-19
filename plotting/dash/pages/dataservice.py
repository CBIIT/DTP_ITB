import os
import random

import numpy as np
from dotenv import load_dotenv
import oracledb
import sys

oracledb.version = "8.3.0"
sys.modules["cx_Oracle"] = oracledb
from sqlalchemy import create_engine
import pymongo
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from lifelines import KaplanMeierFitter
import matplotlib.colors as mcolors
import colorsys
from plotly.validators.scatter.marker import SymbolValidator


class DataService():
    initialized = False
    def __init__(self):
        load_dotenv()
        self.subscr10 = u'\u2081\u2080'
        CONN_STRING = os.getenv('CONN_STRING')
        # Temporary commenting out until confirmed dcc Store works
        #PANEL_NAME_MAP = {"REN": "Renal Cancer", "MEL": "Melanoma", "PRO": "Prostate Cancer", "CNS": "CNS Cancer",
        #                 "LEU": "Leukemia", "OVA": "Ovarian Cancer", "COL": "Colon Cancer", "BRE": "Breast Cancer",
        #                "LNS": "Non-Small Cell Lung Cancer"}

        # Mongo
        self.CLIENT = pymongo.MongoClient(CONN_STRING, connect=True)
        print(f'Mongo Client initialized...')
        self.DB = self.CLIENT.get_database('NCIDCTD')
        print(f'Mongo NCIDCTD DB initialized...')
        self.FIVEDOSE_COLL = self.DB.get_collection('fivedose')
        self.ONEDOSE_COLL = self.DB.get_collection('onedose')
        self.INVIVO_COLL = self.DB.get_collection('invivo')
        self.COMPOUNDS_COLL = self.DB.get_collection('compounds')
        print(f'Collections initialized...')

        # Chart Styles
        self.PLOT_STYLE_DF = pd.read_csv(
            os.path.abspath('../dash/assets/plot_styles.csv'))  # /dash/assets/    /dash/pages/


        colors = []
        mcolors.XKCD_COLORS
        for name, hex in mcolors.CSS4_COLORS.items():
            rgb = mcolors.hex2color(hex)
            ihls = colorsys.rgb_to_hls(*rgb)
            if ihls[2] <= 0.75 and ihls[1] <= 0.65:
                colors.append(name)

        random.shuffle(colors)
        self.COLORS = colors
        symbols = SymbolValidator().values
        random.shuffle(symbols)
        self.SYMBOLS = symbols

        # exprIds
        # try:
        #     if self.EXPIDS:
        #         pass
        # except:
        #     self.load_exp_ids()
        #     print(f'Five dose exp ids loaded...')
        #
        #     self.load_comp_nscs()
        #     print(f'Compound NSCs loaded...')
        #
        #     self.get_invivo_expids()
        #     print(f'Invivo Exp Nbrs loaded...')
        #
        #     self.get_od_expids()
        #     print(f'One Dose expIds loaded...')

    def __del__(self):
        #self.engine.dispose(close=True)
        self.CLIENT.close()
        print('Closing connections and destructing.')

    # def load_comp_nscs(self):
    #     nscs = [d['nsc'] for d in
    #             (self.COMPOUNDS_COLL.aggregate([
    #                 {
    #                     '$match': {
    #                         'soldata': {
    #                             '$exists': True
    #                         },
    #                         'cas': {
    #                             '$exists': True
    #                         },
    #                         'mf': {
    #                             '$exists': True
    #                         },
    #                         'mw': {
    #                             '$exists': True
    #                         },
    #                         'distribution_code_desc': {
    #                             '$exists': True
    #                         },
    #                         'agreement_type_desc': {
    #                             '$exists': True
    #                         },
    #                         'mv_dtp_disregistration_short': {
    #                             '$exists': True
    #                         },
    #                         'cmpd_chem_name': {
    #                             '$exists': True
    #                         }
    #                     }
    #                 },{
    #                     '$project': {
    #                         '_id':0,
    #                         'nsc': 1
    #                     },
    #
    #                 }
    #             ]))
    #             ]
    #     self.COMP_NSCS = nscs
    #
    # def load_exp_ids(self):
    #     '''
    #     Returns a list of documents, {expid: 'string', fivedose_nsc: number}
    #     The expid field is repeated as there are many NSCs in each experiment
    #     '''
    #     ids = [d for d in
    #            (self.FIVEDOSE_COLL.aggregate(
    #                [
    #                    {
    #                        '$project': {
    #                            'expid': 1,
    #                            'nsc': '$tline.nsc',
    #                            '_id': 0
    #                        }
    #                    }, {
    #                    '$unwind': {
    #                        'path': '$nsc'
    #                    }
    #                }, {
    #                    '$group': {
    #                        '_id': {
    #                            'expid': '$expid'
    #                        },
    #                        'nsc': {
    #                            '$addToSet': '$nsc'
    #                        }
    #                    }
    #                }, {
    #                    '$project': {
    #                        'expid': '$_id.expid',
    #                        'nsc': 1,
    #                        '_id': 0
    #                    }
    #                }
    #                ]
    #            ))
    #            ]
    #     uniques = []
    #     nsc_dict = {}
    #     for x in ids:
    #         uniques.append(x['expid'])
    #         nsc_dict[x['expid']] = x['nsc']
    #     uniques.sort()
    #     self.EXPIDS = uniques
    #     self.NSC_DICT = nsc_dict
    #
    # def get_invivo_expids(self):
    #     data = self.INVIVO_COLL.aggregate([
    #         {
    #             '$project': {
    #                 'exp_nbr': 1,
    #                 'invivonsc': 1,
    #                 '_id': 0
    #             }
    #         }
    #     ])
    #     data = [d for d in data]
    #     invivo_dict = {}
    #     for invivo in data:
    #         try:
    #             nscs = invivo['invivonsc'].replace('\'', '').split(',')
    #             nscs = [int(x) for x in nscs]
    #             invivo_dict[str(invivo['exp_nbr'])] = nscs
    #         except KeyError:
    #             continue
    #     self.INVIVO_DICT = invivo_dict
    #
    # def get_od_expids(self):
    #     data = self.ONEDOSE_COLL.aggregate([
    #         {
    #             '$project': {
    #                 'expid': 1,
    #                 'onedosensc': 1,
    #                 '_id': 0
    #             }
    #         }
    #     ])
    #     data = [d for d in data]
    #     onedose_dict = {}
    #     for od in data:
    #         nscs = od['onedosensc'].replace('\'', '').split(',')
    #         nscs = [int(x) for x in nscs]
    #         onedose_dict[str(od['expid'])] = nscs
    #     self.ONEDOSE_DICT = onedose_dict

    def get_df_by_nsc(self, nsc, exp_id):
        data = [d for d in
                (self.FIVEDOSE_COLL.aggregate(
                    [
                        {
                            '$match': {
                                'expid': exp_id
                            }
                        }, {
                        '$project': {
                            '_id': 0,
                            'tline': 1
                        }
                    }, {
                        '$unwind': {
                            'path': '$tline'
                        }
                    }, {
                        '$replaceRoot': {
                            'newRoot': '$tline'
                        }
                    }, {
                        '$match': {
                            'nsc': int(nsc)
                        }
                    }
                    ])
                )
                ]

        df = pd.DataFrame(data)
        return df

    def get_od_df_by_nsc(self, nsc, expid):
        data = [d for d in
                (self.ONEDOSE_COLL.aggregate(
                    [
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
                            'path': '$tline'
                        }
                    }, {
                        '$replaceRoot': {
                            'newRoot': '$tline'
                        }
                    }, {
                        '$match': {
                            'Nsc': int(nsc)
                        }
                    }, {
                        '$project': {
                            'nsc': '$Nsc',
                            'panel_name': '$cellpnl.panelnme',
                            'cell_name': '$cellline.cellname',
                            'panel_code': '$cellline.panelcde',
                            'growth': '$GrowthPercent.Average'
                        }
                    }
                    ])
                )
                ]

        df = pd.DataFrame(data)

        return df

    def join_panel(self, val, panel_map):
        for key in panel_map.keys():
            if val == key:
                return panel_map[key]
        return 'not found'

    def create_grouped_data_dict(self, df):
        data_dict = dict()
        for row in range(df.index.size):
            panelcde = df.iloc[row].cellline['panelcde']
            cellline = df.iloc[row].cellline['cellname']
            conc_resp = [x for x in df.iloc[row].wgroup]
            conc = [x['conc'] for x in conc_resp]
            growth = [x['wg_growth_percent']['Average'] for x in conc_resp]
            growth_dict = {'conc': conc, cellline: growth}

            tdf = pd.DataFrame(growth_dict)
            tdf.set_index('conc', inplace=True)

            if panelcde in data_dict.keys():
                data_dict[panelcde] = pd.concat([data_dict[panelcde], tdf], axis=1)
            else:
                data_dict[panelcde] = tdf

        return data_dict

    def create_conc_resp_df(self, df):
        new_df = None
        for row in range(df.index.size):
            cellline = df.iloc[row].cellline['cellname']
            conc_resp = [x for x in df.iloc[row].wgroup]
            conc = [x['conc'] for x in conc_resp]
            growth = [x['wg_growth_percent']['Average'] for x in conc_resp]
            growth_dict = {'conc': conc, cellline: growth}

            tdf = pd.DataFrame(growth_dict)
            tdf.set_index('conc', inplace=True)
            if new_df is None:
                new_df = tdf.copy()
            else:
                new_df = pd.concat([new_df, tdf], axis=1)

        return new_df

    def get_conc_resp_graph(self, df, nsc):
        conc_resp_fig = go.Figure()
        nsc_df = self.create_conc_resp_df(df)
        for cell in nsc_df.columns:
            style = self.PLOT_STYLE_DF[self.PLOT_STYLE_DF['line_name'] == cell][
                ['cell_line_symbol', 'panel_color', 'cell_line_line_pattern']]
            line_pattern = str(
                style['cell_line_line_pattern'].iat[0] if not style['cell_line_line_pattern'].isna().any() else 'solid')

            conc_resp_fig.add_trace(
                go.Scatter(
                    x=nsc_df[cell].index,
                    y=nsc_df[cell].values,
                    mode='lines+markers',
                    name=f'{cell}',
                    line_shape='spline',
                    marker={'symbol': f"{style['cell_line_symbol'].iat[0]}-open", 'size': 12},
                    line={'color': style['panel_color'].iat[0], 'dash': line_pattern}
                ))
        conc_resp_fig.update_xaxes(title=f'Concentration (log{self.subscr10} mol)', )
        conc_resp_fig.update_yaxes(title='Growth Inhibition Pct (GI%)')
        conc_resp_fig.update_layout(title=f'NSC-{nsc} 5-Concentration Response', title_x=.44,
                                    legend_title_text='Cell Lines', )
        return conc_resp_fig

    def get_conc_resp_graph_by_panel(self, nsc_df, nsc, panel):
        # print(f'IN GET_CONC_RESP_GRAPH_BY_PANEL | nsc:{nsc}, panel:{panel}')
        conc_resp_fig = go.Figure()

        for cell in nsc_df.columns:
            style = \
            self.PLOT_STYLE_DF[(self.PLOT_STYLE_DF['panel_cde'] == panel) & (self.PLOT_STYLE_DF['line_name'] == cell)][
                ['cell_line_symbol', 'panel_color', 'cell_line_line_pattern']]
            line_pattern = str(
                style['cell_line_line_pattern'].iat[0] if not style['cell_line_line_pattern'].isna().any() else 'solid')
            conc_resp_fig.add_trace(
                go.Scatter(
                    x=nsc_df[cell].index,
                    y=nsc_df[cell].values,
                    mode='lines+markers',
                    name=f'{cell}',
                    line_shape='spline',
                    marker={'symbol': f"{style['cell_line_symbol'].iat[0]}-open", 'size': 12},
                    line={'color': style['panel_color'].iat[0], 'dash': line_pattern}
                ))
        conc_resp_fig.update_xaxes(title=f'Concentration (log{self.subscr10} mol)')
        conc_resp_fig.update_yaxes(title='Growth Inhibition Pct (GI%)')
        conc_resp_fig.update_layout(title=f'{panel} Response', title_x=.48, legend_title_text='Cell Lines', )
        return conc_resp_fig

    def get_nscs_by_expid(self, expid):
        nsc_list = self.FIVEDOSE_COLL.aggregate([
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

    def get_mean_graphs_data(self, nsc, expid):
        print(f'IN GET MEAN_GRAPHS_DATA WITH {nsc} and expid {expid}')
        data = self.FIVEDOSE_COLL.aggregate([
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
            }, {
                '$match': {
                    'tline.nsc': int(nsc)
                }
            }, {
                '$project': {
                    'cellname': '$tline.cellline.cellname',
                    'panel': '$tline.cellpnl.panelnme',
                    'tgi': '$tline.tgi.Average',
                    'gi50': '$tline.gi50.Average',
                    'lc50': '$tline.lc50.Average'
                }
            }
        ])
        df = pd.DataFrame([d for d in data])

        gi50 = df[['cellname', 'panel', 'gi50']]
        lc50 = df[['cellname', 'panel', 'lc50']]
        tgi = df[['cellname', 'panel', 'tgi']]

        # Add the delta [to the mean] columns
        gi50_mean = gi50['gi50'].mean()
        gi50['delta'] = gi50['gi50'].copy().apply(lambda x: x - gi50_mean)
        lc50_mean = lc50['lc50'].mean()
        lc50['delta'] = lc50['lc50'].copy().apply(lambda x: x - lc50_mean)
        tgi_mean = tgi['tgi'].mean()
        tgi['delta'] = tgi['tgi'].copy().apply(lambda x: x - tgi_mean)

        # set as instance variables
        self.LC50_DF = lc50
        self.GI50_DF = gi50
        self.TGI_DF = tgi

        print(f"Data loaded for GI50,LC50,TGI for nsc {nsc}")

    def get_tgi_graph(self, nsc):
        xr = (self.TGI_DF['delta'].abs().max()) * 1.10
        bar1 = px.bar(self.TGI_DF,
                      x="delta",
                      y="cellname",
                      labels={"delta": f"Total Growth Inhibition Conc (Log{self.subscr10} Mol) Mean Deltas",
                              "cellname": "Cell Line"},
                      barmode='relative', color='panel',
                      orientation='h',
                      title=f"TGI | NSC {nsc}",
                      height=750,
                      range_x=[xr, -xr]
                      )
        bar1.update_traces(width=1)
        bar1.update_layout(title_x=0.45)
        bar1.update_yaxes(categoryorder="total descending", tickmode="linear")

        return bar1

    def get_gi50_graph(self, nsc):
        xr = (self.GI50_DF['delta'].abs().max()) * 1.10
        bar1 = px.bar(self.GI50_DF,
                      x="delta",
                      y="cellname",
                      labels={"delta": f"Growth Inhibition 50 Conc (Log{self.subscr10} Mol) Mean Deltas",
                              "cellname": "Cell Line"},
                      barmode='relative', color='panel',
                      orientation='h',
                      title=f"GI50 | NSC {nsc}",
                      height=750,
                      range_x=[xr, -xr]
                      )
        bar1.update_traces(width=1)
        bar1.update_layout(title_x=0.45)
        bar1.update_yaxes(categoryorder="total descending", tickmode="linear")

        return bar1

    def get_lc50_graph(self, nsc):
        xr = (self.LC50_DF['delta'].abs().max()) * 1.10
        bar1 = px.bar(self.LC50_DF,
                      x="delta",
                      y="cellname",
                      labels={"delta": f"Lethal 50 Conc (Log{self.subscr10} Mol) Mean Deltas", "cellname": "Cell Line"},
                      barmode='relative', color='panel',
                      orientation='h',
                      title=f"LC50 | NSC {nsc}",
                      height=750,
                      range_x=[xr, -xr]
                      )
        bar1.update_traces(width=1)
        bar1.update_layout(title_x=0.45)
        bar1.update_yaxes(categoryorder="total descending", tickmode="linear")

        return bar1

    def get_od_growth_graphs(self, df, expid, nsc):
        ddf = df.copy()

        # Mean Growth Graph
        mean = df['growth'].mean()
        ddf['delta'] = ddf['growth'].apply(lambda x: x - mean)
        xr = ddf['delta'].abs().max() * 1.10
        mean_graph = px.bar(
            ddf,
            x='delta',
            y='cell_name',
            labels={"delta": f"Average Growth % Delta from the Mean", "cell_name": "Cell Line"},
            barmode='relative', color='panel_name',
            orientation='h',
            title=f"Average Growth Mean Delta | NSC {nsc}",
            height=750,
            range_x=[xr, -xr]
        )
        mean_graph.update_traces(width=1)
        mean_graph.update_layout(title_x=0.45)
        mean_graph.update_yaxes(categoryorder="total descending", tickmode="linear")

        xr = ddf['growth'].abs().max() * 1.10
        growth_graph = px.bar(
            ddf,
            x='delta',
            y='cell_name',
            labels={"delta": f"Average Growth Percentage", "cell_name": "Cell Line"},
            barmode='relative', color='panel_name',
            orientation='h',
            title=f"Average Growth | NSC {nsc}",
            height=750,
            range_x=[-xr, xr]
        )
        growth_graph.update_traces(width=1)
        growth_graph.update_layout(title_x=0.45)
        growth_graph.update_yaxes(categoryorder="total ascending", tickmode="linear")

        return [growth_graph, mean_graph]

    # Helper function for KM Graph, to get decimal values
    # Utility Function
    def make_survivals(self, kmdf):
        survival_list = list()
        n = kmdf['at_risk'].iloc()[0]
        for i, x in enumerate(kmdf['at_risk']):
            s = ((x - kmdf['observed'].iloc()[i]) / n)
            survival_list.append(s)
        return survival_list

    def get_km_graph(self, expid, nsc, group):
        grp = int(group)
        pipeline = [
            {
                '$match': {
                    'expid': expid
                }
            }, {
                '$project': {
                    'tgroup.animal.death_day': 1,
                    '_id': 0,
                    'tgroup.nsc_therapy.nsc': 1,
                    'expid': 1,
                    'cellline.cellname': 1,
                    'cellline.panelcde': 1
                }
            }, {
                '$unwind': {
                    'path': '$tgroup',
                    'preserveNullAndEmptyArrays': False
                }
            }, {
                '$set': {
                    'animals': '$tgroup.animal.death_day',
                    'nsc': '$tgroup.nsc_therapy.nsc'
                }
            }, {
                '$unset': 'tgroup'
            }, {
                '$match': {
                    '$or': [
                        {
                            'nsc': {
                                '$eq': 999999
                            }
                        }, {
                            'nsc': {
                                '$eq': int(nsc)
                            }
                        }
                    ]
                }
            }, {
                '$set': {
                    'nsc': {'$first': '$nsc'}
                }
            }
        ]
        data = self.INVIVO_COLL.aggregate(pipeline)
        df = pd.DataFrame([d for d in data])

        # Prepare columns for KMF
        delta = [1 for _ in range(len(df['animals'][grp]))]
        time = df['animals'][grp]
        time.sort()
        group = [df['nsc'][grp] for x in delta]

        # Create KM Object
        kmf = KaplanMeierFitter()
        kmf.fit(durations=time, event_observed=delta, )

        # Create a DF from the KM Data Object
        km_df = kmf.event_table.copy()

        # Add in slightly transformed survival rates
        km_df['survival_rate'] = self.make_survivals(km_df)

        # Confidence Interval values
        ci_df = kmf.confidence_interval_
        ci_df.columns = ['lower_ci', 'upper_ci']
        km_df = km_df.join(ci_df)

        # Create the Plotly Figure
        cellline = df['cellline'][grp]['cellname']
        nsc = df['nsc'][grp]
        title_txt = f'Invivo Study | Cell {cellline} | NSC {nsc}'
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=km_df.index, y=km_df['survival_rate'], line_shape='hv', mode='lines',
                                 line_color='rgb(0,176,246)', name='Survival Line'))
        fig.add_trace(go.Scatter(x=km_df.index, y=km_df['upper_ci'], line_shape='hv', mode='lines',
                                 line_color='rgba(255,255,255,0)', name='Upper Confidence Interval', showlegend=False))
        fig.add_trace(go.Scatter(x=km_df.index, y=km_df['lower_ci'], fill='tonexty', line_shape='hv', mode='lines',
                                 fillcolor='rgba(0,176,246,0.2)', line_color='rgba(255,255,255,0)',
                                 name='Lower Confidence Interval', showlegend=False))
        fig.update_layout(title_text=title_txt, autosize=True)
        fig.update_xaxes(range=[0, (km_df.index.max() * 1.05)], title_text='Timeline (days)')
        fig.update_yaxes(title_text='Survival Rate')

        # It is the case that some Invivo experiments are spread out and worked on
        # at different time intervals.  The follow up ones don't always have a 999999 control
        # in the experiment.  I'm not sure if the data model will change or if we need to somehow
        # combine experiments that refer to an old control or somehow connect experiments to their
        # control parents.  Seems odd.
        try:
            control_trace = self.get_km_control(df[df['nsc'] == 999999].copy())
            fig.add_trace(control_trace)
        except:
            print('Control Exception encountered.')

        return fig

    def get_km_control(self, df):
        key = 0
        if df.size == 0:
            raise Exception('No control found in experiment')
        elif df.size > 1:
            delta = [1 for _ in range(len(df['animals'][key]))]
            time = df['animals'][key]
            time.sort()

            kmf2 = KaplanMeierFitter()
            kmf2.fit(durations=time, event_observed=delta, )

            # Create a DF from the KM Data Object
            km2_df = kmf2.event_table.copy()

            # Add in slightly transformed survival rates
            km2_df['survival_rate'] = self.make_survivals(km2_df)

            control_trace = go.Scatter(x=km2_df.index, y=km2_df['survival_rate'], line_shape='hv', mode='lines',
                                       line_color='rgb(0,0,0)', name='Control')
            return control_trace
        else:
            delta = [1 for _ in range(len(df['animals']))]
            time = df['animals']
            time.sort()

            kmf2 = KaplanMeierFitter()
            kmf2.fit(durations=time, event_observed=delta, )

            # Create a DF from the KM Data Object
            km2_df = kmf2.event_table.copy()

            # Add in slightly transformed survival rates
            km2_df['survival_rate'] = self.make_survivals(km2_df)

            control_trace = go.Scatter(x=km2_df.index, y=km2_df['survival_rate'], line_shape='hv', mode='lines',
                                       line_color='rgb(0,0,0)', name='Control')

            return control_trace

    def get_anml_weight_graphs(self, expid, nsc, group):
        grp = int(group)
        pipeline = [
            {
                '$match': {
                    'expid': expid
                }
            }, {
                '$project': {
                    'tgroup.animal': 1,
                    '_id': 0,
                    'tgroup.nsc_therapy.nsc': 1,
                    'expid': 1,
                    'cellline.cellname': 1,
                    'cellline.panelcde': 1
                }
            }, {
                '$unwind': {
                    'path': '$tgroup',
                    'preserveNullAndEmptyArrays': False
                }
            }, {
                '$set': {
                    'animals': '$tgroup.animal.animal_nbr',
                    'weight': '$tgroup.animal.animal_history',
                    'tumor': '$tgroup.animal.tumor_history',
                    'nsc': '$tgroup.nsc_therapy.nsc'
                }
            }, {
                '$unset': 'tgroup'
            }, {
                '$match': {
                    '$or': [
                        {
                            'nsc': {
                                '$eq': 999999
                            }
                        }, {
                            'nsc': {
                                '$eq': int(nsc)
                            }
                        }
                    ]
                }
            }, {
                '$set': {
                    'nsc': {
                        '$first': '$nsc'
                    }
                }
            }
        ]
        data = self.INVIVO_COLL.aggregate(pipeline)
        data = [d for d in data]

        # animal_nbr will have a list of animal subject numbers
        # for the first group of testing
        animal_nbr = data[grp]['animals']

        anml_data_dict_wt = dict()
        for i, wt in enumerate(data[grp]['weight']):
            anml_data_dict_wt[animal_nbr[i]] = pd.DataFrame(wt)

        anml_data_dict_tum = dict()
        for i, wt in enumerate(data[grp]['tumor']):
            anml_data_dict_tum[animal_nbr[i]] = pd.DataFrame(wt)

        cell_line = data[grp]['cellline']['cellname']
        panel_code = data[grp]['cellline']['panelcde']

        # Create a Figure with animal weights
        animal_weight_fig = self.get_animal_weight_figure(anml_data_dict_wt, cell_line, panel_code, nsc, expid)
        tumor_fig = self.get_tumor_weight_figure(anml_data_dict_tum, cell_line, panel_code, nsc, expid)

        weights_dict = dict()

        weights_dict['weight'] = animal_weight_fig
        weights_dict['tumor'] = tumor_fig

        return weights_dict

    def get_tumor_weight_figure(self, anml_data_dict, cell_line, panel_code, nsc, expid):
        fig = go.Figure()

        for animal in anml_data_dict.keys():
            fig.add_trace(
                go.Scatter(
                    x=anml_data_dict[animal]['obs_day'],
                    y=anml_data_dict[animal]['tumor_wt'],
                    name=f'Subject {animal}'
                )
            )

        fig.add_trace(self.get_median_trace(anml_data_dict, 'tumor_wt'))

        fig.update_layout(title=self.get_invivo_title(cell_line, panel_code, nsc, expid, 'Tumor Weight'))
        fig.update_yaxes(title_text='Animal Tumor Weight(mg)')
        fig.update_xaxes(title_text='Observation Period(days)')

        return fig

    def get_animal_weight_figure(self, anml_data_dict, cell_line, panel_code, nsc, expid):

        fig = go.Figure()

        for animal in anml_data_dict.keys():
            fig.add_trace(
                go.Scatter(
                    x=anml_data_dict[animal]['obs_day'],
                    y=anml_data_dict[animal]['net_weight'],
                    name=f'Subject {animal}'
                )
            )

        fig.add_trace(self.get_median_trace(anml_data_dict, 'net_weight'))

        fig.update_layout(title=self.get_invivo_title(cell_line, panel_code, nsc, expid, 'Animal Weight'))
        fig.update_yaxes(title_text='Animal Net Weight(g)')
        fig.update_xaxes(title_text='Observation Period (days)')

        return fig

    def get_invivo_title(self, cell_line, panel_code, nsc, expid, type):
        nsc_title = f'NSC {str(nsc)}'
        if str(nsc) == '999999':
            nsc_title = 'Control'

        fig_title = f'{type} | {nsc_title} | {panel_code} - {cell_line} | ExpID {expid}'

        return fig_title

    def get_median_trace(self, anml_data_dict, wt_key):
        median_dict = dict()
        for x in anml_data_dict.keys():
            animal = anml_data_dict[x]
            for day in animal.iterrows():
                data = day[1][wt_key]
                key = day[1]['obs_day']
                if key in median_dict.keys():
                    tmp_list = median_dict[key]
                    tmp_list.append(data)
                    median_dict[key] = tmp_list.copy()
                else:
                    median_dict[key] = [data]
        medians = list()
        for key in median_dict.keys():
            med = pd.Series(median_dict[key]).median()
            medians.append(med)

        fig = go.Scatter(
            x=list(median_dict.keys()),
            y=medians,
            name='Median',
            line_color='black',
            line_dash='dash'
        )
        return fig

    def get_invivo_group_numbers(self, nsc, expid):
        pipeline = [
            {
                '$match': {
                    'expid': expid
                }
            }, {
                '$project': {
                    'tgroup.animal': 1,
                    '_id': 0,
                    'tgroup.nsc_therapy.nsc': 1
                }
            }, {
                '$unwind': {
                    'path': '$tgroup',
                    'preserveNullAndEmptyArrays': False
                }
            }, {
                '$set': {
                    'animals': '$tgroup.animal.animal_nbr',
                    'nsc': '$tgroup.nsc_therapy.nsc'
                }
            }, {
                '$match': {
                    'nsc': int(nsc)
                }
            }, {
                '$set': {
                    'nsc': {
                        '$first': '$nsc'
                    }
                }
            }, {
                '$count': 'count'
            }
        ]

        data = self.INVIVO_COLL.aggregate(pipeline)
        res = [d for d in data]
        print("DEBUG FROM GET INVIVO GROUP NUMBERS:")
        print(f"NSC: {nsc} | EXPID: {expid}")
        print(f"RES:\n {res}")
        print("***********************************************")

        return range(0, res[0]['count'])

    def get_invivo_box_plots(self, expid, nsc, group):
        pipeline = [
            {
                '$match': {
                    'expid': expid
                }
            }, {
                '$project': {
                    'tgroup.animal': 1,
                    '_id': 0,
                    'tgroup.nsc_therapy.nsc': 1,
                    'expid': 1,
                    'cellline.cellname': 1,
                    'cellline.panelcde': 1
                }
            }, {
                '$unwind': {
                    'path': '$tgroup',
                    'preserveNullAndEmptyArrays': False
                }
            }, {
                '$set': {
                    'animals': '$tgroup.animal.animal_nbr',
                    'weight': '$tgroup.animal.animal_history',
                    'tumor': '$tgroup.animal.tumor_history',
                    'nsc': '$tgroup.nsc_therapy.nsc'
                }
            }, {
                '$unset': 'tgroup'
            }, {
                '$match': {
                    '$or': [
                        {
                            'nsc': {
                                '$eq': 999999
                            }
                        }, {
                            'nsc': {
                                '$eq': int(nsc)
                            }
                        }
                    ]
                }
            }, {
                '$set': {
                    'nsc': {
                        '$first': '$nsc'
                    }
                }
            }
        ]

        data = self.INVIVO_COLL.aggregate(pipeline)
        data = [d for d in data]

        group_num = int(group)
        print(f"expid: {expid} | nsc:{nsc} | group_num:{group_num}")

        weights = data[group_num]['weight']
        cellline = data[group_num]['cellline']
        nsc = data[group_num]['nsc']
        tumor_weights = data[group_num]['tumor']

        cell_nsc_text = f"NSC {nsc} | {cellline['panelcde']} - {cellline['cellname']}"

        df = None
        for i, w in enumerate(tumor_weights):
            name = f"animal {i}"
            if i == 0:
                df = pd.DataFrame(w)
                df = df[['tumor_wt', 'obs_day']]
                df.set_index('obs_day', inplace=True)
                df.columns = [name]
            else:
                temp_df = pd.DataFrame(w)
                temp_df = temp_df[['tumor_wt', 'obs_day']]
                temp_df.set_index('obs_day', inplace=True)
                temp_df.columns = [name]
                df = pd.concat([df, temp_df], axis=1)
        tumor_box = px.box(df.transpose(), labels={'value': 'Weight (mg)', 'obs_day': 'Time (days)'},
                           title=f'Animal Tumor Weight Box Plots {cell_nsc_text}')

        df = None
        for i, w in enumerate(weights):
            name = f"animal {i}"
            if i == 0:
                df = pd.DataFrame(w)
                df = df[['obs_day','net_weight']]
                df.set_index('obs_day', inplace=True)
                df.columns = [name]
            else:
                temp_df = pd.DataFrame(w)
                temp_df = temp_df[['obs_day','net_weight']]
                temp_df.set_index('obs_day', inplace=True)
                temp_df.columns = [name]
                df = pd.concat([df, temp_df], axis=1)
        box = px.box(df.transpose(), labels={'value': 'Net Weight (g)', 'obs_day': 'Time (days)'},
                     title=f'Animal Weight Box Plots {cell_nsc_text}')

        return {'tumor': tumor_box, 'weight': box}

    def get_comp_data(self, nsc):
        print(f'IN dataservice LINE 964')
        comp = self.COMPOUNDS_COLL.aggregate([
                            {
                                '$match': {
                                    'nsc': int(nsc)
                                }
                            }
                        ])
        return comp.next()

    def get_invivo_summary_plots(self,expid):
        data = self.INVIVO_COLL.aggregate([
                {
                    '$match': {
                        'expid': expid
                    }
                }, {
                    '$project': {
                        'expid': 1,
                        'tgroup': 1,
                        'cell': '$cellline.cellname',
                        'panel': '$cellline.panelcde',
                        'implant_date': 1,
                        'staging_date': 1,
                        '_id': 0
                    }
                }, {
                    '$unwind': {
                        'path': '$tgroup'
                    }
                }, {
                    '$project': {
                        'expid': 1,
                        'cell': 1,
                        'panel': 1,
                        'implant_date': 1,
                        'staging_date': 1,
                        'schedule': {
                            '$arrayElemAt': [
                                '$tgroup.nsc_therapy.treatment_schedule', 0
                            ]
                        },
                        'group_type': '$tgroup.group_type.description',
                        'group_size': '$tgroup.nbr_animals',
                        'animals_nt_wt': '$tgroup.animal.animal_history.net_weight',
                        'animals_md_tm_wt': '$tgroup.animal.tumor_history.tumor_wt',
                        'animals_obs_days': '$tgroup.animal.animal_history.obs_day',
                        'nsc': {
                            '$arrayElemAt': [
                                '$tgroup.nsc_therapy.nsc', 0
                            ]
                        }
                    }
                }, {
                    '$set': {
                        'animal_data': {
                            '$zip': {
                                'inputs': [
                                    '$animals_nt_wt', '$animals_md_tm_wt', '$animals_obs_days'
                                ]
                            }
                        }
                    }
                }, {
                    '$project': {
                        'expid': 1,
                        'cell': 1,
                        'panel': 1,
                        'nsc': 1,
                        'group_type': 1,
                        'group_size': 1,
                        'implant_date': 1,
                        'staging_date': 1,
                        'animal_data': 1,
                        'schedule': 1
                    }
                }
            ])
        data = [d for d in data]

        implant_dt = data[0]['implant_date']
        staging_dt = data[0]['staging_date']
        # Next, we shall consolidate our data into plotly friendly structures
        data_dict = {}
        group_num = 1
        # for each Group { dict with a key of animal_data }
        for group in data:
            net_wts = []
            tum_wts = []
            obsv_time = None

            data_dict_key = f'Group{group_num}'

            # Separate all the data into net_wts, tumor_wts
            for animal in group['animal_data']:
                net_wts.append(animal[0])
                tum_wts.append(animal[1])
                if obsv_time is None:
                    obsv_time = animal[2]
                elif obsv_time is not None:
                    if len(obsv_time) < len(animal[2]):
                        obsv_time = animal[2]
                else:
                    print('Error Setting Observation Time')
            if len(net_wts) == 0:
                continue
            # Some of the data is missing observation timestamps.
            #if obsv_time.size == 0:
            #    obsv_time = range(0,len(net_wts[0])-1)

            # Make a dictionary that contains group data organized into DFs

            # Make a dataframe that has a mean col
            netwt_df = pd.DataFrame(net_wts).transpose()
            netwt_df['mean'] = netwt_df.mean(axis=1)
            net_wt_obsv_time = obsv_time[:len(netwt_df['mean'])]
            netwt_df['obsv_time'] = net_wt_obsv_time
            netwt_df.fillna(method='ffill', inplace=True)
            netwt_df.set_index('obsv_time', inplace=True,)

            tumwt_df = pd.DataFrame(tum_wts).transpose()
            tumwt_df['median'] = tumwt_df.median(axis=1)
            tum_wt_obsv_time = obsv_time[:len(tumwt_df['median'])]
            tumwt_df['obsv_time'] = tum_wt_obsv_time
            tumwt_df.fillna(method='ffill', inplace=True)
            tumwt_df.set_index('obsv_time', inplace=True)

            # Make two members of data dict at net_wt,tum_wt
            grp_data = {'net_wt': netwt_df, 'tum_wt': tumwt_df}

            # Obviously we add it like this.
            data_dict[data_dict_key] = grp_data

            # increase the count because this is straightforward.
            group_num += 1

        # Now it's time to make Two Plotly Figures
        # create the two Figure objects on which we will apply plots
        net_wt = go.Figure()
        tum_wt = go.Figure()

        # To keep track of the group number as we process data, also used to group data.
        grp_num = 1

        # Ensure unique colors for each trace
        color_list = random.sample(range(len(self.COLORS)),k=len(data_dict.keys()))
        # Set up an index value to be incremented over the following loop
        color_count = 0

        symbol_list = random.sample(range(len(self.SYMBOLS)),k=len(data_dict.keys()))
        symbol_count = 0

        for key in data_dict.keys():
            # Get each dataframe of net weith and tumor from the data dict
            nt_box_data = data_dict[key]['net_wt']
            tum_box_data = data_dict[key]['tum_wt']

            nt_mean = data_dict[key]['net_wt']['mean']
            tum_med = data_dict[key]['tum_wt']['median']

            # Since they share the same index, we will extract that
            index = None
            if nt_box_data.index.equals(tum_box_data.index):
                index = nt_box_data.index
            else:
                print('Indexes are not the same! This is bad.')
                break

            # Ignore the last column, which is mean or median
            nt_box_data = nt_box_data[nt_box_data.columns[:-1]]
            tum_box_data = tum_box_data[tum_box_data.columns[:-1]]

            x_vals = []
            grp_size = len(nt_box_data.columns)
            for i in index:
                for j in range(0, grp_size):
                    x_vals.append(i)

            nt_box_y = []
            tum_box_y = []

            for i in index:
                # iterate over the rows to create a box plot and add to each figure
                for y in nt_box_data.loc[i]:
                    # For multi-grouped box plots, we have to make a giant list
                    # of each y value.
                    nt_box_y.append(y)

                for y in tum_box_data.loc[i]:
                    tum_box_y.append(y)

            # Increment the group number

            try:
                color_num = color_list[color_count]
                symbol_num = symbol_list[symbol_count]
                net_wt.add_trace(
                    go.Box(y=nt_box_y, x=x_vals, name=f'Group {grp_num}', marker=dict(color=self.COLORS[color_num])))
                tum_wt.add_trace(
                    go.Box(y=tum_box_y, x=x_vals, name=f'Group {grp_num}', marker=dict(color=self.COLORS[color_num])))

                net_wt.add_trace(
                    go.Scatter(x=nt_mean.index, y=nt_mean, mode='lines+markers', name=f'Group {grp_num} - Mean',
                               line=dict(width=0.5, color=self.COLORS[color_num]),
                               marker=dict(symbol=self.SYMBOLS[symbol_num], color=self.COLORS[color_num])))
                tum_wt.add_trace(
                    go.Scatter(x=tum_med.index, y=tum_med, mode='lines+markers', name=f'Group {grp_num} - Median',
                               line=dict(width=0.5, color=self.COLORS[color_num]),
                               marker=dict(symbol=self.SYMBOLS[symbol_num], color=self.COLORS[color_num])))
            except IndexError as e:
                e.args
            grp_num += 1
            color_count += 1
            symbol_count += 1

        # After all the boxes are added, we set each figure to be Group mode to handle
        # the repeated X values
        net_wt.update_layout(
            title='Net Weight', title_x=0.5,
            yaxis_title='Net Weight (g)', xaxis_title='Days Post-Implant',
            boxmode='group',  # group boxes together for diff traces of x value
        )
        tum_wt.update_layout(
            title='Tumor Weight', title_x=0.5,
            yaxis_title='Tumor Weight (mg)', xaxis_title='Date Post-Implant',
            boxmode='group',# group boxes together for diff traces of x value
        )

        # fill out data table for descriptions, dictionary
        descriptions = []
        for i in range(1,(len(data)+1)):
            if 'panel' not in data[i-1].keys():
                data[i-1]['panel'] = '(Panel N/A)'
            if 'nsc' not in data[i-1].keys():
                data[i-1]['nsc'] = '(No NSC)'
            descriptions.append({'group': f'Group {i}', 'description': f'Type: {data[i-1]["group_type"]}; NSC: {data[i-1]["nsc"]}; Schedule: {data[i-1]["schedule"]}; Cell {data[i-1]["cell"]}; Panel: {data[i-1]["panel"]}; Size: {data[i-1]["group_size"]}'})
        return {'expid':data[0]['expid'],'net_wt_fig': net_wt, 'tum_wt_fig': tum_wt, 'implant_dt': implant_dt,'staging_dt': staging_dt, 'descriptions': descriptions}

dataService = DataService()
