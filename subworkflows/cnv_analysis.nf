nextflow.enable.dsl=2

/*
========================================================================================
    SUBWORKFLOW: CNV ANALYSIS
========================================================================================
    Core CNV analysis for paired and single samples with summary generation
----------------------------------------------------------------------------------------
*/

include { CNV_ANALYSIS_PAIRED; CNV_ANALYSIS_SINGLE; CNV_DIFFERENTIAL_ANALYSIS } from '../modules/local/cnv/cnv_core'
include { CNV_SUMMARY_SINGLE; CNV_PLOT_SUMMARY; CNV_PAIRED_TABLES_SUMMARY; CNV_SINGLE_TABLES_SUMMARY; CNV_PAIRED_SUMMARY_MD; CNV_SINGLE_SUMMARY_MD } from '../modules/local/cnv/cnv_summary'

workflow CNV_ANALYSIS {
    
    take:
        vcf_annotated           // path: annotated VCF file
        paired_sample_annotations // channel: paired sample annotations
        single_sample_annotations // channel: single sample annotations
    
    main:
        // Log workflow start
        log.info """
        ================================================================================
        CNV ANALYSIS WORKFLOW STARTED
        ================================================================================
        VCF file: ${vcf_annotated}
        ================================================================================
        """

        // Prepare sample channels
        paired_samples = paired_sample_annotations
            .splitCsv(header: true, sep:"\t")
            .map { row -> tuple(row.sex, row.pre, row.post) }

        single_samples = single_sample_annotations
            .splitCsv(header: true, sep:"\t")
            .map { row -> tuple(row.sex, row.pre, row.post) }

        // Step 1: Paired CNV analysis
        CNV_ANALYSIS_PAIRED(
            vcf_annotated,
            paired_samples
        )

        // Step 2: Differential CNV analysis for paired samples
        CNV_DIFFERENTIAL_ANALYSIS(
            CNV_ANALYSIS_PAIRED.out.cnv_analysis
        )

        // Step 3: Single sample CNV analysis
        CNV_ANALYSIS_SINGLE(
            vcf_annotated,
            single_samples
        )

        // Step 4: Single sample CNV summaries
        CNV_SUMMARY_SINGLE(
            CNV_ANALYSIS_SINGLE.out.cnv_analysis_single
        )

        // Step 5: Generate plot summaries
        paired_grouped = CNV_DIFFERENTIAL_ANALYSIS.out.cnv_differential_results.groupTuple()
        CNV_PLOT_SUMMARY(paired_grouped)

        // Step 6: Create table summaries
        summary_samples_paired = CNV_PLOT_SUMMARY.out.cnv_summary_sample.collect()
        summary_paths_paired = CNV_DIFFERENTIAL_ANALYSIS.out.cnv_differential_results_paths.collect()
        CNV_PAIRED_TABLES_SUMMARY(summary_paths_paired)

        summary_samples_single = CNV_SUMMARY_SINGLE.out.cnv_single_pre.collect()
        summary_paths_single = CNV_SUMMARY_SINGLE.out.cnv_single_path.collect()
        CNV_SINGLE_TABLES_SUMMARY(summary_paths_single)

        // Step 7: Create markdown summaries
        CNV_PAIRED_SUMMARY_MD(summary_samples_paired, summary_paths_paired)
        CNV_SINGLE_SUMMARY_MD(summary_samples_single, summary_paths_single)

        // Log workflow completion
        CNV_PAIRED_TABLES_SUMMARY.out.cnv_table_summary.view { summary ->
            log.info """
            ================================================================================
            CNV ANALYSIS WORKFLOW COMPLETED
            ================================================================================
            CNV analysis completed successfully
            ================================================================================
            """
        }

    emit:
        // Paired CNV results
        paired_cnv_analysis = CNV_ANALYSIS_PAIRED.out.cnv_analysis
        paired_differential = CNV_DIFFERENTIAL_ANALYSIS.out.cnv_differential
        paired_table_summary = CNV_PAIRED_TABLES_SUMMARY.out.cnv_table_summary
        paired_summary_md = CNV_PAIRED_SUMMARY_MD.out.summary_md
        
        // Single CNV results
        single_cnv_analysis = CNV_ANALYSIS_SINGLE.out.cnv_analysis_single
        single_cnv_summary = CNV_SUMMARY_SINGLE.out.cnv_single
        single_table_summary = CNV_SINGLE_TABLES_SUMMARY.out.cnv_table_summary
        single_summary_md = CNV_SINGLE_SUMMARY_MD.out.summary_md
}
