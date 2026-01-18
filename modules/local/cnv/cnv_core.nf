nextflow.enable.dsl=2

/*
========================================================================================
    CNV ANALYSIS: CORE ANALYSIS
========================================================================================
    Core CNV analysis processes for paired and single samples
----------------------------------------------------------------------------------------
*/

process CNV_ANALYSIS_PAIRED {
    
    tag "11_CNV (CNV_ANALYSIS_PAIRED) | ${post} vs ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/6.1_CNV_analysis", mode: 'copy', overwrite: true, pattern: "outdir_${post}_${pre}"

    conda "${baseDir}/env/preproc.yaml"

    input:
        path vcf_baf_lrr
        tuple val(sex), val(pre), val(post)

    output:
        tuple val(sex), val(pre), val(post), path("outdir_${post}_${pre}"), emit: cnv_analysis

    when:
        vcf_baf_lrr && pre && post

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting CNV analysis for paired samples: ${post} vs ${pre}"
        
        mkdir -p outdir_${post}_${pre}
        
        # Run bcftools cnv for paired analysis
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Running bcftools cnv analysis"
        cmd="bcftools cnv -s ${post} -l ${params.weight_lrr} -t ^${params.excluded_chr} -o outdir_${post}_${pre}"
        cmd="\$cmd -c ${pre}"
        cmd="\$cmd ${vcf_baf_lrr}"
        eval "\$cmd"
        
        # Modified validation to check file size
        if [ ! -s "outdir_${post}_${pre}/summary.${post}.tab" ]; then
            echo "Error: Empty or missing summary.${post}.tab"
            exit 1
        fi
        
        # Update file checks to verify non-empty files
        required_files=(
            "${sprintf(params.summary_pattern, post)}"
            "${sprintf(params.dat_pattern, post)}"
            "${sprintf(params.cn_pattern, post)}"
            "${sprintf(params.summary_pattern, pre)}"
            "${sprintf(params.dat_pattern, pre)}"
            "${sprintf(params.cn_pattern, pre)}"
        )
        
        for f in "\${required_files[@]}"; do
            if [ ! -s "outdir_${post}_${pre}/\$f" ]; then
                echo "Empty or missing required file: \$f"
                exit 1
            fi
        done
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: CNV analysis completed for ${post} vs ${pre}"
        echo "Results saved in: outdir_${post}_${pre}/"
        """
}

process CNV_ANALYSIS_SINGLE {
    
    tag "12_CNV (CNV_ANALYSIS_SINGLE) | ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/7.1_CNV_analysis_single", mode: 'copy', overwrite: true, pattern: "outdir_${pre}"

    conda "${baseDir}/env/preproc.yaml"

    input:
        path vcf_baf_lrr
        tuple val(sex), val(pre), val(post)

    output:
        tuple val(sex), val(pre), val(post), path("outdir_${pre}"), emit: cnv_analysis_single

    when:
        vcf_baf_lrr && pre

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting CNV analysis for single sample: ${pre}"
        
        mkdir -p outdir_${pre}
        
        # Run bcftools cnv for single sample analysis
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Running bcftools cnv analysis"
        cmd="bcftools cnv -s ${pre} -l ${params.weight_lrr} -t ^0,25,26 -o outdir_${pre}"
        cmd="\$cmd ${vcf_baf_lrr}"
        eval "\$cmd"

        
        # Modified validation to check file size
        if [ ! -s "outdir_${pre}/summary.${pre}.tab" ]; then
            echo "Error: Empty or missing summary.${pre}.tab"
            exit 1
        fi
        
        # Add additional file checks
        required_files_single=(
            "${sprintf(params.summary_pattern, pre)}"
            "${sprintf(params.dat_pattern, pre)}"
            "${sprintf(params.cn_pattern, pre)}"
        )
        
        for f in "\${required_files_single[@]}"; do
            if [ ! -s "outdir_${pre}/\$f" ]; then
                echo "Empty or missing required file: \$f"
                exit 1
            fi
        done
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: CNV analysis completed for ${pre}"
        echo "Results saved in: outdir_${pre}/"
        """
}

process CNV_DIFFERENTIAL_ANALYSIS {
    
    tag "13_CNV (CNV_DIFFERENTIAL_ANALYSIS) | ${post} vs ${pre}"
    label 'process_medium'

    // publishDir "${params.outdir}/6.2_CNV_differential", mode: 'copy', overwrite: true, pattern: "${post}_${pre}"

    conda "${baseDir}/env/renv.yaml"

    input:
        tuple val(sex), val(pre), val(post), path(cnv_dir)

    output:
        tuple val(sex), val(pre), val(post), path(cnv_dir), path("${post}_${pre}"), emit: cnv_differential
        tuple val(pre), val(post), path("${post}_${pre}"), emit: cnv_differential_results
        path "${post}_${pre}", emit: cnv_differential_results_paths

    when:
        cnv_dir && pre && post

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting differential CNV analysis: ${post} vs ${pre}"
        
        mkdir "${post}_${pre}"
        
        ${projectDir}/bin/cnv/summary_diffCN_run.R \\
            --inputdir . \\
            --post ${post} \\
            --pre ${pre} \\
            --sample_name ${pre} \\
            --sex ${sex} \\
            --outf ${post}_${pre}/ \\
            --fold_fun ${projectDir}/bin/functions/ \\
            --qs_thr ${params.qs_thr} \\
            --nSites_thr ${params.nSites_thr} \\
            --nHet_thr ${params.nHet_thr} \\
            --CN_len_thr ${params.CN_len_thr} \\
            --CN_len_thr_big ${params.CN_len_thr_big} \\
            --width_plot ${params.width_plot}
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Differential CNV analysis completed for ${post} vs ${pre}"
        """
}
