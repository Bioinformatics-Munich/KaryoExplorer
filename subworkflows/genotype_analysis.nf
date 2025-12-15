nextflow.enable.dsl=2

/*
========================================================================================
    SUBWORKFLOW: GENOTYPE ANALYSIS
========================================================================================
    Handles genotype matching, sample annotation, and validation
----------------------------------------------------------------------------------------
*/

include { GT_MATCH_PAIRED_SAMPLES; GT_MATCH_SINGLE_SAMPLES; GT_EMIT_PAIRED_SAMPLES; GT_EMIT_SINGLE_SAMPLES; GT_CREATE_SAMPLE_ANNOTATION_PAIRED; GT_CREATE_SAMPLE_ANNOTATION_SINGLE } from '../modules/local/genotyping/genotype_matching'

workflow GENOTYPE_ANALYSIS {
    
    take:
        gt_comp                 // path: genotype comparison file
        samplesTable_filt       // path: filtered samples table
        annotation_file_paired  // path: paired annotation file
        annotation_file_single  // path: single annotation file
    
    main:
        // Log workflow start
        log.info """
        ================================================================================
        GENOTYPE ANALYSIS WORKFLOW STARTED
        ================================================================================
        GT comparison: ${gt_comp}
        Filtered samples: ${samplesTable_filt}
        ================================================================================
        """

        // Step 1: Genotype matching for paired samples
        GT_MATCH_PAIRED_SAMPLES(
            gt_comp,
            samplesTable_filt,
            annotation_file_paired
        )

        // Step 2: Genotype matching for single samples
        GT_MATCH_SINGLE_SAMPLES(
            gt_comp,
            samplesTable_filt,
            annotation_file_single
        )

        // Step 3: Extract sample IDs
        GT_EMIT_PAIRED_SAMPLES(
            GT_MATCH_PAIRED_SAMPLES.out.annotation_file
        )

        GT_EMIT_SINGLE_SAMPLES(
            GT_MATCH_SINGLE_SAMPLES.out.annotation_file
        )

        // Step 4: Create sample annotations
        GT_CREATE_SAMPLE_ANNOTATION_PAIRED(
            GT_MATCH_PAIRED_SAMPLES.out.annotation_file,
            GT_EMIT_PAIRED_SAMPLES.out.samples.splitText().map{ it.replaceAll(/\n/, '') }
        )

        GT_CREATE_SAMPLE_ANNOTATION_SINGLE(
            GT_MATCH_SINGLE_SAMPLES.out.annotation_file,
            GT_EMIT_SINGLE_SAMPLES.out.samples.splitText().map{ it.replaceAll(/\n/, '') }
        )

        // Log workflow completion
        GT_CREATE_SAMPLE_ANNOTATION_PAIRED.out.samplestab.view { samples ->
            log.info """
            ================================================================================
            GENOTYPE ANALYSIS WORKFLOW COMPLETED
            ================================================================================
            Sample annotations created successfully
            ================================================================================
            """
        }

    emit:
        // Paired samples
        paired_qc_dir = GT_MATCH_PAIRED_SAMPLES.out.qc_paired_dir
        paired_annotation = GT_MATCH_PAIRED_SAMPLES.out.annotation_file
        paired_samples = GT_EMIT_PAIRED_SAMPLES.out.samples
        paired_sample_annotations = GT_CREATE_SAMPLE_ANNOTATION_PAIRED.out.samplestab
        
        // Single samples
        single_qc_dir = GT_MATCH_SINGLE_SAMPLES.out.qc_single_dir
        single_annotation = GT_MATCH_SINGLE_SAMPLES.out.annotation_file
        single_samples = GT_EMIT_SINGLE_SAMPLES.out.samples
        single_sample_annotations = GT_CREATE_SAMPLE_ANNOTATION_SINGLE.out.samplestab
}
