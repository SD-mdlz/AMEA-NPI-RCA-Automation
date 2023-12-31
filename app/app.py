from collections import OrderedDict
import datetime
import json
from dash import Dash, dcc, html, Input, Output, State, dash_table, ctx, get_asset_url
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import os
from data_consolidation import generate_consolidated_file, save_consolidated_file, read_consolidated_file, column_list
from sql import download_data, upload_data
from data_prep import get_data
from dash.dash_table import DataTable, FormatTemplate
pd.set_option('mode.chained_assignment', None)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], prevent_initial_callbacks=True, suppress_callback_exceptions=True)

global df
global df_target
# df = generate_consolidated_file()
# df = pd.read_csv('data/NPI_RCA.csv')
# df = read_consolidated_file()
# df = generate_consolidated_file()
df = download_data("Tbl_Dash_Test_v2")

# df_target = pd.read_csv('data/NPI AC Targets.csv')
df_target = download_data("Tbl_Dash_Test_v2_AC")

print(df.shape)

def get_app_header():
    header = dbc.Row([
        dbc.Col(html.Img(src=get_asset_url('MDLZ Logo.jpg'), alt='mdlz-logo', height=60), width=1),
        dbc.Col(html.Div('Amea npi rca application', className='app-header')),
        dbc.Col(html.Img(src=get_asset_url('CAT Logo.jpeg'), alt='cat-logo', height=60), width=1),
    ],
    justify='end',
    class_name='title-bar')
    return header

tab_lables = ['Home', 'NPI Analysis', 'Submit RCA', 'RCA Adoption', 'AC Targets']

def get_filtered_df(df, filters):
    # print(filters)
    df_filtered = df.copy()
    for filter in filters:
        if filter is not None and filters[filter] is not None and len(filters[filter]) != 0:
            if filter == 'Total Inv ($K)':
                df_filtered = df_filtered[df_filtered[filter].between(filters[filter][0], filters[filter][1])]
            else:    
                df_filtered = df_filtered[df_filtered[filter].isin(filters[filter])]
    return df_filtered

def get_filtered_df_trend(df, filters):
    # print(filters)
    df_filtered = df.copy()
    for filter in filters:
        if filter is not None and filters[filter] is not None and len(filters[filter]) != 0 and filter!='Month':
            df_filtered = df_filtered[df_filtered[filter].isin(filters[filter])]
    return df_filtered

def get_filter_row_npi(df, filters, view, filter_labels):
    df_filtered = get_filtered_df(df, filters)
    values = []
    for i in range(len(filter_labels)):
        if filters!={} and filter_labels[i] == list(filters.keys())[0]:
            values.append([item for item in df[filter_labels[i]].dropna().unique()])
        else:
            values.append([item for item in df_filtered[filter_labels[i]].dropna().unique()])
    row = dbc.Row([
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(filter_labels[i], class_name='card-filters-header'),    
                    dbc.CardBody(
                        dcc.Dropdown(
                            values[i],
                            id="f-"+ view +"-"+filter_labels[i],
                            value=filters[filter_labels[i]] if filter_labels[i] in filters else [],
                            multi=True,
                        ),
                        class_name='card-filters-body',
                    )
                ]
            ),
        class_name='px-1',
        ) for i in range(len(filter_labels))
        ] 
        +
        [
            dbc.Container(
                dbc.Row([
                    dbc.Button('Apply', id='filter-apply-'+view, class_name='filter-button-right'), 
                    dbc.Button('Clear', id='filter-clear-'+view, class_name='filter-button-right')
                ],
                ),
            class_name='filter-button-container',
            fluid=True
            )
        ],
        class_name='card-filters-row'
    )
    return row

def get_kpi_row(df, filters):
    df = get_filtered_df(df, filters)
    kpi = ['Total Inv ($K)', 'NPI Inv ($K)', 'Blocked Inv ($K)', 'Excess Inv ($K)', 'IWND Inv ($K)', 'NPI Inv (%)']

    row = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(kpi[i], class_name='card-summary-header'),
                dbc.CardBody(
                    '$ {:,.0f} K'.format(round(df[kpi[i]].astype(float).sum(),0)) if kpi[i] != 'NPI Inv (%)' else '{:,.0f} %'.format(round(df['NPI Inv ($K)'].sum()/df['Total Inv ($K)'].sum()*100)), 
                    class_name='card-summary-body'
                )
            ])
        )
        for i in range(len(kpi))
    ],
    class_name='card-summary-row')
    return row

def npi_chart(i, df):
    chart_height = 250
    chart_name = 'npi-'+str(i+1)
    df = get_data(df, chart_name)
    if chart_name=='npi-1':
        fig = px.bar(df, x='BU', y='NPI %', height=chart_height, text='NPI %')
        fig.update_layout(
            title_x=0.5,
            xaxis={'showline':False, 
            'showgrid':False}, 
            yaxis={'showline':False}, 
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0)
            )
        fig.update_traces(textfont_size=12, textangle=0, marker_color='#724D8D')
        chart = dcc.Graph(figure=fig)
    elif chart_name=='npi-2':
        fig = px.line(df, x='Month', y='NPI %', markers=True, height=chart_height)
        fig.update_layout(
            xaxis={'showline':False, 
            'showgrid':False}, 
            yaxis={'showline':False}, 
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0)
            )
        fig.update_traces(marker_color='#E18719', line_color='#E18719')
        chart = dcc.Graph(figure=fig)
    elif chart_name=='npi-3':
        fig = px.pie(df, values='NPI Components', names=df.index, height=chart_height, color=df.index, color_discrete_map={'Excess Inv ($K)':'#623E23', 'Blocked Inv ($K)':'#E18719', 'IWND Inv ($K)':'#287819'})
        fig.update_layout(
            xaxis={'showline':False, 
            'showgrid':False}, 
            yaxis={'showline':False}, 
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0))
        chart = dcc.Graph(figure=fig)
    elif chart_name=='npi-4':
        # print(df)
        chart = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                dict(id = 'Global Category', name='Global Category'),
                dict(id = 'SKU-Desc', name='SKU-Desc'),
                dict(id = 'Total Inv ($K)', name='Total Inv ($K)', type='numeric', format=dash_table.FormatTemplate.money(2)),
                dict(id = 'NPI Inv ($K)', name='NPI Inv ($K)', type='numeric', format=dash_table.FormatTemplate.money(2)),
                dict(id = 'NPI %', name='NPI %', type='numeric', format=dash_table.FormatTemplate.percentage(2)),
            ],
            style_table={'height': chart_height, 'overflowY': 'auto'},
            style_cell={'textAlign': 'left'},
            sort_action='native'
        )
    elif chart_name=='npi-5':
        fig = px.bar(df, x='RCA', y='NPI Inv ($K)', height=chart_height)
        fig.update_layout(
            xaxis={'showline':False, 
            'showgrid':False}, 
            yaxis={'showline':False}, 
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0))
        x_labels = [i.replace(' ', '<br>') for i in list(df['RCA'])]
        fig.update_xaxes(tickvals=list(df['RCA']), ticktext=x_labels)
        colors = ['#4F2170', '#E18719', '#287819', '#623E23', '#A52323']
        fig.update_traces(marker_color=colors)
        chart = dcc.Graph(figure=fig)
    else:
        html.Div('no data')
    return chart

def get_charts_row_npi(df, filters):
    title_list = ['NPI % by BU', 'NPI % Trend', 'NPI Split ($K) by Components', 'SKU Details', 'NPI Inv ($K) by Reason Codes']
    df_trend = get_filtered_df_trend(df, filters)
    df = get_filtered_df(df, filters)
    row = dbc.Col([
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(title_list[0], className='card-chart-header'), 
                    dbc.CardBody(npi_chart(0, df), className='card-chart-body')
                ], class_name='card-charts'), 
                width=4
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(title_list[1], className='card-chart-header'), 
                    dbc.CardBody(npi_chart(1, df_trend), className='card-chart-body')
                ], class_name='card-charts'), 
                width=4
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(title_list[2], className='card-chart-header'), 
                    dbc.CardBody(npi_chart(2, df), className='card-chart-body')
                ], class_name='card-charts'), 
                width=4
            )
            # for i in range(3)
            ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(title_list[3], className='card-chart-header'), 
                    dbc.CardBody(npi_chart(3, df), className='card-chart-body')
                ], class_name='card-charts'), 
            width=8),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(title_list[4], className='card-chart-header'), 
                    dbc.CardBody(npi_chart(4, df), className='card-chart-body')
                ], class_name='card-charts'), 
            width=4)
            ]
            ),
        ],
    class_name='card-charts-col')
    return row

def get_npi_content(df, filters):
    content = dbc.Container(
        dbc.Col([
            get_filter_row_npi(df, filters, "npi", filter_labels_1),
            get_kpi_row(df, filters),
            get_charts_row_npi(df, filters)
        ],
        align='center'),
    fluid=True,
    class_name='tab-container-npi-analysis',
    id='npi-content'
    )
    return content

def get_filter_row_submit_rca(df, filters, view, filter_labels):
    df_filtered = get_filtered_df(df, filters)
    values = []
    slider = filter_labels[-1]
    filter_labels = filter_labels[:-1]
    for i in range(len(filter_labels)):
        if filters!={} and filter_labels[i] == list(filters.keys())[0]:
            values.append([item for item in df[filter_labels[i]].dropna().unique()])
        else:
            values.append([item for item in df_filtered[filter_labels[i]].dropna().unique()])
    row = dbc.Row(
        [
            dbc.Container(
                dbc.Row([
                    dbc.Button('Refresh', id='refresh-'+view, class_name='filter-button-left'), 
                ],
                ),
            class_name='filter-button-container',
            fluid=True
            )
        ]
        +
        [
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(filter_labels[i], class_name='card-filters-header'),    
                    dbc.CardBody(
                        dcc.Dropdown(
                            values[i],
                            id="f-"+ view +"-"+filter_labels[i],
                            # class_name='card-filters-drop',
                            value=filters[filter_labels[i]] if filter_labels[i] in filters else [],
                            multi=True,
                        ),
                        class_name='card-filters-body',
                        # style={"height":"80px", "overflowY":"scroll"}
                    )
                ]
            ),
        class_name='px-1',
        ) for i in range(len(filter_labels))
        ]
        +
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(slider, class_name='card-filters-header'),    
                        dbc.CardBody(
                            dcc.RangeSlider(
                                df[slider].min(),
                                df[slider].max(),
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                id="f-"+ view +"-"+slider
                            ),
                            class_name='card-filters-body',
                            # style={"height":"80px", "overflowY":"scroll"}
                        )
                    ]
                ),
            class_name='px-1',
            )
        ]
        +
        [
            dbc.Container(
                dbc.Row([
                    dbc.Button('Apply', id='filter-apply-'+view, class_name='filter-button-right'), 
                    dbc.Button('Clear', id='filter-clear-'+view, class_name='filter-button-right')
                ],
                ),
            class_name='filter-button-container',
            fluid=True
            )
        ],
        class_name='card-filters-row'
    )
    return row

def get_table(df):

    cols = ['Month', 'BU', 'Country', 'Global Category', 'SKU-Desc', 'Location Code', 'Total Inv ($K)', 'NPI Inv ($K)', 'RCA', 'Driver', 'DIOH Opp', 'Comments', 'Included in Provision', 'Timing of resolution (M)', 'RCA Status']
    cols_data = []
    for col in cols:
        editable = False
        if col in ['RCA', 'Comments', 'Included in Provision', 'Timing of resolution (M)']:
            editable=True
        if col in ['RCA', 'Included in Provision', 'Timing of resolution (M)']:
            cols_data.append({"name": col, "id": col, "editable" : editable, "presentation":"dropdown"})
        # type='numeric', format=dash_table.FormatTemplate.money(2)
        elif col in ['Total Inv ($K)', 'NPI Inv ($K)']:
            cols_data.append({"name": col, "id": col, "editable" : editable, 'type':'numeric', 'format':dash_table.FormatTemplate.money(2)})
        else:
            cols_data.append({"name": col, "id": col, "editable" : editable})
    
    RCA_options = ['Demand reduction (forward)', 'Demand under-consumption', 'NPD assumptions', 'Production compliance', 'Incorrect Max setting', 'Supply delays', 'Pre-build', 'Run-out SKU', 'Defective (Not saleable)', 'Master Data Error', 'System forecasting issue', 'Sample stock', 'System issue', 'DC inbalance', 'Returns', 'Other', 'Blocked Stock Sorting']
    
    table = dash_table.DataTable(
        df.to_dict('records'), 
        columns=cols_data,
        editable=True,
        dropdown={
            'RCA':{
                'options':[
                    {'label':i, 'value':i} for i in RCA_options
                ]
            },
            'Included in Provision':{
                'options':[
                    {'label':i, 'value':i} for i in ['Y', 'N']
                ]
            }, 
            'Timing of resolution (M)':{
                'options':[
                    {'label':i, 'value':i} for i in ['1', '2', '3']
                ]
            }
        },
        # page_size=1000,
        # fixed_rows={'headers': True},
        style_cell={'textAlign': 'left'},
        style_table={'overflowY': 'auto', 'marginTop':'20px', 'height':'500px'},
        style_data_conditional=[
            {
                'if':{
                    'filter_query':'{RCA Status} = "RCA Missing"',
                    'column_id': 'RCA Status'
                },
                'backgroundColor':'#FFC7CE',
                'color':'#9C0006'
            },
            {
                'if':{
                    'filter_query':'{RCA Status} = "RCA Available"',
                    'column_id': 'RCA Status'
                },
                'backgroundColor':'#C6EFCE',
                'color':'#006100'
            }
        ],
        style_header={
            'backgroundColor':'#4F2170',
            'color':'#FFFFFF',
            'fontFamily':'mdlz'
        },
        style_header_conditional=[
            {
                'if':{
                    'column_id':col
                },
                'backgroundColor':'#E18719',
            }
            for col in ['RCA', 'Included in Provision', 'Timing of resolution (M)']
        ]
        +
        [
            {
                'if':{
                    'column_id':col
                },
                # 'backgroundColor':'#287819',
                'backgroundColor':'#666666',
            }
            for col in ['Driver', 'DIOH Opp', 'RCA Status']
        ]
        +
        [
            {
                'if':{
                    'column_id':col
                },
                'backgroundColor':'#2D6EAA',
            }
            for col in ['Comments']
        ]
        ,
        id='rca-table',
    )
    return table

def get_rca_summary_table(df):
    df = get_data(df, 'rca_status_summary')
    table = dash_table.DataTable(
        df.to_dict('records'),
        fill_width=False,
        style_cell={'textAlign': 'left', 'minWidth':'150px'},
    )
    return table

def get_rca_row(df):
    content = dbc.Row([
        dbc.Col(get_rca_summary_table(df)),
        dbc.Col(html.Img(src=get_asset_url('legend.jpg'), alt='cat-logo', height=30)),
        dbc.Container(
            dbc.Row([
                dbc.Button('Check', id='rca-check', class_name='rca-botton-button'),
                dbc.Button('Submit', id='rca-submit', class_name='rca-botton-button')
            ]),
            # style={'width':'100px'},
            class_name='rca-botton-button-container'
        )
    ],
    class_name='rca-bottom-container'
    )
    return content

def get_sumbit_rca_content(df, filters):    
    df = get_data(df, 'calculate')
    df = get_filtered_df(df, filters)
    content = dbc.Container(
        dbc.Col([
            get_filter_row_submit_rca(df, filters, "rca", filter_labels_2),
            get_table(df),
            get_rca_row(df)
        ],
        align='center'),
    fluid=True,
    class_name='tab-container-submit-rca',
    id='rca-content'
    )
    return content

def get_filter_row_rca_adoption(df, filters, view, filter_labels):
    df = get_filtered_df(df, filters)
    values = []
    for i in range(len(filter_labels)):
        values.append([item for item in df[filter_labels[i]].dropna().unique()])
    row = dbc.Row(
        [
            dbc.Container(
                dbc.Row([
                    dbc.Button('Refresh', id='refresh-'+view, class_name='filter-button-rca-left'), 
                    dbc.Button('Export', id='export-'+view, class_name='filter-button-rca-left')
                ],
                ),
            class_name='filter-button-container',
            fluid=True
            )
        ]
        +
        [
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(filter_labels[i], class_name='card-filters-header'),    
                    dbc.CardBody(
                        dcc.Dropdown(
                            values[i],
                            id="f-"+ view +"-"+filter_labels[i],
                            value=filters[filter_labels[i]] if filter_labels[i] in filters else [],
                            multi=True,
                        ),
                        class_name='card-filters-body',
                    )
                ]
            ),
        class_name='px-1',
        ) for i in range(len(filter_labels))
        ] 
        +
        [
            dbc.Container(
                dbc.Row([
                    dbc.Button('Apply', id='filter-apply-'+view, class_name='filter-button-right'), 
                    dbc.Button('Clear', id='filter-clear-'+view, class_name='filter-button-right')
                ],
                ),
            class_name='filter-button-container',
            fluid=True
            )
        ],
        class_name='card-filters-row'
    )
    return row

def rca_chart(i, df, mode):
    y_col = 'Count' if mode=='Count' else 'NPI Inv ($K)'
    chart_height = 250
    chart_name = 'rca-'+str(i+1)
    df = get_data(df, chart_name)
    if chart_name=='rca-1':
        fig = px.bar(df, x='BU', y=y_col, height=chart_height, text=y_col)
        fig.update_layout(
            title_x=0.5,
            xaxis={'showline':False,
            'showgrid':False},
            yaxis={'showline':False},
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0)
            )
        fig.update_traces(textfont_size=12, textangle=0, marker_color='#724D8D')
        chart = dcc.Graph(figure=fig)
    elif chart_name=='rca-2':
        fig = px.bar(df, x='Global Category', y=y_col, height=chart_height, text=y_col)
        fig.update_layout(
            title_x=0.5,
            xaxis={'showline':False,
            'showgrid':False},
            yaxis={'showline':False},
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0)
            )
        fig.update_traces(textfont_size=12, textangle=0, marker_color='#724D8D')
        chart = dcc.Graph(figure=fig)
    elif chart_name=='rca-3':
        fig = px.bar(df, x='Month', y=y_col, height=chart_height, text=y_col)
        fig.update_layout(
            title_x=0.5,
            xaxis={'showline':False,
            'showgrid':False},
            yaxis={'showline':False},
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0)
            )
        fig.update_traces(textfont_size=12, textangle=0, marker_color='#724D8D')
        chart = dcc.Graph(figure=fig)
    elif chart_name=='rca-4':
        fig = px.pie(df, values=y_col, names='RCA Status', height=chart_height, color='RCA Status', color_discrete_map={'Not applicable':'#2D6EAA', 'RCA Missing':'#E18719', 'RCA Available':'#287819'})
        fig.update_layout(
            xaxis={'showline':False, 
            'showgrid':False}, 
            yaxis={'showline':False}, 
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0))
        chart = dcc.Graph(figure=fig)
    elif chart_name=='rca-5':
        fig = px.bar(df, x='Driver', y=y_col, height=chart_height, text=y_col)
        fig.update_layout(
            title_x=0.5,
            xaxis={'showline':False,
            'showgrid':False},
            yaxis={'showline':False},
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0)
            )
        fig.update_traces(textfont_size=12, textangle=0, marker_color='#2D6EAA')
        chart = dcc.Graph(figure=fig)
    elif chart_name=='rca-6':
        fig = px.bar(df, x='RCA', y=y_col, height=chart_height, text=y_col)
        fig.update_layout(
            title_x=0.5,
            xaxis={'showline':False,
            'showgrid':False},
            yaxis={'showline':False},
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title=None,
            margin=dict(l=0,r=0,b=0,t=0)
            )
        x_labels = [i.replace(' ', '<br>') for i in list(df['RCA'])]
        fig.update_xaxes(tickvals=list(df['RCA']), ticktext=x_labels)
        colors = ['#4F2170', '#E18719', '#287819', '#623E23', '#A52323']
        fig.update_traces(textfont_size=12, textangle=0, marker_color=colors)
        chart = dcc.Graph(figure=fig)
    else:
        html.Div('no data')
    return chart

def get_charts_row_rca(df, filters, item):
    title_list = ['Missed RCA by BU (' + (item) + ')', 'Missed RCA by Category (' + (item) + ')', 'Missed RCA by Month (' + (item) + ')', '% RCA (' + (item) + ')', 'NPI Inv by Drivers (' + (item) + ')', 'RCA Breakdown (' + (item) + ')']
    # df_trend = get_filtered_df_trend(df, filters)
    df = get_filtered_df(df, filters)
    row = dbc.Col([
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(title_list[i], className='card-chart-header'), 
                    dbc.CardBody(rca_chart(i, df, item), className='card-chart-body')
                ], class_name='card-charts'), 
                width=4
            )
            for i in range(3)
            ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(title_list[i], className='card-chart-header'), 
                    dbc.CardBody(rca_chart(i, df, item), className='card-chart-body')
                ], class_name='card-charts'), 
                width=4
            )
            for i in range(3, 6)
            ])
        ],
    class_name='card-charts-col')
    return row

def get_toggle_row(item):
    count = item=='Count'
    usd = item=='USD'
    content = dbc.Container([
        html.Div('Select incompleteness by >>',style={'display':'inline'}),
        dbc.Button(
            "Count", 
            disabled = count,
            class_name="md-2 rca-adoption-toggle-button",
            id="rca-adoption-toggle-count"
        ),
        dbc.Button(
            "USD", 
            disabled = usd, 
            class_name="me-md-2 rca-adoption-toggle-button",
            id="rca-adoption-toggle-usd"
        ),
    ],
    class_name='rca-adoption-toggle-container', 
    fluid=True)
    return content

def get_rca_adoption_content(df, filters, item):
    content = dbc.Container(
        dbc.Col([
            get_filter_row_rca_adoption(df, filters, "rca-adoption", filter_labels_1),
            get_toggle_row(item),
            get_charts_row_rca(df, filters, item)
        ],
        align='center'),
    fluid=True,
    class_name='tab-container-rca-analysis',
    id='rca-adoption-content'
    )
    return content

def get_ac_target_table(df, is_editable):
    df = df.sort_values(by='BU')
    percentage = FormatTemplate.percentage(2)
    cols_data = []
    for col in df.columns:
        if col in ['BU', 'Market', 'Year']:
            cols_data.append({"name": col, "id": col, "editable" : False})
        else:
            cols_data.append({"name": col, "id": col, "editable" : True if is_editable else False, "type":"numeric"})
    table = dash_table.DataTable(
        df.to_dict('records'),
        columns=cols_data,
        # editable=True,
        fill_width=False,
        style_cell={
            'textAlign': 'left', 
            'minWidth':'80px', 
            'border': '1px solid black'},
        style_header={
            'backgroundColor':'#4F2170',
            'color':'#FFFFFF',
            'fontFamily':'mdlz',
            'border': '1px solid black'
        },
        style_data_conditional=[
            {
                'if':{
                    'filter_query':'{Market} = "'+ col +'"',
                },
                'backgroundColor':'#957AA9',
                'color':'#FFFFFF'
            }
            for col in ['ANZ', 'Greater China', 'India BU', 'Japan', 'MENAP', 'SEA', 'SSA', 'AMEA']
        ],
        id='ac-target-table'
    )
    return table

def get_ac_target_content(df, year):
    year_list = df['Year'].unique()
    if year is None:
        year = max(df['Year'])
    is_editable = True if year == max(df['Year']) else False
    df = df[df['Year'] == year]
    content = dbc.Container(
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader('Year', class_name='card-filters-header'),    
                        dbc.CardBody(
                            dcc.Dropdown(
                            year_list,
                            id="f-ac-target-year",
                            multi=True,
                            )
                        )
                    ]
                ),
                width=1
            ),
            dbc.Col(get_ac_target_table(df, is_editable)),
            dbc.Col(dbc.Button('Update', disabled=not is_editable, class_name='ac-target-update-button', id='ac-target-update'),)
        ],
        align='start',
        class_name='ac-target-row'),
    fluid=True,
    class_name='tab-container-ac-target',
    id='ac-target-content'
    )
    return content

def get_tab_content(tab_lable):
    roles = ['BU Supply Planning', 'Supply Planner Viewer', 'Regional Admin Team']
    if tab_lable=='Home':
        tab = dbc.Container(
            dbc.Row([
                dbc.Col([
                    html.Img(src=get_asset_url('Home Img.jpg'), alt='home-image', height=500)
                ],
                ),
                dbc.Col([
                    dbc.Col('Select your role', class_name='home-role-text'),
                    dbc.Col([dbc.Col(dbc.Button(role, class_name='home-role-btn')) for role in roles])
                ],
                )
            ],
            justify='center',
            ),
        fluid=True,
        class_name='tab-container-home'
        )
    elif tab_lable=='NPI Analysis':
        tab = get_npi_content(df, {})
    elif tab_lable=='Submit RCA':
        tab = get_sumbit_rca_content(df, {})
    elif tab_lable=='RCA Adoption':
        tab = get_rca_adoption_content(df, {}, 'Count')
    elif tab_lable=='AC Targets':
        tab = get_ac_target_content(df_target, None)
    return tab

def get_tabs(active_tab):
    content = dbc.Container([
        dbc.Button(tab_lables[i],
            id='tab-' + str(i),
            class_name='tab-lable-items',
            style={'backgroundColor':'#4F2170', 'color':'white'} if tab_lables[i] == active_tab else {},
        )
        for i in range(5)]
        +
        [
            get_tab_content(
                tab_lables[
                    tab_lables.index(active_tab)
                ]
            )
        ],
        class_name='tab-list-content',
        fluid=True
    )
    return content

# def get_tabs():
#     tabs = dbc.Tabs([
#         dbc.Tab(
#             get_tab_content(tab_lables[i]),
#             label=tab_lables[i],
#             label_class_name='tab-lable-items',
#             active_label_style={'backgroundColor':'#4F2170', 'color':'white'},
#         )
#         for i in range(5)],
#         # active_tab='tab-4',
#         id='tab'
#         )
#     return tabs

def get_filters_alert(view):
    return dbc.Alert(
        id="alert-filter-"+view,
        is_open=False,
        fade=True,
        duration=2500,
        style={"position": "fixed", "top": 20, "right": 10, "width": 350, "zIndex": 1},
        color="danger"
    )

def get_save_alert():
    return dbc.Alert(
        id="alert-save",
        is_open=False,
        fade=True,
        duration=2500,
        style={"position": "fixed", "top": 20, "right": 10, "width": 350, "zIndex": 1},
        color="success"
    )

def get_ac_target_alert():
    return dbc.Alert(
        id="alert-ac-target",
        is_open=False,
        fade=True,
        duration=2500,
        style={"position": "fixed", "top": 20, "right": 10, "width": 350, "zIndex": 1},
        color="success"
    )

filter_labels_1 = ['Month', 'BU', 'Country', 'Location Code', 'Global Category', 'SKU-Desc']
filter_labels_2 = ['BU', 'Country', 'Location Code', 'Global Category', 'SKU-Desc', 'RCA Status', 'Total Inv ($K)']

def get_layout():
    layout = dbc.Container([
        dcc.Store(id='data', data=df.to_dict('records')),
        dcc.Store(id='data-filter-rca', data={}),
        get_filters_alert('npi'),
        get_filters_alert('rca'),
        get_save_alert(),
        get_ac_target_alert(),
        get_app_header(),
        dbc.Container(
            get_tabs(tab_lables[tab_lables.index('Home')]),
            class_name="tab-container",
            id="tab-container",
            fluid=True
        ),
        dcc.Download(id='export-csv'),
    ],
    fluid=True
    )
    return layout

app.layout = get_layout()

def get_inputs(df, df_new):
    df_new = get_data(df_new, 'calculate')
    key_cols = ['Week', 'SKU Code', 'Location Code']
    data_cols = ['RCA', 'Driver', 'DIOH Opp', 'Comments', 'Included in Provision', 'Timing of resolution (M)', 'RCA Status']
    df_new = df_new[key_cols + data_cols]
    for col in data_cols:
        df_new = df_new.fillna('')
    df = df.merge(df_new, on=key_cols, how='left')
    for col in data_cols:
        df[col] = df[col+'_x'].where(df[col+'_y'].isna(), df[col+'_y'])
    df = df.drop([col+'_x' for col in data_cols]+[col+'_y' for col in data_cols], axis=1)
    return df

def update_targets(df, df_new):
    year = df_new['Year'].unique()[0]
    df = df[df['Year']!=year]
    df = pd.concat([df, df_new])
    upload_data(df, "Tbl_Dash_Test_v2_AC")
    return df

# Tab CALLBACK
@app.callback(
    Output("tab-container", "children"),
    Input("tab-0", "n_clicks"),
    Input("tab-1", "n_clicks"),
    Input("tab-2", "n_clicks"),
    Input("tab-3", "n_clicks"),
    Input("tab-4", "n_clicks"),
    prevent_initial_call=True,
)
def tab_callback(t1_click,t2_click,t3_click,t4_click,t5_click):
    tab = ctx.triggered_id
    return get_tabs(tab_lables[int(tab[4:])])

# NPI CALLBACK
@app.callback(
    Output("npi-content", "children"),
    Output("alert-filter-npi", "children"),
    Output("alert-filter-npi", "is_open"),
    Input("filter-apply-npi", "n_clicks"),
    Input("filter-clear-npi", "n_clicks"),
    State("f-npi-Month", "value"),
    State("f-npi-BU", "value"),
    State("f-npi-Country", "value"),
    State("f-npi-Location Code", "value"),
    State("f-npi-Global Category", "value"),
    State("f-npi-SKU-Desc", "value"),
    prevent_initial_call=True,
)
def npi_callback(apply_click, clear_click, f_month, f_bu, f_country, f_location, f_category, f_sku):
    filters={}
    if ctx.triggered_id == "filter-apply-npi":
        filters_new = [f_month, f_bu, f_country, f_location, f_category, f_sku]
        for i, filter in enumerate(filter_labels_1):
            filters[filter] = filters_new[i]
        if get_filtered_df(df,filters).empty:
            return get_npi_content(df, {}), "The selected filter combination was incorrect. Please select valid filters.", True
        else:
            return get_npi_content(df, filters), "", False
    elif ctx.triggered_id == "filter-clear-npi":
        return get_npi_content(df, {}), "", False

# SUBMIT RCA CALLBACK
@app.callback(
    Output("rca-content", "children"),
    Output("alert-filter-rca", "children"),
    Output("alert-filter-rca", "is_open"),
    Output("alert-save", "children"),
    Output("alert-save", "is_open"),
    Input("filter-apply-rca", "n_clicks"),
    Input("filter-clear-rca", "n_clicks"),
    Input("rca-check", "n_clicks"),
    Input("rca-submit", "n_clicks"),
    Input("refresh-rca", "n_clicks"),
    State("f-rca-BU", "value"),
    State("f-rca-Country", "value"),
    State("f-rca-Location Code", "value"),
    State("f-rca-Global Category", "value"),
    State("f-rca-SKU-Desc", "value"),
    State("f-rca-RCA Status", "value"),
    State("f-rca-Total Inv ($K)", "value"),
    State("data-filter-rca", "data"),
    State("rca-table", "data"),
    prevent_initial_call=True,
)
def rca_callback(apply_click, clear_click, check_click, submit_click, refresh_click, f_bu, f_country, f_location, f_category, f_sku, f_status, f_total_inv, filters, data):
    print(ctx.triggered_id)
    global df
    if refresh_click:
        # df = read_consolidated_file()
        df = download_data("Tbl_Dash_Test_v2")
        return get_sumbit_rca_content(df, {}), "", False, "", False
    df_new = pd.DataFrame(data)
    if ctx.triggered_id == "rca-check":
        return get_sumbit_rca_content(df_new, filters), "", False, "", False
    if ctx.triggered_id == "filter-clear-rca":
        df_temp = get_inputs(df, df_new)
        return get_sumbit_rca_content(df_temp, {}), "", False, "", False
    else:
        filters_new = [f_bu, f_country, f_location, f_category, f_sku, f_status, f_total_inv]
        for i, filter in enumerate(filter_labels_2):
            filters[filter] = filters_new[i]
        if get_filtered_df(df_new, filters).empty:
            return get_sumbit_rca_content(df, {}), "The selected filter combination was incorrect. Please select valid filters.", True, "", False
        else:
            if ctx.triggered_id == "rca-submit":
                # save_consolidated_file(df)
                df = get_inputs(df, df_new)
                upload_data(df[column_list], "Tbl_Dash_Test_v2")
                return get_sumbit_rca_content(df, filters), "", False, "File Saved Successfully", True
            return get_sumbit_rca_content(df_new, filters), "", False, "", False

# RCA ADOPTION CALLBACK
@app.callback(
    Output("rca-adoption-content", "children"),
    Input("refresh-rca-adoption", "n_clicks"),
    Input("filter-apply-rca-adoption", "n_clicks"),
    Input("filter-clear-rca-adoption", "n_clicks"),
    Input("rca-adoption-toggle-count", "n_clicks"),
    Input("rca-adoption-toggle-usd", "n_clicks"),
    State("f-rca-adoption-Month", "value"),
    State("f-rca-adoption-BU", "value"),
    State("f-rca-adoption-Country", "value"),
    State("f-rca-adoption-Location Code", "value"),
    State("f-rca-adoption-Global Category", "value"),
    State("f-rca-adoption-SKU-Desc", "value"),
    State("rca-adoption-toggle-count", "disabled"),
    prevent_initial_call=True,
)
def rca_adoption_callback(refresh_click, apply_click, clear_click, count_click, usd_click, f_month, f_bu, f_country, f_location, f_category, f_sku, count_disabled):
    print(ctx.triggered_id)
    global df
    item = 'Count' if count_disabled else 'USD'
    if ctx.triggered_id == 'rca-adoption-toggle-count':
        item = 'Count'
        return get_rca_adoption_content(df, {}, item)
    if ctx.triggered_id == 'rca-adoption-toggle-usd':
        item = 'USD'
        return get_rca_adoption_content(df, {}, item)
    if ctx.triggered_id == 'refresh-rca-adoption':
        # df = read_consolidated_file()
        df = download_data("Tbl_Dash_Test_v2")
        # df = pd.read_csv(r"\\mznapwapalt002.krft.net\alteryx\MSC_CAT\Reporting\Data\NPI_RCA.csv")
        return get_rca_adoption_content(df, {}, item)
    elif ctx.triggered_id == 'filter-apply-rca-adoption':
        filters={}
        filters_new = [f_month, f_bu, f_country, f_location, f_category, f_sku]
        for i, filter in enumerate(filter_labels_1):
            filters[filter] = filters_new[i]
        return get_rca_adoption_content(df, filters, item)
    elif ctx.triggered_id == 'filter-clear-rca-adoption':
        return get_rca_adoption_content(df, {}, item)

@app.callback(
    Output("export-csv", "data"),
    Input("export-rca-adoption", "n_clicks"),
    prevent_initial_call=True,
)
def export_callback(export_click):
    global df
    if export_click:
        print(export_click)
        print(ctx.triggered_id)
        return dcc.send_data_frame(df[column_list].to_csv, 'NPI_RCA_OP.csv', index = False)

# AC TARGET CALLBACK
@app.callback(
    Output("ac-target-content", "children"),
    Output("alert-ac-target", "children"),
    Output("alert-ac-target", "is_open"),
    Input("f-ac-target-year", "value"),
    Input("ac-target-update", "n_clicks"),
    State("ac-target-table","data"),
    prevent_initial_call=True,
)
def ac_target(year, update_click, data):
    global df_target
    if ctx.triggered_id == 'ac-target-update':
        df_new = pd.DataFrame(data)
        df_target = update_targets(df_target, df_new)
        return get_ac_target_content(df_target, None), 'Targets Uploaded Successfully', True
    else:
        if year is None or len(year) == 0:
            year = None
        else:
            year = year[0]
        return get_ac_target_content(df_target, year), '', False

if __name__ == "__main__":
    # app.run(debug=True, dev_tools_hot_reload_watch_interval=30, dev_tools_hot_reload_interval=30, dev_tools_hot_reload=False)
    # dev_tools_hot_reload=False,
    # app.run(debug=True)
    app.run(debug=False)