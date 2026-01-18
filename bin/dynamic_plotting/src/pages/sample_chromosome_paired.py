import os
import logging
from pathlib import Path
from typing import Dict, Any
from bokeh.embed import json_item
from src.plots.chromosome_plots import generate_chromosome_plot, generate_combined_plots
from src.tables.table_generator import TableGenerator


class ChromosomePageGeneratorPaired:
    """Generate chromosome pages for paired samples, with a dropdown for Pre/Post."""

    def __init__(self, pair_obj, output_manager):
        self.pair_obj = pair_obj
        self.output_manager = output_manager
        self.table_generator = TableGenerator()

    def _ensure_dict_format(self, table_data):
        """Ensure table data is in dictionary format with required keys"""
        if isinstance(table_data, dict) and 'significant' in table_data and 'nonsignificant' in table_data:
            # Handle cases where the tables contain raw strings with newlines
            for key in ['significant', 'nonsignificant']:
                if isinstance(table_data[key], str) and '\n' in table_data[key]:
                    # Clean the string and wrap it in proper HTML
                    content = table_data[key].strip()
                    if "No matching CNV calls found" in content or len(content) < 5:
                        table_data[key] = f"""<div class="info-box_empty">
                            <i class="fas fa-info-circle"></i>
                            No CNV calls found
                        </div>"""
                    elif "Chromosome" in content and "Start" in content:
                        # This appears to be table content, format it properly
                        rows = content.strip().split('\n')
                        if len(rows) > 1:
                            header = rows[0].split('\t')
                            class_name = "detailed-cnv-table"
                            if key == 'significant':
                                class_name += " significant-cnvs"
                            else:
                                class_name += " nonsignificant-cnvs"
                                
                            html_table = f"""<table class="{class_name}">
                                <thead>
                                    <tr>
                                        {"".join([f'<th>{col.strip()}</th>' for col in header])}
                                    </tr>
                                </thead>
                                <tbody>"""
                            
                            for i in range(1, len(rows)):
                                if not rows[i].strip():
                                    continue
                                cols = rows[i].split('\t')
                                html_table += "<tr>" + "".join([f'<td>{col.strip()}</td>' for col in cols]) + "</tr>"
                            
                            html_table += """</tbody></table>"""
                            table_data[key] = html_table
            
            return table_data
        
        # If it's a string or any other format, wrap it in a dict
        placeholder = """<div class="info-box_empty">
            <i class="fas fa-info-circle"></i>
            No data available
        </div>"""
        
        return {
            'significant': table_data if isinstance(table_data, str) else placeholder,
            'nonsignificant': placeholder
        }

    def generate_chromosome_page(self, chromosome: str) -> str:
        
        
        logging.info(f"Called for sample={self.pair_obj.pre.sample_id}, chr={chromosome}")
        for name, obj in [
            ("baf_lrr_data", self.pair_obj.pre.baf_lrr_data),
            ("cnv_data",    self.pair_obj.pre.cnv_detection_filtered),
            ("roh_bed",     self.pair_obj.pre.roh_bed),
            ("union_bed",   self.pair_obj.pre.union_bed),
            ("cn_bed",      self.pair_obj.pre.cn_bed),
        ]:
            if obj is None:
                logging.info(f"  → {name} is None")
            elif hasattr(obj, "columns"):
                logging.info(f"  → {name}.columns = {list(obj.columns)} (n={len(obj)})")
            else:
                logging.info(f"  → {name} is {type(obj)}")
            
            
        try:
            # Filter CNV data for current chromosome
            chrom_cnvs = self.pair_obj.cnv_detection_filtered[
                self.pair_obj.cnv_detection_filtered['Chromosome'] == chromosome
            ]
            chrom_table = self.table_generator.generate_detailed_cnv_table(chrom_cnvs)
            chrom_table = self._ensure_dict_format(chrom_table)

            # Generate pre/post tables for the specific chromosome
            pre_chrom_cnvs = self.pair_obj.pre.cn_summary_data[
                self.pair_obj.pre.cn_summary_data['Chromosome'] == chromosome
            ]
            post_chrom_cnvs = self.pair_obj.post.cn_summary_data[
                self.pair_obj.post.cn_summary_data['Chromosome'] == chromosome
            ]
            
            pre_chrom_table = self.table_generator.generate_detailed_cnv_table_single(pre_chrom_cnvs)
            pre_chrom_table = self._ensure_dict_format(pre_chrom_table)
            
            post_chrom_table = self.table_generator.generate_detailed_cnv_table_single(post_chrom_cnvs)
            post_chrom_table = self._ensure_dict_format(post_chrom_table)

            # # 1) Differential (paired) plot is always visible
            # diff_json = generate_chromosome_plot(
            #     self.pair_obj.post.baf_lrr_data,
            #     self.pair_obj.cnv_detection_filtered,
            #     chromosome,
            #     self.pair_obj.pair_id,
            #     self.pair_obj.roh_bed,
            #     self.pair_obj.union_bed,
            #     self.pair_obj.cn_bed,
            #     cn_summary_data=self.pair_obj.cn_summary_data
            # )
            
            # # 2) Pre and Post individual plots live in the dropdown
            # pre_json = generate_chromosome_plot(
            #     self.pair_obj.pre.baf_lrr_data,
            #     self.pair_obj.pre.cnv_detection_filtered,
            #     chromosome,
            #     self.pair_obj.pre.sample_id,
            #     self.pair_obj.pre.roh_bed,
            #     self.pair_obj.pre.union_bed,
            #     self.pair_obj.pre.cn_bed,
            #     cn_summary_data=self.pair_obj.pre.cn_summary_data
            # )
            # post_json = generate_chromosome_plot(
            #     self.pair_obj.post.baf_lrr_data,
            #     self.pair_obj.post.cnv_detection_filtered,
            #     chromosome,
            #     self.pair_obj.post.sample_id,
            #     self.pair_obj.post.roh_bed,
            #     self.pair_obj.post.union_bed,
            #     self.pair_obj.post.cn_bed,
            #     cn_summary_data=self.pair_obj.post.cn_summary_data
            # )
            
            
            
            combined_json = generate_combined_plots(
                # ---------- PRE track ----------
                pre_baf_lrr   = self.pair_obj.pre.baf_lrr_data,
                pre_cnv       = self.pair_obj.pre.cn_summary_data,

                # ---------- POST track ----------
                post_baf_lrr  = self.pair_obj.post.baf_lrr_data,
                post_cnv      = self.pair_obj.post.cn_summary_data,

                # ---------- DIFF track ----------
                diff_baf_lrr  = self.pair_obj.post.baf_lrr_data,     
                diff_cnv      = self.pair_obj.cnv_detection_filtered, 
                chromosome    = chromosome,
                pre_sample_id = self.pair_obj.pre.sample_id,
                post_sample_id= self.pair_obj.post.sample_id,
                pair_id       = self.pair_obj.pair_id,

                # Overlays -------------  
                pre_roh_bed   = self.pair_obj.pre.roh_bed,
                pre_union_bed = self.pair_obj.pre.union_bed,
                pre_cn_bed    = self.pair_obj.pre.cn_bed,

                post_roh_bed  = self.pair_obj.post.roh_bed,
                post_union_bed= self.pair_obj.post.union_bed,
                post_cn_bed   = self.pair_obj.post.cn_bed,

                diff_roh_bed  = self.pair_obj.roh_bed,   
                diff_union_bed= self.pair_obj.union_bed,
                diff_cn_bed   = self.pair_obj.cn_bed,
                
                # Add segment data with named parameters
                pre_cn_summary_data = self.pair_obj.pre.cn_summary_data,
                post_cn_summary_data = self.pair_obj.post.cn_summary_data,
                diff_cn_summary_data = self.pair_obj.post.cn_summary_data
            )



            # Get home page name for links
            home_page = self.output_manager.get_home_page_name()

            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{self.pair_obj.pair_id} - Chromosome {chromosome}</title>
                <link rel="stylesheet" href="../../../../components/css/styles.css">
                <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                <script src="https://cdn.bokeh.org/bokeh/release/bokeh-3.3.4.min.js"></script>
                <script src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.3.4.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <style>
                  @media print {{
                    .navbar,
                    #download-pdf-btn{{display:none !important;}}
                  }}
                  @page{{size:A2 portrait; margin:10mm;}}
                  /* Force each table area to scroll independently (horizontal) */
                  .table-wrapper {{
                    overflow-x: auto;
                    width: 100%;
                  }}
                  /* Default-hide dropdown content; show when parent has .active */
                  .summary_single-dropdown-content {{
                    display: none;
                  }}
                  .summary_single-dropdown-section.active > .summary_single-dropdown-content {{
                    display: block;
                  }}
                </style>
            </head>
            <body>
                <!-- Header -->
                <nav class="navbar">
                    <div class="logo-container left">
                        <img src="../../../../components/logo/left_icon.png" alt="Left Logo">
                    </div>
                    
                    <div class="nav-center">
                        <a class="home-link" href="../../../../{home_page}">Home</a>
                        <span class="nav-divider">•</span>
                        <a class="home-link" href="../summary_page_{self.pair_obj.pair_id}.html">Pair Summary</a>
                        <span class="nav-divider">•</span>
                        <a class="home-link" href="../../../../components/info.html" title="Documentation">
                            <i class="fas fa-info-circle" style="font-size: 0.9em"></i>
                        </a>
                    </div>

                    <div class="logo-container right">
                        <img src="../../../../components/logo/right_icon.png" alt="Right Logo">
                    </div>
                </nav>

                <div class="content-container">
                    <!-- PDF Button -->
                    <div class="nav-buttons_info_page" style="text-align: right; margin: 10px 0;">
                        <button id="download-pdf-btn" class="action-button_info_page">
                            <i class="fas fa-file-pdf"></i> Save / Print PDF
                        </button>
                    </div>
                    
                    <div class="info-boxes-container">
                        <!-- Left Column - Sample/Chromosome Info -->
                        <div class="info-column left" style="margin-right: auto;">
                            <!-- Pair ID Box -->
                            <div class="info-box">
                                <h3>Pair Information</h3>
                                <div class="value">{self.pair_obj.pair_id}</div>
                                <div class="label">Pair ID</div>
                                
                                <div class="value" style="margin-top: 15px;">{self.pair_obj.pre.sample_id}</div>
                                <div class="label">Pre Sample</div>
                                
                                <div class="value">{self.pair_obj.post.sample_id}</div>
                                <div class="label">Post Sample</div>
                            </div>
                            
                            <!-- Chromosome Info Box -->
                            <div class="info-box">
                                <h3>Chromosome Details</h3>
                                <div class="value">{chromosome}</div>
                                <div class="label">Chromosome Number</div>
                                
                                <div class="cnv-stats">
                                    <h3>CNV Summary</h3>
                                    <ul>
                                        <li>
                                            <span class="stat-label">Total CNVs</span>
                                            <span class="stat-value">{self.pair_obj.chromosome_stats[chromosome]['total_cnvs']}</span>
                                        </li>
                                        <li>
                                            <span class="stat-label">Duplications</span>
                                            <span class="stat-value">{self.pair_obj.chromosome_stats[chromosome]['duplications']}</span>
                                        </li>
                                        <li>
                                            <span class="stat-label">Deletions</span>
                                            <span class="stat-value">{self.pair_obj.chromosome_stats[chromosome]['deletions']}</span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Right Column - LRR Stats -->
                        <div class="info-column right" style="margin-left: auto;">
                            <!-- LRR Stats Box -->
                            <div class="info-box">
                                <h3>LRR Statistics</h3>
                                <div class="label">Calculated based on Sample : {self.pair_obj.post.sample_id}</div>
                                <ul class="cnv-stats">
                                    <li>
                                        <span class="stat-label">Mean LRR</span>
                                        <span class="stat-value {self.get_lrr_status(self.pair_obj.lrr_stats[chromosome]['mean'], 'mean')}">
                                            {self.pair_obj.lrr_stats[chromosome]['mean']:.3f}
                                        </span>
                                    </li>
                                    <li>
                                        <span class="stat-label">Median LRR</span>
                                        <span class="stat-value {self.get_lrr_status(self.pair_obj.lrr_stats[chromosome]['median'], 'median')}">
                                            {self.pair_obj.lrr_stats[chromosome]['median']:.3f}
                                        </span>
                                    </li>
                                    <li>
                                        <span class="stat-label">StdDev LRR</span>
                                        <span class="stat-value {self.get_lrr_status(self.pair_obj.lrr_stats[chromosome]['std'], 'std')}">
                                            {self.pair_obj.lrr_stats[chromosome]['std']:.3f}
                                        </span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <!-- 9-panel PRE / POST / DIFF dashboard -->
                    <div class="chromosome-cnv-section">
                        <h3 style="margin:40px 0 12px;">Combined PRE / POST / DIFF CNV Analysis</h3>
                        <div id="combined-plot"
                            class="responsive-plot_chromosome center-plot"></div>
                    </div>


                <!-- Chromosome-specific CNV Tables -->
                <div class="chromosome-cnv-section">
                    <h3 class="section-title">Chromosome {chromosome} CNV Details</h3>

                    <!-- ===== PRE / POST CNVs ===== -->
                    <h4 class="subsection-title">Pre and Post Sample CNVs</h4>

                    <!-- Pre/Post Sample CNVs in Dropdown -->
                    <div class="summary_single-dropdown-section" style="margin-top: 10px;">
                        <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                            Pre/Post Sample CNVs
                            <span class="dropdown-arrow">▼</span>
                        </button>
                        <div class="summary_single-dropdown-content">
                            <div class="two-column-layout" style="display: flex; gap: 20px;">
                                <!-- ===== PRE COLUMN ===== -->
                                <div class="column" style="flex: 1; min-width: 0;">
                                    <h4>Pre-Sample CNVs</h4>

                                    <!-- Significant Pre-Sample CNVs -->
                                    <div class="summary_single-dropdown-section active">
                                        <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                                            Significant CNVs (p &lt; 0.05)
                                            <span class="dropdown-arrow">▲</span>
                                        </button>
                                        <div class="summary_single-dropdown-content">
                                            <div class="table-wrapper">
                                                {pre_chrom_table['significant']}
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Non-significant Pre-Sample CNVs -->
                                    <div class="summary_single-dropdown-section">
                                        <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                                            Non-significant CNVs (p ≥ 0.05)
                                            <span class="dropdown-arrow">▼</span>
                                        </button>
                                        <div class="summary_single-dropdown-content">
                                            <div class="table-wrapper">
                                                {pre_chrom_table['nonsignificant']}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- ===== POST COLUMN ===== -->
                                <div class="column" style="flex: 1; min-width: 0;">
                                    <h4>Post-Sample CNVs</h4>

                                    <!-- Significant Post-Sample CNVs -->
                                    <div class="summary_single-dropdown-section active">
                                        <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                                            Significant CNVs (p &lt; 0.05)
                                            <span class="dropdown-arrow">▲</span>
                                        </button>
                                        <div class="summary_single-dropdown-content">
                                            <div class="table-wrapper">
                                                {post_chrom_table['significant']}
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Non-significant Post-Sample CNVs -->
                                    <div class="summary_single-dropdown-section">
                                        <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                                            Non-significant CNVs (p ≥ 0.05)
                                            <span class="dropdown-arrow">▼</span>
                                        </button>
                                        <div class="summary_single-dropdown-content">
                                            <div class="table-wrapper">
                                                {post_chrom_table['nonsignificant']}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div> <!-- /.two-column-layout -->
                        </div> <!-- /.summary_single-dropdown-content -->
                    </div> <!-- /.summary_single-dropdown-section (Pre/Post) -->

                    <!-- ===== DIFFERENTIAL CNVs ===== -->
                    <h4 class="subsection-title" style="margin-top: 35px;">Differential CNVs</h4>

                    <!-- Significant Differential CNVs -->
                    <div class="summary_single-dropdown-section active">
                        <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                            Significant Differential CNVs (p &lt; 0.05)
                            <span class="dropdown-arrow">▲</span>
                        </button>
                        <div class="summary_single-dropdown-content">
                            <div class="table-wrapper">
                                {chrom_table['significant']}
                            </div>
                        </div>
                    </div>

                    <!-- Non-significant Differential CNVs -->
                    <div class="summary_single-dropdown-section">
                        <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                            Non-significant Differential CNVs (p ≥ 0.05)
                            <span class="dropdown-arrow">▼</span>
                        </button>
                        <div class="summary_single-dropdown-content">
                            <div class="table-wrapper">
                                {chrom_table['nonsignificant']}
                            </div>
                        </div>
                    </div>
                </div> <!-- /.chromosome-cnv-section -->
                
            </div>

            <!-- Footer -->
            <div id="footer-placeholder"></div>

            <script>
            /* -------- helper to embed a Bokeh JSON item ---------- */
            function embedIfOK(jsonStr, targetId, docId) {{
                const payload = JSON.parse(jsonStr);
                const div     = document.getElementById(targetId);

                if (!payload.error) {{
                    Bokeh.embed.embed_item(payload, targetId, docId);

                    /* tell Bokeh to re-measure after the element is visible */
                    requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
                }} else {{
                    div.innerHTML =
                        `<div class="info-box error"><p>${{payload.error}}</p></div>`;
                }}
            }}

            // PDF conversion function
            async function convertBokehPlotsToImages() {{
              const plots = document.querySelectorAll('.bk-root');
              for (let i = 0; i < plots.length; i++) {{
                const plot = plots[i];
                const container = plot.closest('.plot-container') || plot.parentElement;
                try {{
                  await new Promise(r => setTimeout(r, 500));
                  const canvas = await html2canvas(plot, {{
                    scale: 2,
                    logging: false,
                    useCORS: true,
                    allowTaint: true,
                    backgroundColor: 'white'
                  }});
                  const imgData = canvas.toDataURL('image/png');
                  const img = document.createElement('img');
                  img.src = imgData;
                  img.className = 'bokeh-static-image';
                  img.style.width = '100%';
                  const staticBox = document.createElement('div');
                  staticBox.className = 'bokeh-static-container';
                  staticBox.appendChild(img);
                  plot.style.display = 'none';
                  container.appendChild(staticBox);
                }} catch (err) {{
                  console.error('Plot conversion error:', err);
                }}
              }}
              return true;
            }}

            document.addEventListener("DOMContentLoaded", () => {{
                // PDF button handling
                const btn = document.getElementById('download-pdf-btn');
                if (btn) {{
                  async function prepare() {{
                    try {{
                      await convertBokehPlotsToImages();
                      await new Promise(r => setTimeout(r, 300));
                    }} catch (e) {{
                      console.warn('Preparation for print failed:', e);
                    }}
                  }}

                  function cleanup() {{
                    document.querySelectorAll('.bokeh-static-container').forEach(c => c.remove());
                    document.querySelectorAll('.bk-root').forEach(p => p.style.display = 'block');
                  }}

                  btn.addEventListener('click', async () => {{
                    await prepare();
                    window.print();
                  }});

                  window.addEventListener('afterprint', cleanup);
                }}

                /* ---------- 1. stick / float the footer ------------------ */
                const footer = document.getElementById('footer-placeholder');

                function positionFooter() {{
                    const contentBottom = document
                        .querySelector('.content-container')
                        .getBoundingClientRect().bottom;
                    footer.style.position =
                        (contentBottom < window.innerHeight) ? 'fixed' : 'relative';
                }}

                fetch('../../../../components/footer.html')
                    .then(r => r.text())
                    .then(html => {{
                        footer.innerHTML = html;
                        positionFooter();
                        window.addEventListener('resize', positionFooter);
                    }});
            }});

            /* ---------- 2b. embed the 9-panel dashboard only when the
                            whole page (images, fonts, CSS) is loaded ---- */
            window.addEventListener('load', () => {{
                embedIfOK(`{combined_json}`, 'combined-plot', 'doc_combined');

                // Setup sorting for all detailed CNV tables with column 1 (Start) as default
                setupTableSorting('.detailed-cnv-table', 1);
                
                // Initialize table sorting for tables in dropdowns when they're opened
                document.querySelectorAll('.summary_single-dropdown-toggle').forEach(button => {{
                    button.addEventListener('click', () => {{
                        // Wait for dropdown animation to complete
                        setTimeout(() => {{
                            const dropdownContent = button.nextElementSibling;
                            if (dropdownContent) {{
                                const tables = dropdownContent.querySelectorAll('.detailed-cnv-table');
                                tables.forEach(table => {{
                                    if (!table.getAttribute('data-sorting-initialized')) {{
                                        setupTableSorting(table, 1);
                                        table.setAttribute('data-sorting-initialized', 'true');
                                    }}
                                }});
                            }}
                        }}, 100);
                    }});
                }});
            }});

            function toggleDropdown(button) {{
                /* Prevent the click from bubbling up to parent dropdowns */
                if (typeof event !== 'undefined' && event.stopPropagation) {{
                    event.stopPropagation();
                }}

                const dropdownSection = button.closest('.summary_single-dropdown-section') || 
                                         button.closest('.paired_chromosome-dropdown-section');
                if (!dropdownSection) return;

                /* Toggle visibility */
                dropdownSection.classList.toggle('active');

                /* Flip arrow icon */
                const arrow = button.querySelector('.dropdown-arrow');
                if (arrow) {{
                    arrow.textContent = dropdownSection.classList.contains('active') ? '▲' : '▼';
                }} else {{
                    // Fallback for legacy markup with arrows in innerHTML
                    button.innerHTML = dropdownSection.classList.contains('active')
                        ? button.innerHTML.replace('▼', '▲')
                        : button.innerHTML.replace('▲', '▼');
                }}

                /* Ensure the corresponding content is actually shown/hidden */
                const content = dropdownSection.querySelector('.summary_single-dropdown-content');
                if (content) {{
                    content.style.display = dropdownSection.classList.contains('active') ? 'block' : 'none';
                }}
            }}

            // Style sub-dropdowns
            document.addEventListener('DOMContentLoaded', function() {{
                document.querySelectorAll('.summary_single-dropdown-toggle').forEach(btn => {{
                    // Add the summary_single class to the parent
                    if (btn.parentElement && btn.parentElement.classList.contains('summary_single-dropdown-section')) {{
                        btn.parentElement.classList.add('summary_single-nested-dropdown');
                    }}
                }});
            }});

            // Table sorting functionality
            const getCellValue = (tr, idx) => {{
                const cell = tr.children[idx];
                // Handle cells with links or empty cells
                const link = cell.querySelector('a');
                let value = link ? link.textContent : cell.innerText || cell.textContent;
                return value.trim();
            }};

            // Improved comparer function with number detection and empty cell handling
            const comparer = (idx, asc) => (a, b) => {{
                const v1 = getCellValue(asc ? a : b, idx);
                const v2 = getCellValue(asc ? b : a, idx);
                
                // Handle empty values
                if (!v1 && v2) return 1;
                if (v1 && !v2) return -1;
                if (!v1 && !v2) return 0;
                
                // Handle numeric values with commas and units
                const num1 = v1.replace(/,/g, '').replace(/[^0-9.-]/g, '');
                const num2 = v2.replace(/,/g, '').replace(/[^0-9.-]/g, '');
                
                if (!isNaN(parseFloat(num1)) && !isNaN(parseFloat(num2))) {{
                    return parseFloat(num1) - parseFloat(num2);
                }}
                
                // Default to string comparison
                return v1.toString().localeCompare(v2);
            }};

            const setupTableSorting = (tableSelector, defaultSortColumn = 0) => {{
                const tables = typeof tableSelector === 'string' 
                    ? document.querySelectorAll(tableSelector)
                    : [tableSelector];
                
                tables.forEach(table => {{
                    if (!table || table.getAttribute('data-sorting-initialized') === 'true') return;
                    
                    // Track sorted state
                    let sortColumnIndex = defaultSortColumn;
                    let sortAscending = true;
                    
                    table.setAttribute('data-sorting-initialized', 'true');

                    table.querySelectorAll('th').forEach((th, thIndex) => {{
                        th.style.cursor = 'pointer';
                        
                        th.addEventListener('click', () => {{
                            const tbody = table.querySelector('tbody');
                            if (!tbody) return;
                            
                            // If same column clicked, toggle direction
                            if (sortColumnIndex === thIndex) {{
                                sortAscending = !sortAscending;
                            }} else {{
                                // New column, sort ascending by default
                                sortColumnIndex = thIndex;
                                sortAscending = true;
                            }}
                            
                            // Clear all existing sort indicators
                            table.querySelectorAll('th').forEach(header => {{
                                header.classList.remove('sorted-asc', 'sorted-desc');
                            }});
                            
                            // Add sort indicator
                            th.classList.add(sortAscending ? 'sorted-asc' : 'sorted-desc');
                            
                            // Sort rows
                            Array.from(tbody.querySelectorAll('tr'))
                                .sort(comparer(thIndex, sortAscending))
                                .forEach(tr => tbody.appendChild(tr));
                        }});
                    }});

                    // Initial sort if specified
                    if (defaultSortColumn >= 0) {{
                        const defaultHeader = table.querySelector(`th:nth-child(${{defaultSortColumn + 1}})`);
                        if (defaultHeader) {{
                            defaultHeader.click();
                        }}
                    }}
                }});
            }};

            </script>
        </body>
        </html>
        """
        except Exception as e:
            logging.error(f"Error generating chromosome {chromosome} page: {e}")
            return "<html><body><h3>Error generating page</h3></body></html>"

    def save_chromosome_pages(self):
        """Save pages for each chromosome."""
        if not self.pair_obj.post.available_chromosomes:
            logging.warning("No chromosomes available for %s", self.pair_obj.pair_id)
            return
        pair_dir = self.output_manager.dir_structure.pair_dirs[self.pair_obj.pair_id]
        chrom_dir = os.path.join(pair_dir, f"chromosomes_{self.pair_obj.pair_id}")
        os.makedirs(chrom_dir, exist_ok=True)
        for chrom in self.pair_obj.post.available_chromosomes:
            html = self.generate_chromosome_page(chrom)
            fname = f"chromosome_{chrom.replace(' ','_')}_{self.pair_obj.pair_id}.html"
            with open(os.path.join(chrom_dir, fname), 'w') as f:
                f.write(html)
            logging.info("Saved %s", fname)

    def get_lrr_status(self, value, metric):
        """Same as single-sample logic."""
        try:
            v = float(value)
            if metric == 'std':    return 'good' if v < 0.3   else 'bad'
            if metric in ('mean','median'):
                return 'good' if -0.15 <= v <= 0.15 else 'bad'
        except: pass
        return ''
    
    

