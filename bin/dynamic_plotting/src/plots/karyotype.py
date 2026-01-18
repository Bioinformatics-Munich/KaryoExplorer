from bokeh.plotting import figure, save, output_file
from bokeh.models import (
    ColumnDataSource, CDSView, GroupFilter, BooleanFilter,
    Legend, LegendItem, CustomJS
)
from bokeh.models import Range1d
import numbers
from bokeh.palettes import Category10
from bokeh.transform import factor_cmap
from bokeh.embed import components, json_item
import math
import pandas as pd
import json
from bokeh.plotting import figure
from bokeh.models import HoverTool
from bokeh.embed import json_item
from bokeh.models import LinearAxis

# Chromosome data and visualization functions
ALL_CHROMOSOMES = [
    {"chr": "1",  "length": 248956422, "centromere": 125000000},
    {"chr": "2",  "length": 242193529, "centromere": 93300000},
    {"chr": "3",  "length": 198295559, "centromere": 91000000},
    {"chr": "4",  "length": 190214555, "centromere": 50000000},
    {"chr": "5",  "length": 181538259, "centromere": 48800000},
    {"chr": "6",  "length": 170805979, "centromere": 60500000},
    {"chr": "7",  "length": 159345973, "centromere": 60100000},
    {"chr": "8",  "length": 145138636, "centromere": 45200000},
    {"chr": "9",  "length": 138394717, "centromere": 43000000},
    {"chr": "10", "length": 133797422, "centromere": 39800000},
    {"chr": "11", "length": 135086622, "centromere": 53400000},
    {"chr": "12", "length": 133275309, "centromere": 35500000},
    {"chr": "13", "length": 114364328, "centromere": 17500000},
    {"chr": "14", "length": 107043718, "centromere": 17200000},
    {"chr": "15", "length": 101991189, "centromere": 19000000},
    {"chr": "16", "length": 90338345,  "centromere": 36800000},
    {"chr": "17", "length": 83257441,  "centromere": 25100000},
    {"chr": "18", "length": 80373285,  "centromere": 18500000},
    {"chr": "19", "length": 58617616,  "centromere": 28600000},
    {"chr": "20", "length": 64444167,  "centromere": 27500000},
    {"chr": "21", "length": 46709983,  "centromere": 13200000},
    {"chr": "22", "length": 50818468,  "centromere": 14700000},
    {"chr": "X",  "length": 156040895, "centromere": 60000000},
    {"chr": "Y",  "length": 57227415,  "centromere": 11000000},
]

# Visualization parameters
SCALE = 1e6
CHROM_FULL_WIDTH = 0.4
CHROM_WAIST_WIDTH = 0.1
WAIST_REGION_MB = 2e6
ARC_STEPS = 10
BODY_STEPS = 10
BOTTOM_LABEL_OFFSET = -5



def _normalise_gender(g):
    g = (g or "").strip().upper()
    return "F" if g == "F" else "M"          # default to "M"

def _detect_mode(df, requested):
    """If user did not request a mode, detect from dataframe columns."""
    if requested:
        return requested.lower()
    cols = {c.upper() for c in df.columns}
    # look for the uppercase names
    if "CN_PRE" in cols and "CN_POST" in cols:
        return "differential"
    return "single"





def build_chrom_polygon_capsule(x_center, total_len, centromere_pos):
    """Returns (xs, ys) lists describing a polygon for one chromosome"""
    # Convert to plot units
    totalY = total_len / SCALE
    centY = centromere_pos / SCALE
    
    # The half-circle radius for top/bottom
    r = CHROM_FULL_WIDTH / 2.0
    waist_r = CHROM_WAIST_WIDTH / 2.0
    waist_size = WAIST_REGION_MB / SCALE
    cent_start = max(r, centY - waist_size/2)
    cent_end = min(totalY - r, centY + waist_size/2)

    left_x, left_y = [], []

    # Bottom arc
    for i in range(ARC_STEPS+1):
        yv = r * i / ARC_STEPS
        xoff_sq = r**2 - (r - yv)**2
        xoff = math.sqrt(max(xoff_sq, 0))  # Use math.sqrt instead of np.sqrt
        left_x.append(x_center - xoff)
        left_y.append(yv)

    # Helper function to replace np.linspace
    def linspace(start, stop, num):
        return [start + (stop-start)*i/(num-1) for i in range(num)]

    # Wide region (r..cent_start)
    if cent_start > r:
        for yv in linspace(r, cent_start, BODY_STEPS+1):
            left_x.append(x_center - r)
            left_y.append(yv)

    # Narrow region (cent_start..cent_end)
    if cent_end > cent_start:
        for yv in linspace(cent_start, cent_end, BODY_STEPS+1):
            left_x.append(x_center - waist_r)
            left_y.append(yv)

    # Wide region (cent_end.. totalY - r)
    if (totalY - r) > cent_end:
        for yv in linspace(cent_end, totalY - r, BODY_STEPS+1):
            left_x.append(x_center - r)
            left_y.append(yv)

    # Top arc
    for i in range(ARC_STEPS+1):
        yv = (totalY - r) + r * i / ARC_STEPS
        diff = yv - (totalY - r)
        xoff_sq = r**2 - diff**2
        xoff = math.sqrt(max(xoff_sq, 0))
        left_x.append(x_center - xoff)
        left_y.append(yv)

    # Create right side by mirroring left side
    right_x = [2*x_center - x for x in left_x[::-1]]
    right_y = left_y[::-1]

    return left_x + right_x, left_y + right_y

def get_chromosome_data_from_available(available_chromosomes):
    """Get chromosome data based on available_chromosomes list"""
    # Map available chromosomes to our reference data
    chroms = []
    for c in ALL_CHROMOSOMES:
        if c["chr"] in available_chromosomes:
            chroms.append(c)
    
    # Maintain the original order from available_chromosomes
    return sorted(chroms, key=lambda x: available_chromosomes.index(x["chr"]))

def build_all_chromosomes(available_chromosomes):
    """Build coordinates using available_chromosomes order"""
    chroms_sorted = get_chromosome_data_from_available(available_chromosomes)
    
    all_xs = []
    all_ys = []
    labels = []
    label_xs = []
    label_ys = []

    for i, c in enumerate(chroms_sorted):
        x_center = i * 1.5
        xs, ys = build_chrom_polygon_capsule(x_center, c["length"], c["centromere"])
        all_xs.append(xs)
        all_ys.append(ys)
        labels.append(c["chr"])
        label_xs.append(x_center)
        label_ys.append(BOTTOM_LABEL_OFFSET)

    return all_xs, all_ys, labels, label_xs, label_ys

def generate_karyotype_plot(
    summary_df,
    sample_id: str,
    gender: str = "M",
    reference_genome: str = "GRCh37",
    mode: str | None = None,
    available_chromosomes: list[str] | None = None,
):

    # ---------- helper --------------------------------------------------
    def _wrap_error(msg: str) -> str:
        return json.dumps({"error": msg})

    # ---------- handle empty data ---------------------------------------
    # Don't exit early - generate empty plot with message instead
    is_empty_data = summary_df is None or summary_df.empty
    

    try:
        # ----------------------------------------------------------------
        # 1. sanity checks and settings
        # ----------------------------------------------------------------
        if reference_genome not in {"GRCh37", "GRCh38"}:
            raise ValueError(f"Unsupported reference genome: {reference_genome}")

        # Handle mode detection even with empty data
        if not is_empty_data:
            mode = _detect_mode(summary_df, (mode or "").lower())
        else:
            mode = (mode or "single").lower()
        
        gender = _normalise_gender(gender)

        if mode not in {"single", "differential"}:
            raise ValueError(f"Unsupported mode: {mode!r}")

        plot_width = 1600  
        # Reduce height for empty plots to avoid excessive whitespace
        plot_height = 600 if is_empty_data else 900
        title       = (
            f"Differential Karyotype – {sample_id} (Gender: {gender})"
            if mode == "differential"
            else f"Karyotype Overview – {sample_id} (Gender: {gender})"
        )
        if not available_chromosomes:
            available_chromosomes = [c["chr"] for c in ALL_CHROMOSOMES]
            print("Using chromosomes:", available_chromosomes)
        

        # ----------------------------------------------------------------
        # 2. base figure
        # ----------------------------------------------------------------
        # Calculate x-range first
        num_chromosomes = len(available_chromosomes)
        x_range_end = num_chromosomes * 1.5 + 0.5

        p = figure(
            width=plot_width,
            height=plot_height,
            sizing_mode="stretch_width" if is_empty_data else "scale_width",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="above",
            x_axis_label="Chromosome",
            y_axis_label="Position (Mb) ▴",
            title=title,
            output_backend="webgl",
            x_range=Range1d(start=-1, end=x_range_end),  # Explicit range
        )
        p.min_border_left = 40
        p.min_border_right = 40  # Reduced from 120
        p.min_border_top = 30
        p.min_border_bottom = 50

        # ----------------------------------------------------------------
        # 3. hover + chromosome silhouettes
        # ----------------------------------------------------------------
        hover = HoverTool(
            tooltips=[
                ("Event", "@label"),
                ("Position", "@start{0.00} – @end{0.00} Mb"),
                ("Size", "@length_mb{0.00} Mb"),
                ("P‑value", "@p_value"),
            ],
            renderers=[],
            muted_policy="ignore",
        )
        if mode == "differential":
            hover.tooltips.insert(3, ("Change", "@cn_change"))
        p.add_tools(hover)

        all_xs, all_ys, *_ = build_all_chromosomes(available_chromosomes)

        print(f"Chromosome polygons - X: {len(all_xs)}, Y: {len(all_ys)}")
        print(f"First chromosome coords - X: {all_xs[0][:5]}..., Y: {all_ys[0][:5]}...")

        p.patches(
            all_xs,
            all_ys,
            line_color="black",
            fill_color="#f0f0f0",
            hover_fill_color="#f0f0f0",
            hover_line_color="black",
            hover_fill_alpha=1.0,
            line_width=2,  # Explicit line width
            line_alpha=1,  # Ensure lines are visible
            fill_alpha=0.8  # More opaque fill
        )

        # ----------------------------------------------------------------
        # 4. CNV events + styling
        # ----------------------------------------------------------------
        if not is_empty_data:
            event_data = prepare_event_data(summary_df, available_chromosomes, mode)
            add_event_annotations(p, event_data, hover)
        
        style_plot(p, available_chromosomes)
        

        # p.y_range.start = -10
        p.grid.grid_line_alpha = 0.3
        
        top_xaxis = LinearAxis(                       
            axis_label="Chromosome",
            ticker=p.xaxis[0].ticker,                 
            major_label_overrides=p.xaxis[0].major_label_overrides,
        )
        
        top_xaxis.major_label_text_font_size  = "12pt"
        top_xaxis.major_label_text_font_style = "bold"  
        
        p.add_layout(top_xaxis, 'above') 

        # ----------------------------------------------------------------
        # 5. done → JSON
        # ----------------------------------------------------------------
        # Add empty data flag to the JSON response
        result = json_item(p, "karyotype-plot")
        result['is_empty_data'] = is_empty_data
        
        return json.dumps(result)

    except Exception as exc:
        # Always return *valid* JSON – never None
        return _wrap_error(str(exc))
    
    

def prepare_event_data(summary_df, available_chromosomes, mode="single"):
    """Convert CNV data to plot coordinates using available chromosomes"""
    events = []
    print("prepare_event_data: rows in df =", len(summary_df))
    chroms = get_chromosome_data_from_available(available_chromosomes)
    chrom_positions = {c["chr"]: idx*1.5 for idx, c in enumerate(chroms)}
    
    for _, row in summary_df.iterrows():
        try:
            # Handle chromosome parsing with X/Y support
            raw_chrom = str(row['Chromosome']).strip().upper()
            if raw_chrom.startswith('Chromosome'):
                raw_chrom = raw_chrom[3:]
                
            # Convert to string without forcing integer conversion
            chrom = raw_chrom.replace(" ", "")
            
            # Validate chromosome exists in our data
            if chrom not in chrom_positions:
                continue
                
            # Get reference chromosome length
            chrom_data = next(c for c in ALL_CHROMOSOMES if c["chr"] == chrom)
            max_bp = chrom_data["length"]
            max_mb = max_bp/SCALE
            
            # Auto-detect units and convert to bp
            def convert_units(val):
                # Handle Mb input (values < chromosome length in Mb)
                if val <= max_mb: 
                    return val * SCALE
                # Handle bp input (values > max_mb but < max_bp)
                return min(val, max_bp)
            
            start = convert_units(float(row['Start']))
            end = convert_units(float(row['End']))
            
            # Clip to chromosome boundaries
            start = max(0, min(start, max_bp))
            end = max(0, min(end, max_bp))
            
            if start >= end:  # Discard invalid regions
                continue
                
            # Calculate P-value from QS column
    # ---------- P‑value from (Quality)Score ------------------------
            qs_raw = None
            for cand in ("QS", "QualityScore", "QUAL", "Quality_Score", "Quality"):
                if cand in row and pd.notna(row[cand]):
                    qs_raw = row[cand]
                    break

            if qs_raw is not None:
                try:
                    p_value_num = 10 ** (-float(qs_raw) / 10.0)
                    p_value = f"{p_value_num:.4f}".rstrip('0').rstrip('.') if p_value_num >= 0.0001 else f"{p_value_num:.4e}"
                except Exception:
                    p_value_num, p_value = 1.0, "NA"
            else:
                p_value_num, p_value = 1.0, "NA"

            # Add mode-specific data
            if mode == 'differential':
                cn_pre = float(row.get('CN_pre', 2))
                cn_post = float(row.get('CN_post', 2))
                cn_change = f"CN: {cn_pre:g} -> {cn_post:g}"
                
                event_type = 'deletion' if cn_post < cn_pre else 'duplication'
            else:
                cn_change = f"CN: {row.get('CN', 'NA')}"
                event_type = row['Type'].lower()

            events.append({
                "type": event_type,
                "chrom": chrom,
                "start": start / SCALE,
                "end": end / SCALE,
                "x": chrom_positions[chrom],
                "y": (start + end) / (2 * SCALE),
                "size": min(25, 5 + 2*(end - start)/SCALE),  # Cap maximum size at 25
                "label": f"{row['Type']} Chr{chrom}: {start/1e6:.2f}-{end/1e6:.2f} Mb",
                "length_mb": (end - start) / SCALE,
                "p_value": p_value,
                "p_value_num": p_value_num,
                "cn_change": cn_change
            })
            
        except Exception as e:
            print(f"Skipping invalid CNV row: {str(e)}")
            continue

    return events

from bokeh.models import Legend, LegendItem, BooleanFilter, CustomJS, CDSView

def add_event_annotations(p, events, hover):
    """Add CNV markers with working legend + ≥ 1 Mb size filter."""
    if not events:
        return

    # ------------------------------------------------------------------ #
    # 1. ColumnDataSource  (alpha computed once here)
    # ------------------------------------------------------------------ #
    cds_dict = {k: [] for k in (
        'x','y','size','start','end','label','type',
        'length_mb','p_value','p_value_num','alpha', 'cn_change'  
    )}

    for ev in events:
        p_val = ev['p_value_num']
        ev['alpha'] = 1.0 if p_val <= 0.05 else max(1/(1+(p_val-0.05)*20)**4, 0.1)
        for k in cds_dict:
            cds_dict[k].append(ev[k])

    source = ColumnDataSource(cds_dict)

    # ------------------------------------------------------------------ #
    # 2. real data renderers (unchanged)
    # ------------------------------------------------------------------ #
    del_scatter = p.scatter('x','y', size='size', alpha='alpha',
                            color="#e41a1c", source=source,
                            view=CDSView(filter=GroupFilter(column_name='type',
                                                            group='deletion')),
                            name="del_scatter")

    dup_scatter = p.scatter('x','y', size='size', alpha='alpha',
                            color="#377eb8", source=source,
                            view=CDSView(filter=GroupFilter(column_name='type',
                                                            group='duplication')),
                            name="dup_scatter")

    # ------------------------------------------------------------------ #
    # 3. *new* fixed‑opacity glyphs used only for the legend icons
    # ------------------------------------------------------------------ #
    import math                                      # ← add once at top of file
    nan_pt = {'x':[math.nan], 'y':[math.nan]}        # invisible on canvas

    dup_sym_src = ColumnDataSource(nan_pt)
    del_sym_src = ColumnDataSource(nan_pt)

    dup_sym = p.scatter('x', 'y', size=10, color="#377eb8", alpha=1,
                        source=dup_sym_src, name="dup_sym")
    del_sym = p.scatter('x', 'y', size=10, color="#e41a1c", alpha=1,
                        source=del_sym_src, name="del_sym")

    # ------------------------------------------------------------------ #
    # 4. glyph that drives the ≥ 1 Mb filter (invisible on canvas)
    # ------------------------------------------------------------------ #
    size_filter = p.line([], [], line_width=0, alpha=0, visible=False,
                         name="size_filter")
    # ------------------------------------------------------------------ #
    # 4. Hover shows only real glyphs
    # ------------------------------------------------------------------ #
    hover.renderers = [del_scatter, dup_scatter]

    # ------------------------------------------------------------------ #
    # 5. Callback – rebuild the CDS view each time
    # ------------------------------------------------------------------ #
    cb = CustomJS(args=dict(src=source,
                            del_scatter=del_scatter,
                            dup_scatter=dup_scatter,
                            size_filter=size_filter,
                            original=cds_dict), code="""
        const show_del  = del_scatter.visible;
        const show_dup  = dup_scatter.visible;
        const large_only = size_filter.visible;      // true → ≥1 Mb

        const keep = {x:[],y:[],size:[],start:[],end:[],label:[],type:[],
                      length_mb:[],p_value:[],p_value_num:[],alpha:[], cn_change:[]};

        for (let i = 0; i < original.type.length; i++) {
            const is_dup = original.type[i] === 'duplication';
            const is_del = original.type[i] === 'deletion';
            const is_large = original.length_mb[i] >= 1;

            if ((is_dup && show_dup) || (is_del && show_del)) {
                if (!large_only || is_large) {
                    for (const k in keep) keep[k].push(original[k][i]);
                }
            }
        }
        // replace data in place
        for (const k in keep) src.data[k] = keep[k];
        src.change.emit();
    """)

    del_scatter.js_on_change('visible', cb)
    dup_scatter.js_on_change('visible', cb)
    size_filter.js_on_change('visible', cb)

    # ------------------------------------------------------------------ #
    # 6. Legend – *put the symbol renderer first* in each list
    # ------------------------------------------------------------------ #
    legend = Legend(
        items=[
            LegendItem(label="Duplications", renderers=[dup_sym, dup_scatter]),
            LegendItem(label="Deletions",    renderers=[del_sym, del_scatter]),
            LegendItem(label="≥1 Mb",        renderers=[size_filter]),
        ],
        click_policy="hide",
        location="center",
        orientation="vertical",
        glyph_height=20,
        glyph_width=20,
    )
    p.add_layout(legend, 'right')
    

def style_plot(p, available_chromosomes):
    """Apply styling based on available chromosomes"""
    # Adjust x-axis labels to match available chromosomes
    p.xaxis.ticker = [i*1.5 for i in range(len(available_chromosomes))]
    p.xaxis.major_label_overrides = {
        i*1.5: chrom for i, chrom in enumerate(available_chromosomes)
    }
    
    # Make X-axis labels more prominent
    p.xaxis.major_label_text_font_size = "12pt"
    p.xaxis.major_label_text_font_style = "bold"
    
    # Ensure X-axis is visible and properly styled
    p.xaxis.axis_line_width = 1
    p.xaxis.axis_line_color = "black"
    
    p.yaxis.formatter.use_scientific = False
    p.grid.grid_line_alpha = 0.3
    p.title.text_font_size = "16pt"
    
    # Determine upper limit (top of plot) and add a small white‑space padding
    chroms_sorted = get_chromosome_data_from_available(available_chromosomes)
    max_y = max(c["length"] for c in ALL_CHROMOSOMES
                if c["chr"] in available_chromosomes) / 1e6   # Mb
    bottom_padding = -5                                        # Mb of white space under chr 1 start
    p.y_range = Range1d(max_y, bottom_padding)
    
    p.yaxis.axis_label = "Position (Mb) ▴"  # Add upward arrow indicator
    
    print(f"Y-axis range: {p.y_range.start} - {p.y_range.end}")
    print(f"X-axis range: {p.x_range.start} - {p.x_range.end}")
    