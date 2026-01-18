import logging
from pathlib import Path
from src.tables.table_generator import TableGenerator
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

class HomePageGenerator:
    """Class to generate the paired analysis home page HTML content"""
    
    def __init__(self, pre_samples, post_samples, pairs, output_manager, parameters):
        """Initialize with sample data and output manager"""
        self.pre_samples = pre_samples
        self.post_samples = post_samples
        self.pairs = pairs
        self.output_manager = output_manager
        self.table_generator = TableGenerator()
        self.parameters = parameters
    
    def generate(self) -> str:
        """Generate the complete home page HTML"""
        try:
            # Generate parameter sections
            params = self.parameters
            dropdown_parameters_html = ""
            info_boxes_html = ""
            
            if params:
                # Generate parameters dropdown content
                parameters_list = []
                for section, values in params.data.items():
                    section_html = [f"<div class='parameter-section'><h4>{section.replace('_', ' ').title()}</h4>"]
                    for key, value in values.items():
                        if isinstance(value, dict):
                            section_html.append("<div class='nested-parameters'>")
                            for subkey, subvalue in value.items():
                                section_html.append(f"""
                                <div class="parameter-item">
                                    <span class="stat-label">{subkey.replace('_', ' ').title()}:</span>
                                    <span class="stat-value">{subvalue}</span>
                                </div>
                                """)
                            section_html.append("</div>")
                        else:
                            section_html.append(f"""
                            <div class="parameter-item">
                                <span class="stat-label">{key.replace('_', ' ').title()}:</span>
                                <span class="stat-value">{value}</span>
                            </div>
                            """)
                    section_html.append("</div>")
                    parameters_list.extend(section_html)
                
                dropdown_parameters_html = f"""
                <div class="parameters-container">
                    {"".join(parameters_list)}
                </div>
                """

            # Generate info boxes (same as single page)
            info_boxes_html = f"""
            <div class="info-boxes-container">
                <!-- Left Column - Pipeline Mode -->
                <div class="info-column left" style="margin-right: auto;">
                    <div class="info-box">
                        <h3>Pipeline Mode</h3>
                        <div class="value">Paired Analysis</div>
                        <div class="label">Analysis Type</div>
                    </div>
                </div>
                
                <!-- Right Column - Project Details -->
                <div class="info-column right" style="margin-left: auto;">
                    <div class="info-box">
                        <h3>Project Details</h3>
                        <div class="value">{params.project_ID}</div>
                        <div class="label">Project ID</div>
                        
                        <div class="cnv-stats">
                            <h3>Additional Information</h3>
                            <ul>
                                <li>
                                    <span class="stat-label">Recipient</span>
                                    <span class="stat-value">{params.responsible_person}</span>
                                </li>
                                <li>
                                    <span class="stat-label">Reference Genome</span>
                                    <span class="stat-value">{params.reference_genome}</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            """

            # Generate individual samples table
            individual_data = self._prepare_individual_data()
            individual_table = self.table_generator.generate_individual_qc_table(individual_data)
            
            # Generate paired analyses table
            paired_data = self._prepare_paired_data()
            paired_table = self.table_generator.generate_paired_analysis_table(paired_data, self.output_manager)
            
            # Get home page name for links
            home_page = self.output_manager.get_home_page_name()
            
            # Define header content directly (from styling.py)
            header_content = f"""<nav class="navbar">
    <div class="logo-container left">
        <img src="components/logo/left_icon.png" alt="Institution Logo">
    </div>

    <div class="nav-center">
        <a class="home-link" href="{home_page}">Home</a>
        <a class="home-link" href="components/info.html" title="Documentation">
            <i class="fas fa-info-circle" style="font-size: 0.9em"></i>
        </a>
    </div>

    <div class="logo-container right">
        <img src="components/logo/right_icon.png" alt="Project Logo">
    </div>
</nav>"""

            # Use footer placeholder to load from footer.html
            footer_placeholder = '<div id="footer-placeholder"></div>'
            
            # Generate the complete HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="components/css/styles.css">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <style>
                  @media print {{
                    #header-placeholder,
                    #download-pdf-btn{{display:none !important;}}
                  }}
                  @page{{size:A2 portrait; margin:10mm;}}
                </style>
            </head>
            <body>
                <!-- Header -->
                {header_content}
                
                <!-- Main Content -->
                <div class="content-container">
                    
                    <!-- PDF Button -->
                    <div class="nav-buttons_info_page" style="text-align: right; margin: 10px 0;">
                        <button id="download-pdf-btn" class="action-button_info_page">
                            <i class="fas fa-file-pdf"></i> Save / Print PDF
                        </button>
                    </div>
                    
                    <!-- Parameters Dropdown -->
                    <div class="dropdown-section">
                        <button class="dropdown-toggle">Full Analysis Parameters ▼</button>
                        <div class="dropdown-content">
                            {dropdown_parameters_html}
                        </div>
                    </div>
                    {info_boxes_html}

                    <!-- Individual Samples QC -->
                    <div class="dropdown-section">
                        <button class="dropdown-toggle">Individual Samples QC Data ▼</button>
                        <div class="dropdown-content">
                            {individual_table}
                        </div>
                    </div>
                    
                    <!-- Paired Analyses -->
                    <h2>Available Paired CNV Analyses</h2>
                    {paired_table}
                </div>
                
                <!-- Footer -->
                {footer_placeholder}
                
                <!-- Scripts -->
                <script>
                    // Load footer from external file
                    fetch('components/footer.html')
                        .then(response => response.text())
                        .then(data => document.getElementById('footer-placeholder').innerHTML = data);
                </script>
                <script>
                    // PDF conversion function for tables
                    async function prepareForPrint() {{
                      try {{
                        // Wait a bit to make sure all content is loaded
                        await new Promise(r => setTimeout(r, 300));
                        return true;
                      }} catch (err) {{
                        console.error('Print preparation error:', err);
                        return false;
                      }}
                    }}
                
                    // PDF button functionality
                    document.addEventListener('DOMContentLoaded', () => {{
                      const btn = document.getElementById('download-pdf-btn');
                      if (!btn) return;

                      btn.addEventListener('click', async () => {{
                        await prepareForPrint();
                        window.print();
                      }});
                    }});
                    
                    // Dropdown functionality
                    document.querySelectorAll('.dropdown-toggle').forEach(button => {{
                        button.addEventListener('click', () => {{
                            const content = button.nextElementSibling;
                            content.style.display = content.style.display === 'block' ? 'none' : 'block';
                            button.innerHTML = button.innerHTML.includes('▼') 
                                ? button.innerHTML.replace('▼', '▲') 
                                : button.innerHTML.replace('▲', '▼');
                        }});
                    }});

                    // Table sorting functionality
                    document.addEventListener('DOMContentLoaded', function() {{
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
                            const table = document.querySelector(tableClass);
                            if (!table) return;

                            table.querySelectorAll('th').forEach(th => {{
                                th.style.cursor = 'pointer';
                                th.addEventListener('click', (() => {{
                                    const tbody = table.querySelector('tbody');
                                    Array.from(tbody.querySelectorAll('tr'))
                                        .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
                                        .forEach(tr => tbody.appendChild(tr));
                                    
                                    // Update sorting indicators
                                    const headers = table.querySelectorAll('th');
                                    headers.forEach(header => {{
                                        header.classList.remove('sorted-asc', 'sorted-desc');
                                    }});
                                    th.classList.add(this.asc ? 'sorted-asc' : 'sorted-desc');
                                }}));
                            }});

                            // Initial sort
                            const defaultHeader = table.querySelector(`th:nth-child(${{defaultSortColumn + 1}})`);
                            if (defaultHeader) {{
                                defaultHeader.click();
                            }}
                        }};

                        // Setup sorting for both tables
                        setupTableSorting('.qc-table', 0);      // Sort QC table by Sample Name
                    }});
                </script>
            </body>
            </html>
            """
            
            logging.info("Successfully generated paired home page HTML")
            return html_content
            
        except Exception as e:
            logging.error(f"Error generating home page: {str(e)}")
            raise
    
    def _prepare_individual_data(self) -> List[dict]:
        """Prepare data for individual QC table"""
        data = []
        # Add pre samples
        for sample in self.pre_samples:
            # Calculate total and significant CNVs from cn_summary_data if available
            total_cnvs = 0
            significant_cnvs = 0
            
            if hasattr(sample, 'cn_summary_data') and sample.cn_summary_data is not None and not sample.cn_summary_data.empty:
                # Filter out normal copy numbers first (to match how the summary tables count)
                filtered_data = sample.cn_summary_data.copy()
                
                # Determine if Type column exists, if not create it based on CopyNumber/CN
                if 'Type' not in filtered_data.columns:
                    # Find copy number column
                    cn_col = None
                    for col in ['CopyNumber', 'CN', 'Copy_Number']:
                        if col in filtered_data.columns:
                            cn_col = col
                            break
                    
                    if cn_col:
                        # Create Type column
                        filtered_data['Type'] = filtered_data[cn_col].apply(
                            lambda x: 'Deletion' if x < 2 else 'Duplication' if x > 2 else 'Normal'
                        )
                
                # If Type column exists, filter out Normal entries
                if 'Type' in filtered_data.columns:
                    filtered_data = filtered_data[filtered_data['Type'] != 'Normal']
                
                # Count total CNVs from filtered data
                total_cnvs = len(filtered_data)
                
                # Count significant CNVs if P_value column exists
                if 'P_value' in filtered_data.columns:
                    significant_cnvs = len(filtered_data[filtered_data['P_value'] < 0.05])
                # Try to calculate P_value from quality score if not present
                else:
                    for qs_col in ['Quality', 'QS', 'QualityScore']:
                        if qs_col in filtered_data.columns:
                            # Create P_value column
                            p_values = filtered_data[qs_col].apply(
                                lambda q: 10 ** (-q/10) if pd.notnull(q) else None
                            )
                            significant_cnvs = sum(p < 0.05 for p in p_values if p is not None)
                            break
            
            data.append({
                'Sample Name': sample.sample_id,
                'Type': 'PRE',
                'Sex': sample.pre_sex,
                'Call Rate': sample.call_rate,
                'Call Rate Filtered': sample.call_rate_filt,
                'LRR Stdev': sample.LRR_stdev,
                'total_cnvs': total_cnvs,
                'significant_cnvs': significant_cnvs
            })
            
        # Add post samples
        for sample in self.post_samples:
            # Calculate total and significant CNVs from cn_summary_data if available
            total_cnvs = 0
            significant_cnvs = 0
            
            if hasattr(sample, 'cn_summary_data') and sample.cn_summary_data is not None and not sample.cn_summary_data.empty:
                # Filter out normal copy numbers first (to match how the summary tables count)
                filtered_data = sample.cn_summary_data.copy()
                
                # Determine if Type column exists, if not create it based on CopyNumber/CN
                if 'Type' not in filtered_data.columns:
                    # Find copy number column
                    cn_col = None
                    for col in ['CopyNumber', 'CN', 'Copy_Number']:
                        if col in filtered_data.columns:
                            cn_col = col
                            break
                    
                    if cn_col:
                        # Create Type column
                        filtered_data['Type'] = filtered_data[cn_col].apply(
                            lambda x: 'Deletion' if x < 2 else 'Duplication' if x > 2 else 'Normal'
                        )
                
                # If Type column exists, filter out Normal entries
                if 'Type' in filtered_data.columns:
                    filtered_data = filtered_data[filtered_data['Type'] != 'Normal']
                
                # Count total CNVs from filtered data
                total_cnvs = len(filtered_data)
                
                # Count significant CNVs if P_value column exists
                if 'P_value' in filtered_data.columns:
                    significant_cnvs = len(filtered_data[filtered_data['P_value'] < 0.05])
                # Try to calculate P_value from quality score if not present
                else:
                    for qs_col in ['Quality', 'QS', 'QualityScore']:
                        if qs_col in filtered_data.columns:
                            # Create P_value column
                            p_values = filtered_data[qs_col].apply(
                                lambda q: 10 ** (-q/10) if pd.notnull(q) else None
                            )
                            significant_cnvs = sum(p < 0.05 for p in p_values if p is not None)
                            break
            
            data.append({
                'Sample Name': sample.sample_id,
                'Type': 'POST',
                'Sex': sample.pre_sex,
                'Call Rate': sample.call_rate,
                'Call Rate Filtered': sample.call_rate_filt,
                'LRR Stdev': sample.LRR_stdev,
                'total_cnvs': total_cnvs,
                'significant_cnvs': significant_cnvs
            })
        return data
    
    def _prepare_paired_data(self) -> List[dict]:
        """Prepare grouped data for paired analysis table"""
        grouped = {}
        for pair in self.pairs:
            key = pair.pre.sample_id
            if key not in grouped:
                grouped[key] = {
                    'Pre Sample': pair.pre.sample_id,
                    'Pre Sex': pair.pre.pre_sex,
                    'Posts': []
                }
            grouped[key]['Posts'].append({
                'Post Sample': pair.post.sample_id,
                'Post Sex': pair.post.pre_sex,
                'PI_HAT': pair.PI_HAT,
                'Total CNVs': pair.total_cnvs,
                'Significant CNVs': getattr(pair, 'significant_cnvs', 0),
                'Pair ID': pair.pair_id,
                'Pair Dir': self.output_manager.dir_structure.pair_dirs[pair.pair_id]
            })
        return list(grouped.values())
    
    def save(self, output_path: str):
        """Save the generated HTML to a file"""
        try:
            html_content = self.generate()
            with open(output_path, 'w') as f:
                f.write(html_content)
            logging.info(f"Saved paired home page to {output_path}")
        except Exception as e:
            logging.error(f"Error saving home page: {str(e)}")
            raise
