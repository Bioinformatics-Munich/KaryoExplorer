nextflow.enable.dsl=2

/*
========================================================================================
    SUBWORKFLOW: QUALITY CONTROL
========================================================================================
    Handles data quality control, filtering, and preprocessing
----------------------------------------------------------------------------------------
*/

include { QC_MAIN_ANALYSIS; QC_PREPARE_ANNOTATION } from '../modules/local/qc/quality_control'

workflow QUALITY_CONTROL {
    
    take:
        manifest        // path: manifest file
        par_file        // path: PAR coordinate file
        nhead          // val: number of header lines
        fullTable      // path: full SNP table
        samplesTable   // path: samples table
        snpTable       // path: SNP annotation table
        samples_refs   // path: sample references (optional)
        // QC parameters
        het_up_as
        clust_sep_as
        ABR_mean_as
        AAR_mean_as
        BBR_mean_as
        ABT_mean_low_as
        ABT_mean_up_as
        het_low_as
        MAF_as
        AAT_mean_as
        AAT_dev_as
        BBT_mean_as
        BBT_dev_as
        male_frac
        R_hpY
        female_frac
    
    main:
        // Log workflow start
        log.info """
        ================================================================================
        QUALITY CONTROL WORKFLOW STARTED
        ================================================================================
        Manifest: ${manifest}
        Samples: ${samplesTable}
        SNPs: ${snpTable}
        ================================================================================
        """

        // Step 1: Main QC analysis
        QC_MAIN_ANALYSIS(
            manifest,
            par_file,
            nhead,
            fullTable,
            samplesTable,
            snpTable,
            het_up_as,
            clust_sep_as,
            ABR_mean_as,
            AAR_mean_as,
            BBR_mean_as,
            ABT_mean_low_as,
            ABT_mean_up_as,
            het_low_as,
            MAF_as,
            AAT_mean_as,
            AAT_dev_as,
            BBT_mean_as,
            BBT_dev_as,
            male_frac,
            R_hpY,
            female_frac
        )

        // Step 2: Prepare annotation files
        QC_PREPARE_ANNOTATION(
            QC_MAIN_ANALYSIS.out.samplesTable_filt,
            samples_refs
        )

        // Log workflow completion
        QC_MAIN_ANALYSIS.out.fullTable_filt.view { table ->
            log.info """
            ================================================================================
            QUALITY CONTROL WORKFLOW COMPLETED
            ================================================================================
            Filtered data table: ${table}
            ================================================================================
            """
        }

    emit:
        // QC results
        qc_dir = QC_MAIN_ANALYSIS.out.qc_dir
        fullTable_filt = QC_MAIN_ANALYSIS.out.fullTable_filt
        samplesTable_filt = QC_MAIN_ANALYSIS.out.samplesTable_filt
        samplesTable_filt_QC = QC_MAIN_ANALYSIS.out.samplesTable_filt_QC
        lrr_table = QC_MAIN_ANALYSIS.out.lrr_table
        baf_table = QC_MAIN_ANALYSIS.out.baf_table
        gt_table = QC_MAIN_ANALYSIS.out.gt_table
        gt_comp = QC_MAIN_ANALYSIS.out.gt_comp
        
        // Annotation files
        annotation_file_paired = QC_PREPARE_ANNOTATION.out.annotation_file_paired
        annotation_file_single = QC_PREPARE_ANNOTATION.out.annotation_file_single
        
        // Version information
        r_version = QC_PREPARE_ANNOTATION.out.r_version
}
