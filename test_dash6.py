import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

# Load and process data (keep this part the same)
interest_rates_df = pd.read_csv('fed.csv')
interest_rates_df = interest_rates_df[interest_rates_df['Date'] >= '2017-02-01']
fomc_meetings_df = pd.read_csv('summary.csv')
fomc_meetings_df = pd.merge(fomc_meetings_df, interest_rates_df, how='inner')
fomc_meetings_df[fomc_meetings_df['Rate'].isna()]

interest_rates_df["Date"] = pd.to_datetime(interest_rates_df["Date"])
interest_rates_df.columns = ['Date', 'Close']
interest_rates_df = interest_rates_df.set_index('Date')
data = interest_rates_df

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    html.H1("Fed Funds Target Rate Against FOMC Announcement"),
    dcc.Graph(id='fed-funds-chart'),
    html.Div(id='hover-text', style={
        'width': '100%',
        'height': '200px',
        'padding': '10px',
        'backgroundColor': '#f0f0f0',
        'borderRadius': '5px',
        'marginTop': '20px',
        'overflowY': 'auto'
    }),
    html.Div(id='debug-output')  # Add this for debugging
])

@app.callback(
    Output('fed-funds-chart', 'figure'),
    Input('fed-funds-chart', 'id')
)
def update_graph(dummy):
    # Create the main price trace
    price_trace = go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name='FDTR Index',
        line=dict(color='blue')
    )

    # Create event traces
    event_traces = []
    annotations = []

    for i in range(len(fomc_meetings_df)):
        temp1 = fomc_meetings_df.iloc[i]
        date = temp1['Date']
        label = temp1['Policy Sentiment']
        price = temp1['Rate']
        summary = temp1['Summary (50 words)']

        print(f"Row {i}: Date={date}, Label={label}, Price={price}")  # Debug print

        event_traces.append(go.Scatter(
            x=[date],
            y=[price],
            mode='markers',
            marker=dict(size=8, color='gray'),
            showlegend=False,
            hoverinfo='text',
            hovertext=f'Date: {date}<br>Rate: {price:.2f}%<br>Sentiment: {label}',
            customdata=[summary, date, price, label]  # Make sure this line is correct
        ))
        print(f"Customdata for row {i}: {[summary, date, price, label]}")  # Debug print
        if label == 'D':
            bcolor = "blue"
        elif label == 'H':
            bcolor = "red"
        else:
            bcolor = "green"
        
        annotations.append(dict(
            x=date,
            y=price,
            xref="x",
            yref="y",
            text=label,
            showarrow=True,
            font=dict(
                family="Courier New, monospace",
                size=10,
                color="#ffffff"
            ),
            align="center",
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#636363",
            ax=0,
            ay=-30,
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=4,
            bgcolor=bcolor,
            opacity=0.8
        ))

    # Create the figure
    fig = go.Figure(data=[price_trace] + event_traces)

    # Update layout
    fig.update_layout(
        title='Fed Funds Target Rate Against FOMC Announcement',
        xaxis_title='Date',
        yaxis_title='FDTR Index',
        annotations=annotations,
        hovermode="closest",
        template="plotly_white"
    )

    return fig

@app.callback(
    [Output('hover-text', 'children'),
     Output('debug-output', 'children')],
    Input('fed-funds-chart', 'hoverData')
)
def update_hover_text(hoverData):
    if hoverData is None:
        return "Hover over a marker to see FOMC meeting summary.", "No hover data"
    debug_info = ""
    #debug_info = f"Hover data: {str(hoverData)}"
    
    # Check if we're hovering over an event marker
    if 'customdata' in hoverData['points'][0]:
        customdata = hoverData['points'][0]['customdata']
        
        #debug_info += f"\nCustomdata: {customdata}"
        
        if isinstance(customdata, list):
            summary = customdata[0]  # Assuming summary is the first item
        else:
            summary = customdata
        
        date = hoverData['points'][0]['x']
        rate = hoverData['points'][0]['y']
        
        # Try to get the sentiment directly from fomc_meetings_df
        matching_row = fomc_meetings_df[fomc_meetings_df['Date'] == date]
        if not matching_row.empty:
            label = matching_row['Policy Sentiment'].values[0]
        else:
            label = "N/A"
        
        #debug_info += f"\nFinal values: date={date}, rate={rate}, label={label}"
        
        # Use HTML line breaks instead of newline characters
        hover_text = html.Div([
            html.P(f"Date: {date}"),
            html.P(f"Rate: {rate:.2f}%"),
            html.P(f"Sentiment: {label}"),
            html.P(f"Summary: {summary}")
        ])
        
        return hover_text, debug_info
    else:
        return "Hover over a marker to see FOMC meeting summary.", debug_info

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
