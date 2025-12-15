nextflow.enable.dsl=2

/*
========================================================================================
    DYNAMIC PLOTTING: DATA PREPROCESSING
========================================================================================
    Data preprocessing processes for dynamic plotting and interactive visualization
----------------------------------------------------------------------------------------
*/

process DYNAMIC_PLOT_DATA_PREP_SINGLE {
    tag "$pre"
    label 'process_low'

    publishDir("${params.outdir}/5.0_${params.app_name}_preprocessing/single/${pre}", 
        mode: 'copy',
        overwrite: true,
        saveAs: { filename ->
            if (filename.startsWith('processed/')) "processed/${filename.replaceFirst('processed/','')}"
            else null
        })
    
    publishDir("${params.outdir}/1.0_quality_control/1.4_IBD_Analysis", 
        mode: 'copy',
        overwrite: true,
        pattern: "sample_types_single_w_QC.csv")
    
    publishDir("${params.outdir}/5.0_${params.app_name}_preprocessing", 
        mode: 'copy',
        overwrite: true,
        saveAs: { filename ->
            if (filename.endsWith('.csv') && !filename.startsWith('processed/') && filename != 'sample_types_single_w_QC.csv') filename
            else null
        })

    conda "${baseDir}/env/bokeh.yaml"

    input:
        tuple val(sex), val(pre), val(post), 
              path(summary_tab), 
              path(dat_tab), 
              path(cn_tab),
              path(cnv_detection_filt),
              path(cnv_table),
              path(union_bed),
              path(roh_bed),
              path(cn_bed),
              path(sample_types_single)

    output:
        path("input_files/${summary_tab.name}"), emit: summary
        path("input_files/${dat_tab.name}"), emit: dat
        path("input_files/${cn_tab.name}"), emit: cn
        path("input_files/${cnv_detection_filt.name}"), emit: cnv_detection
        path("input_files/${cnv_table.name}"), emit: cnv_table
        path("input_files/${union_bed.name}"), emit: union_bed
        path("input_files/${roh_bed.name}"), emit: roh_bed
        path("input_files/${cn_bed.name}"), emit: cn_bed
        path("${sample_types_single.name}"), emit: sample_types_single
        path("processed/*.csv"), emit: processed_data
        path("processed/single_preprocess_log.txt"), emit: log_file
        path("processed/*"), emit: all_processed_output
        tuple val(pre), path("${sample_types_single.name}"), path("processed/*.csv"), emit: all_processed_files

    when:
        summary_tab && dat_tab && cn_tab

    script:
        """
        # Create work directory structure
        work_processed_dir="processed"
        work_input_dir="input_files"
        mkdir -p "\$work_processed_dir" "\$work_input_dir"

        mkdir -p example2

        # Copy files to work input directory
        cp ${summary_tab} ${dat_tab} ${cn_tab} ${cnv_detection_filt} ${cnv_table} ${union_bed} ${roh_bed} ${cn_bed} "\$work_input_dir/"

        # Run processing script - outputs to work processed_dir
        python ${baseDir}/bin/dynamic_plotting/data_preprocessing/single_data_preprocessing.py \\
            --sex ${sex} \\
            --pre ${pre} \\
            --post ${post} \\
            --summary_tab "\$work_input_dir/${summary_tab.name}" \\
            --dat_tab "\$work_input_dir/${dat_tab.name}" \\
            --cn_tab "\$work_input_dir/${cn_tab.name}" \\
            --cnv_detection "\$work_input_dir/${cnv_detection_filt.name}" \\
            --cnv_table "\$work_input_dir/${cnv_table.name}" \\
            --union_bed "\$work_input_dir/${union_bed.name}" \\
            --roh_bed "\$work_input_dir/${roh_bed.name}" \\
            --cn_bed "\$work_input_dir/${cn_bed.name}" \\
            --sample_types ${sample_types_single} \\
            --output_dir "\$work_processed_dir"
        """
}

process DYNAMIC_PLOT_DATA_PREP_PAIRED {
    tag "${pre}_${post}"
    label 'process_low'

    publishDir("${params.outdir}/5.0_${params.app_name}_preprocessing/paired/${pre}_${post}", 
        mode: 'copy',
        overwrite: true,
        saveAs: { filename ->
            if (filename.startsWith('processed/')) "processed/${filename.replaceFirst('processed/','')}"
            else null
        })
    
    publishDir("${params.outdir}/1.0_quality_control/1.4_IBD_Analysis", 
        mode: 'copy',
        overwrite: true,
        pattern: "{paired_sample_with_pi_hat.csv,sample_types_single_w_QC.csv}")
    
    publishDir("${params.outdir}/5.0_${params.app_name}_preprocessing", 
        mode: 'copy',
        overwrite: true,
        saveAs: { filename ->
            if (filename.endsWith('.csv') && !filename.startsWith('processed/') && 
                filename != 'paired_sample_with_pi_hat.csv' && filename != 'sample_types_single_w_QC.csv') filename
            else null
        })

    conda "${baseDir}/env/bokeh.yaml"

    input:
        tuple val(sex), val(pre), val(post),
              path(summary_pre), path(dat_pre), path(cn_pre),
              path(summary_post), path(dat_post), path(cn_post),
              path(pair_summary), path(summary_pair_filt),
              path(preUnion), path(preRoh), path(pre_cn_bed),
              path(postUnion), path(postRoh), path(post_cn_bed),
              path(pairedUnion), path(pairedRoh), path(paired_cn_bed),
              path(overlapDir), path(paired_sample_types), path(single_sample_types)

    output:
        path("input_files/${summary_pre.name}"), emit: summary_pre
        path("input_files/${dat_pre.name}"), emit: dat_pre
        path("input_files/${cn_pre.name}"), emit: cn_pre
        path("input_files/${summary_post.name}"), emit: summary_post
        path("input_files/${dat_post.name}"), emit: dat_post
        path("input_files/${cn_post.name}"), emit: cn_post
        path("input_files/${pair_summary.name}"), emit: pair_summary
        path("input_files/${summary_pair_filt.name}"), emit: summary_pair_filt
        path("input_files/${preUnion.name}"), emit: preUnion
        path("input_files/${preRoh.name}"), emit: preRoh
        path("input_files/${pre_cn_bed.name}"), emit: pre_cn_bed
        path("input_files/${postUnion.name}"), emit: postUnion
        path("input_files/${postRoh.name}"), emit: postRoh
        path("input_files/${post_cn_bed.name}"), emit: post_cn_bed
        path("input_files/${pairedUnion.name}"), emit: pairedUnion
        path("input_files/${pairedRoh.name}"), emit: pairedRoh
        path("input_files/${paired_cn_bed.name}"), emit: paired_cn_bed
        path("${paired_sample_types.name}"), emit: paired_sample_types
        path("${single_sample_types.name}"), emit: single_sample_types
        path("processed/*.csv"), emit: processed_data
        path("processed/paired_preprocess_log.txt"), emit: log_file
        path("processed/*"), emit: all_processed_output
        tuple val(pre), val(post), path("${single_sample_types.name}"), path("${paired_sample_types.name}"), 
              path("processed/*.csv"), emit: all_processed_files

    when:
        summary_pre && summary_post && pair_summary

    script:
        """
        # Create work directory structure
        work_processed_dir="processed"
        work_input_dir="input_files"
        mkdir -p "\$work_processed_dir" "\$work_input_dir"

        mkdir -p example2

        # Copy files to work input directory
        cp ${summary_pre} ${dat_pre} ${cn_pre} ${summary_post} ${dat_post} ${cn_post} \\
           ${pair_summary} ${summary_pair_filt} ${preUnion} ${preRoh} ${pre_cn_bed} \\
           ${postUnion} ${postRoh} ${post_cn_bed} ${pairedUnion} ${pairedRoh} ${paired_cn_bed} \\
           ${paired_sample_types} ${single_sample_types} "\$work_input_dir/"

        # Run processing script - outputs to work processed_dir
        python ${baseDir}/bin/dynamic_plotting/data_preprocessing/paired_data_preprocessing.py \\
            --sex ${sex} \\
            --pre ${pre} --post ${post} \\
            --summary_tab_pre "\$work_input_dir/${summary_pre.name}" \\
            --dat_tab_pre "\$work_input_dir/${dat_pre.name}" \\
            --cn_tab_pre "\$work_input_dir/${cn_pre.name}" \\
            --summary_tab_post "\$work_input_dir/${summary_post.name}" \\
            --dat_tab_post "\$work_input_dir/${dat_post.name}" \\
            --cn_tab_post "\$work_input_dir/${cn_post.name}" \\
            --summary_tab "\$work_input_dir/${pair_summary.name}" \\
            --cnv_detection_filt "\$work_input_dir/${summary_pair_filt.name}" \\
            --pre_union_bed "\$work_input_dir/${preUnion.name}" \\
            --post_union_bed "\$work_input_dir/${postUnion.name}" \\
            --pre_roh_bed "\$work_input_dir/${preRoh.name}" \\
            --post_roh_bed "\$work_input_dir/${postRoh.name}" \\
            --pre_cn_bed "\$work_input_dir/${pre_cn_bed.name}" \\
            --post_cn_bed "\$work_input_dir/${post_cn_bed.name}" \\
            --union_bed "\$work_input_dir/${pairedUnion.name}" \\
            --roh_bed "\$work_input_dir/${pairedRoh.name}" \\
            --paired_cn_bed "\$work_input_dir/${paired_cn_bed.name}" \\
            --sample_types "\$work_input_dir/${paired_sample_types.name}" \\
            --output_dir "\$work_processed_dir"
        """
}
