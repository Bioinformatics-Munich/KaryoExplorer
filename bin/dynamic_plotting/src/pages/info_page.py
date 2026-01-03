import json
from src.plots.karyotype import generate_karyotype_plot
from src.plots.cnv_distribution import generate_cnv_distribution_plot
from src.plots.chromosome_plots import generate_chromosome_plot
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from src.utils.simulated_sample_class import (
    SimulatedSingleSample,
    SimulatedPairedPreSample,
    SimulatedPairedPostSample,
    SimulatedPairedClass,
    _classify_csvs,
    load_simulated_samples
)

class InfoPageGenerator:
    def __init__(self,
                 output_manager,
                 single_simulated: list = None,
                 paired_simulated: list = None,
                 support_email: str = ""):
        self.output_manager      = output_manager
        self.directory_structure = output_manager.dir_structure
        self.components_dir      = Path(self.directory_structure.components_dir)
        self.support_email       = support_email

        self.single_simulated = single_simulated or []
        self.paired_simulated = paired_simulated or []

        logging.info("Initialized InfoPageGenerator with components dir: %s",
                     self.components_dir)
    def _to_json(self, obj):
        """Return a JSON string ready for the template."""
        return obj if isinstance(obj, str) else json.dumps(obj)


    def generate(self) -> str:
        """Generate complete information page HTML"""
        logging.info("Generating information page HTML content")
        try:
            # Get metrics for all simulated samples
            single_metrics, paired_metrics = self._get_all_simulated_metrics()
            
            # Generate HTML components
            sim_metrics_html = self._generate_simulated_metrics_html(single_metrics, paired_metrics)
            info_box = self._get_info_box_content(single_metrics, paired_metrics)
            
            # Get karyotype and chromosome plots as JSON
            karyotype_json = self._to_json(generate_karyotype_plot(
                self.single_simulated[0].cnv_detection_filtered,
                self.single_simulated[0].sample_id,
                gender=getattr(self.single_simulated[0], 'pre_sex', None),
                reference_genome='GRCh37',
                mode='single',
                available_chromosomes=self.single_simulated[0].available_chromosomes
            ))
            
            # Handle CNV distribution plot differently since it already returns a JSON string
            try:
                cnv_distribution_json = generate_cnv_distribution_plot(
                    self.single_simulated[0].cnv_detection_filtered,
                    self.single_simulated[0].sample_id,
                    self.single_simulated[0].available_chromosomes,
                    gender=getattr(self.single_simulated[0], 'pre_sex', None)
                )
                # Log what we received
                logging.info(f"CNV distribution type: {type(cnv_distribution_json)}")
                logging.info(f"CNV distribution starts with: {cnv_distribution_json[:100] if isinstance(cnv_distribution_json, str) else 'Not a string'}")
                
                # Ensure it's a string (no need to convert again)
                if not isinstance(cnv_distribution_json, str):
                    cnv_distribution_json = json.dumps(cnv_distribution_json)
            except Exception as e:
                logging.error(f"Error generating CNV distribution plot: {str(e)}")
                cnv_distribution_json = json.dumps({'error': f'Failed to generate CNV distribution: {str(e)}'})
            
            # Include cn_summary_data in all chromosome plot calls
            chromosome_json = self._to_json(generate_chromosome_plot(
                self.single_simulated[0].baf_lrr_data,
                self.single_simulated[0].cnv_detection_filtered,
                self.single_simulated[0].available_chromosomes[0],
                self.single_simulated[0].sample_id,
                self.single_simulated[0].roh_bed,
                self.single_simulated[0].union_bed,
                self.single_simulated[0].cn_bed,
                cn_summary_data=self.single_simulated[0].cn_summary_data
            ))
            
            sections = self._get_info_sections()
            sections_html = self._generate_sections(
                sections,
                karyotype_json,
                cnv_distribution_json,
                chromosome_json
            )
            
            # Get home page name for links
            home_page = self.output_manager.get_home_page_name()
            
            # Define header content directly (from styling.py)
            header_content = f"""<nav class="navbar">
    <div class="logo-container left">
        <img src="logo/left_icon.png" alt="Institution Logo">
    </div>

    <div class="nav-center">
        <a class="home-link" href="../{home_page}">Home</a>
    </div>

    <div class="logo-container right">
        <img src="logo/right_icon.png" alt="Project Logo">
    </div>
</nav>"""

            # Use footer placeholder to load from footer.html
            footer_placeholder = '<div id="footer-placeholder"></div>'
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Analysis Documentation</title>
                    <link rel="stylesheet" href="css/styles.css">
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                    <script src="https://cdn.bokeh.org/bokeh/release/bokeh-3.3.4.min.js"></script>
                    <script src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-3.3.4.min.js"></script>
                    <script src="https://cdn.bokeh.org/bokeh/release/bokeh-tables-3.3.4.min.js"></script>
                <style>
                  @media print {{
                    .navbar,
                    .nav-buttons_info_page,
                    #download-pdf-btn,
                    .dropdown-toggle_info_page{{display:none !important;}}
                    .dropdown-section_info_page,
                    .dropdown-content_info_page{{display:block !important;}}
                  }}
                  @page{{size:A2 portrait; margin:10mm;}}
                </style>
            </head>
            <body>
                <!-- Navigation Header -->
                {header_content}
                
                <!-- Main Content -->
                <div class="content-container_info_page">
        <div class="header-container_info_page">
                    <h1>Analysis Documentation</h1>
            <div class="nav-buttons_info_page">
                <button id="download-pdf-btn" class="action-button_info_page">
                    <i class="fas fa-file-pdf"></i> Save / Print PDF
                </button>
            </div>
        </div>
                    
                    <section class="documentation-sections_info_page">
                        {sections_html}
                    </section>
                </div>
                
                <!-- Footer -->
                {footer_placeholder}
            
            <!-- Scripts -->
            <script>
                // Load footer from external file (both info.html and footer.html are in components/)
                fetch('footer.html')
                    .then(response => response.text())
                    .then(data => document.getElementById('footer-placeholder').innerHTML = data);
            </script>
            <script>
                // Initialize dropdowns after plots
        const initializeDropdowns = () => {{
                document.querySelectorAll('.dropdown-toggle_info_page').forEach(button => {{
                    button.addEventListener('click', function() {{
                        const section = this.closest('.dropdown-section_info_page');
                        section.classList.toggle('active_info_page');
                    }});
            }});
        }};

        // Call this when the page loads
        document.addEventListener('DOMContentLoaded', initializeDropdowns);
    </script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

    <script>
        // Helper function to convert a Bokeh plot to a static image
        async function convertBokehPlotsToImages() {{
            const plots = document.querySelectorAll('.bk-root');
            
            for (let i = 0; i < plots.length; i++) {{
                const plot = plots[i];
                const container = plot.closest('.plot-placeholder_info_page') || plot.parentElement;
                
                try {{
                    // Wait for Bokeh to fully render
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    // Create a canvas element to capture the plot
                    const tempCanvas = await html2canvas(plot, {{
                        scale: 2,
                        logging: false,
                        useCORS: true,
                        allowTaint: true,
                        backgroundColor: 'white'
                    }});
                    
                    // Convert to an image
                    const imgData = tempCanvas.toDataURL('image/png');
                    const img = document.createElement('img');
                    img.src = imgData;
                    img.className = 'bokeh-static-image';
                    img.style.width = '100%';
                    img.style.maxWidth = '100%';
                    img.style.display = 'block';
                    
                    // Create a container for the image
                    const staticContainer = document.createElement('div');
                    staticContainer.className = 'bokeh-static-container';
                    staticContainer.appendChild(img);
                    
                    // Add the static image after the Bokeh plot (don't remove the original plot)
                    plot.style.display = 'none'; // Hide the original plot for PDF capture
                    container.appendChild(staticContainer);
                }} catch (error) {{
                    console.error(`Error converting Bokeh plot ${{i}} to image:`, error);
                }}
            }}
            
            return true;
        }}
    </script>

    <!-- Print / Save as PDF script -->
    <script>
      document.addEventListener('DOMContentLoaded', () => {{
        const printBtn = document.getElementById('download-pdf-btn');

        const dropdowns = () =>
          document.querySelectorAll('.dropdown-section_info_page');

        async function openDropdownsAndFreezePlots() {{
          dropdowns().forEach(s =>
            s.classList.add('active_info_page', 'print-open'));

          // Replace interactive Bokeh plots with static PNGs
          try {{
            await convertBokehPlotsToImages();
            await new Promise(r => setTimeout(r, 300));
          }} catch (e) {{
            console.warn('Plot conversion failed:', e);
          }}
        }}

        function restorePage() {{
          document.querySelectorAll('.bokeh-static-container')
                  .forEach(c => c.remove());
          document.querySelectorAll('.bk-root')
                  .forEach(p => p.style.display = 'block');

          dropdowns().forEach(s =>
            s.classList.remove('active_info_page', 'print-open'));
        }}

        printBtn.addEventListener('click', async () => {{
          await openDropdownsAndFreezePlots();
          window.print();
        }});

        window.addEventListener('afterprint', restorePage);
      }});
    </script>
        </body>
        </html>
        """
            
            logging.info("Successfully generated information page HTML")
            return html_content
            
        except Exception as e:
            logging.error(f"Error generating information page: {str(e)}")
            raise

    def _get_info_sections(self) -> List[Dict]:
        """Return empty list since we'll handle sections directly in HTML"""
        return []

    def _generate_sections(
        self,
        sections: List[Dict],
        single_karyotype_json: str,
        single_cnv_distribution_json: str,
        chromosome_plot_json: str
    ) -> str:
        """Generate sections with headers and styled dropdowns"""
        
        # Generate specific plots for each chromosome and CNV type
        deletion_plot_json = self._to_json(generate_chromosome_plot(
            self.single_simulated[0].baf_lrr_data,
            self.single_simulated[0].cnv_detection_filtered.query("Chromosome == '1' and Type == 'Deletion'"),
            "1",  # chromosome 1
            self.single_simulated[0].sample_id,
            self.single_simulated[0].roh_bed,
            self.single_simulated[0].union_bed,
            self.single_simulated[0].cn_bed,
            cn_summary_data=self.single_simulated[0].cn_summary_data
        ))
        
        duplication_plot_json = self._to_json(generate_chromosome_plot(
            self.single_simulated[0].baf_lrr_data,
            self.single_simulated[0].cnv_detection_filtered.query("Chromosome == '8' and Type == 'Duplication'"),
            "8",  # chromosome 8 for AAA duplication pattern
            self.single_simulated[0].sample_id,
            self.single_simulated[0].roh_bed,
            self.single_simulated[0].union_bed,
            self.single_simulated[0].cn_bed,
            cn_summary_data=self.single_simulated[0].cn_summary_data
        ))
        
        cnloh_plot_json = self._to_json(generate_chromosome_plot(
            self.single_simulated[0].baf_lrr_data,
            self.single_simulated[0].cnv_detection_filtered.query("Chromosome == '7' and Type == 'Cn_loh'"),
            "7",  # chromosome 7 for CN-LOH
            self.single_simulated[0].sample_id,
            self.single_simulated[0].roh_bed,
            self.single_simulated[0].union_bed,
            self.single_simulated[0].cn_bed,
            cn_summary_data=self.single_simulated[0].cn_summary_data
        ))
        
        mixed_plot_json = self._to_json(generate_chromosome_plot(
            self.single_simulated[0].baf_lrr_data,
            self.single_simulated[0].cnv_detection_filtered.query("Chromosome == '19'"),
            "19",  # chromosome 19 for mixed CNV types
            self.single_simulated[0].sample_id,
            self.single_simulated[0].roh_bed,
            self.single_simulated[0].union_bed,
            self.single_simulated[0].cn_bed,
            cn_summary_data=self.single_simulated[0].cn_summary_data
        ))
        
        # Original section HTML (keep all existing code for background, parameters, etc. sections)
        existing_html = f"""
        <div class="main-sections-container_info_page">
            <!-- Biological Background Section -->
            <div class="main-section_info_page">
                <h2>Background</h2>
                
                <div class="dropdown-section_info_page">
                    <button class="dropdown-toggle_info_page">About & How to Cite</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                            <!-- Left Column -->
                            <div class="text-placeholder_info_page">
                                <h3>Who We Are?</h3>
                                <p><strong>Core Facility Bioinformatics and Statistics (CF-BIOS)</strong></p>
                                <p style="font-size: 0.9em; color: #666; margin-bottom: 10px;">Helmholtz Zentrum München GmbH - German Research Center for Environmental Health<br>85764 Neuherberg, Germany</p>
                                
                                <p style="font-size: 0.95em; line-height: 1.6; margin-bottom: 10px;">
                                    The Core Facility Bioinformatics and Statistics (CF-BIOS) provides expert support in bioinformatics and 
                                    statistics for a wide range of research applications. We design and deliver services and workflows in close 
                                    collaboration with data-generating core facilities, ensuring seamless integration and high-quality results.
                                </p>
                                
                                <p style="margin-top: 12px;">
                                    <a href="https://www.helmholtz-munich.de/en/core-facility/bioinformatics-and-statistics" 
                                       target="_blank" 
                                       style="color: #007bff; text-decoration: none; font-weight: 500;">
                                        Visit CF-BIOS Website →
                                    </a>
                                </p>
                                
                                <h3 style="margin-top: 20px;">Associated Publication</h3>
                                <p>[Placeholder: TBA]</p>
                            </div>
                            
                            <!-- Right Column -->
                            <div class="text-placeholder_info_page">
                                <h3>How to Cite</h3>
                                <p style="font-style: italic; background-color: #f8f9fa; padding: 10px; border-left: 3px solid #007bff; border-radius: 4px;">
                                    "We acknowledge the technical support of <strong>Core Facility Bioinformatics and Statistics</strong> at Helmholtz Munich."
                                </p>
                                
                                <h3>Contact & Support</h3>
                                <p>For questions about the technical details of the pipeline or if you encounter any problems, please contact us at:</p>
                                <p style="margin-top: 10px;"><strong>Email:</strong> <a href="mailto:{self.support_email}" style="color: #007bff; text-decoration: none;">{self.support_email}</a></p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dropdown-section_info_page">
                    <button class="dropdown-toggle_info_page">Pipeline Overview</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                            <!-- Left Column -->
                            <div class="text-placeholder_info_page">
                                <h3>KaryoExplorer - Digital Karyotyping Pipeline</h3>
                                <p>KaryoExplorer is a digital karyotyping pipeline that analyzes Illumina genotyping array data to assess the genomic integrity of your samples. By comparing genomic SNP profiles, the pipeline helps evaluate the differentiation quality of stem cells, detecting chromosomal aberrations including copy number variations (CNVs) and loss of heterozygosity (LoH) events. Results are presented in this interactive report.</p>
                                
                                <div class="pipeline-details_info_page">
                                    <h4>What This Report Shows</h4>
                                    <ul>
                                        <li><strong>Deletions and Duplications:</strong> Chromosomal regions with copy number gains or losses</li>
                                        <li><strong>Loss of Heterozygosity:</strong> Regions where one parental allele is lost, including copy-neutral LoH (cnLoH)</li>
                                        <li><strong>Quality Metrics:</strong> Sample quality indicators such as call rate and LRR standard deviation</li>
                                    </ul>

                                    <h4>Visualizations Available</h4>
                                        <ul>
                                        <li><strong>Genome-wide Karyograms:</strong> Overview of all chromosomes with CNV events color-coded by type</li>
                                        <li><strong>Chromosome Views:</strong> Detailed per-chromosome plots showing BAF, LRR, and copy number tracks</li>
                                        <li><strong>ROH Regions:</strong> Highlighted runs of homozygosity with cnLoH candidates marked</li>
                                        </ul>
                                </div>
                            </div>
                            
                            <!-- Right Column -->
                            <div class="text-placeholder_info_page">
                                <div class="analysis-modes_info_page">
                                    <h4>Analysis Modes</h4>
                                    <div class="mode-info_info_page">
                                        <h5>Single-Sample Analysis</h5>
                                        <p style="font-size: 0.95em; margin-bottom: 8px;">Examines one sample to identify CNVs and LoH events. Use this mode to assess the genomic profile of an individual cell line or sample.</p>
                                    </div>
                                    
                                    <div class="mode-info_info_page">
                                        <h5>Paired Analysis (PRE/POST)</h5>
                                        <p style="font-size: 0.95em; margin-bottom: 8px;">Compares two related samples, such as a donor cell line (PRE) and its derived iPSC clone (POST). This mode highlights acquired chromosomal changes that occurred during reprogramming or differentiation.</p>
                                    </div>
                                </div>
                                
                                <div class="pipeline-details_info_page" style="margin-top: 15px;">
                                    <h4>Using This Report</h4>
                                    <p style="font-size: 0.95em; margin-bottom: 10px;">For detailed guidance on interpreting visualizations and performing analysis, see the <strong>"Plots and Their Explanations"</strong> and <strong>"How to Analyze Your Data"</strong> sections below.</p>
                                    <ul>
                                        <li>Navigate using the menu to explore different samples and chromosomes</li>
                                        <li>Zoom and pan on plots to examine regions of interest in detail</li>
                                        <li>Use "Print to PDF" to save the current view for documentation</li>
                                        <li>Export figures as PNG for publications using the toolbar on each plot</li>
                                        </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="dropdown-section_info_page">
                        <button class="dropdown-toggle_info_page">Infinium Array Background</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                                <!-- Left Column - Technology Overview -->
                            <div class="text-placeholder_info_page">
                                    <h3>Illumina Infinium Technology</h3>
                                    <div class="concept-box_info_page">
                                        <p>The Illumina Infinium Global Screening Array (GSA-24) is a high-throughput genotyping platform that enables genome-wide analysis of both SNPs and copy number variations (CNVs).</p>
                                        
                                        <div class="key-points_info_page">
                                            <div class="key-point_info_page">
                                                <span>Using ~700,000 markers per array</span>
                            </div>
                                            <div class="key-point_info_page">
                                                <span>DNA is amplified, fragmented, and hybridized to bead-bound probes.</span>
                                            </div>
                                            <div class="key-point_info_page">
                                                <span>A single-base extension reaction incorporates fluorescently labeled nucleotides, allowing detection of alleles (e.g., A/T or G/C).</span>
                        </div>
                    </div>
                </div>

                                    <h4>Technical Specifications</h4>
                                    <div class="importance-box_info_page">
                                        <div class="criteria-list_info_page">
                                            <div class="criteria-item_info_page">
                                                <div class="criteria-header_info_page">
                                                    <strong>High-Throughput Capacity</strong>
                                                </div>
                                                <div class="criteria-detail_info_page">
                                                    <span class="criteria-desc_info_page">Each BeadChip supports 24 samples, offering efficient scalability for large studies.</span>
                                                </div>
                                            </div>
                                            
                                            <div class="criteria-item_info_page">
                                                <div class="criteria-header_info_page">
                                                    <strong>Data Quality</strong>
                                                </div>
                                                <div class="criteria-detail_info_page">
                                                    <span class="criteria-desc_info_page">The platform achieves a >99.5% call rate per sample.</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Right Column - Data Metrics -->
                            <div class="text-placeholder_info_page">
                                    <div class="application-box_info_page">
                                        <h4>Essential Array Outputs</h4>
                                        <div class="application-grid_info_page">
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>Log R Ratio (LRR)</strong>
                                                    <p>Reflects total signal intensity, used for CNV detection. Values above 0 typically indicate duplications, while values below 0 suggest deletions.</p>
                                                </div>
                                            </div>
                                            
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>B Allele Frequency (BAF)</strong>
                                                    <p>Indicates allelic ratios, useful for identifying allelic imbalance and copy-neutral events. Normal diploid regions show three bands at 0, 0.5, and 1.</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="guide-box_info_page">
                                        <h4>Data Interpretation Pattern</h4>
                                        <div class="feature-list_info_page">
                                            <div class="feature-line_info_page">
                                                <strong>Normal State</strong>
                                                <span>LRR values around 0 with BAF values at 0, 0.5, and 1</span>
                                            </div>
                                            <div class="feature-line_info_page">
                                                <strong>Deletion</strong>
                                                <span>LRR values below 0 with BAF showing only 0 and 1 values</span>
                                            </div>
                                            <div class="feature-line_info_page">
                                                <strong>Duplication</strong>
                                                <span>LRR values above 0 with BAF showing values at 0, 0.33, 0.67, and 1</span>
                                            </div>
                                            <div class="feature-line_info_page">
                                                <strong>Copy-Neutral LOH</strong>
                                                <span>LRR values around 0 with BAF showing only 0 and 1 values</span>
                                            </div>
                                        </div>
                                    </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Parameters Section -->
            <div class="main-section_info_page">
                <h2>Parameters</h2>
                
                <div class="dropdown-section_info_page">
                    <button class="dropdown-toggle_info_page">P-Hat Value & IBD Analysis</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                            <!-- Left Column - P-Hat Value Explanation -->
                            <div class="text-placeholder_info_page">
                                <h3>What is P-Hat Value?</h3>
                                <div class="concept-box_info_page">
                                    <p>In genetics, P-hat (P̂) refers to the estimated proportion of alleles that two samples share identical by descent (IBD).</p>
                                    
                                    <div class="key-points_info_page">
                                        <div class="key-point_info_page">
                                            <span>IBD means two DNA segments are inherited from a common ancestor without any recombination.</span>
                                        </div>
                                        <div class="key-point_info_page">
                                            <span>P̂ tells you how genetically related two samples are (ranges from 0 to 1).</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <h4>Relationship Indicators</h4>
                                <div class="relationship-table_info_page">
                                    <div class="relationship-row_info_page header">
                                        <div>Relationship</div>
                                        <div>Expected P̂</div>
                                    </div>
                                    <div class="relationship-row_info_page">
                                        <div>Identical twins, duplicates</div>
                                        <div class="value high">~1.0</div>
                                    </div>
                                    <div class="relationship-row_info_page">
                                        <div>Parent-offspring</div>
                                        <div class="value medium">~0.5</div>
                                    </div>
                                    <div class="relationship-row_info_page">
                                        <div>Full siblings</div>
                                        <div class="value medium">~0.5</div>
                                    </div>
                                    <div class="relationship-row_info_page">
                                        <div>Half siblings</div>
                                        <div class="value low">~0.25</div>
                                    </div>
                                    <div class="relationship-row_info_page">
                                        <div>Unrelated individuals</div>
                                        <div class="value none">~0.0</div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Right Column - Application in iPSC Research -->
                            <div class="text-placeholder_info_page">
                                <h3>What is IBD Analysis?</h3>
                                <div class="concept-box_info_page">
                                    <p>IBD (Identical By Descent) analysis detects how much DNA two samples share due to inheritance from a common ancestor.</p>
                                    
                                    <div class="application-box_info_page">
                                        <h4>Applications in iPSC Research</h4>
                                        <div class="application-grid_info_page">
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>Verify sample identity</strong>
                                                    <p>Is the iPSC derived from the correct donor?</p>
                                                </div>
                                            </div>
                                            
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>Detect contamination</strong>
                                                    <p>If two supposed independent lines are too similar, something is wrong.</p>
                                                </div>
                                            </div>
                                            
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>Assess clonality</strong>
                                                    <p>Different iPSC lines may come from the same or different initial cells.</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="importance-box_info_page">
                                        <h4>Quality Criteria for iPSC Cells</h4>
                                        <div class="criteria-list_info_page">
                                            <div class="criteria-item_info_page">
                                                <div class="criteria-header_info_page">
                                                    <strong>iPSC matches original donor</strong>
                                                </div>
                                                <div class="criteria-detail_info_page">
                                                    <span class="criteria-indicator_info_page high">P̂ ≈ 1.0</span>
                                                    <span class="criteria-desc_info_page">P̂ between original donor and derived iPSC should be very close to 1.0</span>
                                                </div>
                                            </div>
                                            
                                            <div class="criteria-item_info_page">
                                                <div class="criteria-header_info_page">
                                                    <strong>Different iPSC lines are independent</strong>
                                                </div>
                                                <div class="criteria-detail_info_page">
                                                    <span class="criteria-indicator_info_page none">P̂ ≈ 0.0</span>
                                                    <span class="criteria-desc_info_page">P̂ between iPSCs from different donors should be close to 0.0</span>
                                                </div>
                                            </div>
                                            
                                            <div class="criteria-item_info_page">
                                                <div class="criteria-header_info_page">
                                                    <strong>No contamination</strong>
                                                </div>
                                                <div class="criteria-detail_info_page">
                                                    <span class="criteria-indicator_info_page warning">P̂ ≠ 0.5</span>
                                                    <span class="criteria-desc_info_page">Unexpected high P̂ (~0.5) between "different" samples would raise red flags</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="tool-info_info_page">
                                        <span>We used <strong>PLINK</strong> for IBD analysis in this pipeline.</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="dropdown-section_info_page">
                    <button class="dropdown-toggle_info_page">Quality Score and P-Value Threshold</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                                <!-- Left Column - Phred Score Explanation -->
                            <div class="text-placeholder_info_page">
                                    <h3>Quality Score Calculation</h3>
                                    <div class="concept-box_info_page">
                                        <p>Bcftools applies a Hidden Markov Model (HMM) to segment the genome based on Log R Ratio (LRR) and B Allele Frequency (BAF) data, predicting copy number states across genomic regions.</p>
                                        
                                        <div class="key-points_info_page">
                                            <div class="key-point_info_page">
                                                <span>For each segment, the tool computes the posterior probability P_max of the most likely CNV state.</span>
                            </div>
                                            <div class="key-point_info_page">
                                                <span>This probability is transformed into a Phred-scaled quality score to quantify confidence:</span>
                                            </div>
                                        </div>
                                        
                                        <div style="text-align: center; padding: 15px; background: #f8f8f8; margin: 10px 0; border-radius: 6px; font-family: monospace; font-weight: bold;">
                                            Phred Score (QUAL) = -10 · log₁₀(1 - P_max)
                                        </div>
                                        
                                        <p>This score reflects how likely the predicted CNV state is correct. To convert a Phred score back to a p-value (i.e., the probability that the call is incorrect), the inverse formula is used:</p>
                                        
                                        <div style="text-align: center; padding: 15px; background: #f8f8f8; margin: 10px 0; border-radius: 6px; font-family: monospace; font-weight: bold;">
                                            p = 10^(- QUAL / 10)
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Right Column - Interpretation -->
                                <div class="text-placeholder_info_page">
                                    <div class="application-box_info_page">
                                        <h4>Confidence Thresholds</h4>
                                        <div class="application-grid_info_page">
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>High Confidence</strong>
                                                    <p>Phred score ≥ 13 (p ≤ 0.05) - Displayed in <span style="color: green; font-weight: bold;">green</span> in tables</p>
                                                </div>
                                            </div>
                                            
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>Low Confidence</strong>
                                                    <p>Phred score < 13 (p > 0.05) - Displayed in <span style="color: red; font-weight: bold;">red</span> in tables</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <h4>Phred Score to Error Probability and Accuracy Table</h4>
                                    <div class="relationship-table_info_page" style="margin-top: 15px;">
                                        <div class="relationship-row_info_page header">
                                            <div>Phred Score (Q)</div>
                                            <div>Probability of Incorrect Call (p)</div>
                                            <div>Base Call Accuracy (%)</div>
                                        </div>
                                        <div class="relationship-row_info_page" style="grid-template-columns: 1fr 1fr 1fr;">
                                            <div>5</div>
                                            <div>1 in 3.2</div>
                                            <div>68.4%</div>
                                        </div>
                                        <div class="relationship-row_info_page" style="grid-template-columns: 1fr 1fr 1fr;">
                                            <div>10</div>
                                            <div>1 in 10</div>
                                            <div>90.0%</div>
                                        </div>
                                        <div class="relationship-row_info_page" style="grid-template-columns: 1fr 1fr 1fr; background-color: #f0f7f0;">
                                            <div>13</div>
                                            <div>1 in 20</div>
                                            <div>95.0%</div>
                                        </div>
                                        <div class="relationship-row_info_page" style="grid-template-columns: 1fr 1fr 1fr;">
                                            <div>20</div>
                                            <div>1 in 100</div>
                                            <div>99.0%</div>
                                        </div>
                                        <div class="relationship-row_info_page" style="grid-template-columns: 1fr 1fr 1fr;">
                                            <div>30</div>
                                            <div>1 in 1,000</div>
                                            <div>99.9%</div>
                                        </div>
                                        <div class="relationship-row_info_page" style="grid-template-columns: 1fr 1fr 1fr;">
                                            <div>40</div>
                                            <div>1 in 10,000</div>
                                            <div>99.99%</div>
                                        </div>
                                        <div class="relationship-row_info_page" style="grid-template-columns: 1fr 1fr 1fr;">
                                            <div>50</div>
                                            <div>1 in 100,000</div>
                                            <div>99.999%</div>
                                        </div>
                                    </div>
                                </div>
                        </div>
                    </div>
                </div>

                <div class="dropdown-section_info_page">
                    <button class="dropdown-toggle_info_page">LRR Quality Metrics</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                                <!-- Left Column - Overall LRR Quality -->
                            <div class="text-placeholder_info_page">
                                    <h3>Overall Sample Quality</h3>
                                    <div class="concept-box_info_page">
                                        <p>Log R Ratio (LRR) standard deviation is a key quality indicator for array data. Lower values indicate higher quality data with less noise.</p>
                                        
                                        <div class="key-points_info_page">
                                            <div class="key-point_info_page">
                                                <span>In the sample tables, overall LRR standard deviation is displayed for each sample.</span>
                            </div>
                                            <div class="key-point_info_page">
                                                <span>Values are color-coded for quick quality assessment:</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="importance-box_info_page">
                                        <div class="criteria-list_info_page">
                                            <div class="criteria-item_info_page">
                                                <div class="criteria-header_info_page">
                                                    <strong>Good Quality Data</strong>
                                                </div>
                                                <div class="criteria-detail_info_page">
                                                    <span class="criteria-indicator_info_page high" style="background-color: #e0f7e0; color: green;">LRR StdDev < 0.3</span>
                                                    <span class="criteria-desc_info_page">Lower noise enables more reliable CNV detection, especially for smaller events.</span>
                                                </div>
                                            </div>
                                            
                                            <div class="criteria-item_info_page">
                                                <div class="criteria-header_info_page">
                                                    <strong>Poor Quality Data</strong>
                                                </div>
                                                <div class="criteria-detail_info_page">
                                                    <span class="criteria-indicator_info_page low" style="background-color: #f7e0e0; color: red;">LRR StdDev > 0.3</span>
                                                    <span class="criteria-desc_info_page">Higher noise can lead to false positive/negative CNV calls, particularly for subtle events.</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Right Column - Chromosome-specific metrics -->
                                <div class="text-placeholder_info_page">
                                    <h3>Chromosome-Specific LRR Metrics</h3>
                                    <div class="application-box_info_page">
                                        <p>For detailed quality assessment, we provide LRR metrics for each chromosome individually:</p>
                                        
                                        <div class="application-grid_info_page">
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>Mean LRR</strong>
                                                    <p>Average LRR value across the chromosome. Should be close to zero for normal diploid regions. Consistent deviations may indicate whole-chromosome events.</p>
                                                </div>
                                            </div>
                                            
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>Median LRR</strong>
                                                    <p>Less sensitive to outliers than mean. Provides a robust measure of central tendency for LRR across the chromosome.</p>
                                                </div>
                                            </div>
                                            
                                            <div class="application-item_info_page">
                                                <div class="application-content_info_page">
                                                    <strong>StdDev LRR</strong>
                                                    <p>Measures data noise/variability for each chromosome. Some chromosomes may show higher variability than others.</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="guide-box_info_page">
                                        <h4>Interpretation Guidelines</h4>
                                        <div class="feature-list_info_page">
                                            <div class="feature-line_info_page">
                                                <strong>Uniform Quality</strong>
                                                <span>Most chromosomes should show similar LRR StdDev values in a good quality sample</span>
                                            </div>
                                            <div class="feature-line_info_page">
                                                <strong>Outlier Chromosomes</strong>
                                                <span>Chromosomes with unusually high StdDev may contain complex structural variation</span>
                                            </div>
                                            <div class="feature-line_info_page">
                                                <strong>Mean vs Median</strong>
                                                <span>Large differences between mean and median may indicate skewed data or presence of outliers</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                        </div>
                    </div>
                </div>
            </div>

                <!-- Plots and Their Explanations Section -->
            <div class="main-section_info_page">
                <h2>Plots and Their Explanations</h2>
                
                                <div class="dropdown-section_info_page">
                    <button class="dropdown-toggle_info_page">Karyotype Plot</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                            <!-- Left Column - Bokeh Plot -->
                            <div class="plot-container_info_page">
                                <h3>Karyotype Visualization</h3>
                                <div id="karyotype-plot" class="plot-placeholder_info_page"></div>
                                <script>
                                    try {{
                                        let karyotypeData = {single_karyotype_json};
                                        console.log("Karyotype data initial type:", typeof karyotypeData);
                                        
                                        if (typeof karyotypeData === 'string') {{
                                            try {{
                                                karyotypeData = JSON.parse(karyotypeData);
                                                console.log("Karyotype data parsed");
                                            }} catch (parseError) {{
                                                console.error("Karyotype data parse error:", parseError);
                                            }}
                                        }}
                                        
                                        console.log("Karyotype data final type:", typeof karyotypeData);
                                        
                                        if (karyotypeData && !karyotypeData.error) {{
                                            Bokeh.embed.embed_item(karyotypeData, "karyotype-plot");
                                            console.log("Karyotype plot embedded successfully");
                                        }} else {{
                                            const errorMsg = karyotypeData?.error || 'Karyotype data not available';
                                            console.error("Karyotype plot error:", errorMsg);
                                            document.getElementById('karyotype-plot').innerHTML =
                                                `<div class="plot-error">${{errorMsg}}</div>`;
                                        }}
                                    }} catch (e) {{
                                        console.error('Karyotype plot initialization error:', e);
                                        document.getElementById('karyotype-plot').innerHTML =
                                            `<div class="plot-error">Plot error: ${{e.message}}</div>`;
                                    }}
                                </script>
                            </div>
                            
                            <!-- Right Column - Analysis Guidance -->
                            <div class="text-placeholder_info_page">
                                <div class="guide-box_info_page">
                                    <div class="guide-columns_info_page">
                                        <!-- Left Column - Legend Controls -->
                                        <div class="guide-column-left_info_page">
                                            <h5>Interactive Plot Controls:</h5>
                                            <div class="legend-controls_info_page">
                                                <!-- duplications -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch duplication"></span>
                                                    <div class="legend-text">
                                                        <strong>Duplications</strong>
                                                        <em class="hint">Click to toggle visibility of copy number gains</em>
                                                    </div>
                                                </div>

                                                <!-- deletions -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch deletion"></span>
                                                    <div class="legend-text">
                                                        <strong>Deletions</strong>
                                                        <em class="hint">Click to toggle visibility of copy number losses</em>
                                                    </div>
                                                </div>

                                                <!-- ≥ 1 Mb filter -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch loh"></span>
                                                    <div class="legend-text">
                                                        <strong>≥&nbsp;1&nbsp;Mb Filter</strong>
                                                        <em class="hint">
                                                            Default: off (shows &gt;0.2 Mb events)<br>
                                                            Toggle to show only large CNVs
                                                        </em>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Right Column - Plot Features -->
                                        <div class="guide-column-right_info_page">
                                            <div class="plot-features_info_page">
                                                <h5>Plot Features</h5>
                                                <div class="feature-list_info_page">
                                                    <div class="feature-line_info_page">
                                                        <strong>Chromosome Layout: </strong>
                                                        Vertical tracks represent individual chromosomes starting from 0 Mb 
                                                        at the top-left, extending to their full length at the bottom.
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Event Size: </strong>
                                                        Dot size correlates with CNV event size (in MB) - larger dots represent 
                                                        larger genomic events.
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Color Significance: </strong>
                                                        Full color intensity indicates high significance (p&lt;0.05). 
                                                        Colors fade logarithmically with increasing p-values.
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Interactive Details: </strong>
                                                        Hover over any event to see genomic coordinates, 
                                                        CNV size and p-value.
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Full width bottom section -->
                                    <p class="demo-instruction_info_page">
                                        Try the controls on the simulated Sample 1 karyotype on the left: 
                                        hide duplications, focus on deletions, or activate the ≥1 Mb filter 
                                        to see how the plot responds.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="dropdown-section_info_page">
                    <button class="dropdown-toggle_info_page">CNV Distribution Plot</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                            <!-- Left Column - CNV Distribution Plot -->
                            <div class="plot-container_info_page">
                                <h3>CNV Size Distribution</h3>
                                <div id="cnv-distribution-plot" class="responsive-plot" style="min-height:400px"></div>
                                <script>
                                    try {{
                                        // CNV data may already be parsed JSON or double-stringified
                                        let cnvData = {single_cnv_distribution_json};
                                        console.log("CNV data initial type:", typeof cnvData);
                                        
                                        // If it's a string, try to parse it once
                                        if (typeof cnvData === 'string') {{
                                            try {{
                                                cnvData = JSON.parse(cnvData);
                                                console.log("CNV data parsed once");
                                            }} catch (parseError) {{
                                                console.error("CNV data parse error:", parseError);
                                            }}
                                        }}
                                        
                                        // At this point cnvData should be an object. If it's still a string, try once more
                                        if (typeof cnvData === 'string') {{
                                            try {{
                                                cnvData = JSON.parse(cnvData);
                                                console.log("CNV data parsed twice");
                                            }} catch (parseError2) {{
                                                console.error("CNV data second parse error:", parseError2);
                                            }}
                                        }}
                                        
                                        console.log("CNV data final type:", typeof cnvData);
                                        
                                        if (cnvData && !cnvData.error) {{
                                            Bokeh.embed.embed_item(cnvData, "cnv-distribution-plot");
                                            console.log("CNV plot embedded successfully");
                                        }} else {{
                                            const errorMsg = cnvData?.error || 'CNV data not available';
                                            console.error("CNV plot error:", errorMsg);
                                            document.getElementById('cnv-distribution-plot').innerHTML =
                                                `<div class="plot-error">${{errorMsg}}</div>`;
                                        }}
                                    }} catch (e) {{
                                        console.error('CNV plot initialization error:', e);
                                        document.getElementById('cnv-distribution-plot').innerHTML =
                                            `<div class="plot-error">Plot error: ${{e.message}}</div>`;
                                    }}
                                </script>
                            </div>
                            
                            <!-- Right Column - Analysis Guidance -->
                            <div class="text-placeholder_info_page">
                                <div class="guide-box_info_page">
                                    <div class="guide-columns_info_page">
                                        <!-- Left Column - Legend Controls -->
                                        <div class="guide-column-left_info_page">
                                            <h5>Interactive Plot Controls:</h5>
                                            <div class="legend-controls_info_page">
                                                <!-- duplications -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch duplication"></span>
                                                    <div class="legend-text">
                                                        <strong>Duplications</strong>
                                                        <em class="hint">Click to toggle visibility of duplication counts (blue bars)</em>
                                                    </div>
                                                </div>

                                                <!-- deletions -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch deletion"></span>
                                                    <div class="legend-text">
                                                        <strong>Deletions</strong>
                                                        <em class="hint">Click to toggle visibility of deletion counts (red bars)</em>
                                                    </div>
                                                </div>

                                                <!-- ≥ 1 Mb filter -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch loh"></span>
                                                    <div class="legend-text">
                                                        <strong>≥&nbsp;1&nbsp;Mb Filter</strong>
                                                        <em class="hint">
                                                            Default: off (shows &gt;0.2 Mb events)<br>
                                                            Toggle to show only large CNV events
                                                        </em>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Right Column - Plot Features -->
                                        <div class="guide-column-right_info_page">
                                            <div class="plot-features_info_page">
                                                <h5>Plot Features</h5>
                                                <div class="feature-list_info_page">
                                                    <div class="feature-line_info_page">
                                                        <strong>Chromosome Distribution: </strong>
                                                        X-axis shows chromosomes 1-22, X, Y. Y-axis displays the count 
                                                        of CNV events detected per chromosome.
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Color Coding: </strong>
                                                        Red bars represent deletion events, blue bars represent 
                                                        duplication events for each chromosome.
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Event Counting: </strong>
                                                        Each bar height corresponds to the total number of CNV events 
                                                        of that type detected on the specific chromosome.
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Interactive Legend: </strong>
                                                        Click on legend items to selectively show/hide deletion 
                                                        or duplication counts for focused analysis.
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Full width bottom section -->
                                    <p class="demo-instruction_info_page">
                                        Explore the CNV distribution on the left: click legend items to focus on 
                                        specific CNV types, use the ≥1 Mb filter to examine only large events, 
                                        and observe which chromosomes show the highest CNV burden.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="dropdown-section_info_page">
                    <button class="dropdown-toggle_info_page">BAF-LRR-CN Plots</button>
                    <div class="dropdown-content_info_page">
                        <div class="dropdown-grid_info_page">
                            <!-- Left Column - Chromosome Plot -->
                            <div class="plot-container_info_page">
                                <h3>Chromosome View</h3>
                                <div id="chromosome-plot" class="plot-placeholder_info_page" style="min-height: 900px;"></div>
                                <script>
                                    try {{
                                        // Add debugging for chromosome plot
                                        let chromData = {chromosome_plot_json};
                                        console.log("Chromosome data initial type:", typeof chromData);
                                        
                                        if (typeof chromData === 'string') {{
                                            try {{
                                                chromData = JSON.parse(chromData);
                                                console.log("Chromosome data parsed");
                                            }} catch (parseError) {{
                                                console.error("Chromosome data parse error:", parseError);
                                            }}
                                        }}
                                        
                                        console.log("Chromosome data final type:", typeof chromData);
                                        
                                        if (chromData && !chromData.error) {{
                                            Bokeh.embed.embed_item(chromData, "chromosome-plot");
                                            console.log("Chromosome plot embedded successfully");
                                        }} else {{
                                            const errorMsg = chromData?.error || 'Chromosome plot not available';
                                            console.error("Chromosome plot error:", errorMsg);
                                            document.getElementById('chromosome-plot').innerHTML =
                                                `<div class="plot-error">${{errorMsg}}</div>`;
                                        }}
                                    }} catch (e) {{
                                        console.error('Chromosome plot initialization error:', e);
                                        document.getElementById('chromosome-plot').innerHTML =
                                            `<div class="plot-error">Plot error: ${{e.message}}</div>`;
                                    }}
                                </script>
                            </div>
                            
                            <!-- Right Column - Analysis Guidance -->
                            <div class="text-placeholder_info_page">
                                <div class="guide-box_info_page">
                                    <div class="guide-columns_info_page">
                                        <!-- Left Column - Plot Components -->
                                        <div class="guide-column-left_info_page">
                                            <h5>Combined Plot Components:</h5>
                                            <div class="legend-controls_info_page">
                                                <!-- BAF Plot -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch" style="background-color: #1f77b4;"></span>
                                                    <div class="legend-text">
                                                        <strong>BAF Plot (Blue Dots)</strong>
                                                        <em class="hint">Shows B Allele Frequency for each SNP along the chromosome</em>
                                                    </div>
                                                </div>

                                                <!-- LRR Plot -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch" style="background-color: #2ca02c;"></span>
                                                    <div class="legend-text">
                                                        <strong>LRR Plot (Green Dots)</strong>
                                                        <em class="hint">Displays Log R Ratio values indicating copy number changes</em>
                                                    </div>
                                                </div>

                                                <!-- Copy Number Plot -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch" style="background-color: #ff7f0e;"></span>
                                                    <div class="legend-text">
                                                        <strong>Copy Number Plot</strong>
                                                        <em class="hint">Shows detected CNV events with corresponding copy number changes</em>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <h5>Interactive Legend Controls:</h5>
                                            <div class="legend-controls_info_page">
                                                <!-- CN Regions -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch" style="background-color: #9467bd;"></span>
                                                    <div class="legend-text">
                                                        <strong>CN Regions (CNV Events)</strong>
                                                        <em class="hint">Click to hide/show detected copy number regions for this chromosome</em>
                                                    </div>
                                                </div>

                                                <!-- ROH+CN Overlaps -->
                                                <div class="legend-item_info_page">
                                                    <span class="color-swatch" style="background-color: #8c564b;"></span>
                                                    <div class="legend-text">
                                                        <strong>ROH+CN Overlaps</strong>
                                                        <em class="hint">Shows regions with both ROH and CN changes (possible CN-LOH or copy-LOH)</em>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Right Column - Navigation & Features -->
                                        <div class="guide-column-right_info_page">
                                            <div class="plot-features_info_page">
                                                <h5>CNV Event Visualization:</h5>
                                                <div class="feature-list_info_page">
                                                    <div class="feature-line_info_page">
                                                        <strong>Deletion Events: </strong>
                                                        Purple color with copy number drop (CN < 2) on the copy number plot
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Duplication Events: </strong>
                                                        Green color with copy number increase (CN > 2) on the copy number plot
                                                    </div>
                                                </div>
                                                
                                                <h5>Bokeh Interactive Features:</h5>
                                                <div class="feature-list_info_page">
                                                    <div class="feature-line_info_page">
                                                        <strong>Zoom In/Out: </strong>
                                                        Use mouse wheel or zoom tool to focus on specific genomic regions
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Pan/Navigate: </strong>
                                                        Click and drag to move around the chromosome view
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Reset View: </strong>
                                                        Use the reset tool to return to full chromosome view
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Box Zoom: </strong>
                                                        Select box zoom tool to zoom into a specific rectangular area
                                                    </div>
                                                    <div class="feature-line_info_page">
                                                        <strong>Hover Details: </strong>
                                                        Hover over SNPs to see detailed BAF/LRR values and genomic positions
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Full width bottom section -->
                                    <p class="demo-instruction_info_page">
                                        Explore the combined BAF-LRR-CN plots: use Bokeh tools to zoom into CNV regions, 
                                        toggle legend items to focus on specific events, and examine SNP-level changes 
                                        that support the detected copy number variations.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
                
                <!-- HOW TO ANALYZE YOUR DATA SECTION - ADDED HERE -->
                <div class="main-section_info_page">
                    <h2>How to Analyze your Data</h2>
                    <!-- Deletion Event Analysis Dropdown -->
                    <div class="dropdown-section_info_page">
                        <button class="dropdown-toggle_info_page">Deletion Event Analysis</button>
                        <div class="dropdown-content_info_page">
                            <div class="dropdown-grid_info_page">
                                <!-- Left Column - Plot -->
                                <div class="plot-container_info_page">
                                    <h3>Deletion Example (Chromosome 1)</h3>
                                    <div id="deletion-example-plot" class="plot-placeholder_info_page" style="min-height: 900px;"></div>
                                    <script>
                                        try {{
                                            let delPlotData = {deletion_plot_json};
                                            console.log("Deletion plot data type:", typeof delPlotData);
                                            
                                            if (typeof delPlotData === 'string') {{
                                                try {{
                                                    delPlotData = JSON.parse(delPlotData);
                                                }} catch (parseError) {{
                                                    console.error("Deletion plot parse error:", parseError);
                                                }}
                                            }}
                                            
                                            if (delPlotData && !delPlotData.error) {{
                                                Bokeh.embed.embed_item(delPlotData, "deletion-example-plot");
                                            }} else {{
                                                const errorMsg = delPlotData?.error || 'Deletion plot data not available';
                                                document.getElementById('deletion-example-plot').innerHTML =
                                                    `<div class="plot-error">${{errorMsg}}</div>`;
                                            }}
                                        }} catch (e) {{
                                            console.error('Deletion plot error:', e);
                                            document.getElementById('deletion-example-plot').innerHTML =
                                                `<div class="plot-error">Plot error: ${{e.message}}</div>`;
                                        }}
                                    </script>
                                </div>
                                
                                <!-- Right Column - Explanation -->
                                <div class="text-placeholder_info_page">
                                    <div class="guide-box_info_page">
                                        <h4>Identifying Deletion Events</h4>
                                        <p>Deletion events are characterized by:</p>
                                        <ul>
                                            <li>Decreased LRR values (typically around -0.5)</li>
                                            <li>Absence of heterozygous BAF values (0.5)</li>
                                            <li>BAF values clustered at 0 and 1 only</li>
                                            <li>Fewer SNPs detected in the region</li>
                                        </ul>
                                        
                                        <p>When analyzing potential deletions, look for:</p>
                                        <ul>
                                            <li>Clear downward shift in LRR plot</li>
                                            <li>Absence of the middle BAF band (0.5)</li>
                                            <li>Sharp transitions at deletion boundaries</li>
                                            <li>Consistent pattern across the entire region</li>
                                        </ul>
                                        
                                        <p>Confirmed deletions will have a copy number (CN) of 1 or 0, reflecting the loss of genetic material.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Duplication Event Analysis Dropdown -->
                    <div class="dropdown-section_info_page">
                        <button class="dropdown-toggle_info_page">Duplication Event Analysis</button>
                        <div class="dropdown-content_info_page">
                            <div class="dropdown-grid_info_page">
                                <!-- Left Column - Plot -->
                                <div class="plot-container_info_page">
                                    <h3>Duplication Example (Chromosome 8)</h3>
                                    <div id="duplication-example-plot" class="plot-placeholder_info_page" style="min-height: 900px;"></div>
                                    <script>
                                        try {{
                                            let dupPlotData = {duplication_plot_json};
                                            if (typeof dupPlotData === 'string') {{
                                                try {{
                                                    dupPlotData = JSON.parse(dupPlotData);
                                                }} catch (parseError) {{
                                                    console.error("Duplication plot parse error:", parseError);
                                                }}
                                            }}
                                            
                                            if (dupPlotData && !dupPlotData.error) {{
                                                Bokeh.embed.embed_item(dupPlotData, "duplication-example-plot");
                                            }} else {{
                                                document.getElementById('duplication-example-plot').innerHTML =
                                                    `<div class="plot-error">Duplication plot data not available</div>`;
                                            }}
                                        }} catch (e) {{
                                            console.error('Duplication plot error:', e);
                                            document.getElementById('duplication-example-plot').innerHTML =
                                                `<div class="plot-error">Plot error: ${{e.message}}</div>`;
                                        }}
                                    </script>
                                </div>
                                
                                <!-- Right Column - Explanation -->
                                <div class="text-placeholder_info_page">
                                    <div class="guide-box_info_page">
                                        <h4>Identifying Duplication Events</h4>
                                        <p>Duplication events are characterized by:</p>
                                        <ul>
                                            <li>Increased LRR values (typically around +0.3 to +0.4)</li>
                                            <li>BAF values forming four bands at 0, 0.33, 0.67, and 1</li>
                                            <li>Typically more SNPs detected in the region</li>
                                        </ul>
                                        
                                        <p>When analyzing potential duplications, look for:</p>
                                        <ul>
                                            <li>Clear upward shift in LRR plot</li>
                                            <li>Split of the heterozygous BAF band into two bands at 0.33 and 0.67</li>
                                            <li>Sharp transitions at duplication boundaries</li>
                                            <li>Consistent pattern across the entire region</li>
                                        </ul>
                                        
                                        <p>Confirmed duplications will have a copy number (CN) of 3 or higher, reflecting the gain of genetic material.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Copy Neutral LOH Analysis Dropdown -->
                    <div class="dropdown-section_info_page">
                        <button class="dropdown-toggle_info_page">Copy Neutral LOH Analysis</button>
                        <div class="dropdown-content_info_page">
                            <div class="dropdown-grid_info_page">
                                <!-- Left Column - Plot -->
                                <div class="plot-container_info_page">
                                    <h3>Copy Neutral LOH Example (Chromosome 7)</h3>
                                    <div id="cnloh-example-plot" class="plot-placeholder_info_page" style="min-height: 900px;"></div>
                                    <script>
                                        try {{
                                            let cnlohPlotData = {cnloh_plot_json};
                                            if (typeof cnlohPlotData === 'string') {{
                                                try {{
                                                    cnlohPlotData = JSON.parse(cnlohPlotData);
                                                }} catch (parseError) {{
                                                    console.error("CN-LOH plot parse error:", parseError);
                                                }}
                                            }}
                                            
                                            if (cnlohPlotData && !cnlohPlotData.error) {{
                                                Bokeh.embed.embed_item(cnlohPlotData, "cnloh-example-plot");
                                            }} else {{
                                                document.getElementById('cnloh-example-plot').innerHTML =
                                                    `<div class="plot-error">CN-LOH plot data not available</div>`;
                                            }}
                                        }} catch (e) {{
                                            console.error('CN-LOH plot error:', e);
                                            document.getElementById('cnloh-example-plot').innerHTML =
                                                `<div class="plot-error">Plot error: ${{e.message}}</div>`;
                                        }}
                                    </script>
                                </div>
                                
                                <!-- Right Column - Explanation -->
                                <div class="text-placeholder_info_page">
                                    <div class="guide-box_info_page">
                                        <h4>Identifying Copy Neutral LOH</h4>
                                        <p>Copy neutral loss of heterozygosity (CN-LOH) is characterized by:</p>
                                        <ul>
                                            <li>Normal LRR values (around 0)</li>
                                            <li>Absence of heterozygous BAF values (0.5)</li>
                                            <li>BAF values clustered at only 0 and 1</li>
                                            <li>Normal number of SNPs detected</li>
                                        </ul>
                                        
                                        <p>When analyzing potential CN-LOH regions, look for:</p>
                                        <ul>
                                            <li>No significant shift in LRR plot (distinguishing it from deletions)</li>
                                            <li>Complete absence of the middle BAF band (0.5)</li>
                                            <li>Sharp transitions at region boundaries</li>
                                            <li>Extended regions of homozygosity</li>
                                        </ul>
                                        
                                        <p>CN-LOH represents regions where one parental copy has been lost and the remaining copy has been duplicated, resulting in normal total copy number (CN=2) but loss of heterozygosity.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Mixed CNV Analysis Dropdown -->
                    <div class="dropdown-section_info_page">         
                        <button class="dropdown-toggle_info_page">Mixed CNV Events Analysis</button>
                        <div class="dropdown-content_info_page">
                            <div class="dropdown-grid_info_page">
                                <!-- Left Column - Plot -->
                                <div class="plot-container_info_page">
                                    <h3>Mixed CNV Example (Chromosome 19)</h3>
                                    <div id="mixed-cnv-example-plot" class="plot-placeholder_info_page" style="min-height: 900px;"></div>
                                    <script>
                                        try {{
                                            let mixedPlotData = {mixed_plot_json};
                                            if (typeof mixedPlotData === 'string') {{
                                                try {{
                                                    mixedPlotData = JSON.parse(mixedPlotData);
                                                }} catch (parseError) {{
                                                    console.error("Mixed CNV plot parse error:", parseError);
                                                }}
                                            }}
                                            
                                            if (mixedPlotData && !mixedPlotData.error) {{
                                                Bokeh.embed.embed_item(mixedPlotData, "mixed-cnv-example-plot");
                                            }} else {{
                                                document.getElementById('mixed-cnv-example-plot').innerHTML =
                                                    `<div class="plot-error">Mixed CNV plot data not available</div>`;
                                            }}
                                        }} catch (e) {{
                                            console.error('Mixed CNV plot error:', e);
                                            document.getElementById('mixed-cnv-example-plot').innerHTML =
                                                `<div class="plot-error">Plot error: ${{e.message}}</div>`;
                                        }}
                                    </script>
                                </div>
                                
                                <!-- Right Column - Explanation -->
                                <div class="text-placeholder_info_page">
                                    <div class="guide-box_info_page">
                                        <h4>Analyzing Chromosomes with Multiple CNV Types</h4>
                                        <p>Chromosomes often contain multiple types of CNV events that need to be differentiated:</p>
                                        <ul>
                                            <li>Look for clear transitions between regions with different patterns</li>
                                            <li>Compare LRR shifts with BAF pattern changes to classify each region</li>
                                            <li>Pay attention to the boundaries between different CNV events</li>
                                            <li>Consider the biological context of the sample</li>
                                        </ul>
                                        
                                        <p>Key differentiation points:</p>
                                        <ul>
                                            <li>Deletions: Low LRR, BAF at 0/1 only</li>
                                            <li>Duplications: High LRR, BAF showing 0, 0.33, 0.67, 1 pattern</li>
                                            <li>CN-LOH: Normal LRR, BAF at 0/1 only</li>
                                            <li>Normal regions: Normal LRR, BAF at 0, 0.5, 1</li>
                                        </ul>
                                        
                                        <p>Complex chromosomal alterations might require integration with other genomic data for full interpretation.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        
        return existing_html

    def _get_all_simulated_metrics(self):
        single_metrics = [s.metrics for s in self.single_simulated]
        paired_metrics = [p.combined_metrics for p in self.paired_simulated]
        return single_metrics, paired_metrics

    def _generate_simulated_metrics_html(self, single_metrics, paired_metrics):
        """Generate HTML for both sample types"""
        html = []
        
        # Single samples section
        html.append('<div class="metric-box_info_page"><h3><i class="fas fa-dna"></i> Single Simulations</h3>')
        for sm in single_metrics:
            html.append(f'''
                <div class="metric-subbox_info_page">
                    <h4>{sm['id']}</h4>
                    <div class="metric-grid_info_page">
                        <div class="metric-item_info_page"><span>Chromosomes:</span><span>{sm['total_chromosomes']}</span></div>
                        <div class="metric-item_info_page"><span>CNVs:</span><span>{sm['total_cnvs']}</span></div>
                        <div class="metric-item_info_page"><span>Data Points:</span><span>{sm['data_points']}</span></div>
                        <div class="metric-item_info_page"><span>ROH Regions:</span><span>{sm['total_roh']}</span></div>
                    </div>
                </div>
            ''')
        html.append('</div>')
        
        # Paired samples section
        html.append('<div class="metric-box_info_page"><h3><i class="fas fa-dna"></i> Paired Simulations</h3>')
        for pm in paired_metrics:
            html.append(f'''
                <div class="metric-subbox">
                    <h4>{pm['pair_id']}</h4>
                    <div class="metric-grid">
                        <div class="metric-item_info_page"><span>Shared CNVs:</span><span>{pm['shared_cnvs']}</span></div>
                        <div class="metric-item_info_page"><span>Discordant CNVs:</span><span>{pm['discordant_cnvs']}</span></div>
                        <div class="metric-item_info_page"><span>Total Data Points:</span><span>{pm['combined_data_points']}</span></div>
                        <div class="metric-item_info_page"><span>Total CNVs:</span><span>{pm['total_cnvs']}</span></div>
                    </div>
                </div>
            ''')
        html.append('</div>')
        
        return '\n'.join(html)

    def _get_info_box_content(self, single_metrics, paired_metrics):
        """Generate info box content for all sample types"""
        content = ['<div class="info-box scrollable">']
        
        if single_metrics:
            content.append('<h3><i class="fas fa-vial"></i> Single Simulations</h3>')
            for sm in single_metrics:
                content.append(f'''
                    <p><strong>{sm['id']}:</strong><br>
                    - Directory: {sm['dir']}<br>
                    - Chromosomes: {sm['total_chromosomes']}<br>
                    - Data Points: {sm['data_points']}</p>
                ''')
        
        if paired_metrics:
            content.append('<h3><i class="fas fa-vials"></i> Paired Simulations</h3>')
            for pm in paired_metrics:
                content.append(f'''
                    <p><strong>{pm['pair_id']}:</strong><br>
                    - Directory: {pm['dir']}<br>
                    - Pre Sample: {pm['pre']}<br>
                    - Post Sample: {pm['post']}<br>
                    - Shared CNVs: {pm['shared_cnvs']}</p>
                ''')
        
        content.append('</div>')
        return '\n'.join(content)

    def save(self):
        """Save the information page to components directory"""
        try:
            output_path = self.components_dir / "info.html"
            html_content = self.generate()
            
            with open(output_path, 'w') as f:
                f.write(html_content)
            
            logging.info("Saved information page to: %s", output_path)
            return output_path
            
        except Exception as e:
            logging.error(f"Error saving information page: {str(e)}")
            raise 