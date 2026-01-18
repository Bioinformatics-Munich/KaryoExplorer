import logging
from pathlib import Path
from src.tables.table_generator import TableGenerator
from datetime import datetime

class HomePageGenerator:
    """Class to generate the home page HTML content"""
    
    def __init__(self, samples, output_manager):
        """Initialize with sample data and output manager"""
        self.samples = samples
        self.output_manager = output_manager
        self.table_generator = TableGenerator()
    
    def _prepare_sample_data(self):
        """Prepare sample data for table generation"""
        return [{
            'sample_id': sample.sample_id,
            'sample_type': sample.sample_type,
            'pre_sample': sample.pre_sample,
            'pre_sex': sample.pre_sex,
            'call_rate': sample.call_rate,
            'call_rate_filt': sample.call_rate_filt,
            'LRR_stdev': sample.LRR_stdev,
            'total_cnvs': sample.total_cnvs,
            'significant_cnvs': getattr(sample, 'significant_cnvs', 0)  # Include significant CNVs
        } for sample in self.samples]

    def generate(self) -> str:
        """Generate the complete home page HTML"""
        try:
            # Generate sample table
            sample_table = self.table_generator.generate_sample_table(self._prepare_sample_data(), self.output_manager)
            
            # Get parameters from first sample
            params = self.samples[0].parameters if self.samples else None
            
            # Generate parameters dropdown content
            dropdown_parameters_html = ""
            if params:
                # Convert all parameters to formatted HTML
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

            # Generate info boxes for key parameters
            info_boxes_html = f"""
            <div class="info-boxes-container">
                <!-- Left Column - Pipeline Mode -->
                <div class="info-column left" style="margin-right: auto;">
                    <div class="info-box">
                        <h3>Pipeline Mode</h3>
                        <div class="value">Single Analysis</div>
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

            # Generate the complete HTML
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

                    {sample_table}
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

                    // Add dropdown toggle functionality
                    document.querySelectorAll('.dropdown-toggle').forEach(button => {{
                        button.addEventListener('click', () => {{
                            const content = button.nextElementSibling;
                            content.style.display = content.style.display === 'block' ? 'none' : 'block';
                            button.querySelector('▼').textContent = content.style.display === 'block' ? '▲' : '▼';
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

                        document.querySelectorAll('.cnv-table th').forEach(th => {{
                            th.addEventListener('click', (() => {{
                                const table = th.closest('table');
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

                        // Initial sort by Sample Name (first column)
                        const sampleNameHeader = document.querySelector('.cnv-table th');
                        if (sampleNameHeader) {{
                            sampleNameHeader.click();
                        }}
                    }});
                </script>
            </body>
            </html>
            """
            
            logging.info("Successfully generated home page HTML")
            return html_content
            
        except Exception as e:
            logging.error(f"Error generating home page: {str(e)}")
            raise
    
    def save(self, output_path: str):
        """Save the generated HTML to a file"""
        try:
            html_content = self.generate()
            with open(output_path, 'w') as f:
                f.write(html_content)
            logging.info(f"Saved home page to {output_path}")
        except Exception as e:
            logging.error(f"Error saving home page: {str(e)}")
            raise
