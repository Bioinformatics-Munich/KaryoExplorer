import os
import logging
from pathlib import Path
from typing import Dict, Any
from bokeh.embed import json_item
from src.plots.chromosome_plots import generate_chromosome_plot
from src.tables.table_generator import TableGenerator

class ChromosomePageGeneratorSingle: 
    """Class to generate individual chromosome pages"""
    
    def __init__(self, sample_obj, output_manager):
        self.sample_obj = sample_obj
        self.output_manager = output_manager
        self.table_generator = TableGenerator()  # Add table generator
    
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
        """Generate HTML content for a specific chromosome"""
        try:
            # Filter CNV data for current chromosome
            chrom_cnvs = self.sample_obj.cnv_detection_filtered[
                self.sample_obj.cnv_detection_filtered['Chromosome'] == chromosome
            ]
            
            # Generate chromosome-specific table
            chrom_table = self.table_generator.generate_detailed_cnv_table(chrom_cnvs)
            chrom_table = self._ensure_dict_format(chrom_table)
            
            # Generate chromosome-specific plot
            plot_json = generate_chromosome_plot(
                self.sample_obj.baf_lrr_data,
                self.sample_obj.cnv_detection_filtered,
                chromosome,
                self.sample_obj.sample_id,
                self.sample_obj.roh_bed,
                self.sample_obj.union_bed,
                self.sample_obj.cn_bed,
                cn_summary_data=self.sample_obj.cn_summary_data
            )
            
            # Get home page name for links
            home_page = self.output_manager.get_home_page_name()
            
            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{self.sample_obj.sample_id} - Chromosome {chromosome}</title>
                <link rel="stylesheet" href="../../../../components/css/styles.css">
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
                        <a class="home-link" href="../summary_page_{self.sample_obj.sample_id}.html">Sample Summary</a>
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
                            <!-- Sample ID Box -->
                            <div class="info-box">
                                <h3>Sample Information</h3>
                                <div class="value">{self.sample_obj.sample_id}</div>
                                <div class="label">Sample ID</div>
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
                                            <span class="stat-value">{self.sample_obj.chromosome_stats[chromosome]['total_cnvs']}</span>
                                        </li>
                                        <li>
                                            <span class="stat-label">Duplications</span>
                                            <span class="stat-value">{self.sample_obj.chromosome_stats[chromosome]['duplications']}</span>
                                        </li>
                                        <li>
                                            <span class="stat-label">Deletions</span>
                                            <span class="stat-value">{self.sample_obj.chromosome_stats[chromosome]['deletions']}</span>
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
                                <div class="label">Calculated based on {self.sample_obj.sample_id}</div>
                                <ul class="cnv-stats">
                                    <li>
                                        <span class="stat-label">Mean LRR</span>
                                        <span class="stat-value {self.get_lrr_status(self.sample_obj.lrr_stats[chromosome]['mean'], 'mean')}">
                                            {self.sample_obj.lrr_stats[chromosome]['mean']:.3f}
                                        </span>
                                    </li>
                                    <li>
                                        <span class="stat-label">Median LRR</span>
                                        <span class="stat-value {self.get_lrr_status(self.sample_obj.lrr_stats[chromosome]['median'], 'median')}">
                                            {self.sample_obj.lrr_stats[chromosome]['median']:.3f}
                                        </span>
                                    </li>
                                    <li>
                                        <span class="stat-label">StdDev LRR</span>
                                        <span class="stat-value {self.get_lrr_status(self.sample_obj.lrr_stats[chromosome]['std'], 'std')}">
                                            {self.sample_obj.lrr_stats[chromosome]['std']:.3f}
                                        </span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chromosome-cnv-section">
                        <h3 class="section-title">Chromosome {chromosome} BAF/LRR Plots</h3>
                    <div id="chromosome-plot" class="responsive-plot_chromosome"></div>
                    </div>
                    
                    <div class="chromosome-cnv-section">
                        <h3 class="section-title">Chromosome {chromosome} CNV Details</h3>
                        <div style="margin-top: 20px;">
                            <!-- Significant CNVs -->
                            <div class="summary_single-dropdown-section active">
                                <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                                    Significant CNVs (p < 0.05)
                                    <span class="dropdown-arrow">▲</span>
                                </button>
                                <div class="summary_single-dropdown-content">
                                    {chrom_table['significant']}
                                </div>
                            </div>
                            
                            <!-- Non-significant CNVs in dropdown -->
                            <div class="summary_single-dropdown-section">
                                <button class="summary_single-dropdown-toggle" onclick="toggleDropdown(this)">
                                    Non-significant CNVs (p ≥ 0.05)
                                    <span class="dropdown-arrow">▼</span>
                                </button>
                                <div class="summary_single-dropdown-content">
                                    {chrom_table['nonsignificant']}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer -->
                <div id="footer-placeholder"></div>

                <script>
                    // Toggle dropdown function
                    function toggleDropdown(button) {{
                        const dropdownSection = button.closest('.summary_single-dropdown-section') || 
                                              button.closest('.single_chromosome-dropdown-section');
                        if (!dropdownSection) return;
                        
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

                    document.addEventListener("DOMContentLoaded", function() {{
                        // Load footer
                        fetch('../../../../components/footer.html')
                            .then(response => response.text())
                            .then(data => document.getElementById('footer-placeholder').innerHTML = data);

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

                        // Handle plot embedding
                         const plotData = JSON.parse(`{plot_json}`);
                        if(plotData && !plotData.error) {{
                            Bokeh.embed.embed_item(plotData, "chromosome-plot");
                        }} else {{
                            const errorMessage = plotData?.error || 'Failed to load chromosome plot';
                            document.getElementById('chromosome-plot').innerHTML = `
                                <div class="info-box error">
                                    <h3>Plot Loading Error</h3>
                                    <p>${{errorMessage}}</p>
                                </div>
                            `;
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

                        // Setup sorting for the chromosome-specific CNV table
                        setupTableSorting('.detailed-cnv-table', 1);  // Sort by Start position by default
                    }});
                </script>
            </body>
            </html>
            """
        except Exception as e:
            logging.error(f"Error generating chromosome {chromosome} page: {str(e)}")
            return f"<html><body>Error generating chromosome {chromosome} page</body></html>"

    def save_chromosome_pages(self):
        """Save all chromosome pages for the sample"""
        if not self.sample_obj.available_chromosomes:
            logging.warning(f"No chromosomes available for {self.sample_obj.sample_id}")
            return

        sample_dir = self.output_manager.dir_structure.sample_dirs[self.sample_obj.sample_id]
        chrom_dir = os.path.join(sample_dir, f"chromosomes_{self.sample_obj.sample_id}")
        
        for chrom in self.sample_obj.available_chromosomes:
            try:
                content = self.generate_chromosome_page(chrom)
                safe_chrom = chrom.replace(" ", "_")
                output_path = os.path.join(chrom_dir, f"chromosome_{safe_chrom}_{self.sample_obj.sample_id}.html")
                
                with open(output_path, 'w') as f:
                    f.write(content)
                logging.info(f"Saved chromosome {chrom} page to {output_path}")
            except Exception as e:
                logging.error(f"Failed to save chromosome {chrom} page: {str(e)}")
    
    def get_lrr_status(self, value, metric):
        """Determine if LRR statistic is within acceptable range"""
        try:
            val = float(value)
            if metric == 'std':
                return 'good' if val < 0.3 else 'bad'
            elif metric == 'mean':
                return 'good' if -0.15 <= val <= 0.15 else 'bad'
            elif metric == 'median':
                return 'good' if -0.15 <= val <= 0.15 else 'bad'
            return ''
        except (ValueError, TypeError):
            return ''
