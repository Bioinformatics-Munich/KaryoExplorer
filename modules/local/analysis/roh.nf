nextflow.enable.dsl=2

/*
========================================================================================
    SPECIALIZED ANALYSIS: RUNS OF HOMOZYGOSITY (RoH)
========================================================================================
    RoH analysis and overlap with CNV regions
----------------------------------------------------------------------------------------
*/

process ROH_ANALYSIS_SINGLE {
    tag "${pre_sample}"
    label 'process_medium'
    
    publishDir "${params.outdir}/4.0_roh_loh_analysis/4.1_roh_loh_single/bcftools_algorithm", 
        mode: 'copy', 
        overwrite: true,
        pattern: "${pre_sample}/{roh,cnv}/*"
    
    publishDir "${params.outdir}/4.0_roh_loh_analysis/4.1_roh_loh_single", 
        mode: 'copy',
        overwrite: true,
        pattern: "overlap/${pre_sample}/**"

    conda "${baseDir}/env/preproc.yaml"
    
    input:
        tuple val(sample_id), val(type), val(pre_sample), val(post_sample), path(vcf_baf_lrr)
    
    output:
        path("${pre_sample}/roh/*"), emit: roh_results
        path("${pre_sample}/cnv/*"), emit: cnv_results
        path("overlap/${pre_sample}/analysis/*.{bed,txt}"), emit: analysis_files
        path("overlap/${pre_sample}/data/*.bed"), emit: data_files
        path("overlap/${pre_sample}/analysis/${pre_sample}_analysis_report.txt"), emit: analysis_report
        tuple val(pre_sample), 
              path("overlap/${pre_sample}/data/${pre_sample}_union_merged_with_length.bed"), 
              path("overlap/${pre_sample}/data/${pre_sample}_roh_with_length.bed"), 
              path("overlap/${pre_sample}/data/${pre_sample}_cn_with_length.bed"), 
              emit: roh_data_files_tuple
        tuple val(pre_sample), val(post_sample), 
              path("overlap/${pre_sample}/data/${pre_sample}_union_merged_with_length.bed"), 
              path("overlap/${pre_sample}/data/${pre_sample}_roh_with_length.bed"), 
              path("overlap/${pre_sample}/data/${pre_sample}_cn_with_length.bed"), 
              emit: roh_data_files_tuple_with_post

    when:
        type == 'single'
    
    script:
        """
        # Create directory structure
        mkdir -p overlap/${pre_sample}/{analysis,data}
        
        # Create compressed and indexed VCF
        bgzip -c "${vcf_baf_lrr}" > input.vcf.gz
        tabix -p vcf input.vcf.gz
        
        # Run bcftools roh analysis
        ${projectDir}/bin/analysis/RoH_analysis_single.sh "input.vcf.gz" "${pre_sample}" "${params.weight_lrr}"
        
        # Verify ROH file exists before Python analysis
        if [ ! -f "${pre_sample}/roh/roh.txt" ]; then
            echo "Warning: No ROH file found, creating empty dataset"
            mkdir -p "${pre_sample}/roh"
            touch "${pre_sample}/roh/roh.txt"
        fi

        # Run initial Python analysis
        python ${projectDir}/bin/analysis/RoH_CN_overlap_single_QC.py \\
            --roh "${pre_sample}/roh/roh.txt" \\
            --cn_summary "${pre_sample}/cnv/summary.${pre_sample}.tab" \\
            --dat "${pre_sample}/cnv/dat.${pre_sample}.tab" \\
            --cn "${pre_sample}/cnv/cn.${pre_sample}.tab" \\
            --output_dir "overlap/${pre_sample}/analysis" \\
            --sample "${pre_sample}"

        # Define paths for bed files
        roh_bed="overlap/${pre_sample}/analysis/${pre_sample}.roh_data.bed"
        cn_bed="overlap/${pre_sample}/analysis/${pre_sample}.cn_data.bed"
        outdir="overlap/${pre_sample}/data"
        mkdir -p "\$outdir"

        # Generate intermediate files
        if [[ -s "\$roh_bed" && -s "\$cn_bed" ]]; then
            # Calculate lengths for ROH and CN
            awk '{print \$0 "\t" \$3-\$2}' "\$roh_bed" > "\${outdir}/${pre_sample}_roh_with_length.bed"
            awk '{print \$0 "\t" \$3-\$2}' "\$cn_bed" > "\${outdir}/${pre_sample}_cn_with_length.bed"
            
            # Generate combined and sorted data
            cat "\$roh_bed" "\$cn_bed" > "\${outdir}/${pre_sample}_combined_data.bed"
            bedtools sort -i "\${outdir}/${pre_sample}_combined_data.bed" > "\${outdir}/${pre_sample}_sorted_combined_data.bed"
            
            # Generate union
            bedtools merge -i "\${outdir}/${pre_sample}_sorted_combined_data.bed" > "\${outdir}/${pre_sample}_union_merged.bed"
            awk '{print \$0 "\t" \$3-\$2}' "\${outdir}/${pre_sample}_union_merged.bed" > "\${outdir}/${pre_sample}_union_merged_with_length.bed"
            
            # Generate intersections
            bedtools intersect -a "\$roh_bed" -b "\$cn_bed" -wao > "\${outdir}/${pre_sample}_overlap_ROH_asA.bed"
            bedtools intersect -a "\$cn_bed" -b "\$roh_bed" -wao > "\${outdir}/${pre_sample}_overlap_CN_asA.bed"
        else
            touch "\${outdir}/${pre_sample}_roh_with_length.bed"
            touch "\${outdir}/${pre_sample}_cn_with_length.bed"
            touch "\${outdir}/${pre_sample}_combined_data.bed"
            touch "\${outdir}/${pre_sample}_sorted_combined_data.bed"
            touch "\${outdir}/${pre_sample}_union_merged.bed"
            touch "\${outdir}/${pre_sample}_union_merged_with_length.bed"
            touch "\${outdir}/${pre_sample}_overlap_ROH_asA.bed"
            touch "\${outdir}/${pre_sample}_overlap_CN_asA.bed"
        fi

        # Run overlap analysis
        python ${projectDir}/bin/analysis/RoH_CN_overlap.py \\
            --roh_with_len "\${outdir}/${pre_sample}_roh_with_length.bed" \\
            --cn_with_len "\${outdir}/${pre_sample}_cn_with_length.bed" \\
            --roh_perspective "\${outdir}/${pre_sample}_overlap_ROH_asA.bed" \\
            --cn_perspective "\${outdir}/${pre_sample}_overlap_CN_asA.bed" \\
            --union_with_len "\${outdir}/${pre_sample}_union_merged_with_length.bed" \\
            --sample "${pre_sample}" \\
            --output_dir "overlap/${pre_sample}/analysis" \\
            --log "overlap/${pre_sample}/analysis/${pre_sample}_analysis_report.txt"
        """
}

process ROH_ANALYSIS_PAIRED {
    tag "${pre_sample}_${post_sample}"
    label 'process_medium'
    
    publishDir "${params.outdir}/4.0_roh_loh_analysis/4.2_roh_loh_paired/bcftools_algorithm", 
        mode: 'copy', 
        overwrite: true,
        pattern: "${pre_sample}_${post_sample}/{roh,cnv}/*"
    
    publishDir "${params.outdir}/4.0_roh_loh_analysis/4.2_roh_loh_paired", 
        mode: 'copy',
        overwrite: true,
        pattern: "overlap/${pre_sample}_${post_sample}/**"

    conda "${baseDir}/env/preproc.yaml"
    
    input:
        tuple val(sample_id), val(type), val(pre_sample), val(post_sample), path(vcf_baf_lrr)
    
    output:
        path("${pre_sample}_${post_sample}/roh/*"), emit: roh_results
        path("${pre_sample}_${post_sample}/cnv/*"), emit: cnv_results
        path("overlap/${pre_sample}_${post_sample}/analysis/*.{bed,txt}"), emit: analysis_files
        path("overlap/${pre_sample}_${post_sample}/data/*.bed"), emit: data_files
        path("overlap/${pre_sample}_${post_sample}/analysis/${pre_sample}_${post_sample}_analysis_report.txt"), emit: analysis_report
        tuple val(pre_sample), val(post_sample),
              path("overlap/${pre_sample}_${post_sample}/data/${pre_sample}_${post_sample}_union_merged_with_length.bed"), 
              path("overlap/${pre_sample}_${post_sample}/data/${pre_sample}_${post_sample}_roh_with_length.bed"), 
              path("overlap/${pre_sample}_${post_sample}/data/${pre_sample}_${post_sample}_cn_with_length.bed"), 
              emit: roh_data_files_tuple    

    when:
        type == 'paired'
    
    script:
        """
        # Create directory structure
        
        mkdir -p "${pre_sample}_${post_sample}/cnv" "${pre_sample}_${post_sample}/roh"
        mkdir -p overlap/${pre_sample}_${post_sample}/{analysis,data}

        # Create compressed and indexed VCF
        bgzip -c "${vcf_baf_lrr}" > input.vcf.gz
        tabix -p vcf input.vcf.gz

        # Run bcftools roh analysis
        ${projectDir}/bin/analysis/RoH_analysis_paired.sh "input.vcf.gz" "${pre_sample}" "${post_sample}" "${params.weight_lrr}"
        
        # Verify ROH files exist before Python analysis
        if [ ! -f "${pre_sample}_${post_sample}/roh/roh_diff.txt" ]; then
            echo "Warning: No ROH differential file found, creating empty dataset"
            touch "${pre_sample}_${post_sample}/roh/roh_diff.txt"
        fi

        # Run initial Python analysis for paired samples
        python ${projectDir}/bin/analysis/RoH_CN_overlap_paired_QC.py \\
            --roh "${pre_sample}_${post_sample}/roh/roh_diff.txt" \\
            --cn_summary "${pre_sample}_${post_sample}/cnv/summary.tab" \\
            --output_dir "overlap/${pre_sample}_${post_sample}/analysis" \\
            --pre_sample "${pre_sample}" \\
            --post_sample "${post_sample}"

        # Define paths for bed files
        roh_bed="overlap/${pre_sample}_${post_sample}/analysis/${pre_sample}_${post_sample}.roh_data.bed"
        cn_bed="overlap/${pre_sample}_${post_sample}/analysis/${pre_sample}_${post_sample}.cn_data.bed"
        outdir="overlap/${pre_sample}_${post_sample}/data"
        mkdir -p "\$outdir"

        # Generate intermediate files
        if [[ -s "\$roh_bed" && -s "\$cn_bed" ]]; then
            # Calculate lengths for ROH and CN
            awk '{print \$0 "\t" \$3-\$2}' "\$roh_bed" > "\${outdir}/${pre_sample}_${post_sample}_roh_with_length.bed"
            awk '{print \$0 "\t" \$3-\$2}' "\$cn_bed" > "\${outdir}/${pre_sample}_${post_sample}_cn_with_length.bed"
            
            # Generate combined and sorted data
            cat "\$roh_bed" "\$cn_bed" > "\${outdir}/${pre_sample}_${post_sample}_combined_data.bed"
            bedtools sort -i "\${outdir}/${pre_sample}_${post_sample}_combined_data.bed" > "\${outdir}/${pre_sample}_${post_sample}_sorted_combined_data.bed"
            
            # Generate union
            bedtools merge -i "\${outdir}/${pre_sample}_${post_sample}_sorted_combined_data.bed" > "\${outdir}/${pre_sample}_${post_sample}_union_merged.bed"
            awk '{print \$0 "\t" \$3-\$2}' "\${outdir}/${pre_sample}_${post_sample}_union_merged.bed" > "\${outdir}/${pre_sample}_${post_sample}_union_merged_with_length.bed"
            
            # Generate intersections
            bedtools intersect -a "\$roh_bed" -b "\$cn_bed" -wao > "\${outdir}/${pre_sample}_${post_sample}_overlap_ROH_asA.bed"
            bedtools intersect -a "\$cn_bed" -b "\$roh_bed" -wao > "\${outdir}/${pre_sample}_${post_sample}_overlap_CN_asA.bed"
        else
            touch "\${outdir}/${pre_sample}_${post_sample}_roh_with_length.bed"
            touch "\${outdir}/${pre_sample}_${post_sample}_cn_with_length.bed"
            touch "\${outdir}/${pre_sample}_${post_sample}_combined_data.bed"
            touch "\${outdir}/${pre_sample}_${post_sample}_sorted_combined_data.bed"
            touch "\${outdir}/${pre_sample}_${post_sample}_union_merged.bed"
            touch "\${outdir}/${pre_sample}_${post_sample}_union_merged_with_length.bed"
            touch "\${outdir}/${pre_sample}_${post_sample}_overlap_ROH_asA.bed"
            touch "\${outdir}/${pre_sample}_${post_sample}_overlap_CN_asA.bed"
        fi

        # Run overlap analysis
        python ${projectDir}/bin/analysis/RoH_CN_overlap.py \\
            --roh_with_len "\${outdir}/${pre_sample}_${post_sample}_roh_with_length.bed" \\
            --cn_with_len "\${outdir}/${pre_sample}_${post_sample}_cn_with_length.bed" \\
            --roh_perspective "\${outdir}/${pre_sample}_${post_sample}_overlap_ROH_asA.bed" \\
            --cn_perspective "\${outdir}/${pre_sample}_${post_sample}_overlap_CN_asA.bed" \\
            --union_with_len "\${outdir}/${pre_sample}_${post_sample}_union_merged_with_length.bed" \\
            --sample "${pre_sample}_${post_sample}" \\
            --output_dir "overlap/${pre_sample}_${post_sample}/analysis" \\
            --log "overlap/${pre_sample}_${post_sample}/analysis/${pre_sample}_${post_sample}_analysis_report.txt"
        """
}