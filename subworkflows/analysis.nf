nextflow.enable.dsl=2

/*
========================================================================================
    SUBWORKFLOW: SPECIALIZED ANALYSIS
========================================================================================
    LoH, RoH, and IBD analysis workflows
----------------------------------------------------------------------------------------
*/

include { LOH_ANALYSIS_SINGLE; LOH_ANALYSIS_PAIRED } from '../modules/local/analysis/loh'
include { ROH_ANALYSIS_SINGLE; ROH_ANALYSIS_PAIRED } from '../modules/local/analysis/roh'
include { IBD_ANALYSIS; SAMPLE_TYPES_SINGLE; SAMPLE_TYPES_PAIRED } from '../modules/local/analysis/ibd'

workflow SPECIALIZED_ANALYSIS {
    
    take:
        vcf_annotated           // path: annotated VCF file
        gsplink                 // path: PLINK files
        samples_manifest        // path: combined samples manifest
        samples_table_qc        // path: QC samples table
        single_cnv_summary      // channel: single CNV summary results
        paired_differential     // channel: paired differential results
    
    main:
        // Log workflow start
        log.info """
        ================================================================================
        SPECIALIZED ANALYSIS WORKFLOW STARTED
        ================================================================================
        VCF file: ${vcf_annotated}
        PLINK data: ${gsplink}
        ================================================================================
        """

        // Step 1: Sample type classification
        SAMPLE_TYPES_SINGLE(
            samples_manifest,
            samples_table_qc
        )

        SAMPLE_TYPES_PAIRED(
            samples_manifest
        )

        // Step 2: IBD Analysis
        IBD_ANALYSIS(
            gsplink,
            SAMPLE_TYPES_PAIRED.out.sample_csv_paired
        )

        // Step 3: RoH Analysis for single samples
        single_samples = SAMPLE_TYPES_SINGLE.out.sample_csv_single
            .splitCsv(header: true)
            .filter { it.type == 'single' }
            .map { row -> 
                tuple(
                    row.sample_id, 
                    row.type, 
                    row.pre_sample, 
                    row.post_sample
                )
            }

        single_analysis = single_samples.combine(vcf_annotated)
        ROH_ANALYSIS_SINGLE(single_analysis)

        // Step 4: RoH Analysis for paired samples
        paired_samples = SAMPLE_TYPES_PAIRED.out.sample_csv_paired
            .splitCsv(header: true)
            .filter { it.type == 'paired' }
            .map { row -> 
                tuple(
                    row.sample_id, 
                    row.type, 
                    row.pre_sample, 
                    row.post_sample
                )
            }

        paired_analysis = paired_samples.combine(vcf_annotated)
        ROH_ANALYSIS_PAIRED(paired_analysis)

        // Step 5: LoH Analysis (optional - based on available data)
        // Note: LoH analysis requires specific CNV summary data structure
        // This will be connected when CNV data is properly structured

        // Log workflow completion
        ROH_ANALYSIS_SINGLE.out.roh_data_files_tuple.view { roh_data ->
            log.info """
            ================================================================================
            SPECIALIZED ANALYSIS WORKFLOW COMPLETED
            ================================================================================
            RoH and IBD analysis completed successfully
            ================================================================================
            """
        }

    emit:
        // Sample classifications
        single_sample_types = SAMPLE_TYPES_SINGLE.out.sample_csv_single
        single_sample_types_qc = SAMPLE_TYPES_SINGLE.out.sample_csv_single_w_QC
        paired_sample_types = SAMPLE_TYPES_PAIRED.out.sample_csv_paired
        
        // IBD results
        ibd_results = IBD_ANALYSIS.out.ibd_results
        pi_hat_results = IBD_ANALYSIS.out.pi_hat_results
        
        // RoH results
        roh_single_results = ROH_ANALYSIS_SINGLE.out.roh_data_files_tuple
        roh_paired_results = ROH_ANALYSIS_PAIRED.out.roh_data_files_tuple
}
