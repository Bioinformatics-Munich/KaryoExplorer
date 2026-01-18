nextflow.enable.dsl=2

/*
========================================================================================
    REPORTING: FINAL REPORTS & DOCUMENTATION
========================================================================================
    Final report generation and documentation processes
----------------------------------------------------------------------------------------
*/

process PARAMETER_REPORT {
    
    tag "Generating parameter report"
    label 'process_low'

    publishDir "${params.outdir}/0.0_information/0.3_reports", mode: 'copy', overwrite: true

    input:
        // No inputs needed - uses global params

    output:
        path "pipeline_parameters.json", emit: parameters
        path "parameter_report.md", emit: parameter_md

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Generating parameter report"
        
        # Create JSON parameter file
        cat > pipeline_parameters.json << EOF
        {
            "pipeline_info": {
                "name": "${params.app_name}",
                "version": "${params.pipeline_version}",
                "run_date": "\$(date)",
                "nextflow_version": "${workflow.nextflow.version}",
                "command_line": "${workflow.commandLine}",
                "profile": "${workflow.profile}",
                "work_dir": "${workflow.workDir}",
                "project_dir": "${workflow.projectDir}"
            },
            "project_info": {
                "project_ID": "${params.project_ID}",
                "responsible_person": "${params.responsible_person}"
            },
            "input_parameters": {
                "manifest": "${params.manifest}",
                "PAR": "${params.PAR}",
                "fullTable": "${params.fullTable}",
                "samplesTable": "${params.samplesTable}",
                "snpTable": "${params.snpTable}",
                "gsplink": "${params.gsplink}",
                "fasta": "${params.fasta}",
                "outdir": "${params.outdir}"
            },
            "cnv_parameters": {
                "excluded_chr": "${params.excluded_chr}",
                "cnv_p_threshold": ${params.cnv_p_threshold},
                "baf_threshold": ${params.baf_threshold},
                "lrr_min": ${params.lrr_min},
                "lrr_max": ${params.lrr_max},
                "lohc_threshold": ${params.lohc_threshold},
                "min_sites": ${params.min_sites},
                "weight_lrr": ${params.weight_lrr}
            },
            "reference_genome": {
                "par_file": "${params.PAR}",
                "detected": "\$(basename ${params.PAR} | grep -q 'GRCh37' && echo 'GRCh37' || echo 'GRCh38')"
            },
            "qc_parameters": {
                "qs_thr": ${params.qs_thr},
                "nSites_thr": ${params.nSites_thr},
                "nHet_thr": ${params.nHet_thr},
                "CN_len_thr": ${params.CN_len_thr},
                "CN_len_thr_big": ${params.CN_len_thr_big},
                "width_plot": ${params.width_plot},
                "clust_sep_as": ${params.clust_sep_as},
                "ABR_mean_as": ${params.ABR_mean_as},
                "AAR_mean_as": ${params.AAR_mean_as},
                "BBR_mean_as": ${params.BBR_mean_as},
                "ABT_mean_low_as": ${params.ABT_mean_low_as},
                "ABT_mean_up_as": ${params.ABT_mean_up_as},
                "het_low_as": ${params.het_low_as},
                "het_up_as": ${params.het_up_as},
                "MAF_as": ${params.MAF_as},
                "AAT_mean_as": ${params.AAT_mean_as},
                "AAT_dev_as": ${params.AAT_dev_as},
                "BBT_mean_as": ${params.BBT_mean_as},
                "BBT_dev_as": ${params.BBT_dev_as},
                "male_frac": ${params.male_frac},
                "R_hpY": ${params.R_hpY},
                "female_frac": ${params.female_frac}
            }
        }
EOF

        # Create Markdown parameter report
        cat > parameter_report.md << EOF
# ${params.app_name} - Parameter Report

**Generated on:** \$(date)  
**Pipeline Version:** ${params.pipeline_version}  
**Nextflow Version:** ${workflow.nextflow.version}  
**Profile:** ${workflow.profile}  

        ## Command Line
        \\`\\`\\`
        ${workflow.commandLine}
        \\`\\`\\`

## Project Information
| Parameter | Value |
|-----------|-------|
| Project ID | ${params.project_ID} |
| Responsible Person | ${params.responsible_person} |

## Input Files
| Parameter | Value |
|-----------|-------|
| Manifest | ${params.manifest} |
| PAR File | ${params.PAR} |
| Full Table | ${params.fullTable} |
| Samples Table | ${params.samplesTable} |
| SNP Table | ${params.snpTable} |
| PLINK Data | ${params.gsplink} |
| Reference FASTA | ${params.fasta} |
| Output Directory | ${params.outdir} |

## CNV Analysis Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| excluded_chr | ${params.excluded_chr} | Chromosomes excluded from analysis |
| cnv_p_threshold | ${params.cnv_p_threshold} | CNV probability threshold |
| baf_threshold | ${params.baf_threshold} | B-allele frequency threshold |
| lrr_min | ${params.lrr_min} | Minimum Log R Ratio |
| lrr_max | ${params.lrr_max} | Maximum Log R Ratio |
| lohc_threshold | ${params.lohc_threshold} | Loss of heterozygosity threshold |
| min_sites | ${params.min_sites} | Minimum number of sites |
| weight_lrr | ${params.weight_lrr} | LRR weight parameter |

## Quality Control Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| clust_sep_as | ${params.clust_sep_as} | Cluster separation threshold |
| ABR_mean_as | ${params.ABR_mean_as} | ABR mean threshold |
| AAR_mean_as | ${params.AAR_mean_as} | AAR mean threshold |
| BBR_mean_as | ${params.BBR_mean_as} | BBR mean threshold |
| het_up_as | ${params.het_up_as} | Upper heterozygosity threshold |
| male_frac | ${params.male_frac} | Male fraction threshold |
| female_frac | ${params.female_frac} | Female fraction threshold |
EOF
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Parameter report generation completed"
        """
}

process HTML_OUTPUT_DESCRIPTION {
    
    tag "Generating HTML output description"
    label 'process_low'

    publishDir "${params.outdir}", mode: 'copy', overwrite: true

    conda "${baseDir}/env/pandoc.yaml"

    input:
        path r_version
        path plink_version
        path bcftools_version
        path vcftools_version

    output:
        path "README.html", emit: html_description

    when:
        r_version && plink_version && bcftools_version && vcftools_version

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Generating HTML output description from Outputs.md"
        
        # Copy Outputs.md from docs directory
        cp ${baseDir}/docs/Outputs.md ./Outputs.md
        
        # Replace <app_name> placeholder with actual app_name parameter
        sed -i 's|<app_name>|${params.app_name}|g' ./Outputs.md
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Replaced <app_name> placeholder with: ${params.app_name}"
        
        # Append version information
        echo "" >> ./Outputs.md
        echo "# Software Versions" >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo "**Generated on:** \$(date)" >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo "## Tools Used" >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo "- **R Version:**" >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo '```' >> ./Outputs.md
        head -n 1 ${r_version} >> ./Outputs.md
        echo '```' >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo "- **PLINK Version:**" >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo '```' >> ./Outputs.md
        head -n 1 ${plink_version} >> ./Outputs.md
        echo '```' >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo "- **BCFtools Version:**" >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo '```' >> ./Outputs.md
        head -n 1 ${bcftools_version} >> ./Outputs.md
        echo '```' >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo "- **VCFtools Version:**" >> ./Outputs.md
        echo "" >> ./Outputs.md
        echo '```' >> ./Outputs.md
        head -n 1 ${vcftools_version} >> ./Outputs.md
        echo '```' >> ./Outputs.md
        
        # Create custom CSS file for better styling
        cat > custom_style.css << 'EOF'
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #24292e;
    background-color: #f6f8fa;
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
}
#TOC {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 20px;
    margin-bottom: 30px;
    box-shadow: 0 1px 3px rgba(27,31,35,0.12);
    position: relative;
}
#TOC h2 {
    margin-top: 0;
    color: #24292e;
    font-size: 1.5em;
    cursor: pointer;
    user-select: none;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
#TOC h2:hover {
    color: #0969da;
}
#TOC h2::after {
    content: '▼';
    font-size: 0.8em;
    transition: transform 0.3s ease;
    margin-left: 10px;
}
#TOC.collapsed h2::after {
    transform: rotate(-90deg);
}
#TOC-content {
    max-height: 600px;
    overflow-y: auto;
    transition: max-height 0.3s ease;
}
#TOC.collapsed #TOC-content {
    max-height: 0;
    overflow: hidden;
}
#TOC ul {
    list-style-type: none;
    padding-left: 20px;
}
#TOC li {
    margin: 8px 0;
}
#TOC a {
    color: #0969da;
    text-decoration: none;
}
#TOC a:hover {
    text-decoration: underline;
}
main {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 45px;
    box-shadow: 0 1px 3px rgba(27,31,35,0.12);
}
h1 {
    border-bottom: 3px solid #2c3e50;
    padding-bottom: 0.3em;
    color: #2c3e50;
    font-size: 2.5em;
    margin-top: 24px;
    margin-bottom: 16px;
}
h2 {
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.3em;
    color: #34495e;
    font-size: 2em;
    margin-top: 24px;
    margin-bottom: 16px;
}
h3 {
    color: #2980b9;
    font-size: 1.5em;
    margin-top: 24px;
    margin-bottom: 16px;
}
h4 {
    color: #27ae60;
    font-size: 1.25em;
}
code {
    background-color: #f6f8fa;
    border: 1px solid #d0d7de;
    border-radius: 3px;
    font-size: 85%;
    padding: 0.2em 0.4em;
    font-family: ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace;
}
pre {
    background-color: #f6f8fa;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 16px;
    overflow: auto;
    line-height: 1.45;
}
pre code {
    background-color: transparent;
    border: none;
    padding: 0;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0;
    box-shadow: 0 1px 3px rgba(27,31,35,0.1);
}
th {
    background-color: #3498db;
    color: white;
    font-weight: 600;
    padding: 12px;
    text-align: left;
    border: 1px solid #2980b9;
}
td {
    padding: 12px;
    border: 1px solid #d0d7de;
}
tr:nth-child(even) {
    background-color: #f6f8fa;
}
tr:hover {
    background-color: #e3f2fd;
}
blockquote {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 15px 20px;
    margin: 20px 0;
    border-radius: 4px;
    color: #856404;
}
a {
    color: #0969da;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
hr {
    border: 0;
    border-top: 2px solid #d0d7de;
    margin: 24px 0;
}
.version-info {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-left: 4px solid #28a745;
    padding: 15px 20px;
    margin: 20px 0;
    border-radius: 4px;
    color: #155724;
}
EOF
        
        # Convert Markdown to HTML using pandoc with embedded CSS styling
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Converting Outputs.md to README.html using pandoc"
        pandoc Outputs.md -o README.html \\
            --standalone \\
            --metadata title="${params.app_name} - Output Guide" \\
            --toc \\
            --toc-depth=3 \\
            --css=custom_style.css \\
            --self-contained
        
        # Add JavaScript to make TOC collapsible by inserting before closing tags
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Adding interactive TOC collapse functionality"
        
        # Create temp file with JavaScript
        cat > toc_script.js << 'JSEOF'
<script>
document.addEventListener('DOMContentLoaded', function() {
    var toc = document.getElementById('TOC');
    if (toc) {
        // Wrap TOC content
        var tocH2 = toc.querySelector('h2');
        var tocContent = document.createElement('div');
        tocContent.id = 'TOC-content';
        
        // Move all children after h2 into the content div
        var children = Array.from(toc.children);
        children.forEach(function(child) {
            if (child !== tocH2) {
                tocContent.appendChild(child);
            }
        });
        toc.appendChild(tocContent);
        
        // Add click handler to h2
        tocH2.addEventListener('click', function() {
            toc.classList.toggle('collapsed');
        });
        
        // Add title attribute for hint
        tocH2.title = 'Click to expand/collapse';
    }
});
</script>
JSEOF
        
        # Insert JavaScript before closing body tag
        sed -i 's|</body>|<script>|' README.html
        cat toc_script.js | grep -v '<script>' >> README.html
        echo '</body>' >> README.html
        echo '</html>' >> README.html
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: HTML output description generation completed"
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: CSS styling embedded in README.html for portable viewing"
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Interactive Table of Contents added"
        """
}
