from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, CustomJS, CustomJSTickFormatter,
    HoverTool, Legend, LegendItem, Div, Range1d         # ← NEW
)
from bokeh.transform import dodge
from bokeh.layouts import column
from bokeh.embed import json_item
import pandas as pd
import json


def generate_cnv_distribution_plot(cnv_data, sample_id, available_chromosomes, gender=None):
    """Generate interactive CNV count plot with gender‑aware analysis."""
    print(f"Debug - CNV data columns: {cnv_data.columns if cnv_data is not None else 'No data'}")
    print(f"Debug - CNV data entries: {len(cnv_data) if cnv_data is not None else 0}")
    
    # Track if data is empty - but don't return error, generate empty plot instead
    is_empty_data = cnv_data is None or len(cnv_data) == 0

    try:
        # Handle empty data - create empty counts for all chromosomes
        if is_empty_data:
            all_chroms = [str(c) for c in available_chromosomes]
            counts = {
                k: {c: 0 for c in all_chroms}
                for k in ['del_medium', 'del_large', 'dup_medium', 'dup_large']
            }
        # Handle single sample (pre/post) data structure
        elif 'CopyNumber' in cnv_data.columns:  # Single sample case
            df = cnv_data.copy()
            # Create Type from CopyNumber
            df['Type'] = df['CopyNumber'].apply(
                lambda x: 'Deletion' if x < 2 else 'Duplication' if x > 2 else 'Normal'
            )
            # Filter out normal regions
            df = df[df['Type'] != 'Normal']
            # Create length column
            df['Length'] = (df['End'] - df['Start']) / 1e6
            
        # Handle differential CNV data
        else:  
            if cnv_data is None or cnv_data.empty:
                return json.dumps({'error': 'No CNV data available'})
                
            required_cols = ['Chromosome', 'Start', 'End', 'Type']
            if not all(col in cnv_data.columns for col in required_cols):
                missing = [col for col in required_cols if col not in cnv_data.columns]
                return json.dumps({'error': f"Missing required columns: {', '.join(missing)}"})

            df = cnv_data.copy()
            df['Length'] = (df['End'] - df['Start']) / 1e6
            df = df[df['Type'].isin(['Deletion', 'Duplication'])]

        # Common processing for data (skip if empty)
        if not is_empty_data:
            df['length_category'] = pd.cut(
                df['Length'],
                bins=[0, 0.2, 1.0, float('inf')],
                labels=['<0.2Mb', '0.2-1.0Mb', '>1.0Mb'],
                include_lowest=True
            )

            # ------------------------- chromosome sets ------------------------
            # Convert to strings while preserving order
            all_chroms = [str(c) for c in available_chromosomes]
            
            # Keep ALL chromosomes from available_chromosomes (don't filter df here)
            # Just ensure we only count chromosomes in the allowed list
            df['Chromosome'] = df['Chromosome'].astype(str)
            df = df[df['Chromosome'].isin(all_chroms)]

            # --------------------------- counting -----------------------------
            # Initialize counts for ALL chromosomes in available_chromosomes
            counts = {
                k: {c: 0 for c in all_chroms}
                for k in ['del_medium', 'del_large', 'dup_medium', 'dup_large']
            }

            for _, row in df.iterrows():
                chrom = str(row['Chromosome'])
                cnv_type = row['Type']
                length_cat = row['length_category']

                if chrom not in all_chroms:
                    continue  # skip chromosomes not in our list

                if cnv_type == 'Deletion':
                    if length_cat == '0.2-1.0Mb':
                        counts['del_medium'][chrom] += 1
                    elif length_cat == '>1.0Mb':
                        counts['del_large'][chrom] += 1
                else:
                    if length_cat == '0.2-1.0Mb':
                        counts['dup_medium'][chrom] += 1
                    elif length_cat == '>1.0Mb':
                        counts['dup_large'][chrom] += 1
        else:
            # Already initialized counts above for empty data
            all_chroms = [str(c) for c in available_chromosomes]

        # --------------------- ColumnDataSource ---------------------------
        cds = {
            'chromosomes': all_chroms,
            'del_medium': [counts['del_medium'][c] for c in all_chroms],
            'del_large':  [counts['del_large'][c] for c in all_chroms],
            'dup_medium': [counts['dup_medium'][c] for c in all_chroms],
            'dup_large':  [counts['dup_large'][c] for c in all_chroms],
        }
        cds['dup_total'] = [m + l for m, l in zip(cds['dup_medium'], cds['dup_large'])]
        cds['del_total'] = [m + l for m, l in zip(cds['del_medium'], cds['del_large'])]

        source = ColumnDataSource(cds)

        # ------------------ FIXED y‑axis range (NEW) ----------------------
        axis_max = max(max(cds['dup_total']), max(cds['del_total']))
        y_fixed = Range1d(0, max(1, axis_max * 1.1))            # 10 % head-room

        # -------------------------- figure --------------------------------
        p = figure(
            x_range=all_chroms,
            height=400,  # Fixed height for better mobile experience
            sizing_mode='stretch_width',  # Makes plot responsive
            title=f'CNV Counts – {sample_id}',
            toolbar_location='above',
            tools='pan,box_zoom,reset,save',
            x_axis_label='Chromosome',
            y_axis_label='Number of CNVs',
            y_range=y_fixed,
            min_width=600,  # Minimum width before mobile layout kicks in
            max_width=1200,  # Maximum width on large screens
            margin=(0, 20, 0, 20)  # Add horizontal padding
        )

        dup_bars = p.vbar(
            x=dodge('chromosomes', -0.15, range=p.x_range),
            top='dup_total',
            width=0.3,
            color='#377eb8',
            alpha=0.6,
            muted_alpha=0.1,
            source=source,
        )

        del_bars = p.vbar(
            x=dodge('chromosomes', 0.15, range=p.x_range),
            top='del_total',
            width=0.3,
            color='#e41a1c',
            alpha=0.6,
            muted_alpha=0.1,
            source=source,
        )

        # invisible glyph to drive size filter
        size_toggle = p.line([], [], line_width=0, alpha=0, visible=True)
        size_toggle.muted = True

        size_cb = CustomJS(args=dict(src=source, tog=size_toggle), code="""
            const d = src.data;
            const largeOnly = !tog.muted;
            for (let i = 0; i < d['dup_total'].length; i++) {
                if (largeOnly) {
                    d['dup_total'][i] = d['dup_large'][i];
                    d['del_total'][i] = d['del_large'][i];
                } else {
                    d['dup_total'][i] = d['dup_medium'][i] + d['dup_large'][i];
                    d['del_total'][i] = d['del_medium'][i] + d['del_large'][i];
                }
            }
            src.change.emit();
            // y-axis stays unchanged because it is a fixed Range1d
        """)
        size_toggle.js_on_change('muted', size_cb)

        # --------------------------- legend -------------------------------
        legend = Legend(
            items=[
                LegendItem(label='Duplications', renderers=[dup_bars]),
                LegendItem(label='Deletions',   renderers=[del_bars]),
                LegendItem(label='≥1.0 Mb',     renderers=[size_toggle]),
            ],
            click_policy='mute',
            location='center',
            orientation='vertical',
            glyph_height=20,
            glyph_width=20,
        )
        p.add_layout(legend, 'right')

        # ----------------------- hover & styling --------------------------
        p.add_tools(HoverTool(tooltips=[
            ('Chromosome', '@chromosomes'),
            ('Duplications (0.2-1 Mb)', '@dup_medium'),
            ('Duplications (>1 Mb)',    '@dup_large'),
            ('Deletions (0.2-1 Mb)',    '@del_medium'),
            ('Deletions (>1 Mb)',       '@del_large'),
        ]))

        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = '#eeeeee'
        p.ygrid.grid_line_alpha = 0.6
        p.x_range.range_padding = 0.02

        # ----------------------- gender banner ----------------------------
        gender_text = {
            'F': "Gender: Female",
            'M': "Gender: Male"
        }.get(gender, "Gender: Unknown")

        banner = Div(text=f"<div style='text-align:center;margin-bottom:12px;'><strong>{gender_text}</strong></div>")

        # Create layout
        layout = column(
            banner, 
            p, 
            sizing_mode='stretch_width',
            css_classes=['responsive-plot']
        )

        # Add empty data flag to the JSON response
        result = json_item(layout)
        result['is_empty_data'] = is_empty_data
        
        return json.dumps(result)

    except Exception as e:
        return json.dumps({'error': str(e)})