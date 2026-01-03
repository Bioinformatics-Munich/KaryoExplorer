#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*
========================================================================================
DIGITAL KARYOTYPING PIPELINE - MAIN WORKFLOW
========================================================================================
Main workflow orchestrating all pipeline steps with clean process naming for logs.
Following Nextflow best practices with modular organization.
----------------------------------------------------------------------------------------
*/

// Import all processes directly for clean logging (no nested workflow prefixes)
include { MANIFEST_GET_REF_ALLELE } from '../modules/local/input/manifest'
include { VCF_CREATE_FROM_PLINK; VCF_CORRECT_REF_ALT; VCF_ANNOTATE_BAF_LRR } from '../modules/local/input/vcf'
include { QC_MAIN_ANALYSIS; QC_PREPARE_ANNOTATION } from '../modules/local/qc/quality_control'
include { GT_MATCH_PAIRED_SAMPLES; GT_MATCH_SINGLE_SAMPLES; GT_EMIT_PAIRED_SAMPLES; GT_EMIT_SINGLE_SAMPLES; GT_CREATE_SAMPLE_ANNOTATION_PAIRED; GT_CREATE_SAMPLE_ANNOTATION_SINGLE } from '../modules/local/genotyping/genotype_matching'
include { CNV_ANALYSIS_PAIRED; CNV_ANALYSIS_SINGLE; CNV_DIFFERENTIAL_ANALYSIS } from '../modules/local/cnv/cnv_core'
include { CNV_SUMMARY_SINGLE; CNV_PLOT_SUMMARY; CNV_PAIRED_TABLES_SUMMARY; CNV_SINGLE_TABLES_SUMMARY; CNV_PAIRED_SUMMARY_MD; CNV_SINGLE_SUMMARY_MD } from '../modules/local/cnv/cnv_summary'
include { IBD_ANALYSIS; SAMPLE_TYPES_SINGLE; SAMPLE_TYPES_PAIRED } from '../modules/local/analysis/ibd'
include { ROH_ANALYSIS_SINGLE; ROH_ANALYSIS_PAIRED } from '../modules/local/analysis/roh'
include { CNV_PLOT_PAIRED; CNV_PLOT_SINGLE; LRR_BAF_PLOT_PAIRED; LRR_BAF_PLOT_SINGLE } from '../modules/local/plotting/cnv_plots'
include { DYNAMIC_PLOT_DATA_PREP_SINGLE; DYNAMIC_PLOT_DATA_PREP_PAIRED } from '../modules/local/dynamic_plotting/dynamic_plotting_data_preprocessing'
include { DYNAMIC_PLOT_SINGLE; DYNAMIC_PLOT_PAIRED } from '../modules/local/dynamic_plotting/dynamic_plotting'
include { PARAMETER_REPORT; HTML_OUTPUT_DESCRIPTION } from '../modules/local/reporting/reports'

workflow DK {
    take:
    manifest
    par
    nhead
    fullTable
    samplesTable
    snpTable
    gsplink
    fasta
    samples_refs
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
    hetexcess_quality_threshold

    main:
    
    // ================================
    // STEP 1: QUALITY CONTROL
    // ================================
    
    QC_MAIN_ANALYSIS(
        manifest,
        par,
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
        female_frac,
        hetexcess_quality_threshold
    )

    QC_PREPARE_ANNOTATION(
        QC_MAIN_ANALYSIS.out.samplesTable_filt,
        samples_refs
    )

    // ================================
    // STEP 2: INPUT PREPARATION
    // ================================

    MANIFEST_GET_REF_ALLELE(
        manifest,
        fasta
    )

    VCF_CREATE_FROM_PLINK(
        gsplink
    )

    VCF_CORRECT_REF_ALT(
        VCF_CREATE_FROM_PLINK.out.vcf,
        MANIFEST_GET_REF_ALLELE.out.manifest_ref
    )

    VCF_ANNOTATE_BAF_LRR(
        QC_MAIN_ANALYSIS.out.fullTable_filt,
        VCF_CORRECT_REF_ALT.out.vcf_corrected,
        QC_MAIN_ANALYSIS.out.lrr_table,
        QC_MAIN_ANALYSIS.out.baf_table
    )

    // ================================
    // STEP 3: GENOTYPE ANALYSIS
    // ================================

    GT_MATCH_PAIRED_SAMPLES(
        QC_MAIN_ANALYSIS.out.gt_comp,
        QC_MAIN_ANALYSIS.out.samplesTable_filt,
        QC_PREPARE_ANNOTATION.out.annotation_file_paired
    )

    GT_MATCH_SINGLE_SAMPLES(
        QC_MAIN_ANALYSIS.out.gt_comp,
        QC_MAIN_ANALYSIS.out.samplesTable_filt,
        QC_PREPARE_ANNOTATION.out.annotation_file_single
    )

    GT_EMIT_PAIRED_SAMPLES(
        GT_MATCH_PAIRED_SAMPLES.out.annotation_file
    )

    GT_EMIT_SINGLE_SAMPLES(
        GT_MATCH_SINGLE_SAMPLES.out.annotation_file
    )

    GT_CREATE_SAMPLE_ANNOTATION_PAIRED(
        GT_MATCH_PAIRED_SAMPLES.out.annotation_file,
        GT_EMIT_PAIRED_SAMPLES.out.samples.splitText().map{ it.replaceAll(/\n/, '') }
    )

    GT_CREATE_SAMPLE_ANNOTATION_SINGLE(
        GT_MATCH_SINGLE_SAMPLES.out.annotation_file,
        GT_EMIT_SINGLE_SAMPLES.out.samples.splitText().map{ it.replaceAll(/\n/, '') }
    )

    // ================================
    // STEP 4: CNV ANALYSIS
    // ================================

    // Prepare sample channels
    paired_samples = GT_CREATE_SAMPLE_ANNOTATION_PAIRED.out.samplestab
        .splitCsv(header: true, sep:"\t")
        .map { row -> tuple(row.sex, row.pre, row.post) }

    single_samples = GT_CREATE_SAMPLE_ANNOTATION_SINGLE.out.samplestab
        .splitCsv(header: true, sep:"\t")
        .map { row -> tuple(row.sex, row.pre, row.post) }

    CNV_ANALYSIS_PAIRED(
        VCF_ANNOTATE_BAF_LRR.out.vcf_annotated,
        paired_samples
    )

    CNV_DIFFERENTIAL_ANALYSIS(
        CNV_ANALYSIS_PAIRED.out.cnv_analysis
    )

    CNV_ANALYSIS_SINGLE(
        VCF_ANNOTATE_BAF_LRR.out.vcf_annotated,
        single_samples
    )

    CNV_SUMMARY_SINGLE(
        CNV_ANALYSIS_SINGLE.out.cnv_analysis_single
    )

    // Generate summaries
    paired_grouped = CNV_DIFFERENTIAL_ANALYSIS.out.cnv_differential_results.groupTuple()
    CNV_PLOT_SUMMARY(paired_grouped)

    summary_samples_paired = CNV_PLOT_SUMMARY.out.cnv_summary_sample.collect()
    summary_paths_paired = CNV_DIFFERENTIAL_ANALYSIS.out.cnv_differential_results_paths.collect()
    CNV_PAIRED_TABLES_SUMMARY(summary_paths_paired)

    summary_samples_single = CNV_SUMMARY_SINGLE.out.cnv_single_pre.collect()
    summary_paths_single = CNV_SUMMARY_SINGLE.out.cnv_single_path.collect()
    CNV_SINGLE_TABLES_SUMMARY(summary_paths_single)

    CNV_PAIRED_SUMMARY_MD(summary_samples_paired, summary_paths_paired)
    CNV_SINGLE_SUMMARY_MD(summary_samples_single, summary_paths_single)

    // ================================
    // STEP 5: SPECIALIZED ANALYSIS
    // ================================

    // Create combined samples manifest
    samples_manifest = GT_CREATE_SAMPLE_ANNOTATION_SINGLE.out.samplestab
        .mix(GT_CREATE_SAMPLE_ANNOTATION_PAIRED.out.samplestab)
        .collectFile(name: 'combined_manifest.tsv')

    SAMPLE_TYPES_SINGLE(
        samples_manifest,
        QC_MAIN_ANALYSIS.out.samplesTable_filt_QC
    )

    SAMPLE_TYPES_PAIRED(
        samples_manifest
    )

    // RoH Analysis
    single_samples_roh = SAMPLE_TYPES_SINGLE.out.sample_csv_single
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

    single_analysis = single_samples_roh.combine(VCF_ANNOTATE_BAF_LRR.out.vcf_annotated)
    ROH_ANALYSIS_SINGLE(single_analysis)

    paired_samples_roh = SAMPLE_TYPES_PAIRED.out.sample_csv_paired
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

    paired_analysis = paired_samples_roh.combine(VCF_ANNOTATE_BAF_LRR.out.vcf_annotated)
    ROH_ANALYSIS_PAIRED(paired_analysis)

    // ================================
    // STEP 6: VISUALIZATION
    // ================================

    CNV_PLOT_PAIRED(CNV_DIFFERENTIAL_ANALYSIS.out.cnv_differential)
    CNV_PLOT_SINGLE(CNV_SUMMARY_SINGLE.out.cnv_single)

    LRR_BAF_PLOT_PAIRED(CNV_DIFFERENTIAL_ANALYSIS.out.cnv_differential)
    LRR_BAF_PLOT_SINGLE(CNV_SUMMARY_SINGLE.out.cnv_single)

    // Dynamic plotting - fix channel structure to match legacy
    // Create properly keyed CNV channel
    cnvSingle_ch = CNV_SUMMARY_SINGLE.out.cnv_single
        .map { sex, pre, post, cnv_dir, summary_dir ->
            tuple(
                pre,  // key
                sex, pre, post,
                file("${cnv_dir}/summary.${pre}.tab"),
                file("${cnv_dir}/dat.${pre}.tab"), 
                file("${cnv_dir}/cn.${pre}.tab"),
                file("${summary_dir}/CNV_detection_filt_${pre}.tsv"),
                file("${summary_dir}/CNV_detection_chromosomes_${pre}.tsv")  // cnv_detection_chromosomes
            )
        }

    // Add CNV table summary to each sample
    cnvSingle_ch_with_table = cnvSingle_ch
        .combine(CNV_SINGLE_TABLES_SUMMARY.out.cnv_table_summary)
        .map { pre, sex, pre_dup, post, summary_tab, dat_tab, cn_tab, cnv_detection_filt, cnv_detection_chromosomes, cnv_table ->
            tuple(
                pre,  // key
                sex, pre_dup, post, summary_tab, dat_tab, cn_tab, cnv_detection_filt, cnv_detection_chromosomes, cnv_table
            )
        }

    // Create properly keyed RoH channel  
    rohData_ch_single = ROH_ANALYSIS_SINGLE.out.roh_data_files_tuple
        .map { pre_sample, union_bed, roh_bed, cn_bed ->
            tuple(
                pre_sample,  // key
                union_bed, roh_bed, cn_bed
            )
        }

    // Join CNV and RoH channels and create final input structure
    dynamicPlotInput_single = cnvSingle_ch_with_table
        .join(rohData_ch_single, by: 0)
        .map { pre, sex, pre_dup, post, summary_tab, dat_tab, cn_tab, cnv_detection_filt, cnv_detection_chromosomes, cnv_table, union_bed, roh_bed, cn_bed ->
            tuple(
                sex, pre, post, summary_tab, dat_tab, cn_tab, cnv_detection_filt, cnv_table, union_bed, roh_bed, cn_bed
            )
        }

    single_sample_types_w_qc_ch = SAMPLE_TYPES_SINGLE.out.sample_csv_single_w_QC
    combinedDynamicPlotInput_single = dynamicPlotInput_single.combine(single_sample_types_w_qc_ch)

    DYNAMIC_PLOT_DATA_PREP_SINGLE(combinedDynamicPlotInput_single)

    ch_sample_types_single = DYNAMIC_PLOT_DATA_PREP_SINGLE.out.all_processed_files
        .map { pre, sample_types_single, csv_files -> sample_types_single }
        .first()
        .ifEmpty { file('NO_SAMPLE_TYPES.csv') }

    ch_processed_csvs_single = DYNAMIC_PLOT_DATA_PREP_SINGLE.out.all_processed_files
        .map { pre, sample_types_single, csv_files -> csv_files }
        .flatten()
        .collect()          

    // ================================
    // STEP 7: REPORTING
    // ================================

    PARAMETER_REPORT()
    
    ch_parameters_single = PARAMETER_REPORT.out.parameters

    HTML_OUTPUT_DESCRIPTION(
        QC_PREPARE_ANNOTATION.out.r_version,
        VCF_CREATE_FROM_PLINK.out.version,
        VCF_ANNOTATE_BAF_LRR.out.bcftools_version,
        VCF_ANNOTATE_BAF_LRR.out.vcftools_version
    )

    DYNAMIC_PLOT_SINGLE(
        ch_sample_types_single,
        ch_processed_csvs_single,
        ch_parameters_single
    )

    // ================================
    // IBD ANALYSIS (Legacy Compatible)
    // ================================
    
    IBD_ANALYSIS(
        gsplink, 
        SAMPLE_TYPES_PAIRED.out.sample_csv_paired
    )

    // ================================
    // PAIRED DYNAMIC PLOTTING (Legacy Compatible)
    // ================================

    // CNV paired channel (key = [pre,post])
    cnvPaired_ch = CNV_DIFFERENTIAL_ANALYSIS.out.cnv_differential
        .map { sex, pre, post, cnvDir, summaryDir ->
            tuple(
                [pre, post],  // key
                sex, pre, post,
                file("${cnvDir}/summary.${pre}.tab"),
                file("${cnvDir}/dat.${pre}.tab"),
                file("${cnvDir}/cn.${pre}.tab"),
                file("${cnvDir}/summary.${post}.tab"),
                file("${cnvDir}/dat.${post}.tab"),
                file("${cnvDir}/cn.${post}.tab"),
                file("${cnvDir}/summary.tab"),                              // pair summary
                file("${summaryDir}/summary_pair_filt_${post}_${pre}.tsv")  // filtered calls
            )
        }

    // ROH channels (legacy approach)
    singleRohCh = ROH_ANALYSIS_SINGLE.out.roh_data_files_tuple
                    .map { sample, unionBed, rohBed, cn_bed -> tuple(sample, unionBed, rohBed, cn_bed) }

    pairedRohCh = ROH_ANALYSIS_PAIRED.out.roh_data_files_tuple
                    .map { pre, post, unionBed, rohBed, paired_cn_bed -> 
                        tuple(pre, post, unionBed, rohBed, paired_cn_bed) 
                    }

    // PRE side join
    preJoined = pairedRohCh            // (pre, post, pairedUnion, pairedRoh, paired_cn_bed)
                    .combine(            // keeps every pair
                            singleRohCh, // (pre, preUnion, preRoh, pre_cn_bed)
                            by: 0)       // key = pre

    // Re-key on POST
    byPost = preJoined.map { pre,
                             post,
                             pairedUnion,
                             pairedRoh,
                             paired_cn_bed,
                             preUnion,
                             preRoh,
                             pre_cn_bed ->
        tuple(
          post, 
          pre, 
          preUnion, 
          preRoh, 
          pre_cn_bed,       // single-sample cn
          pairedUnion, 
          pairedRoh, 
          paired_cn_bed     // paired-sample cn
        )
    }

    // POST side join
    postJoined = byPost
                    .combine(            // keeps every pair
                             singleRohCh, // (post, postUnion, postRoh, post_cn_bed)
                             by: 0)       // key = post

    // Final ROH paired channel (key = [pre,post])
    finalRohCh = postJoined.map { post,
                                  pre,
                                  preUnion, preRoh, pre_cn_bed,
                                  pairedUnion, pairedRoh, paired_cn_bed,
                                  postUnion, postRoh, post_cn_bed ->

        // emit a tuple whose first element is the [pre,post] key,
        // followed by everything in the order your dynamicPlotInput_paired.map expects:
        tuple(
          [pre, post], 
          // (these next 3 fields line up with the _preDup/_postDup you ignore)
          pre, post,   
          // single-pre ROH
          preUnion, preRoh, pre_cn_bed,
          // single-post ROH
          postUnion, postRoh, post_cn_bed,
          // paired ROH
          pairedUnion, pairedRoh, paired_cn_bed
        )
    }

    // Dynamic-plot input channel (flat tuple)
    dynamicPlotInput_paired = cnvPaired_ch
        .join(finalRohCh, by: 0)
        .map { key,                           // 1

              // — CNV block (11 values) —
              sex, pre, post,                // 3
              summary_pre, dat_pre, cn_pre,  // 3
              summary_post, dat_post, cn_post, // 3
              pair_summary, summary_pair_filt, // 2

              // — ROH block (11 values) —
              _preDup, _postDup,             // 2 dups
              preUnion, preRoh, pre_cn_bed,  // 3 single-pre (incl. cn)
              postUnion, postRoh, post_cn_bed,// 3 single-post (incl. cn)
              pairedUnion, pairedRoh, paired_cn_bed -> // 3 paired (incl. cn)

          def overlapDir = pairedUnion.parent

          tuple(
            sex, pre, post,
            summary_pre, dat_pre, cn_pre,
            summary_post, dat_post, cn_post,
            pair_summary, summary_pair_filt,
            preUnion, preRoh, pre_cn_bed,
            postUnion, postRoh, post_cn_bed,
            pairedUnion, pairedRoh, paired_cn_bed,
            overlapDir
          )
        }

    paired_sample_types_ch_w_phat = IBD_ANALYSIS.out.pi_hat_results
    single_sample_types_ch_w_LRR = SAMPLE_TYPES_SINGLE.out.sample_csv_single_w_QC

    combinedDynamicPlotInput_paired_IBD = dynamicPlotInput_paired.combine(paired_sample_types_ch_w_phat)
    combinedDynamicPlotInput_paired = combinedDynamicPlotInput_paired_IBD.combine(single_sample_types_ch_w_LRR)

    DYNAMIC_PLOT_DATA_PREP_PAIRED(combinedDynamicPlotInput_paired)

    // Prepare channels for paired dynamic plotting (legacy compatible)
    ch_sample_types_paired = DYNAMIC_PLOT_DATA_PREP_PAIRED.out.all_processed_files
        .map { pre, post, sample_types_single, sample_types_paired, csv_files ->
            tuple(sample_types_single, sample_types_paired)
        }
        .first()

    ch_processed_csvs_paired = DYNAMIC_PLOT_DATA_PREP_PAIRED.out.all_processed_files
        .map { pre, post, sample_types_single, sample_types_paired, csv_files ->
            csv_files
        }
        .flatten()  
        .collect()   

    ch_parameters_paired = PARAMETER_REPORT.out.parameters

    DYNAMIC_PLOT_PAIRED(ch_sample_types_paired, ch_processed_csvs_paired, ch_parameters_paired)
}
