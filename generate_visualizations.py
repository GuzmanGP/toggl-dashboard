import plotly.express as px

def generate_visualizations(filtered_df):
    # Crea una gráfica de anillos múltiples con el proyecto y las tags
    fig = px.sunburst(filtered_df, path=['pid', 'tags'], title='Distribution of time entries by project and tag')
    fig.show()
