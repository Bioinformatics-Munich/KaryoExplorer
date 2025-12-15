from __future__ import annotations
"""
Utilities for producing interactive chromosome‑level Bokeh plots.

Exports:
    generate_chromosome_plot()
    generate_combined_plots()

Functions return a JSON string generated via ``bokeh.embed.json_item``
which you can embed directly in any Bokeh‑JS front‑end.  The JSON bundle
contains one of the following layouts:

* **generate_chromosome_plot** – a single 3‑panel view:
    - LRR scatter   (± ROH / CN shading)
    - BAF scatter   (± ROH / CN shading)
    - Continuous CNV profile (CN 2 baseline + del/dup segments)

* **generate_combined_plots** – a dashboard of *nine* linked panels
  arranged as                         

      +------------------+------------------+
      |    PRE (3)       |    POST (3)      |
      +------------------+------------------+
      |        DIFF (3 – full width)        |
      +-------------------------------------+

  Pan/zoom in any pane propagates to all others because their ``x_range``
  objects are shared.
"""

import json
import logging
import numpy as np
from typing import Union

import pandas as pd
from bokeh.embed import json_item
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from bokeh.layouts import row, column
from bokeh.models  import Div, Spacer

__all__ = ["generate_chromosome_plot", "generate_combined_plots"]


# -------------------------------------------------------------------
# Colour palette (colour‑blind friendly)
# -------------------------------------------------------------------
CLR_LRR     = "#1f77b4"   # blue
CLR_BAF     = "#2ca02c"   # green
CLR_BASE    = "#e74c3c"   # red baseline CN = 2
CLR_DUP     = "#0eff4a"   # orange (duplications)
CLR_DEL     = "#9467bd"   # purple (deletions)
CLR_ROH     = "#90EE90"   # light green (ROH regions)
CLR_CN      = "#c4a0ff"   # soft lavender (CN regions)
CLR_OVERLAP = "#ff6961"   # light red (overlaps)
CLR_SEGMENT = "#ff7f0e"   # orange for segments

# =========================================================================
# INTERNAL: build a 3‑panel chromosome view **and return the live Bokeh grid**
# =========================================================================

def _build_chromosome_grid(
    baf_lrr_data: pd.DataFrame,
    cnv_data: pd.DataFrame,
    chromosome: Union[str, int],
    sample_id: str,
    roh_bed: pd.DataFrame | None = None,
    union_bed: pd.DataFrame | None = None,
    cn_bed: pd.DataFrame | None = None,
    cn_summary_data: pd.DataFrame | None = None,
    *,
    x_range_shared: Range1d | None = None,
    panel_width: int = 1000,
):
    """Return a *live* Bokeh ``gridplot`` containing the 3 panes.

    This function now implements cnLoH-specific filtering:
    - CN regions (lavender): Only CN = 1 (copy-loss LoH)
    - Union regions (light red): Only CN = 2 + ROH overlaps (cnLoH candidates)
    - ROH regions (light green): All ROH regions
    """
    try:
        # ---- slice all inputs ------------------------------------------------
        chr_str = str(chromosome)
        chr_baf = baf_lrr_data[baf_lrr_data["Chromosome"] == chr_str]
        chr_cnv = cnv_data[cnv_data["Chromosome"] == chr_str]
        chr_roh = (
            roh_bed[roh_bed["Chromosome"] == chr_str] if roh_bed is not None else pd.DataFrame()
        )
        
        # ===== cnLoH-SPECIFIC FILTERING IMPLEMENTATION =====
        logging.info(f"=== cnLoH Filtering for Chr {chr_str} ===")
        
        # Step 1: Filter CN regions to show ONLY CN = 1 (copy-loss LoH)
        chr_cn_filtered = pd.DataFrame()
        if cn_bed is not None and not cn_bed.empty:
            chr_cn_raw = cn_bed[cn_bed["Chromosome"] == chr_str]
            logging.info(f"Raw CN regions for chr {chr_str}: {len(chr_cn_raw)}")
            
            # Filter CN regions based on actual copy number from summary data
            if cn_summary_data is not None and not cn_summary_data.empty:
                chr_segments = cn_summary_data[cn_summary_data["Chromosome"] == chr_str]
                
                # Only keep CN regions that correspond to CN = 1 segments (copy-loss LoH)
                cn_copyloss = []
                for _, cn_region in chr_cn_raw.iterrows():
                    cn_start, cn_end = cn_region["Start"], cn_region["End"]
                    
                    # Find overlapping segments with CN = 1 (copy-loss LoH)
                    for _, segment in chr_segments.iterrows():
                        seg_start, seg_end = segment["Start"], segment["End"]
                        cn_value = segment["CopyNumber"]
                        
                        # Check for overlap and CN = 1 (copy-loss LoH only)
                        if (cn_start < seg_end and cn_end > seg_start and cn_value == 1):
                            # Calculate overlap region
                            overlap_start = max(cn_start, seg_start)
                            overlap_end = min(cn_end, seg_end)
                            
                            if overlap_start < overlap_end:
                                cn_copyloss.append({
                                    "Chromosome": chr_str,
                                    "Start": overlap_start,
                                    "End": overlap_end,
                                    "Length": overlap_end - overlap_start
                                })
                
                chr_cn_filtered = pd.DataFrame(cn_copyloss)
                logging.info(f"Filtered CN regions (CN = 1 only, copy-loss LoH): {len(chr_cn_filtered)}")
            else:
                # Fallback: use original CN regions if no summary data
                chr_cn_filtered = chr_cn_raw
                logging.warning(f"No summary data available, using all CN regions: {len(chr_cn_filtered)}")
        
        # Step 2: Calculate CN = 2 + ROH overlaps for cnLoH candidates
        chr_cnloh_overlaps = pd.DataFrame()
        if (cn_summary_data is not None and not cn_summary_data.empty and 
            not chr_roh.empty):
            
            chr_segments = cn_summary_data[cn_summary_data["Chromosome"] == chr_str]
            cn2_segments = chr_segments[chr_segments["CopyNumber"] == 2]
            
            logging.info(f"CN=2 segments for cnLoH detection: {len(cn2_segments)}")
            logging.info(f"ROH regions for overlap: {len(chr_roh)}")
            
            # Calculate CN=2 + ROH overlaps
            cnloh_candidates = []
            for _, cn2_seg in cn2_segments.iterrows():
                cn2_start, cn2_end = cn2_seg["Start"], cn2_seg["End"]
                
                for _, roh_region in chr_roh.iterrows():
                    roh_start, roh_end = roh_region["Start"], roh_region["End"]
                    
                    # Calculate overlap
                    overlap_start = max(cn2_start, roh_start)
                    overlap_end = min(cn2_end, roh_end)
                    
                    if overlap_start < overlap_end:
                        cnloh_candidates.append({
                            "Chromosome": chr_str,
                            "Start": overlap_start,
                            "End": overlap_end,
                            "Length": overlap_end - overlap_start
                        })
            
            chr_cnloh_overlaps = pd.DataFrame(cnloh_candidates)
            logging.info(f"cnLoH candidate overlaps (CN=2+ROH): {len(chr_cnloh_overlaps)}")
        
        # Use the filtered/calculated regions instead of original union_bed
        chr_uni = chr_cnloh_overlaps
        chr_cn = chr_cn_filtered
        
        # Log final region counts for visualization
        logging.info(f"Final visualization regions for chr {chr_str}:")
        logging.info(f"  - ROH regions (light green): {len(chr_roh)}")
        logging.info(f"  - Copy-loss LoH regions (soft lavender): {len(chr_cn)}")
        logging.info(f"  - cnLoH candidates (light red): {len(chr_uni)}")
        
        # Filter segment summary data for this chromosome if available
        chr_segments = pd.DataFrame()
        if cn_summary_data is not None:
            # Filter segments for this chromosome - expecting columns:
            # Region,Chromosome,Start,End,CopyNumber,Quality,nSites,nHETs
            chr_segments = cn_summary_data[cn_summary_data["Chromosome"] == chr_str].copy()
            logging.info(f"Found {len(chr_segments)} segments in summary data for chromosome {chr_str}")

        if chr_baf.empty:
            raise ValueError(f"No BAF/LRR data for chr {chr_str}")

        # ---- choose the right CN column --------------------------------------
        if "CopyNumber" in chr_cnv.columns:
            cn_col = "CopyNumber"
        elif "CN_post" in chr_cnv.columns:
            cn_col = "CN_post"
        elif "CN" in chr_cnv.columns:
            cn_col = "CN"
        else:
            raise ValueError("No recognized CN column in CNV data")

        # ---- shared ColumnDataSource for scatter points ----------------------
        src_pts = ColumnDataSource(
            {
                "pos": chr_baf["Position"],
                "baf": chr_baf["BAF"],
                "lrr": chr_baf["LRR"],
            }
        )

        # ---- Calculate segment statistics or use provided segment data ------
        # Only calculate if no segment data was provided
        segment_stats = {}
        
        if len(chr_segments) > 0:
            # Use the provided segment data
            logging.info(f"Using {len(chr_segments)} segments from provided summary data")
            
            for _, segment in chr_segments.iterrows():
                start, end = segment["Start"], segment["End"]
                
                # Calculate segment statistics from points within the segment
                segment_data = chr_baf[(chr_baf["Position"] >= start) & (chr_baf["Position"] <= end)]
                
                if not segment_data.empty:
                    lrr_values = segment_data["LRR"]
                    baf_values = segment_data["BAF"]
                    
                    segment_stats[f"{start}-{end}"] = {
                        "start": start,
                        "end": end,
                        "lrr_mean": np.mean(lrr_values) if len(lrr_values) > 0 else 0,
                        "lrr_median": np.median(lrr_values) if len(lrr_values) > 0 else 0,
                        "lrr_stddev": np.std(lrr_values) if len(lrr_values) > 1 else 0,
                        "cn": segment["CopyNumber"],
                        "n_sites": segment["nSites"],
                        "n_hets": segment["nHETs"],
                        "quality": segment["Quality"]
                    }
        else:
            # Calculate from points if no segment data provided (original method)
            logging.info(f"Calculating segment statistics from points for chromosome {chr_str}")
            
            for _, segment in chr_cnv.iterrows():
                start, end = segment["Start"], segment["End"]
                
                # Filter data points within this segment
                segment_data = chr_baf[(chr_baf["Position"] >= start) & (chr_baf["Position"] <= end)]
                
                if not segment_data.empty:
                    lrr_values = segment_data["LRR"]
                    baf_values = segment_data["BAF"]
                    
                    segment_stats[f"{start}-{end}"] = {
                        "start": start,
                        "end": end,
                        "lrr_mean": np.mean(lrr_values),
                        "lrr_median": np.median(lrr_values),
                        "lrr_stddev": np.std(lrr_values) if len(lrr_values) > 1 else 0,
                        "cn": segment[cn_col],
                        "n_sites": segment.get("nSites", "NA"),
                        "n_hets": segment.get("nHETs", "NA"),
                        "quality": segment.get("Quality", "NA")
                    }

        # Debug segment stats calculation
        if len(segment_stats) > 0:
            logging.info(f"Final segment count: {len(segment_stats)} segments for chromosome {chr_str}")
            for key, stat in list(segment_stats.items())[:3]:  # Log first 3 for debugging
                logging.info(f"Segment {key}: LRR mean={stat['lrr_mean']:.3f}, CN={stat['cn']}")
        else:
            logging.warning(f"No segment statistics calculated for chromosome {chr_str}")

        # ---- common figure kwargs -------------------------------------------
        common = dict(
            width=panel_width,
            height=250,
            tools="pan,wheel_zoom,box_zoom,reset,save",
            toolbar_location="right",
            x_axis_label=f"Coordinate (chr {chr_str})",
            output_backend="canvas",
        )

        # helper to avoid double quotes in titles
        def _s(x: str) -> str:
            return x.replace("\"", "'").replace("\n", " ")

        sid = _s(sample_id)

        # ---------------------------------------------------------------------
        # LRR panel
        # ---------------------------------------------------------------------
        fig_kw = common.copy()
        if x_range_shared is not None:          # <- guard against None
            fig_kw["x_range"] = x_range_shared

        p_lrr = figure(
            title=f"LRR – {sid} – Chr {chr_str}",
            y_axis_label="LRR",
            **fig_kw,                           # <- use the guarded kwargs
        )

        lmn, lmx = float(chr_baf["LRR"].min()), float(chr_baf["LRR"].max())
        pad = (lmx - lmn) * 0.05 if lmx > lmn else 0.1
        p_lrr.y_range = Range1d(lmn - pad, lmx + pad)

        # Updated legend labels for cnLoH visualization
        if not chr_roh.empty:
            src_roh = ColumnDataSource(chr_roh)
            p_lrr.quad(
                left="Start",
                right="End",
                bottom=lmn - pad,
                top=lmx + pad,
                source=src_roh,
                fill_color=CLR_ROH,
                fill_alpha=0.3,
                legend_label="ROH regions",
                muted_alpha=0.1,
            )
        if not chr_cn.empty:
            src_cn = ColumnDataSource(chr_cn)
            p_lrr.quad(
                left="Start",
                right="End",
                bottom=lmn - pad,
                top=lmx + pad,
                source=src_cn,
                fill_color=CLR_CN,
                fill_alpha=0.3,
                legend_label="Copy-loss LoH",
                muted_alpha=0.1,
            )
        if not chr_uni.empty:
            src_uni = ColumnDataSource(chr_uni)
            p_lrr.quad(
                left="Start",
                right="End",
                bottom=lmn - pad,
                top=lmx + pad,
                source=src_uni,
                fill_color=CLR_OVERLAP,
                fill_alpha=0.5,
                legend_label="cnLoH candidates (CN=2+ROH)",
                muted_alpha=0.1,
            )

        r_lrr = p_lrr.scatter(
            "pos",
            "lrr",
            source=src_pts,
            color=CLR_LRR,
            size=2,
            alpha=0.6,
            legend_label="LRR",
            muted_alpha=0.1,
        )
        p_lrr.add_tools(
            HoverTool(
                tooltips=[("Pos", "@pos{0,0}"), ("LRR", "@lrr{0.000}")],
                renderers=[r_lrr],
            )
        )

        # ------------------------------------------------------------------
        # Segments – draw all at once with a single renderer so we get
        #           one legend entry and simpler hover handling
        # ------------------------------------------------------------------
        start_list = []
        end_list = []
        mean_lrr_list = []
        median_lrr_list = []
        stddev_lrr_list = []
        cn_list = []
        n_sites_list = []
        n_hets_list = []
        quality_list = []
        for key, stats in segment_stats.items():
            start, end = stats["start"], stats["end"]
            mean_lrr = stats["lrr_mean"]
            # Ensure mean_lrr is within visible range
            if mean_lrr < lmn - pad:
                mean_lrr = lmn - pad + 0.01
                logging.warning(f"Adjusted segment LRR mean to be in visible range: {mean_lrr}")
            elif mean_lrr > lmx + pad:
                mean_lrr = lmx + pad - 0.01
                logging.warning(f"Adjusted segment LRR mean to be in visible range: {mean_lrr}")
            start_list.append(start)
            end_list.append(end)
            mean_lrr_list.append(mean_lrr)
            median_lrr_list.append(f"{stats['lrr_median']:.3f}")
            stddev_lrr_list.append(f"{stats['lrr_stddev']:.3f}")
            cn_list.append(str(stats['cn']))
            n_sites_list.append(str(stats['n_sites']))
            n_hets_list.append(str(stats['n_hets']))
            quality_list.append(str(stats['quality']))

        if start_list:
            segment_source = ColumnDataSource(
                data=dict(
                    xs=[[s, e] for s, e in zip(start_list, end_list)],
                    ys=[[m, m] for m in mean_lrr_list],
                    start=start_list,
                    end=end_list,
                    mean_lrr=[f"{m:.3f}" for m in mean_lrr_list],
                    median_lrr=median_lrr_list,
                    stddev_lrr=stddev_lrr_list,
                    cn=cn_list,
                    n_sites=n_sites_list,
                    n_hets=n_hets_list,
                    quality=quality_list,
                )
            )

            r_segments = p_lrr.multi_line(
                xs="xs",
                ys="ys",
                source=segment_source,
                line_color=CLR_SEGMENT,
                line_width=5,
                alpha=1.0,
                legend_label="Segments",
                muted_alpha=0.0,
            )

            p_lrr.add_tools(
                HoverTool(
                    tooltips=[
                        ("Segment", "@start{0,0}-@end{0,0}"),
                        ("Copy Number", "@cn"),
                        ("Mean LRR", "@mean_lrr"),
                        ("Median LRR", "@median_lrr"),
                        ("StdDev LRR", "@stddev_lrr"),
                        ("Quality", "@quality"),
                        ("Sites", "@n_sites"),
                        ("HETs", "@n_hets"),
                    ],
                    renderers=[r_segments],
                    line_policy="nearest",
                    mode="mouse",
                )
            )

        p_lrr.legend.click_policy = "hide"
        p_lrr.add_layout(p_lrr.legend[0], "right")

        # ---------------------------------------------------------------------
        # BAF panel (shares x‑range with LRR panel)
        # ---------------------------------------------------------------------
        p_baf = figure(
            title=f"BAF – {sid} – Chr {chr_str}",
            y_axis_label="BAF",
            x_range=p_lrr.x_range,
            **common,
        )
        p_baf.y_range = Range1d(0, 1)

        # Apply same filtering to BAF panel with updated legend labels
        if not chr_roh.empty:
            p_baf.quad(
                left="Start",
                right="End",
                bottom=0,
                top=1,
                source=src_roh,
                fill_color=CLR_ROH,
                fill_alpha=0.3,
                legend_label="ROH regions",
                muted_alpha=0.1,
            )
        if not chr_cn.empty:
            p_baf.quad(
                left="Start",
                right="End",
                bottom=0,
                top=1,
                source=src_cn,
                fill_color=CLR_CN,
                fill_alpha=0.3,
                legend_label="Copy-loss LoH",
                muted_alpha=0.1,
            )
        if not chr_uni.empty:
            p_baf.quad(
                left="Start",
                right="End",
                bottom=0,
                top=1,
                source=src_uni,
                fill_color=CLR_OVERLAP,
                fill_alpha=0.5,
                legend_label="cnLoH candidates (CN=2+ROH)",
                muted_alpha=0.1,
            )

        r_baf = p_baf.scatter(
            "pos",
            "baf",
            source=src_pts,
            color=CLR_BAF,
            size=2,
            alpha=0.6,
            legend_label="BAF",
            muted_alpha=0.1,
        )
        p_baf.add_tools(
            HoverTool(
                tooltips=[("Pos", "@pos{0,0}"), ("BAF", "@baf{0.000}")],
                renderers=[r_baf],
            )
        )

        # Skip segment visualization for BAF plots
        segment_renderers_baf = []

        p_baf.legend.click_policy = "hide"
        p_baf.add_layout(p_baf.legend[0], "right")

        # ---------------------------------------------------------------------
        # CNV panel (shares x‑range with LRR panel)
        # ---------------------------------------------------------------------
        p_cnv = figure(
            title=f"CN Profile – {sid} – Chr {chr_str}",
            y_axis_label="Copy Number",
            x_range=p_lrr.x_range,
            **common,
        )
        p_cnv.y_range = Range1d(-0.1, 4.1)
        p_cnv.yaxis.ticker = [0, 1, 2, 3, 4]
        p_cnv.yaxis.major_label_overrides = {i: f"CN{i}" for i in range(5)}

        prev = float(chr_baf["Position"].min())
        seg_r = []
        base_r = []

        for _, row in chr_cnv.sort_values("Start").iterrows():
            start, end = float(row["Start"]), float(row["End"])
            cnv_val = float(row[cn_col])

            if "Type" in row and pd.notna(row["Type"]):
                lbl = str(row["Type"]).title()
            else:
                lbl = "Duplication" if cnv_val > 2 else "Deletion"

            clr = CLR_DUP if "Dup" in lbl else CLR_DEL

            # baseline to start of event
            r0 = p_cnv.line(
                [prev, start],
                [2, 2],
                color=CLR_BASE,
                line_width=2,
                alpha=0.8,
                legend_label="CN=2 baseline",
                muted_alpha=0.1,
            )
            base_r.append(r0)

            # vertical drop/rise
            p_cnv.line(
                [start, start],
                [2, cnv_val],
                color=CLR_BASE,
                line_width=2,
                alpha=0.8,
            )
            # event segment
            r1 = p_cnv.line(
                [start, end],
                [cnv_val, cnv_val],
                color=clr,
                line_width=4,
                alpha=0.9,
                legend_label=lbl,
                muted_alpha=0.1,
            )
            seg_r.append(r1)

            # back to baseline
            p_cnv.line(
                [end, end],
                [cnv_val, 2],
                color=CLR_BASE,
                line_width=2,
                alpha=0.8,
            )
            prev = end

        # tail baseline
        r_last = p_cnv.line(
            [prev, float(chr_baf["Position"].max())],
            [2, 2],
            color=CLR_BASE,
            line_width=2,
            alpha=0.8,
            legend_label="CN=2 baseline",
            muted_alpha=0.1,
        )
        base_r.append(r_last)

        all_r = seg_r + base_r
        p_cnv.add_tools(
            HoverTool(
                tooltips=[("Pos", "$x{0,0}"), ("CN", "$y")],
                renderers=all_r,
                mode="mouse",
            )
        )
        p_cnv.legend.click_policy = "hide"
        p_cnv.add_layout(p_cnv.legend[0], "right")

        # ---------------------------------------------------------------------
        # compose and return grid
        # ---------------------------------------------------------------------
        grid = gridplot(
            [[p_lrr], [p_baf], [p_cnv]],
            sizing_mode="stretch_width",
            toolbar_location="right",
        )
        return grid

    except Exception as exc:
        logging.error("Plot generation failed: %s", exc)
        logging.error("_build_chromosome_grid failed: %s", exc)
        err_json = json.dumps({"error": str(exc)})
        return err_json

 


# =========================================================================
# PUBLIC: 3×3 linked dashboard (pre / post / diff)
# =========================================================================

def generate_combined_plots(
    pre_baf_lrr: pd.DataFrame,      pre_cnv: pd.DataFrame,
    post_baf_lrr: pd.DataFrame,     post_cnv: pd.DataFrame,
    diff_baf_lrr: pd.DataFrame,     diff_cnv: pd.DataFrame,
    chromosome: Union[str, int],
    pre_sample_id: str, post_sample_id: str, pair_id: str,
    pre_roh_bed: pd.DataFrame | None = None,   pre_union_bed: pd.DataFrame | None = None,
    pre_cn_bed:  pd.DataFrame | None = None,
    post_roh_bed: pd.DataFrame | None = None,  post_union_bed: pd.DataFrame | None = None,
    post_cn_bed: pd.DataFrame | None = None,
    diff_roh_bed: pd.DataFrame | None = None,  diff_union_bed: pd.DataFrame | None = None,
    diff_cn_bed:  pd.DataFrame | None = None,
    pre_cn_summary_data: pd.DataFrame | None = None,
    post_cn_summary_data: pd.DataFrame | None = None,
    diff_cn_summary_data: pd.DataFrame | None = None,
) -> str:
    """
    Return a JSON bundle with

        +---------------------+----------------------+
        |   PRE (3 panels)    |   POST (3 panels)    |
        +---------------------+----------------------+
        |        DIFF (3 panels – full width)        |
        +--------------------------------------------+
    """
    try:
        chr_str = str(chromosome)

        # ---------- 1. shared x-range -------------------------------------------------
        pos_min = min(
            pre_baf_lrr.loc[pre_baf_lrr["Chromosome"] == chr_str, "Position"].min(),
            post_baf_lrr.loc[post_baf_lrr["Chromosome"] == chr_str, "Position"].min(),
            diff_baf_lrr.loc[diff_baf_lrr["Chromosome"] == chr_str, "Position"].min(),
        )
        pos_max = max(
            pre_baf_lrr.loc[pre_baf_lrr["Chromosome"] == chr_str, "Position"].max(),
            post_baf_lrr.loc[post_baf_lrr["Chromosome"] == chr_str, "Position"].max(),
            diff_baf_lrr.loc[diff_baf_lrr["Chromosome"] == chr_str, "Position"].max(),
        )
        if pd.isna(pos_min) or pd.isna(pos_max):
            raise ValueError(f"Chromosome {chr_str} has no positions in one of the data sets")
        if pos_min == pos_max:
            pos_min -= 1
            pos_max += 1

        shared_range = Range1d(float(pos_min), float(pos_max))

        # figure widths --------------------------------------------------------
        full_w  = 1000               # DIFF grid (spans the whole row)
        half_w  = full_w // 2        # each of PRE / POST

        # ---------- 3. build the three 3-panel sub-grids ------------------------------
        pre_grid  = _build_chromosome_grid(
            pre_baf_lrr,  pre_cnv,  chromosome,  pre_sample_id,
            pre_roh_bed,  pre_union_bed,  pre_cn_bed,
            cn_summary_data=pre_cn_summary_data,
            x_range_shared = shared_range,
            panel_width    = half_w,
        )

        post_grid = _build_chromosome_grid(
            post_baf_lrr, post_cnv, chromosome, post_sample_id,
            post_roh_bed, post_union_bed, post_cn_bed,
            cn_summary_data=post_cn_summary_data,
            x_range_shared = shared_range,
            panel_width    = half_w,
        )

        diff_grid = _build_chromosome_grid(
            diff_baf_lrr, diff_cnv, chromosome, pair_id,
            diff_roh_bed, diff_union_bed, diff_cn_bed,
            cn_summary_data=diff_cn_summary_data,
            x_range_shared = shared_range,
            panel_width    = full_w,
        )
            
        # ───────── 4. coloured section headers ──────────────────────────────
        hdr_css = (
            "font-family:Inter, sans-serif;"
            "color:#7d3c98; margin:0; text-align:center;"      # ← centred text
        )
        pre_hdr  = Div(text=f"<h3 style='{hdr_css}'>PRE&nbsp;{pre_sample_id}&nbsp;Chr&nbsp;{chr_str}</h3>",
                    width=half_w, height=30)
        post_hdr = Div(text=f"<h3 style='{hdr_css}'>POST&nbsp;{post_sample_id}&nbsp;Chr&nbsp;{chr_str}</h3>",
                    width=half_w, height=30)
        diff_hdr = Div(text=f"<h3 style='{hdr_css}'>DIFFERENTIAL&nbsp;CNV&nbsp;ANALYSIS&nbsp;"
                            f"{pair_id}&nbsp;Chr&nbsp;{chr_str}</h3>",
                    width=full_w, height=30)

        # ───────── 5. assemble dashboard ────────────────────────────────────
        pre_column  = column(pre_hdr, Spacer(height=4), pre_grid,  sizing_mode="stretch_width")
        post_column = column(post_hdr, Spacer(height=4), post_grid, sizing_mode="stretch_width")

        layout = column(
            row(pre_column, post_column, sizing_mode="stretch_width"),  # PRE | POST
            diff_hdr,
            diff_grid,                                                  # DIFF (full width)
            sizing_mode="stretch_width",
        )

        return json.dumps(json_item(layout))

    except Exception as exc:
        logging.error("generate_combined_plots failed: %s", exc)
        return json.dumps({"error": str(exc)})

def generate_chromosome_plot(
    baf_lrr_data: pd.DataFrame,
    cnv_data: pd.DataFrame,
    chromosome: Union[str, int],
    sample_id: str,
    roh_bed: pd.DataFrame | None = None,
    union_bed: pd.DataFrame | None = None,
    cn_bed: pd.DataFrame | None = None,
    cn_summary_data: pd.DataFrame | None = None,
    *,
    _return_grid: bool = False,
) -> str | gridplot:
    """
    Public API — behaves exactly like the original function.
    If ``_return_grid`` is True you get the live Bokeh grid instead of JSON.
    
    Parameters:
    -----------
    baf_lrr_data: DataFrame with BAF and LRR values per position
    cnv_data: DataFrame with CNV segments
    chromosome: Chromosome to plot
    sample_id: Sample identifier
    roh_bed: ROH regions (optional)
    union_bed: Union of ROH and CN regions (optional)
    cn_bed: CN regions (optional)
    cn_summary_data: Segment summary data with statistics (optional)
    _return_grid: Whether to return the grid object instead of JSON
    """
    try:
        grid = _build_chromosome_grid(
            baf_lrr_data,
            cnv_data,
            chromosome,
            sample_id,
            roh_bed,
            union_bed,
            cn_bed,
            cn_summary_data=cn_summary_data,
            x_range_shared=None,
            panel_width=1000,
        )
        if _return_grid:
            return grid
        
        # Handle case where grid is a string (error message) rather than a grid object
        if isinstance(grid, str):
            return grid
            
        # Convert grid to JSON
        return json.dumps(json_item(grid))

    except Exception as exc:
        logging.error("generate_chromosome_plot failed: %s", exc)
        return json.dumps({"error": str(exc)})
