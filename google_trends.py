from pytrends.request import TrendReq
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

def analyze_government_project_trends(project_name, timeframe='today 12-m', geo='GB'):
    """
    Analyze Google Trends data for a UK government project with Plotly visualizations.
    
    Parameters:
    - project_name: str, the name of the government project to analyze
    - timeframe: str, time period (e.g., 'today 12-m' for last 12 months, 'today 5-y' for 5 years)
    - geo: str, country code (default 'GB' for United Kingdom)
    
    Returns:
    - Dictionary with trends data and insights
    """
    
    # Initialize pytrends with simpler parameters
    pytrends = TrendReq(hl='en-GB', tz=0)
    
    # Build payload with delay
    time.sleep(2)  # Add delay before first request
    pytrends.build_payload([project_name], timeframe=timeframe, geo=geo)
    
    # Get interest over time
    time.sleep(2)  # Add delay between requests
    interest_over_time = pytrends.interest_over_time()
    
    if interest_over_time.empty:
        return {
            'error': f'No data found for "{project_name}". Try a different search term or timeframe.'
        }
    
    # Remove 'isPartial' column if it exists
    if 'isPartial' in interest_over_time.columns:
        interest_over_time = interest_over_time.drop(columns=['isPartial'])
    
    # Get interest by region (UK regions/cities) with retry logic
    max_retries = 3
    interest_by_region = pd.DataFrame()
    for attempt in range(max_retries):
        try:
            time.sleep(3)  # Add delay before request
            if geo == 'GB':
                interest_by_region = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True)
            else:
                interest_by_region = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Could not fetch regional data after {max_retries} attempts. Continuing without it.")
    
    if not interest_by_region.empty:
        top_regions = interest_by_region.nlargest(10, project_name)
    else:
        top_regions = pd.DataFrame()
    
    # Get related queries with retry logic
    related_queries = None
    for attempt in range(max_retries):
        try:
            time.sleep(3)  # Add delay before request
            related_queries = pytrends.related_queries()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Could not fetch related queries after {max_retries} attempts. Continuing without them.")
                related_queries = {project_name: {'top': None, 'rising': None}}
    
    # Calculate statistics
    avg_interest = interest_over_time[project_name].mean()
    max_interest = interest_over_time[project_name].max()
    max_interest_date = interest_over_time[project_name].idxmax()
    current_interest = interest_over_time[project_name].iloc[-1]
    
    # Determine trend direction (comparing last month to previous month)
    recent_data = interest_over_time[project_name].tail(8)
    if len(recent_data) >= 8:
        recent_avg = recent_data.tail(4).mean()
        previous_avg = recent_data.head(4).mean()
        trend = "↑ Increasing" if recent_avg > previous_avg else "↓ Decreasing" if recent_avg < previous_avg else "→ Stable"
    else:
        trend = "→ Insufficient data"
    
    # UK General Election date
    election_date = pd.Timestamp('2024-07-04')
    
    # Create interactive time series plot
    fig_timeline = go.Figure()
    
    fig_timeline.add_trace(go.Scatter(
        x=interest_over_time.index,
        y=interest_over_time[project_name],
        mode='lines',
        name='Interest',
        line=dict(color='#005EB8', width=3),  # NHS Blue / UK Gov Blue
        fill='tozeroy',
        fillcolor='rgba(0, 94, 184, 0.2)',
        hovertemplate='<b>Date:</b> %{x|%d %b %Y}<br><b>Interest:</b> %{y}/100<extra></extra>'
    ))
    
    # Add UK General Election line if within timeframe
    if election_date >= interest_over_time.index.min() and election_date <= interest_over_time.index.max():
        # Add vertical line using add_shape instead of add_vline
        fig_timeline.add_shape(
            type="line",
            x0=election_date,
            x1=election_date,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="#D4351C", width=2, dash="solid")
        )
        # Add annotation separately
        fig_timeline.add_annotation(
            x=election_date,
            y=1.02,
            yref="paper",
            text="UK General Election",
            showarrow=False,
            textangle=-90,
            font=dict(size=12, color="#D4351C"),
            xanchor="center",
            yanchor="bottom"
        )
    
    # Add peak marker
    fig_timeline.add_trace(go.Scatter(
        x=[max_interest_date],
        y=[max_interest],
        mode='markers+text',
        name='Peak',
        marker=dict(color='#D4351C', size=12, symbol='star'),  # UK Gov Red
        text=['Peak'],
        textposition='top center',
        hovertemplate=f'<b>Peak Interest</b><br>Date: {max_interest_date.strftime("%d %b %Y")}<br>Value: {max_interest}/100<extra></extra>'
    ))
    
    # Add average line
    fig_timeline.add_hline(
        y=avg_interest,
        line_dash="dash",
        line_color="#00703C",  # UK Gov Green
        annotation_text=f"Average: {avg_interest:.1f}",
        annotation_position="right"
    )
    
    fig_timeline.update_layout(
        title=dict(
            text=f'Google Trends: Public Interest in "{project_name}"',
            font=dict(size=18, color='#0B0C0C')
        ),
        xaxis_title='Date',
        yaxis_title='Search Interest (0-100)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=False,
        font=dict(family="Arial, sans-serif")
    )
    
    # Save timeline
    fig_timeline.write_html(f'{project_name.replace(" ", "_")}_timeline.html')
    
    # Create regional interest bar chart (only if data available)
    fig_regions = None
    if not top_regions.empty:
        fig_regions = go.Figure()
        
        regions_data = top_regions[project_name].sort_values(ascending=True)
        
        fig_regions.add_trace(go.Bar(
            y=regions_data.index,
            x=regions_data.values,
            orientation='h',
            marker=dict(
                color=regions_data.values,
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="Interest")
            ),
            text=regions_data.values,
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Interest: %{x}/100<extra></extra>'
        ))
        
        region_type = "UK Regions/Cities" if geo == 'GB' else "Countries"
        
        fig_regions.update_layout(
            title=dict(
                text=f'Top 10 {region_type} by Interest in "{project_name}"',
                font=dict(size=18, color='#0B0C0C')
            ),
            xaxis_title='Search Interest (0-100)',
            yaxis_title='Region',
            template='plotly_white',
            height=500,
            font=dict(family="Arial, sans-serif")
        )
        
        # Save regions chart
        fig_regions.write_html(f'{project_name.replace(" ", "_")}_regions.html')
    
    # Create related queries chart if available
    fig_queries = None
    if related_queries and project_name in related_queries and related_queries[project_name]['top'] is not None:
        top_queries = related_queries[project_name]['top'].head(10)
        
        fig_queries = go.Figure()
        
        fig_queries.add_trace(go.Bar(
            y=top_queries['query'],
            x=top_queries['value'],
            orientation='h',
            marker=dict(color='#4C2C92'),  # UK Gov Purple
            text=top_queries['value'],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Search Value: %{x}<extra></extra>'
        ))
        
        fig_queries.update_layout(
            title=dict(
                text=f'Top Related Search Queries for "{project_name}"',
                font=dict(size=18, color='#0B0C0C')
            ),
            xaxis_title='Search Value',
            yaxis_title='Query',
            template='plotly_white',
            height=500,
            yaxis={'categoryorder': 'total ascending'},
            font=dict(family="Arial, sans-serif")
        )
        
        fig_queries.write_html(f'{project_name.replace(" ", "_")}_related_queries.html')
    
    # Compile results
    results = {
        'project_name': project_name,
        'timeframe': timeframe,
        'geography': 'United Kingdom' if geo == 'GB' else geo,
        'statistics': {
            'average_interest': round(avg_interest, 2),
            'peak_interest': int(max_interest),
            'peak_date': max_interest_date.strftime('%d %B %Y'),
            'current_interest': int(current_interest),
            'trend': trend
        },
        'top_regions': top_regions.to_dict()[project_name] if not top_regions.empty else {},
        'related_queries': related_queries,
        'interest_over_time': interest_over_time,
        'visualizations': {
            'timeline': fig_timeline
        }
    }
    
    if fig_regions:
        results['visualizations']['regions'] = fig_regions
    if fig_queries:
        results['visualizations']['queries'] = fig_queries
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"UK GOVERNMENT PROJECT TRENDS ANALYSIS: {project_name}")
    print(f"{'='*70}")
    print(f"Timeframe: {timeframe}")
    print(f"Geography: {results['geography']}")
    print(f"\nKEY STATISTICS:")
    print(f"  • Average Interest: {results['statistics']['average_interest']}/100")
    print(f"  • Peak Interest: {results['statistics']['peak_interest']}/100 on {results['statistics']['peak_date']}")
    print(f"  • Current Interest: {results['statistics']['current_interest']}/100")
    print(f"  • Recent Trend: {results['statistics']['trend']}")
    
    if not top_regions.empty:
        region_type = "UK Regions/Cities" if geo == 'GB' else "Countries"
        print(f"\nTOP 10 {region_type.upper()} BY INTEREST:")
        for i, (region, interest) in enumerate(top_regions.to_dict()[project_name].items(), 1):
            print(f"  {i}. {region}: {interest}/100")
    
    if related_queries and project_name in related_queries and related_queries[project_name]['top'] is not None:
        print(f"\nTOP RELATED SEARCH QUERIES:")
        for i, row in related_queries[project_name]['top'].head(5).iterrows():
            print(f"  • {row['query']} (search value: {row['value']})")
    
    print(f"\n✓ Interactive charts saved:")
    print(f"  - {project_name.replace(' ', '_')}_timeline.html")
    if fig_regions:
        print(f"  - {project_name.replace(' ', '_')}_regions.html")
    if fig_queries:
        print(f"  - {project_name.replace(' ', '_')}_related_queries.html")
    print(f"{'='*70}\n")
    
    # Display plots (will open in browser or show in notebook)
    fig_timeline.show()
    if fig_regions:
        fig_regions.show()
    if fig_queries:
        fig_queries.show()
    
    return results


# Example usage for UK government projects:
if __name__ == "__main__":
    # Example 1: HS2 Railway Project
    results = analyze_government_project_trends(
        project_name="HS2",
        timeframe="today 5-y",
        geo="GB"
    )
    
    # Wait before running another query to avoid rate limits
    # time.sleep(30)
    
    # Example 2: Universal Credit
    # results = analyze_government_project_trends(
    #     project_name="Universal Credit",
    #     timeframe="today 12-m",
    #     geo="GB"
    # )