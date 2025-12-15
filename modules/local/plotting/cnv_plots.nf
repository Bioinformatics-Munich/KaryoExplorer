nextflow.enable.dsl=2

/*
========================================================================================
    PLOTTING: CNV VISUALIZATION
========================================================================================
    CNV plotting processes for paired and single samples
----------------------------------------------------------------------------------------
*/

process CNV_PLOT_PAIRED {
    
    tag "16_PLOT (CNV_PLOT_PAIRED) | ${post} vs ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/07_cnv_plots_paired", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(sex), val(pre), val(post), path(cnv_dir), path(summary_dir)

    output:
        tuple val(sex), val(pre), val(post), path("${post}_${pre}_plots"), emit: cnv_plots

    when:
        cnv_dir && summary_dir

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting CNV plotting for ${post} vs ${pre}"
        
        mkdir -p "${post}_${pre}_plots"
        
        ${projectDir}/bin/plotting/plot_summary_cnv_QC_run.R \\
            --inputdir . \\
            --post ${post} \\
            --pre ${pre} \\
            --sample_name ${post}_${pre} \\
            --fold_fun ${projectDir}/bin/functions/ \\
            --sex ${sex} \\
            --outf ${post}_${pre}_plots \\
            --width_plot 20
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: CNV plotting completed for ${post} vs ${pre}"
        """
}

process CNV_PLOT_SINGLE {
    
    tag "17_PLOT (CNV_PLOT_SINGLE) | ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/7.3_CNV_plot_single", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(sex), val(pre), val(post), path(cnv_dir), path(summary_dir)

    output:
        tuple val(sex), val(pre), path("${pre}_plots"), emit: cnv_plots

    when:
        cnv_dir && summary_dir

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting CNV plotting for single sample: ${pre}"
        
        mkdir -p "${pre}_plots"
        
        ${projectDir}/bin/plotting/plot_single_cnv_QC_run.R \\
            --inputdir . \\
            --fold_fun ${projectDir}/bin/functions/ \\
            --line ${pre} \\
            --sample_name ${pre} \\
            --sex ${sex} \\
            --outf ${pre}_plots
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: CNV plotting completed for ${pre}"
        """
}

process LRR_BAF_PLOT_PAIRED {
    
    tag "18_PLOT (LRR_BAF_PLOT_PAIRED) | ${post} vs ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/6.4_LRR_BAF_plots_paired", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(sex), val(pre), val(post), path(cnv_dir), path(summary_dir)

    output:
        tuple val(sex), val(pre), val(post), path("${post}_${pre}_lrr_baf_plots"), emit: lrr_baf_plots

    when:
        cnv_dir

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting LRR-BAF plotting for ${post} vs ${pre}"
        
        mkdir -p "${post}_${pre}_lrr_baf_plots"
        
        ${projectDir}/bin/plotting/plot_LRR-BAF_pair_run.R \\
            --inputfold outdir_${post}_${pre}/ \\
            --chr 0 \\
            --outf ${post}_${pre}_lrr_baf_plots/ \\
            --post ${post} \\
            --pre ${pre}
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: LRR-BAF plotting completed for ${post} vs ${pre}"
        """
}

process LRR_BAF_PLOT_SINGLE {
    
    tag "19_PLOT (LRR_BAF_PLOT_SINGLE) | ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/08_lrr_baf_plots_single", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(sex), val(pre), val(post), path(cnv_dir), path(summary_dir)

    output:
        tuple val(sex), val(pre), path("${pre}_lrr_baf_plots"), emit: lrr_baf_plots

    when:
        cnv_dir

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting LRR-BAF plotting for single sample: ${pre}"
        
        mkdir -p "${pre}_lrr_baf_plots"
        
        ${projectDir}/bin/plotting/plot_LRR-BAF_single_run.R \\
            --inputfold outdir_${pre} \\
            --line_id ${pre} \\
            --chr 0 \\
            --outf ${pre}_lrr_baf_plots
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: LRR-BAF plotting completed for ${pre}"
        """
}
