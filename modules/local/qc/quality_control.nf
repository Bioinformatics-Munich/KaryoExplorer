nextflow.enable.dsl=2

/*
========================================================================================
    QUALITY CONTROL
========================================================================================
    Processes for data quality control and preprocessing
----------------------------------------------------------------------------------------
*/

process QC_MAIN_ANALYSIS {
    
    tag "01_QC (QC_MAIN_ANALYSIS) | ${manifest.simpleName}"
    label 'process_medium'

    publishDir "${params.outdir}/1.0_quality_control/1.1_QC_results", 
        mode: 'copy', 
        overwrite: true,
        pattern: "QC_results_flat/*",
        saveAs: { filename -> filename.replaceFirst("QC_results_flat/", "") }
    
    conda "${baseDir}/env/renv.yaml"

    input:
        path manifest
        path par_file
        val nhead
        path fullTable
        path samplesTable
        path snpTable
        val het_up_as
        val clust_sep_as
        val ABR_mean_as
        val AAR_mean_as
        val BBR_mean_as
        val ABT_mean_low_as
        val ABT_mean_up_as
        val het_low_as
        val MAF_as
        val AAT_mean_as
        val AAT_dev_as
        val BBT_mean_as
        val BBT_dev_as
        val male_frac
        val R_hpY
        val female_frac

    output:
        path "QC_results_flat/*", emit: qc_files
        path "QC_results", emit: qc_dir
        path "Full_Data_Table_filt.txt", emit: fullTable_filt
        path "Samples_Table_filt.txt", emit: samplesTable_filt
        path "Samples_Table_filt_QC.tsv", emit: samplesTable_filt_QC
        path "LRR_table.txt", emit: lrr_table
        path "BAF_table.txt", emit: baf_table
        path "GT_table.txt", emit: gt_table
        path "GT_comp.txt", emit: gt_comp

    when:
        manifest && par_file && fullTable && samplesTable && snpTable

    script:
        manifest_name = manifest.simpleName
        manifest_name = manifest_name.replaceAll(/-/, '.')
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting main QC analysis for ${manifest_name}"
        
        mkdir -p QC_results
        
        # Step 1: Build PAR SNP file
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Building PAR SNP file"
        ${projectDir}/bin/qc/PAR_SNP_build_run.R --manifest_file $manifest --PAR_file $par_file --n_header_line $nhead
        
        # Step 2: Extract LRR/BAF data and perform QC
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracting LRR/BAF data and performing quality control"
        ${projectDir}/bin/qc/QC_extract_LRR_BAF_run.R \\
            --manifest_name $manifest_name \\
            --SNP_table_file $snpTable \\
            --Full_table_file $fullTable \\
            --Sample_table_file $samplesTable \\
            --PAR_file PAR_SNPs.txt \\
            --ncores ${task.cpus} \\
            --fold_fun ${projectDir}/bin/functions/ \\
            --het_up_as ${het_up_as} \\
            --clust_sep_as ${clust_sep_as} \\
            --ABR_mean_as ${ABR_mean_as} \\
            --AAR_mean_as ${AAR_mean_as} \\
            --BBR_mean_as ${BBR_mean_as} \\
            --ABT_mean_low_as ${ABT_mean_low_as} \\
            --ABT_mean_up_as ${ABT_mean_up_as} \\
            --het_low_as ${het_low_as} \\
            --MAF_as ${MAF_as} \\
            --AAT_mean_as ${AAT_mean_as} \\
            --AAT_dev_as ${AAT_dev_as} \\
            --BBT_mean_as ${BBT_mean_as} \\
            --BBT_dev_as ${BBT_dev_as} \\
            --male_frac ${male_frac} \\
            --R_hpY ${R_hpY} \\
            --female_frac ${female_frac}
        
        # Step 3: Generate QC plots
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Generating QC plots"
        
        # Create temporary file with sample_ID for plotting script compatibility
        cp Samples_Table_filt.txt temp_plot_samples.txt
        sed -i '1s/Sample\\.ID/sample_ID/' temp_plot_samples.txt
        
        ${projectDir}/bin/plotting/plot_sample_QC_run.R --sample_table_file temp_plot_samples.txt --SNP_table_info_file info_QC.txt --outf 'QC_results'
        
        # Copy results to QC directory
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Organizing QC results"
        cp Full_Data_Table_filt.txt Samples_Table_filt.txt LRR_table.txt BAF_table.txt GT_table.txt GT_comp.txt GT_comp.tsv LRR_stdev_table.tsv Samples_Table_filt_QC.tsv QC_results/
        cp QC_results/Samples_Table_filt.txt QC_results/Samples_Table_filt.tsv
        
        # Standardize column names to Sample.ID convention
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Standardizing column names to Sample.ID convention"
        sed -i '1s/sample_ID/Sample.ID/' Samples_Table_filt.txt
        
        # Create flat directory for publishing
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Creating flat QC results directory for publishing"
        mkdir -p QC_results_flat
        cp QC_results/* QC_results_flat/
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: QC analysis completed successfully"
        echo "Filtered samples: \$(tail -n +2 Samples_Table_filt.txt | wc -l)"
        echo "QC SNPs: \$(tail -n +2 Full_Data_Table_filt.txt | wc -l)"
        """
}

process QC_PREPARE_ANNOTATION {
    
    tag "01_QC (QC_PREPARE_ANNOTATION) | Preparing annotation files"
    label 'process_low'

    conda 'r-argparse'

    input:
        path samplesTable
        path samples_refs

    output:
        path "annotation_file_paired.csv", emit: annotation_file_paired
        path "annotation_file_single.csv", emit: annotation_file_single
        path "R.version.txt", emit: r_version

    when:
        samplesTable

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Preparing annotation files for sample matching"
        
        if [[ -n "${samples_refs}" && "${samples_refs}" != "" ]]; then
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Using provided sample references file"
            ${projectDir}/bin/qc/create_annotation_file.R --samples_table ${samplesTable} --sample_ref ${samples_refs}
            
            # Keep original output file names
            cp 3_annotation_file.paired.csv annotation_file_paired.csv
            cp 3_annotation_file.single.csv annotation_file_single.csv
        else
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: No sample references provided, creating empty annotation files"
            touch annotation_file_paired.csv
            touch annotation_file_single.csv
        fi
        
        # Get R version
        R --version > R.version.txt
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Annotation file preparation completed"
        """
}
