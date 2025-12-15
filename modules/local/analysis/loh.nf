nextflow.enable.dsl=2

/*
========================================================================================
    SPECIALIZED ANALYSIS: LOSS OF HETEROZYGOSITY (LoH)
========================================================================================
    LoH analysis for single and paired samples
----------------------------------------------------------------------------------------
*/

process LOH_ANALYSIS_SINGLE {
    
    tag "LoH analysis: ${pre}"
    label 'process_medium'

    publishDir "${params.outdir}/12_loh_analysis/single", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(sex), val(pre), path(summary_tab), path(dat_tab), path(cn_tab)

    output:
        tuple val(sex), val(pre), path("${pre}_LoH_results.tsv"), emit: loh_results

    when:
        summary_tab && dat_tab && cn_tab

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting LoH analysis for single sample: ${pre}"
        
        ${projectDir}/bin/analysis/LoH_analysis_single.R \\
            --summary ${summary_tab} \\
            --data ${dat_tab} \\
            --cn ${cn_tab} \\
            --sample_id ${pre} \\
            --sex ${sex} \\
            --outdir ./
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: LoH analysis completed for ${pre}"
        """
}

process LOH_ANALYSIS_PAIRED {
    
    tag "LoH analysis: ${post} vs ${pre}"
    label 'process_medium'

    publishDir "${params.outdir}/12_loh_analysis/paired", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(sex), val(pre), val(post), 
              path(pre_summary), path(pre_data), path(pre_cn),
              path(post_summary), path(post_data), path(post_cn),
              val(comparison_id)

    output:
        tuple val(sex), val(pre), val(post), path("${comparison_id}_LoH_results.tsv"), emit: loh_results

    when:
        pre_summary && pre_data && pre_cn && post_summary && post_data && post_cn

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting LoH analysis for paired samples: ${post} vs ${pre}"
        
        ${projectDir}/bin/analysis/LoH_analysis_paired.R \\
            --pre_summary ${pre_summary} \\
            --pre_data ${pre_data} \\
            --pre_cn ${pre_cn} \\
            --post_summary ${post_summary} \\
            --post_data ${post_data} \\
            --post_cn ${post_cn} \\
            --pre_id ${pre} \\
            --post_id ${post} \\
            --sex ${sex} \\
            --outdir ./
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: LoH analysis completed for ${post} vs ${pre}"
        """
}
