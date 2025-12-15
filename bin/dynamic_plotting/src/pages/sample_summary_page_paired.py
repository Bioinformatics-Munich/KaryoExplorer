import os
import logging
from pathlib import Path
from typing import Dict, Any
from src.tables.table_generator import TableGenerator
from src.plots.cnv_distribution import generate_cnv_distribution_plot
from src.utils.css_styles.table_styles import get_table_styles
import json
from src.plots.karyotype import generate_karyotype_plot

class SampleSummaryGenerator:
    """Class to generate paired sample summary pages"""
    
    def __init__(self, pair_obj, output_manager):
        """Initialize with pair object and output manager"""
        self.pair_obj = pair_obj
        self.output_manager = output_manager
        self.table_generator = TableGenerator()
    
    def _ensure_dict_format(self, table_data):
        """Ensure table data is in dictionary format with required keys"""
        if isinstance(table_data, dict) and 'significant' in table_data and 'nonsignificant' in table_data:
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
    
    def generate(self) -> str:
        """Generate the complete sample summary HTML"""
        try:
            # Get pair data through the pre/post attributes
            pair_id = self.pair_obj.pair_id
            pre_sample = self.pair_obj.pre.pre_sample
            post_sample = self.pair_obj.post.pre_sample
            p_hat = getattr(self.pair_obj, 'PI_HAT', 'N/A')
            
            # Format and color P_HAT
            if p_hat != 'N/A':
                p_hat_value = float(p_hat)
                p_hat_display = f"{p_hat_value:.4f}"
                p_hat_color = '#e74c3c' if p_hat_value < 0.9 else '#2ecc71'
            else:
                p_hat_display = 'N/A'
                p_hat_color = '#2c3e50'  # Default neutral color
            
            # Generate pre/post tables
            pre_cnv_table = self.table_generator.generate_cnv_summary_table_pre(
                self.pair_obj.pre.cn_summary_data
            )
            post_cnv_table = self.table_generator.generate_cnv_summary_table_post(
                self.pair_obj.post.cn_summary_data
            )
            
            differential_cnv_table = self.table_generator.generate_cnv_summary_table_differential(
                self.pair_obj.cnv_detection_filtered
            )
            
            # Generate detailed differential CNV table
            detailed_differential_tables = self.table_generator.generate_detailed_cnv_table(
                self.pair_obj.cnv_detection_filtered
            )
            detailed_differential_tables = self._ensure_dict_format(detailed_differential_tables)
            
            # Split pre/post CNV tables into significant and non-significant
            detailed_pre_CNV_tables = self.table_generator.generate_detailed_cnv_table_single(
                self.pair_obj.pre.cn_summary_data
            )
            detailed_pre_CNV_tables = self._ensure_dict_format(detailed_pre_CNV_tables)
            
            detailed_post_CNV_tables = self.table_generator.generate_detailed_cnv_table_single(
                self.pair_obj.post.cn_summary_data
            )
            detailed_post_CNV_tables = self._ensure_dict_format(detailed_post_CNV_tables)
        

            # Generate individual sample plots
            try:
                bokeh_pre_cnv_distribution_summary = generate_cnv_distribution_plot(
                    self.pair_obj.pre.cn_summary_data,
                    self.pair_obj.pre.sample_id,
                    self.pair_obj.pre.available_chromosomes,
                    gender=self.pair_obj.pre.pre_sex
                )
                bokeh_post_cnv_distribution_summary = generate_cnv_distribution_plot(
                    self.pair_obj.post.cn_summary_data,
                    self.pair_obj.post.sample_id,
                    self.pair_obj.post.available_chromosomes,
                    gender=self.pair_obj.post.pre_sex
                )
                
                # Add individual karyotype plots
                bokeh_pre_karyotype = generate_karyotype_plot(
                    self.pair_obj.pre.cn_summary_data,
                    self.pair_obj.pre.sample_id,
                    gender=self.pair_obj.pre.pre_sex,
                    reference_genome='GRCh37',
                    mode='single',
                    available_chromosomes=self.pair_obj.pre.available_chromosomes
                )
                bokeh_post_karyotype = generate_karyotype_plot(
                    self.pair_obj.post.cn_summary_data,
                    self.pair_obj.post.sample_id,
                    gender=self.pair_obj.post.pre_sex,
                    reference_genome='GRCh37',
                    mode='single',
                    available_chromosomes=self.pair_obj.post.available_chromosomes
                )
            except Exception as e:
                logging.error(f"Error generating individual plots: {str(e)}")
                bokeh_pre_cnv_distribution_summary = bokeh_post_cnv_distribution_summary = json.dumps({'error': 'Failed to generate individual plots'})
                bokeh_pre_karyotype = bokeh_post_karyotype = json.dumps({'error': 'Failed to generate individual karyotypes'})

            # Generate differential CNV plot
            try:
                bokeh_differential_cnv_distribution_summary = generate_cnv_distribution_plot(
                    self.pair_obj.cnv_detection_filtered,
                    f"{self.pair_obj.pre.sample_id} vs {self.pair_obj.post.sample_id}",
                    self.pair_obj.post.available_chromosomes,
                    gender=getattr(self.pair_obj.post, 'pre_sex', None)
                )
            except Exception as e:
                logging.error(f"Error generating differential CNV plot: {str(e)}")
                bokeh_differential_cnv_distribution_summary = json.dumps({'error': 'Failed to generate differential CNV visualization'})
                
            # Generate differential karyotype plot
            try:
                bokeh_differential_karyotype = generate_karyotype_plot(
                    self.pair_obj.cnv_detection_filtered,
                    f"{self.pair_obj.pre.sample_id} vs {self.pair_obj.post.sample_id}",
                    gender=getattr(self.pair_obj.post, 'pre_sex', None),
                    reference_genome='GRCh37',
                    mode='differential',
                    available_chromosomes=self.pair_obj.post.available_chromosomes
                )
            except Exception as e:
                logging.error(f"Error generating differential karyotype plot: {str(e)}")
                bokeh_differential_karyotype = json.dumps({'error': 'Failed to generate karyotype visualization'})
                
            # Get home page name for links
            home_page = self.output_manager.get_home_page_name()
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{pair_id} - Paired Analysis</title>
                <link rel="stylesheet" href="../../../components/css/styles.css">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                <!-- Add Bokeh resources -->
                <script src="https://cdn.bokeh.org/bokeh/release/bokeh-3.3.4.min.js"></script>
                <script src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.3.4.min.js"></script>
                <script src="https://cdn.bokeh.org/bokeh/release/bokeh-tables-3.3.4.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <style>
                  @media print {{
                    .navbar,
                    #download-pdf-btn{{display:none !important;}}
                  }}
                  @page{{size:A2 portrait; margin:10mm;}}
                  
                  {get_table_styles()}
                  /* Force each table area to scroll independently (horizontal) */
                  .table-wrapper {{
                    overflow-x: auto;
                    width: 100%;
                  }}
                  /* Default-hide dropdown content; show when parent has .active */
                  .summary_single-dropdown-content {{
                    display: none;        /* hidden until parent .active */
                  }}
                  /* Keep pre‑ / post‑sample columns side‑by‑side at equal width
                     and let each inner table scroll horizontally */
                  .two-column-layout {{
                    display: flex;
                    gap: 20px;
                    align-items: flex-start;
                  }}
                  .two-column-layout > .column {{
                    flex: 1 1 0;   /* ~50 % share, never grows past available half */
                    min-width: 0;  /* allow table-wrapper overflow-x */
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
                        <img src="../../../components/logo/left_icon.png" alt="Left Logo">
                    </div>
                    
                    <div class="nav-center">
                        <a class="home-link" href="../../../{home_page}">Home</a>
                        <span class="nav-divider">•</span>
                        <a class="home-link" href="./summary_page_{self.pair_obj.pair_id}.html">Pair Summary</a>
                        <span class="nav-divider">•</span>
                        <a class="home-link" href="../../../components/info.html" title="Documentation">
                            <i class="fas fa-info-circle" style="font-size: 0.9em"></i>
                        </a>
                    </div>

                    <div class="logo-container right">
                        <img src="../../../components/logo/right_icon.png" alt="Right Logo">
                    </div>
                </nav>

                <!-- Main Content -->
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
                                
                                <div class="value">{self.pair_obj.pre.pre_sex}</div>
                                <div class="label">Pre Sample Sex</div>

                                <div class="value">{self.pair_obj.post.pre_sex}</div>
                                <div class="label">Post Sample Sex</div>
                            </div>
                        </div>

                        <div class="right-info-group">
                            <div class="info-box p-hat-box">
                                <strong>P_HAT Value</strong>
                                <span class="p-hat-value" style="color: {p_hat_color}">
                                    {p_hat_display}
                                </span>
                            </div>
                        </div>
                    </div>

                    <h2>CNV Statistics Summary</h2>
                    <div class="stats-container">
                        <div class="summary_single-dropdown-section">
                            <button class="summary_single-dropdown-toggle">
                                Pre/Post Analysis
                                <span class="dropdown-arrow">▼</span>
                            </button>
                            <div class="summary_single-dropdown-content">
                                <div class="vertical-layout no-bg">
                                    <div class="section">
                                        <h4>Pre Sample ({pre_sample})</h4>
                                        <div class="table-wrapper horizontal-scroll">
                                            {pre_cnv_table}
                                        </div>
                                    </div>
                                    <div class="section">
                                        <h4>Post Sample ({post_sample})</h4>
                                        <div class="table-wrapper horizontal-scroll">
                                            {post_cnv_table}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="differential-section">
                            <h3 class="section-title">Differential CNV Statistics</h3>
                            <div class="table-wrapper horizontal-scroll">
                                {differential_cnv_table}
                            </div>
                        </div>
                    </div>

                    <div class="plot-section">
                        <h3 class="section-title">Differential CNV Distribution</h3>
                        
                        <div class="summary_single-dropdown-section">
                            <button class="summary_single-dropdown-toggle">
                                Individual Sample CNV Distributions
                                <span class="dropdown-arrow">▼</span>
                            </button>
                            <div class="summary_single-dropdown-content">
                                <div class="two-column-layout no-bg">
                                    <div class="column natural-column">
                                        <h4>Pre Sample ({pre_sample})</h4>
                                        <div id="pre-cnv-plot" class="responsive-plot"></div>
                                    </div>
                                    <div class="column natural-column">
                                        <h4>Post Sample ({post_sample})</h4>
                                        <div id="post-cnv-plot" class="responsive-plot"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="plot-container">
                            <div id="diff-cnv-plot" class="responsive-plot"></div>
                        </div>
                    </div>

                    <div class="plot-section">
                        <h3 class="section-title">Karyotype Overview</h3>
                        
                        <div class="summary_single-dropdown-section">
                            <button class="summary_single-dropdown-toggle">
                                Individual Sample Karyotypes
                                <span class="dropdown-arrow">▼</span>
                            </button>
                            <div class="summary_single-dropdown-content">
                                <div class="two-column-layout no-bg">
                                    <div class="column natural-column">
                                        <h4>Pre Sample ({pre_sample})</h4>
                                        <div id="pre-karyotype-plot" class="responsive-plot_karyotype"></div>
                                    </div>
                                    <div class="column natural-column">
                                        <h4>Post Sample ({post_sample})</h4>
                                        <div id="post-karyotype-plot" class="responsive-plot_karyotype"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="plot-container">
                            <div id="diff-karyotype-plot" class="responsive-plot_karyotype"></div>
                        </div>
                    </div>
                    
                    <h4 class="subsection-title">Chromosome details</h4>
                    {self._get_chromosome_selector()}

                    <!-- Detailed CNV Table -->
                    <div class="detailed-cnv-section" style="margin-top: 2rem;">
                        <h3 class="section-title">Pre Post CNV Tables</h3>
                        <div class="summary_single-dropdown-section">
                            <button class="summary_single-dropdown-toggle">
                                Pre/Post Sample CNVs
                                <span class="dropdown-arrow">▼</span>
                            </button>
                            <div class="summary_single-dropdown-content">
                                <div class="two-column-layout">
                                    <!-- ===== PRE‑SAMPLE COLUMN ===== -->
                                    <div class="column">
                                        <h4>Pre‑Sample CNVs</h4>

                                        <!-- Significant Pre‑Sample CNVs – expanded by default -->
                                        <div class="summary_single-dropdown-section active">
                                            <button class="summary_single-dropdown-toggle">
                                                Significant CNVs (p &lt; 0.05)
                                                <span class="dropdown-arrow">▲</span>
                                            </button>
                                            <div class="summary_single-dropdown-content">
                                                <div class="table-wrapper">
                                                    {detailed_pre_CNV_tables['significant']}
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Non‑significant Pre‑Sample CNVs – collapsed by default -->
                                        <div class="summary_single-dropdown-section">
                                            <button class="summary_single-dropdown-toggle">
                                                Non‑significant CNVs (p ≥ 0.05)
                                                <span class="dropdown-arrow">▼</span>
                                            </button>
                                            <div class="summary_single-dropdown-content">
                                                <div class="table-wrapper">
                                                    {detailed_pre_CNV_tables['nonsignificant']}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- ===== POST‑SAMPLE COLUMN ===== -->
                                    <div class="column">
                                        <h4>Post‑Sample CNVs</h4>

                                        <!-- Significant Post‑Sample CNVs – expanded by default -->
                                        <div class="summary_single-dropdown-section active">
                                            <button class="summary_single-dropdown-toggle">
                                                Significant CNVs (p &lt; 0.05)
                                                <span class="dropdown-arrow">▲</span>
                                            </button>
                                            <div class="summary_single-dropdown-content">
                                                <div class="table-wrapper">
                                                    {detailed_post_CNV_tables['significant']}
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Non‑significant Post‑Sample CNVs – collapsed by default -->
                                        <div class="summary_single-dropdown-section">
                                            <button class="summary_single-dropdown-toggle">
                                                Non‑significant CNVs (p ≥ 0.05)
                                                <span class="dropdown-arrow">▼</span>
                                            </button>
                                            <div class="summary_single-dropdown-content">
                                                <div class="table-wrapper">
                                                    {detailed_post_CNV_tables['nonsignificant']}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div> <!-- /.two-column-layout -->
                            </div> <!-- /.summary_single-dropdown-content -->
                        </div>
                        
                        <h4 class="subsection-title">Differential CNV Details</h4>
                        
                        <!-- Significant Differential CNVs in dropdown, expanded by default -->
                        <div class="summary_single-dropdown-section active">
                            <button class="summary_single-dropdown-toggle">
                                Significant CNVs (p < 0.05)
                                <span class="dropdown-arrow">▲</span>
                            </button>
                            <div class="summary_single-dropdown-content">
                                <div class="table-wrapper">
                                    {detailed_differential_tables['significant']}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Non-significant Differential CNVs in dropdown, collapsed by default -->
                        <div class="summary_single-dropdown-section">
                            <button class="summary_single-dropdown-toggle">
                                Non-significant CNVs (p ≥ 0.05)
                                <span class="dropdown-arrow">▼</span>
                            </button>
                            <div class="summary_single-dropdown-content">
                                <div class="table-wrapper">
                                    {detailed_differential_tables['nonsignificant']}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer -->
                <div id="footer-placeholder"></div>

                <!-- Scripts -->
                <script>
                    // Add this at the top level of the script section, before DOMContentLoaded
                    function toggleDropdown(button, event) {{
                        // Handle both original dropdown-section and the new summary_single-dropdown-section classes
                        const dropdownSection = button.closest('.dropdown-section') || button.closest('.summary_single-dropdown-section');
                        if (!dropdownSection) return;
                        
                        // Stop event propagation to parent dropdowns
                        if (event) {{
                            event.stopPropagation();
                        }}
                        
                        dropdownSection.classList.toggle('active');
                        
                        // Update arrow indicator if present
                        const arrow = button.querySelector('.dropdown-arrow');
                        if (arrow) {{
                            arrow.textContent = dropdownSection.classList.contains('active') ? '▲' : '▼';
                        }} else {{
                            // Legacy handling for buttons that have the arrow inside the text itself
                            if (dropdownSection.classList.contains('active')) {{
                                button.innerHTML = button.innerHTML.replace('▼', '▲');
                            }} else {{
                                button.innerHTML = button.innerHTML.replace('▲', '▼');
                            }}
                        }}
                        
                        // If this is a parent dropdown with nested dropdowns inside,
                        // make sure we don't close the parent when clicking on children
                        if (dropdownSection.classList.contains('active')) {{
                            const nestedButtons = dropdownSection.querySelectorAll('.summary_single-dropdown-toggle');
                            nestedButtons.forEach(btn => {{
                                if (btn !== button) {{
                                    btn.addEventListener('click', function(e) {{
                                        e.stopPropagation();
                                    }}, {{ once: true }});
                                }}
                            }});
                        }}
                        /* Ensure the corresponding content is actually shown/hidden */
                        const content = dropdownSection.querySelector('.summary_single-dropdown-content');
                        if (content) {{
                            content.style.display = dropdownSection.classList.contains('active') ? 'block' : 'none';
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

                    document.addEventListener('DOMContentLoaded', () => {{
                      const btn = document.getElementById('download-pdf-btn');
                      if (!btn) return;

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
                      
                      // Initialize all nested dropdowns properly
                      document.querySelectorAll('.summary_single-dropdown-section .summary_single-dropdown-section').forEach(nestedDropdown => {{
                          nestedDropdown.classList.add('summary_single-nested-dropdown');
                          
                          // Add special styling to buttons inside nested dropdowns
                          const nestedButton = nestedDropdown.querySelector('.summary_single-dropdown-toggle');
                          if (nestedButton) {{
                              nestedButton.classList.add('sub-dropdown');
                          }}
                      }});
                      
                      // Replace the onclick attribute handlers with proper event listeners
                      document.querySelectorAll('.summary_single-dropdown-toggle').forEach(button => {{
                          // Remove the existing onclick attribute
                          button.removeAttribute('onclick');
                          
                          // Add a proper event listener
                          button.addEventListener('click', function(event) {{
                              toggleDropdown(this, event);
                          }});
                      }});
                    }});

                    document.addEventListener("DOMContentLoaded", async function() {{
                        try {{
                            // Load footer
                            fetch('../../../components/footer.html')
                                .then(response => response.text())
                                .then(data => document.getElementById('footer-placeholder').innerHTML = data);

                            // Handle individual plots
                            try {{
                                const prePlotJson = {bokeh_pre_cnv_distribution_summary};
                                if (prePlotJson && !prePlotJson.error) {{
                                    Bokeh.embed.embed_item(prePlotJson, "pre-cnv-plot");
                                }} else {{
                                    document.getElementById('pre-cnv-plot').innerHTML = 
                                        '<div class="info-box_empty">' + (prePlotJson && prePlotJson.error ? prePlotJson.error : 'No pre-sample plot data') + '</div>';
                                }}
                            }} catch (error) {{
                                console.error("Pre sample plot error:", error);
                                document.getElementById('pre-cnv-plot').innerHTML = 
                                    '<div class="info-box_empty">Error loading pre-sample plot</div>';
                            }}

                            try {{
                                const postPlotJson = {bokeh_post_cnv_distribution_summary};
                                if (postPlotJson && !postPlotJson.error) {{
                                    Bokeh.embed.embed_item(postPlotJson, "post-cnv-plot");
                                }} else {{
                                    document.getElementById('post-cnv-plot').innerHTML = 
                                        '<div class="info-box_empty">' + (postPlotJson && postPlotJson.error ? postPlotJson.error : 'No post-sample plot data') + '</div>';
                                }}
                            }} catch (error) {{
                                console.error("Post sample plot error:", error);
                                document.getElementById('post-cnv-plot').innerHTML = 
                                    '<div class="info-box_empty">Error loading post-sample plot</div>';
                            }}

                            // Add individual karyotype plot handling
                            try {{
                                const preKaryoJson = {bokeh_pre_karyotype};
                                if (preKaryoJson && !preKaryoJson.error) {{
                                    Bokeh.embed.embed_item(preKaryoJson, "pre-karyotype-plot");
                                }} else {{
                                    document.getElementById('pre-karyotype-plot').innerHTML = 
                                        '<div class="info-box_empty">' + (preKaryoJson && preKaryoJson.error ? preKaryoJson.error : 'No pre-sample karyotype data') + '</div>';
                                }}
                            }} catch (error) {{
                                console.error("Pre karyotype plot error:", error);
                                document.getElementById('pre-karyotype-plot').innerHTML = 
                                    '<div class="info-box_empty">Error loading pre-sample karyotype</div>';
                            }}

                            try {{
                                const postKaryoJson = {bokeh_post_karyotype};
                                if (postKaryoJson && !postKaryoJson.error) {{
                                    Bokeh.embed.embed_item(postKaryoJson, "post-karyotype-plot");
                                }} else {{
                                    document.getElementById('post-karyotype-plot').innerHTML = 
                                        '<div class="info-box_empty">' + (postKaryoJson && postKaryoJson.error ? postKaryoJson.error : 'No post-sample karyotype data') + '</div>';
                                }}
                            }} catch (error) {{
                                console.error("Post karyotype plot error:", error);
                                document.getElementById('post-karyotype-plot').innerHTML = 
                                    '<div class="info-box_empty">Error loading post-sample karyotype</div>';
                            }}

                            // Handle differential plot data
                            const diffPlotJson = {bokeh_differential_cnv_distribution_summary};
                            
                            if (diffPlotJson && !diffPlotJson.error) {{
                                // Version check
                                if (Bokeh._version !== diffPlotJson.version) {{
                                    console.warn('Version mismatch: JS ' + Bokeh._version + ' vs Python ' + diffPlotJson.version);
                                }}
                                Bokeh.embed.embed_item(diffPlotJson, "diff-cnv-plot");
                            }} else {{
                                const errorMsg = diffPlotJson && diffPlotJson.error ? diffPlotJson.error : 'Failed to load differential visualization';
                                document.getElementById('diff-cnv-plot').innerHTML = 
                                    '<div class="info-box_empty">' + errorMsg + '</div>';
                            }}

                            // Handle karyotype plot data
                            try {{
                                const karyotypeJson = {bokeh_differential_karyotype};
                                if (karyotypeJson && !karyotypeJson.error) {{
                                    Bokeh.embed.embed_item(karyotypeJson, "diff-karyotype-plot");
                                }} else {{
                                    document.getElementById('diff-karyotype-plot').innerHTML = 
                                        '<div class="info-box_empty">' + (karyotypeJson && karyotypeJson.error ? karyotypeJson.error : 'No karyotype data available') + '</div>';
                                }}
                            }} catch (error) {{
                                console.error("Karyotype plot error:", error);
                                document.getElementById('diff-karyotype-plot').innerHTML = 
                                    '<div class="info-box_empty">Error loading karyotype visualization</div>';
                            }}

                            // Table sorting functionality
                            const getCellValue = (tr, idx) => {{
                                const cell = tr.children[idx];
                                const link = cell.querySelector('a');
                                return link ? link.textContent : cell.innerText || cell.textContent;
                            }};

                            // Fixed comparer function
                            const comparer = (idx, asc) => (a, b) => {{
                                const v1 = getCellValue(asc ? a : b, idx);
                                const v2 = getCellValue(asc ? b : a, idx);
                                if (!isNaN(parseFloat(v1)) && !isNaN(parseFloat(v2))) {{
                                    return parseFloat(v1) - parseFloat(v2);
                                }}
                                return v1.toString().localeCompare(v2);
                            }};

                            const setupTableSorting = (tableClass, defaultSortColumn = 0) => {{
                                const tables = document.querySelectorAll(tableClass);
                                tables.forEach(table => {{
                                    if (!table) return;
                                    
                                    // Track sorted state
                                    let sortColumnIndex = defaultSortColumn;
                                    let sortAscending = true;
                                    
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
                                    
                                    // Initial sort - default column ascending
                                    const defaultHeader = table.querySelector(`th:nth-child(${{defaultSortColumn + 1}})`);
                                    if (defaultHeader) {{
                                        defaultHeader.click();  // Initial sort
                                    }}
                                }});
                            }};

                            // Setup sorting for all table types with appropriate default sorting columns
                            setupTableSorting('.cnv-table', 0);              // Sort CNV summary tables by first column
                            setupTableSorting('.detailed-cnv-table', 1);     // Sort detailed CNV tables by Start position
                            setupTableSorting('.significant-cnvs', 1);       // Sort significant CNVs table
                            setupTableSorting('.nonsignificant-cnvs', 1);    // Sort non-significant CNVs table
                            setupTableSorting('.parameters-table', 0);       // Sort parameters table by parameter name
                            setupTableSorting('.qc-table', 0);               // Sort QC table by first column
                            setupTableSorting('.paired-table', 0);           // Sort paired analysis table by first column

                            // Style sub-dropdowns
                            document.querySelectorAll('.sub-dropdown').forEach(btn => {{
                                // The styling is handled in table_styles.py
                            }});

                        }} catch (error) {{
                            console.error("Initialization error:", error);
                            document.getElementById('diff-cnv-plot').innerHTML = 
                                '<div class="info-box_empty">Error: ' + error.message + '</div>';
                        }}
                    }});
                </script>
            </body>
            </html>
            """
            logging.info(f"Generated summary page for {pair_id}")
            return html_content
            
        except Exception as e:
            logging.error(f"Error generating summary page: {str(e)}")
            raise
    
    def save(self):
        """Save the generated HTML to the pair's directory"""
        try:
            pair_dir = self.output_manager.dir_structure.pair_dirs[self.pair_obj.pair_id]
            output_path = os.path.join(pair_dir, f"summary_page_{self.pair_obj.pair_id}.html")
            
            html_content = self.generate()
            with open(output_path, 'w') as f:
                f.write(html_content)
            logging.info(f"Saved paired summary page to {output_path}")
        except Exception as e:
            logging.error(f"Error saving summary page: {str(e)}")
            raise

    def _get_chromosome_selector(self):
        """Generate chromosome navigation buttons"""
        if not hasattr(self.pair_obj.post, 'available_chromosomes') or not self.pair_obj.post.available_chromosomes:
            logging.warning(f"No chromosomes available for pair {self.pair_obj.pair_id}")
            return '<div class="info-box_empty">No chromosome data available</div>'
        
        buttons = []
        for chrom in self.pair_obj.post.available_chromosomes:
            safe_chrom = chrom.replace(" ", "_")
            href = f"chromosomes_{self.pair_obj.pair_id}/chromosome_{safe_chrom}_{self.pair_obj.pair_id}.html"
            buttons.append(
                f'<button class="chromosome-button" data-chromosome="{chrom}" '
                f'onclick="window.location.href=\'{href}\'">{chrom}</button>'
            )
        return f"""
        <div class="chromosome-selector-container">
            <div class="chromosome-buttons">
                {"\n".join(buttons)}
            </div>
        </div>
        """
