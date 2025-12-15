nextflow.enable.dsl=2

/*
========================================================================================
    SUBWORKFLOW: INPUT PREPARATION
========================================================================================
    Handles manifest processing, VCF creation, and data preprocessing
----------------------------------------------------------------------------------------
*/

include { MANIFEST_GET_REF_ALLELE } from '../modules/local/input/manifest'
include { VCF_CREATE_FROM_PLINK; VCF_CORRECT_REF_ALT; VCF_ANNOTATE_BAF_LRR } from '../modules/local/input/vcf'

workflow INPUT_PREPARATION {
    
    take:
        manifest        // path: manifest file
        fasta          // path: reference fasta
        gsplink        // path: PLINK files directory
        fullTable_filt // path: filtered full table
        lrr_table      // path: LRR table
        baf_table      // path: BAF table
    
    main:
        // Log workflow start
        log.info """
        ================================================================================
        INPUT PREPARATION WORKFLOW STARTED
        ================================================================================
        Manifest: ${manifest}
        Reference: ${fasta}
        PLINK data: ${gsplink}
        ================================================================================
        """

        // Step 1: Process manifest to get reference alleles
        MANIFEST_GET_REF_ALLELE(
            manifest,
            fasta
        )

        // Step 2: Convert PLINK to VCF
        VCF_CREATE_FROM_PLINK(
            gsplink
        )

        // Step 3: Correct VCF reference alleles using manifest
        VCF_CORRECT_REF_ALT(
            VCF_CREATE_FROM_PLINK.out.vcf,
            MANIFEST_GET_REF_ALLELE.out.manifest_ref
        )

        // Step 4: Annotate VCF with BAF/LRR data
        VCF_ANNOTATE_BAF_LRR(
            fullTable_filt,
            VCF_CORRECT_REF_ALT.out.vcf_corrected,
            lrr_table,
            baf_table
        )

        // Log workflow completion
        VCF_ANNOTATE_BAF_LRR.out.vcf_annotated.view { vcf ->
            log.info """
            ================================================================================
            INPUT PREPARATION WORKFLOW COMPLETED
            ================================================================================
            Final annotated VCF: ${vcf}
            ================================================================================
            """
        }

    emit:
        // Primary outputs
        vcf_annotated = VCF_ANNOTATE_BAF_LRR.out.vcf_annotated
        snps_qc = VCF_ANNOTATE_BAF_LRR.out.snps_qc
        manifest_ref = MANIFEST_GET_REF_ALLELE.out.manifest_ref
        
        // Version information
        plink_version = VCF_CREATE_FROM_PLINK.out.version
        bcftools_version = VCF_ANNOTATE_BAF_LRR.out.bcftools_version
        vcftools_version = VCF_ANNOTATE_BAF_LRR.out.vcftools_version
}
