nextflow.enable.dsl=2

/*
========================================================================================
    CNV ANALYSIS: SUMMARY & REPORTING
========================================================================================
    CNV summary processes and table generation
----------------------------------------------------------------------------------------
*/

process CNV_SUMMARY_SINGLE {
    
    tag "CNV summary: ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/7.2_CNV_single", mode: 'copy', overwrite: true, pattern: "${pre}"

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(sex), val(pre), val(post), path(cnv_dir)

    output:
        tuple val(sex), val(pre), val(post), path(cnv_dir), path("${pre}"), emit: cnv_single
        val pre, emit: cnv_single_pre
        path "${pre}", emit: cnv_single_path

    when:
        cnv_dir && pre

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting CNV summary for single sample: ${pre}"
        
        mkdir "${pre}"
        
        ${projectDir}/bin/cnv/summary_CNSingleAnalysis_run.R \\
            --inputdir outdir_${pre} \\
            --line ${pre} \\
            --sample_name ${pre} \\
            --sex ${sex} \\
            --outf ${pre}/ \\
            --fold_fun ${projectDir}/bin/functions/ \\
            --qs_thr ${params.qs_thr} \\
            --nSites_thr ${params.nSites_thr} \\
            --nHet_thr ${params.nHet_thr} \\
            --CN_len_thr ${params.CN_len_thr} \\
            --width_plot ${params.width_plot}
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: CNV summary completed for ${pre}"
        """
}

process CNV_PLOT_SUMMARY {
    
    tag "CNV plot summary: ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/09_cnv_differential_summary", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(pre), val(post), path(summary_dirs)

    output:
        val pre, emit: cnv_summary_sample

    when:
        pre && summary_dirs

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting CNV plot summary for ${pre}"
        
        IFS=', ' read -r -a postarray <<< "${post.join(',')}"
        
        ${projectDir}/bin/cnv/summary_diffCNmultiple.R --outf ${pre} --post \${postarray[*]} --pre ${pre} --width_plot 20
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: CNV plot summary completed for ${pre}"
        """
}

process CNV_PAIRED_TABLES_SUMMARY {
    
    tag "Creating paired CNV tables summary"
    label 'process_low'

    // publishDir "${params.outdir}/8_CNV_single_paired_summary/paired", mode: 'copy', overwrite: true

    input:
        path summary_paths

    output:
        path "CNV_table_summary_paired.tsv", emit: cnv_table_summary

    when:
        summary_paths

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Creating paired CNV tables summary"
        
        # Combine all summary files
        find . -name "*filt*.tsv" -type f | head -1 | xargs head -1 > CNV_table_summary_paired.tsv
        find . -name "*filt*.tsv" -type f -exec tail -n +2 {} \\; >> CNV_table_summary_paired.tsv
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Paired CNV tables summary completed"
        echo "Combined \$(find . -name '*filt*.tsv' | wc -l) summary files"
        """
}

process CNV_SINGLE_TABLES_SUMMARY {
    
    tag "Creating single CNV tables summary"
    label 'process_low'

    // publishDir "${params.outdir}/8_CNV_single_paired_summary/single", mode: 'copy', overwrite: true

    input:
        path summary_paths

    output:
        path "CNV_table_summary_single.tsv", emit: cnv_table_summary

    when:
        summary_paths

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Creating single CNV tables summary"
        
        # Use legacy approach - explicit path handling like the original code
        IFS=', ' read -r -a patharray <<< "${summary_paths.join(',')}"
        
        # Create header from first file
        if [ \${#patharray[@]} -gt 0 ]; then
            head -n 1 "\${patharray[0]}/CNV_detection_filt_\${patharray[0]}.tsv" > CNV_table_summary_single.tsv
            
            # Append data from all files
            for path in "\${patharray[@]}"
            do
                if [ -f "\${path}/CNV_detection_filt_\${path}.tsv" ]; then
                    tail -n +2 "\${path}/CNV_detection_filt_\${path}.tsv" >> CNV_table_summary_single.tsv
                else
                    echo "Warning: File \${path}/CNV_detection_filt_\${path}.tsv not found"
                fi
            done
        else
            echo "sample\tchr\tstart\tend\tcn\tqs\tnSites\tnHets\tlength\ttype" > CNV_table_summary_single.tsv
        fi
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Single CNV tables summary completed"
        echo "Combined \${#patharray[@]} summary files"
        """
}

process CNV_PAIRED_SUMMARY_MD {
    
    tag "Creating paired CNV markdown summary"
    label 'process_low'

    // publishDir "${params.outdir}/8_CNV_single_paired_summary", mode: 'copy', overwrite: true

    input:
        val summary_samples
        path summary_paths

    output:
        path "CNV_summary_paired.md", emit: summary_md

    when:
        summary_samples && summary_paths

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Creating paired CNV markdown summary"
        
        echo "# CNV Analysis Summary - Paired Samples" > CNV_summary_paired.md
        echo "" >> CNV_summary_paired.md
        echo "Analysis completed on: \$(date)" >> CNV_summary_paired.md
        echo "" >> CNV_summary_paired.md
        echo "## Summary Statistics" >> CNV_summary_paired.md
        echo "- Total samples analyzed: \$(echo '${summary_samples}' | tr ' ' '\\n' | wc -l)" >> CNV_summary_paired.md
        echo "- Analysis directories: \$(echo '${summary_paths}' | tr ' ' '\\n' | wc -l)" >> CNV_summary_paired.md
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Paired CNV markdown summary completed"
        """
}

process CNV_SINGLE_SUMMARY_MD {
    
    tag "Creating single CNV markdown summary"
    label 'process_low'

    // publishDir "${params.outdir}/8_CNV_single_paired_summary", mode: 'copy', overwrite: true

    input:
        val summary_samples
        path summary_paths

    output:
        path "CNV_summary_single.md", emit: summary_md

    when:
        summary_samples && summary_paths

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Creating single CNV markdown summary"
        
        echo "# CNV Analysis Summary - Single Samples" > CNV_summary_single.md
        echo "" >> CNV_summary_single.md
        echo "Analysis completed on: \$(date)" >> CNV_summary_single.md
        echo "" >> CNV_summary_single.md
        echo "## Summary Statistics" >> CNV_summary_single.md
        echo "- Total samples analyzed: \$(echo '${summary_samples}' | tr ' ' '\\n' | wc -l)" >> CNV_summary_single.md
        echo "- Analysis directories: \$(echo '${summary_paths}' | tr ' ' '\\n' | wc -l)" >> CNV_summary_single.md
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Single CNV markdown summary completed"
        """
}
