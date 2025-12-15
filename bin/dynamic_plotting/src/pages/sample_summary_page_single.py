import os
import logging
import json
from pathlib import Path
from typing import Dict, Any
from src.tables.table_generator import TableGenerator
from src.plots.cnv_distribution import generate_cnv_distribution_plot
from src.plots.karyotype import generate_karyotype_plot
from src.utils.css_styles.table_styles import get_table_styles
from bokeh.embed import json_item

class SampleSummaryGeneratorSingle:
    """Class to generate single sample summary pages"""
    
    def __init__(self, sample_obj, output_manager):
        """Initialize with sample object and output manager"""
        self.sample_obj = sample_obj
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
            lrr_stdev = getattr(self.sample_obj, 'LRR_stdev', 'N/A')
            lrr_stdev = f"{float(lrr_stdev):.4g}" if lrr_stdev != 'N/A' else 'N/A'
            lrr_color = '#e74c3c' if (lrr_stdev != 'N/A' and float(lrr_stdev) > 0.3) else '#2ecc71'
            
            # Generate CNV summary table
            cnv_table = self.table_generator.generate_cnv_summary_table(self.sample_obj.cnv_detection_filtered)
            
            try:
                cnv_json_str = generate_cnv_distribution_plot(
                    self.sample_obj.cnv_detection_filtered,
                    self.sample_obj.sample_id,
                    self.sample_obj.available_chromosomes,
                    gender=getattr(self.sample_obj, "pre_sex", None),
                )
                if not isinstance(cnv_json_str, str):
                    cnv_json_str = json.dumps(cnv_json_str)

                bokeh_cnv_distribution_summary = cnv_json_str

            except Exception as e:
                logging.error(f"Error generating CNV plot: {e}")
                bokeh_cnv_distribution_summary = json.dumps(
                    {"error": "Failed to generate CNV distribution visualization"}
                )
            
            try:
                karyotype_json = generate_karyotype_plot(
                    self.sample_obj.cnv_detection_filtered,
                    self.sample_obj.sample_id,
                    gender=getattr(self.sample_obj, 'pre_sex', None),
                    reference_genome='GRCh37',
                    mode='single',
                    available_chromosomes=self.sample_obj.available_chromosomes
                )
            except Exception as e:
                logging.error(f"Error generating karyotype plot: {str(e)}")
                karyotype_json = json.dumps({'error': 'Failed to generate karyotype visualization'})
            
            safe_bokeh_cnv = bokeh_cnv_distribution_summary  
            safe_karyotype = karyotype_json 
            
            # Generate detailed CNV tables (significant and non-significant)
            detailed_cnv_tables = self.table_generator.generate_detailed_cnv_table(
                self.sample_obj.cnv_detection_filtered
            )
            detailed_cnv_tables = self._ensure_dict_format(detailed_cnv_tables)
            
            significant_cnv_table = detailed_cnv_tables['significant']
            nonsignificant_cnv_table = detailed_cnv_tables['nonsignificant']
            
            # Get home page name for links
            home_page = self.output_manager.get_home_page_name()
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{self.sample_obj.sample_id} - Single Analysis</title>
                <link rel="stylesheet" href="../../../components/css/styles.css">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
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
                        <a class="home-link" href="./summary_page_{self.sample_obj.sample_id}.html">Sample Summary</a>
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
                    <!-- PDF Button (moved from navbar to under main content) -->
                    <div class="nav-buttons_info_page" style="text-align: right; margin: 10px 0;">
                        <button id="download-pdf-btn" class="action-button_info_page">
                            <i class="fas fa-file-pdf"></i> Save / Print PDF
                        </button>
                    </div>
                    
                    <div class="layout-wrapper">
                        <div class="left-info-group">
                            <!-- Pair ID Box -->
                            <div class="info-box">
                                <h3>Sample Information</h3>
                                <div class="value">{self.sample_obj.sample_id}</div>
                                <div class="label">Sample ID</div>
                                
                                <div class="value" style="margin-top: 15px;">{getattr(self.sample_obj, 'pre_sex', 'N/A')}</div>
                                <div class="label">Sex</div>
                                
                                <div class="value">{getattr(self.sample_obj, 'sample_type', 'N/A')}</div>
                                <div class="label">Sample Type</div>
                            </div>
                        </div>

                        <div class="right-info-group">
                            <div class="info-box lrr-box">
                                <strong>LRR StDev</strong>
                                <span class="lrr-value" style="color: {lrr_color}">
                                    {lrr_stdev if lrr_stdev != 'N/A' else 'N/A'}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- CNV Statistics Section -->
                    <div class="stats-container">
                        <h3 class="section-title">CNV Statistics</h3>
                        <div class="table-wrapper horizontal-scroll">
                            {cnv_table}
                        </div>
                    </div>
                    
                    <!-- CNV Distribution Section -->
                    <div class="plot-section">
                        <h3 class="section-title">CNV Distribution</h3>
                        <div class="plot-container">
                            <div id="cnv-distribution-plot" class="responsive-plot"></div>
                        </div>
                    </div>
                    
                    <!-- Karyotype Overview Section -->
                    <div class="plot-section">
                        <h3 class="section-title">Karyotype Overview</h3>
                        <div class="plot-container">
                            <div id="karyotype-plot" class="responsive-plot_karyotype"></div>
                        </div>           
                        
                        <h4 class="subsection-title">Chromosome details</h4>
                        <!-- Add chromosome selector -->
                        {self._get_chromosome_selector()}
                    </div>
                    
                     <div class="plot-section">   
                        <!-- New Detailed CNV Table -->
                        <div class="cnv-details-section">
                            <h4 class="subsection-title">CNV Details</h4>
                            
                            <!-- Significant CNVs in dropdown (expanded by default) -->
                            <div class="summary_single-dropdown-section active">
                                <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                                    Significant CNVs (p < 0.05)
                                    <span class="dropdown-arrow">▲</span>
                                </button>
                                <div class="summary_single-dropdown-content">
                                    {significant_cnv_table}
                                </div>
                            </div>
                            
                            <!-- Non-significant CNVs in dropdown -->
                            <div class="summary_single-dropdown-section">
                                <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                                    Non-significant CNVs (p ≥ 0.05)
                                    <span class="dropdown-arrow">▼</span>
                                </button>
                                <div class="summary_single-dropdown-content">
                                    {nonsignificant_cnv_table}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                </div>

                <!-- Footer -->
                <div id="footer-placeholder"></div>

                <!-- Scripts -->
                <script>
                  function toggleDropdown(button) {{
                    const dropdownSection = button.closest('.summary_single-dropdown-section');
                    dropdownSection.classList.toggle('active');
                    
                    // Update arrow icon
                    const arrow = button.querySelector('.dropdown-arrow');
                    if (dropdownSection.classList.contains('active')) {{
                        arrow.textContent = '▲';
                    }} else {{
                        arrow.textContent = '▼';
                    }}
                  }}
                  
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
                </script>
                <script>
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
                  }});
                </script>
                <script>
                    document.addEventListener("DOMContentLoaded", async function() {{
                        try {{
                            // Load footer
                            fetch('../../../components/footer.html')
                                .then(response => response.text())
                                .then(data => document.getElementById('footer-placeholder').innerHTML = data);

                            // FIX 2: Directly use the JSON objects
                            let cnvPlotData = {safe_bokeh_cnv};
                            let karyotypePlotData = {safe_karyotype};

                            // FIX 3: Handle non-object cases
                            if (typeof cnvPlotData === 'string') {{
                                try {{ cnvPlotData = JSON.parse(cnvPlotData); }}
                                catch (e) {{ 
                                    console.error("CNV JSON parse error:", e);
                                    cnvPlotData = {{ error: 'Invalid CNV data' }};
                                }}
                            }}
                            
                            if (typeof karyotypePlotData === 'string') {{
                                try {{ karyotypePlotData = JSON.parse(karyotypePlotData); }}
                                catch (e) {{
                                    console.error("Karyotype JSON parse error:", e);
                                    karyotypePlotData = {{ error: 'Invalid karyotype data' }};
                                }}
                            }}

                            // Fix 4: Handle boolean values safely
                            const cnvPlotJson = cnvPlotData.error ? cnvPlotData : {{
                                ...cnvPlotData,
                                version: cnvPlotData.version || '3.3.4'
                            }};
                            
                            const karyotypePlotJson = karyotypePlotData.error ? karyotypePlotData : {{
                                ...karyotypePlotData,
                                version: karyotypePlotData.version || '3.3.4'
                            }};

                            // Embed plots with version safety
                            try {{
                                if (!cnvPlotJson.error) {{
                                    Bokeh.embed.embed_item(cnvPlotJson, "cnv-distribution-plot");
                                }} else {{
                                    throw new Error(cnvPlotJson.error);
                                }}
                            }} catch (error) {{
                                console.error("CNV Plot Error:", error);
                                document.getElementById('cnv-distribution-plot').innerHTML = 
                                    `<div class="info-box_empty">${{error.message}}</div>`;
                            }}

                            if (karyotypePlotJson && !karyotypePlotJson.error) {{
                                if (Bokeh.version !== karyotypePlotJson.version) {{
                                    console.warn(`Version mismatch: JS ${{Bokeh.version}} vs Python ${{karyotypePlotJson.version}}`);
                                }}
                                Bokeh.embed.embed_item(karyotypePlotJson, "karyotype-plot");
                            }} else {{
                                const errorMsg = karyotypePlotJson?.error || 'Failed to load karyotype visualization';
                                document.getElementById('karyotype-plot').innerHTML = 
                                    `<div class="info-box_empty">${{errorMsg}}</div>`;
                            }}

                            // Table sorting functionality
                            const getCellValue = (tr, idx) => {{
                                const cell = tr.children[idx];
                                // Handle cells with links
                                const link = cell.querySelector('a');
                                return link ? link.textContent : cell.innerText || cell.textContent;
                            }};
                            
                            const comparer = (idx, asc) => (a, b) => {{
                                const v1 = getCellValue(asc ? a : b, idx);
                                const v2 = getCellValue(asc ? b : a, idx);
                                // Parse as float for numeric columns
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
                            
                            // Setup sorting for all tables
                            setupTableSorting('.cnv-table', 0);      // Sort CNV tables by first column
                            setupTableSorting('.detailed-cnv-table', 1);  // Sort detailed CNV table by Start position
                            setupTableSorting('.significant-cnvs', 1);  // Sort significant CNVs table by Start position
                            setupTableSorting('.nonsignificant-cnvs', 1);  // Sort non-significant CNVs table by Start position

                            // Add chromosome button interactions
                            document.querySelectorAll('.chromosome-button').forEach(button => {{
                                button.addEventListener('click', function() {{
                                    document.querySelectorAll('.chromosome-button').forEach(btn => {{
                                        btn.classList.remove('active');
                                    }});
                                    this.classList.add('active');
                                    const chromosome = this.dataset.chromosome;
                                    console.log('Selected chromosome:', chromosome);
                                }});
                            }});
                        }} catch (error) {{
                            console.error("Initialization error:", error);
                            document.getElementById('cnv-distribution-plot').innerHTML = 
                                `<div class="info-box_empty">Error: ${{error.message}}</div>`;
                            document.getElementById('karyotype-plot').innerHTML = 
                                `<div class="info-box_empty">Error: ${{error.message}}</div>`;
                        }}
                    }});
                </script>
            </body>
            </html>
            """
            
            logging.info(f"Generated summary page for {self.sample_obj.sample_id}")
            return html_content
            
        except Exception as e:
            logging.error(f"Error generating summary page: {str(e)}")
            return f"""
            <!DOCTYPE html>
            <html>
            <body>
                <div class="error-box">
                    Error generating summary: {str(e)}
                </div>
            </body>
            </html>
            """
    
    def save(self):
        """Save the generated HTML to the sample's directory"""
        try:
            sample_dir = self.output_manager.dir_structure.sample_dirs[self.sample_obj.sample_id]
            output_path = os.path.join(sample_dir, f"summary_page_{self.sample_obj.sample_id}.html")
            
            html_content = self.generate()
            with open(output_path, 'w') as f:
                f.write(html_content)
            logging.info(f"Saved single sample summary page to {output_path}")
        except Exception as e:
            logging.error(f"Error saving summary page: {str(e)}")
            raise

    def _get_chromosome_selector(self):
        """Generate HTML for chromosome selector"""
        
        # Relative URL Construction (in SampleSummaryGeneratorSingle._get_chromosome_selector()):
        
        if not self.sample_obj.available_chromosomes:
            return '<div class="info-box_empty">No chromosome data available</div>'
        buttons = []
        sample_id = self.sample_obj.sample_id
        for chrom in self.sample_obj.available_chromosomes:
            safe_chrom = chrom.replace(" ", "_")
            # Relative path from summary page to chromosome pages
            href = f"chromosomes_{sample_id}/chromosome_{safe_chrom}_{sample_id}.html"
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
