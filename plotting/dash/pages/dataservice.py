"""
The DataService module was originally designed to be a singleton service to handle all database pooling connections
along with handling business logic, so that the main content pages This is an ever-growing module that might be
divided or not.
"""
import os
import random

import numpy as np
from dotenv import load_dotenv

import pymongo
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from lifelines import KaplanMeierFitter
import matplotlib.colors as mcolors
import colorsys
from plotly.validators.scatter.marker import SymbolValidator


class DataService():
    """
    The DataService handles all initialization of data connections and business logic processing.
    """
    initialized = False
    def __init__(self):
        """
        This function initializes the connections and pre-loads the experiment IDs for dcc.Store. Additionally,
        it loads the styles from plot_styles.csv which define the COMPARE style-standards.
        """
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
        self.CELLS_COLL = self.DB.get_collection('fivedose_cells')
        print(f'Collections initialized...')

        # Chart Styles
        self.PLOT_STYLE_DF = pd.read_csv(
            os.path.abspath('../dash/assets/plot_styles.csv'))  # /dash/assets/    /dash/pages/

        # Creates a specific set of colors that contrast well against a light background
        colors = []
        for name, hex in mcolors.CSS4_COLORS.items():
            rgb = mcolors.hex2color(hex)
            ihls = colorsys.rgb_to_hls(*rgb)
            if ihls[2] <= 0.75 and ihls[1] <= 0.65:
                colors.append(name)

        # The colors list is shuffled along with the symbols to create a feeling of random
        # styles for other, non-standardized plotting styles.
        random.shuffle(colors)
        self.COLORS = colors
        symbols = SymbolValidator().values
        random.shuffle(symbols)
        self.SYMBOLS = symbols

    def __del__(self):
        """
        Tries to close all open database connections in the event of application exit.
        :return: noting?
        """
        #self.engine.dispose(close=True)
        self.CLIENT.close()
        print('Closing connections and destructing.')

    def get_df_by_nsc(self, nsc, exp_id):
        """
        MongoDB aggregation query to retrieve data for an NSC from a specific experiment.
        :param nsc: string: NSC within experiment
        :param exp_id: string: experiment ID
        :return: DataFrame: dataFrame of the experiment data for the given NSC
        """
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
        """
        Get onedose data from experiment by NSC and experiment ID
        :param nsc: string: NSC for which we want data from within the experiment
        :param expid: string: experiment ID for which we are looking for result data
        :return: DataFrame: dataFrame of the onedose experiment data
        """
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

    def create_grouped_data_dict(self, df):
        """
        Create a dictionary of values divided up into the cell line panels as the keys.
        :param df: DataFrame: dataFrame of experiment data
        :return: dict: dictionary of data by cell line panel code
        """
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
        """
        Create a dataframe that pivots data based on concentration and subsequent growth percentage values
        :param df: DataFrame: dataframe of response data in five dose.
        :return: DataFrame: dataframe using concentrations as the index value, cell line as columns, and growth values
        """
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
        """
        Entry point to generate a concentration response plot from a dataframe from a fivedose experiment.
        :param df: DataFrame: dataframe of experiment data
        :param nsc: string: NSC in the experiment
        :return: Figure: returns a plotly figure object containing the plot
        """
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
        """
        Create a conc response graph when doing so for only a specific cell line panel.
        :param nsc_df: DataFrame: the panel-specific dataframe of experiment result data
        :param nsc: string: NSC from the experiment
        :param panel: string: cell line panel
        :return: Figure: the plotly Figure object containing the response curve
        """
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
        """
        Create a list of NSCs based on the experiment ID in Fivedose collection.
        :param expid: string: fivedose experiment ID
        :return: list: list of NSCs in the fivedose experiment
        """
        nsc_list = self.FIVEDOSE_COLL.aggregate([
            {
                '$match': {
                    'expid': expid
                }
            }, {
                '$project': {
                    '_id': 0,
                    'fivedosensc': 1
                }
            }
        ])
        # This will be a list of one item since it's a string of the NSCs and not an array
        nsc_list = [d['fivedosensc'] for d in nsc_list]

        # This takes the first (and only) item in the list and creates a list with comma delimited values
        return nsc_list[0].replace('\'', '').split(',')

    def get_mean_graphs_data(self, nsc, expid):
        """
        Initializes the instance data for the graphs of fivedose TGI, GI50, and LC50. Sets them as instance variables
        in order to prevent additional database calls. It's not really necessary, but it is just for speed improvement.
        :param nsc: string: the NSC of the experiment
        :param expid: string: the experiment ID
        :return:None: simply a helping function to optimize some performance
        """
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
        # TODO: this delta value is incorrect and needs to be recalculated based on internal DTP 'delta' formula
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
        """
        Creates the TGI graph for fivedose data.
        :param nsc: string: NSC used for the experiment
        :return: Figure: the TGI plot for fivedose experiment
        """
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
        """
        Creates the GI50 graph for fivedose data.
        :param nsc: string: NSC used for the experiment
        :return: Figure: the GI50 plot for fivedose experiment
        """
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
        """
        Creates the LC50 graph for fivedose data.
        :param nsc: string: NSC used for the experiment
        :return: Figure: the LC50 plot for fivedose experiment
        """
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
        """
        Create the Onedose growth graphs for the given experiment and NSC.
        :param df: DataFrame: onedose dataframe of experiment data specific to NSC
        :param expid: string: the experiment ID
        :param nsc: string: an NSC within the experiment
        :return: list: list of two Figures, the first is growth percentage and the second is the mean graph
        """
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

    def make_survivals(self, kmdf):
        """
        Helper function for KM Graph, to get decimal values
        :param kmdf: Lifelines.KMF: Kaplan-Meier object based on survival data
        :return: list: list of the survival rates in decimal form ie 0.7, 0.6, 0.5, etc
        """
        survival_list = list()
        n = kmdf['at_risk'].iloc()[0]
        for i, x in enumerate(kmdf['at_risk']):
            s = ((x - kmdf['observed'].iloc()[i]) / n)
            survival_list.append(s)
        return survival_list

    def get_km_graph(self, expid, nsc, group):
        """
        Creates the Kaplan-Meier Survival plot.
        :param expid: string: experiment ID of the invivo experiment
        :param nsc: string: NSC data within the experiment
        :param group: string: group number within the experiment
        :return: Figure: plotly figure representing the KM survival line
        """
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
        """
        Creates the Plotly trace of the control group survival rates.
        :param df: DataFrame: dataframe of the experiment
        :return: Graph_Object: plotly scatter graph object of the survival line.
        """
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
        """
        Creates the plots for the animal net weight and tumor weight in invivo experiments per group.
        :param expid: string: the experiment ID
        :param nsc: string: the NSC within the experiment
        :param group: int: the group number within the experiment
        :return: dict: key for each plotly figure.
        """
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
        """
        Creates the actual plotly figure that contains the graph.
        :param anml_data_dict: dict: data structure that contains animal data within the group
        :param cell_line: string: the cell line being examined.
        :param panel_code: string: the panel to which the cell belongs
        :param nsc: string: the NSC used in this part of the experiment
        :param expid: string: the experiment ID for the invivo experiment
        :return: Figure: a plotly figure for the animal group
        """

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
        """
        Helper function to create the title of the plot
        :param cell_line: string: cell line being tested
        :param panel_code: string: panel to which the cell line belongs
        :param nsc: string: the NSC being tested
        :param expid: string: the experiment ID
        :param type: sttring: the type of experiment
        :return: string: descriptive title string for a plot
        """
        nsc_title = f'NSC {str(nsc)}'
        if str(nsc) == '999999':
            nsc_title = 'Control'

        fig_title = f'{type} | {nsc_title} | {panel_code} - {cell_line} | ExpID {expid}'

        return fig_title

    def get_median_trace(self, anml_data_dict, wt_key):
        """
        Create a trace for a plotly figure to represent the median value
        :param anml_data_dict: dict: dict that contains animal data within the group
        :param wt_key: string: the key for which data set to examine, net weight or tumor.
        :return: Figure: scatter plot representing the median weight
        """
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
        """
        Retrieve the group numbers within the experiment
        :param nsc: string: NSC to be examined within the experiment
        :param expid: string: experiment ID of the invivo experiment
        :return: list(range): list of the animal group numbers of the experiment
        """
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

        return range(0, res[0]['count'])

    def get_invivo_box_plots(self, expid, nsc, group):
        """
        Entry point to create the box plots for the invivo experiment for net weight and tumor weight.
        :param expid: string: the invivo experiment ID
        :param nsc: nsc: the NSC being examined within the experiment
        :param group: string: the specific group number within the experiment
        :return: dict: a dictionary with keys: weight and tumor that each have a plotly box plot Figure as the value
        """
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
        """
        Return all compound collection fields given a specific NSC
        :param nsc: string: NSC for which we want to retrieve compound data
        :return: dict: document representing the compound with all the fields as keys, and values per the data model
        """
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
        """
        Generate the plots and table data for an invivo experiment summary, similar to supplier
        reports format.
        :param expid: string: the experiment ID of the invivo experiment
        :return: dict: contains a dictionary with keys: 'expid', 'net_wt_fig', 'tum_wt_fig', 'tum_wt', 'implant_dt',
            'staging_dt', and 'descriptions'; these are all used within the presentation of the data.
        """
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
                print(e.args)
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

    def get_cell_graphs(self, cell):
        """
        Experimental function to see if we could aggregate data of cell lines across all experiments.
        :param cell: string: the cell line to examine
        :return: list: list of figures for each of five dose experiment data per experiment.
        """
        data = [ d for d in
                    self.CELLS_COLL.aggregate(
                    [
                        {
                            '$match': {
                                '_id': cell
                            }
                        }
                    ])
                ]
        # Keys are _id, tgi, lhiconc, nsc
        total = len(data[0]['results'])

        expid = []
        one = []
        two = []
        three = []
        four = []
        five = []
        nsc = []
        total = len(data[0]['results'])

        for i,d in enumerate(data[0]['results']):
            try:
                expid.append(d['expid'])
            except:
                print(f'Failed on cell graphs for {d}')
                expid.append('Failed')

            try:
                nsc.append(str(d['nsc']))
            except:
                print(f'Failed on cell graphs for {d}')
                nsc.append(str(0))

            try:
                one.append(d['growth_pct'][0])
            except IndexError or KeyError:
                one.append(np.NaN)

            try:
                two.append(d['growth_pct'][1])
            except IndexError or KeyError:
                two.append(np.NaN)

            try:
                three.append(d['growth_pct'][2])
            except IndexError or KeyError:
                three.append(np.NaN)

            try:
                four.append(d['growth_pct'][3])
            except IndexError or KeyError:
                four.append(np.NaN)

            try:
                five.append(d['growth_pct'][4])
            except IndexError or KeyError:
                five.append(np.NaN)




        df = pd.DataFrame({'expid': expid, 'nsc':nsc, 'one':one, 'two': two, 'three': three, 'four': four, 'five': five})

        fig1 = px.scatter(data_frame=df[['nsc','one','expid']].sort_values(by='one',ascending=True), x='nsc', y='one', title=f'First Doses', range_y=[(df['one'].max()*1.1), -110.0])
        fig2 = px.scatter(data_frame=df[['nsc','two','expid']].sort_values(by='two',ascending=True), x='nsc', y='two', title=f'Second Doses', range_y=[(df['two'].max()*1.1), -110.0])
        fig3 = px.scatter(data_frame=df[['nsc','three','expid']].sort_values(by='three',ascending=True), x='nsc', y='three', title=f'Thrid Doses', range_y=[(df['three'].max()*1.1), -110.0])
        fig4 = px.scatter(data_frame=df[['nsc','four','expid']].sort_values(by='four',ascending=True), x='nsc', y='four', title=f'Fourth Doses', range_y=[(df['four'].max()*1.1), -110.0])
        fig5 = px.scatter(data_frame=df[['nsc','five','expid']].sort_values(by='five',ascending=True), x='nsc', y='five', title=f'Fifth Doses', range_y=[(df['five'].max()*1.1), -110.0])

        figures = [fig1,fig2,fig3,fig4,fig5]
        return figures

    def get_all_expids_by_nsc(self, insc):
        """
        Return a dataframe of expid, type, description, date.
        All the collections have a text index on respective, root-level nsc list.
        With that index, you can use the match/text/search formula in the agg pipeline.
        :param insc: string: NSC reprsenting an index value
        :return: DataFrame: with columns of expid, type, description, and date for a given NSC across all experiments.
        """

        data_dict = {'Expid':[],'Type':[], 'Description':[]}
        nsc = str(insc)
        # Five Dose dictionary loading
        data = [d for d in
            self.FIVEDOSE_COLL.aggregate([
                    {
                        '$match': {
                              '$text': {
                                '$search': nsc
                              }
                        }
                    }, {
                        '$project': {
                            '_id': 0,
                            'expid': 1,
                            'description': '$testtype.long_descript'
                        }
                    }
                ])
            ]
        for d in data:
            data_dict['Expid'].append(d['expid'])
            data_dict['Type'].append('Five Dose')
            data_dict['Description'].append(d['description'])

        # One Dose dictionary Loading
        data = [d for d in
                self.ONEDOSE_COLL.aggregate([
                    {
                        '$match': {
                              '$text': {
                                '$search': nsc
                              }
                        }
                        }, {
                        '$project': {
                            '_id': 0,
                            'expid': 1,
                            'description': '$testtype.long_descript'
                        }
                    }
                    ]
                )]
        for d in data:
            data_dict['Expid'].append(d['expid'])
            data_dict['Type'].append('One Dose')
            data_dict['Description'].append(d['description'])

        # Invivo dictionary Loading
        data = [d for d in
                self.INVIVO_COLL.aggregate([
                    {
                        '$match': {
                              '$text': {
                                '$search': nsc
                              }
                        }
                    }, {
                        '$project': {
                            '_id': 0,
                            'expid': 1,
                            'description': '$assay_type.description'
                        }
                    }
                ]
                )]
        for d in data:
            data_dict['Expid'].append(d['expid'])
            data_dict['Type'].append('Invivo')
            data_dict['Description'].append(d['description'])


        return pd.DataFrame(data_dict)

    def get_fivedose_heatmap(self, expid, type):
        """
        Create a heatmap of a five dose experiment given an experiment ID for GI50, TGI, and LC50
        :param expid: string: the experiment ID of a five dose experiment
        :param type: string: which metric to use for dataset; the GI50, LC50, or TGI
        :return: Figure: plotly Heatmap for the experiment based on metric of GI50, LC50, or TGI across all NSCs
        """
        df = pd.DataFrame(self.FIVEDOSE_COLL.aggregate([
            {
                '$match': {
                    'expid': expid
                }
            }, {
                '$project': {
                    'nsc': '$tline.nsc',
                    'cell_line': '$tline.cellline.cellname',
                    'panel': '$tline.cellline.panelcde',
                    type: f'$tline.{type}.Average',
                    '_id': 0
                }
            }
        ]).next() )

        # , dtype={'nsc': 'string', 'cell_line':'string', 'panel': 'string', 'gi50': 'float64'}
        df['nsc'] = df['nsc'].apply(lambda x: str(x))

        table = pd.pivot_table(df, values=type, index=['cell_line'], columns=['nsc']).fillna(0)
        # Thought --> Create traces PER panel group and combine on figure object.
        fig = go.Figure(data=go.Heatmap(x=table.columns,
                                        y=table.index,
                                        z=table.values,
                                        colorscale=['red', 'orange', 'yellow', 'green', 'black'],
                                        showlegend=False
                                        ))
        fig.update_traces(colorbar_title_text='Concentration (log10 Molar)', selector=dict(type='heatmap'))
        fig.update_layout(
            title=f'Exp {expid} {type} Heatmap',
            title_x=0.5,
            xaxis_title='NSC',
            yaxis_title='Cell Line',
            height=(60 * 15)
        )
        fig.update_yaxes(tickmode="linear")

        return fig

# This line ensures it is modular and semi-singleton. I say semi-singelton because I know that, for some reason,
# Dash initializes two modules of DataService. I would have to do something hacky to ensure there is only one within
# the given python process.
dataService = DataService()
