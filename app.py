#!/usr/bin/env python3
import datetime

import pandas as pd 
from pathlib import Path


import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

path = "/home/ernesto/desarrollo/COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"

def ls3(path):
    """
    Retorna una lista de archivos de una ruta (path) dada.
    :param path: Ruta del directorio donde se encuentran los archivos a listar
    :return filenames 
    """
    return [obj.name for obj in Path(path).iterdir() if obj.is_file()]

def getData(country="Venezuela",date="03-13-2020",path=path,encoding="ISO-8859-1"):
    """
    Obtiene los datos desde una fecha y para un país, de la ruta definida de archivos csv.
    :param country: País que se quiere generar el dataframe
    :param date: Fecha desde que se va a tomar los datos para el dataframe
    :param path: Ruta donde se encuentran los archivos csv
    :param encoding: Codificación a la que se encuentran los archivos csv.
    :return df: Dataframe con los datos extraídos de los csv desde una fecha dada y para un país.
    """
    # Se obtiene los nombres de los archivos.
    lista = [file for file in ls3(path) if file.split(".")[-1] == "csv"]
    # Se lee los archivos csv y se convierten en varios dataframe en un diccionario ordenados por fecha.
    df = {item.split(".")[0]:pd.read_csv(path+ "/" +item,encoding=encoding) for item in lista}
    # Se lista las fechas
    dates = [item.split(".")[0] for item in lista]
    # Se renombras las columnas de los dataframes.
    for i,date in enumerate(dates):
        if "Country_Region" in list(df[date].columns) or "Province_State" in list(df[date].columns) or "Last_Update" in list(df[date].columns):
            df[date].rename(columns={"Country_Region": 'Country/Region',"Last_Update":"Last Update","Province_State": "Province/State"},inplace=True)
    # Se convierten las fechas en datetime y se ordenan
    dates2 = sorted([datetime.datetime.strptime(date,"%m-%d-%Y") for date in dates])
    # Se ordena los dataframes en una lista
    if country != None:
        data = [df[d.strftime("%m-%d-%Y")][df[d.strftime("%m-%d-%Y")]["Country/Region"] == country] for d in dates2 if d >= datetime.datetime.strptime(date,"%m-%d-%Y")]
    else: 
        data = [df[d.strftime("%m-%d-%Y")] for d in dates2 if d >= datetime.datetime.strptime(date,"%m-%d-%Y")]

    #Se concatena los dataframes en uno sólo y se retorna
    data_df = pd.concat(data)
    return data_df 

def AddColumnRate(df,column_name):
    """
    Agrega una columna al dataframe, dicha columna es la diferencia entre la próxima row y el row actual
    :param df: DataFrame a agregar la columna.
    :param column_name: Columna a la que se quiere calcular la diferencia.
    :return df: Retorna un dataframe con la columna adicional que tiene la diferencia por día.
    """
    elements = []
    # Se recorre el dataframe
    for i in range(len(df)):
        # Si es la fila inicial se toma su valor
        if i == 0: 
            elements.append(df.iloc[0][column_name]) 
        else:
            # Si no es el inicial se calcula la diferencia de su valor actual con el anterior
            elements.append(df.iloc[i][column_name] - df.iloc[i-1][column_name])
    # Se agrega la lista al dataframe
    df.insert(4,f"rate_{column_name}",elements)
    return df 

def DataProcessor(df):
    """
    Se remueve columnas del dataframe, se define el index, se reemplaza los NA y se agrega dos columnas.
    :param df: Dataframe a procesar
    :return df: DataFrame procesado
    """
    # Se obtiene el nombre de una columna a remover
    remove = list(df.columns)[0]
    # Se remueve la lista de columnas
    df.drop(labels=["Province/State","Latitude","Longitude","Admin2","Lat","Long_","Combined_Key","FIPS",remove],axis=1,inplace=True)
    df.drop(labels=[df.columns[-2]],axis=1,inplace=True)
    # Se reemplaza NA por 0.
    df.fillna(0,inplace=True)
    # Se conviernte las fechas que son string a datetime
    df['Last Update']= pd.to_datetime(df['Last Update'])
    # Se define las fechas como indice
    df.set_index("Last Update",inplace=True)
    # Se calcula los rate de confirmados y muertes
    return df 

start = "01-01-2020"
df = getData(country=None,date=start)
df = DataProcessor(df)
countries = list(set(df["Country/Region"]))
select_graph = ["Deaths","Confirmed","rate_Deaths","rate_Confirmed"]
app = dash.Dash()


app.layout = html.Div(children=[
    html.H1(children='Reports Covid-19'),

    html.Div(children='''
        Covid-19 -Cases per Country.
    '''),
    dcc.Dropdown(
                id='countries',
                options=[{'label': country, 'value': country} for country in countries],
                value='Venezuela'
            ),
    dcc.RadioItems(
                id='graph',
                options=[{'label': i, 'value': i} for i in select_graph],
                value='Confirmed',
                labelStyle={'display': 'inline-block'}
            ),
    html.Div(id='output-table'style={'width': '49%', 'float': 'right', 'display': 'inline-block'}),
    html.Div(id='output-graph'),
])  

@app.callback(
    Output(component_id='output-graph', component_property='children'),
    [Input(component_id='countries', component_property='value'),Input(component_id='graph', component_property='value')]
)
def update_value(input_data,graph_input):
    
    df[df["Country/Region"] == input_data]
    data = AddColumnRate(df[df["Country/Region"] == input_data],"Confirmed")
    data = AddColumnRate(data,"Deaths")

    return dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': data.index, 'y': data[graph_input], 'type': 'line', 'name': input_data},
            ],
            'layout': {
                'title': f"{graph_input} - {input_data}"
            }
        }
    )


@app.callback(
    Output(component_id='output-table', component_property='children'),
    [Input(component_id='countries', component_property='value')]
)
def update_value2(input_data):
    
    df[df["Country/Region"] == input_data]
    data = AddColumnRate(df[df["Country/Region"] == input_data],"Confirmed")
    data = AddColumnRate(data,"Deaths")

    return dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in data.columns],
                data=data.to_dict("rows"),
    )

if __name__ == '__main__':
    app.run_server(debug=True)
