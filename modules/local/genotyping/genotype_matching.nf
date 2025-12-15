nextflow.enable.dsl=2

/*
========================================================================================
    GENOTYPING: GENOTYPE MATCHING & VALIDATION
========================================================================================
    Processes for genotype matching, sample annotation, and validation
----------------------------------------------------------------------------------------
*/

process GT_MATCH_PAIRED_SAMPLES {
    
    tag "06_GT | Paired sample matching"
    label 'process_low'

    publishDir "${params.outdir}/1.0_quality_control/1.3_paired_matching", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        path gt_comp
        path samplesTable_filt
        path annotation_file

    output:
        path "*", emit: qc_paired_dir
        path "annotation_file_GTmatch.csv", emit: annotation_file

    when:
        gt_comp && samplesTable_filt

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting genotype matching for paired samples"
        
        if [[ \$(wc -l <${annotation_file}) -ge 2 ]]; then
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Processing genotype matching with annotation file"
            
            # Convert Sample.ID to sample_ID for R script compatibility (temporary)
            cp ${samplesTable_filt} temp_samples_table.txt
            sed -i '1s/Sample\\.ID/sample_ID/' temp_samples_table.txt
            
            ${projectDir}/bin/genotyping/GT_match_run.R --comp_GT_file ${gt_comp} --Samples_table_file temp_samples_table.txt --ann_file ${annotation_file} --outf ./
            
            # Move files from 3_QC_paired subfolder to current directory if they exist
            if [ -d "3_QC_paired" ]; then
                mv 3_QC_paired/* ./
                rmdir 3_QC_paired
            fi
        else
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: No annotation file provided, creating empty annotation file"
            touch annotation_file_GTmatch.csv
        fi
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Paired sample genotype matching completed"
        """
}

process GT_MATCH_SINGLE_SAMPLES {
    
    tag "07_GT | Single sample matching"
    label 'process_low'

    publishDir "${params.outdir}/1.0_quality_control/1.2_single_matching", mode: 'copy', overwrite: true

    conda "${baseDir}/env/renv.yaml"

    input:
        path gt_comp
        path samplesTable_filt
        path annotation_file

    output:
        path "*", emit: qc_single_dir
        path "annotation_file_GTmatch.csv", emit: annotation_file

    when:
        gt_comp && samplesTable_filt

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting genotype matching for single samples"
        
        if [[ \$(wc -l <${annotation_file}) -ge 2 ]]; then
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Processing genotype matching with annotation file"
            
            # Convert Sample.ID to sample_ID for R script compatibility (temporary)
            cp ${samplesTable_filt} temp_samples_table.txt
            sed -i '1s/Sample\\.ID/sample_ID/' temp_samples_table.txt
            
            ${projectDir}/bin/genotyping/GT_match_run.R --comp_GT_file ${gt_comp} --Samples_table_file temp_samples_table.txt --ann_file ${annotation_file} --outf ./
            
            # Move files from 3_QC_single subfolder to current directory if they exist
            if [ -d "3_QC_single" ]; then
                mv 3_QC_single/* ./
                rmdir 3_QC_single
            fi
        else
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: No annotation file provided, creating empty annotation file"
            touch annotation_file_GTmatch.csv
        fi
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Single sample genotype matching completed"
        """
}

process GT_EMIT_PAIRED_SAMPLES {
    
    tag "08_GT | Extracting paired sample IDs"
    label 'process_low'

    input:
        path annotation_file

    output:
        path "paired_samples.txt", emit: samples

    when:
        annotation_file

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracting paired sample IDs"
        
        if [[ \$(wc -l <${annotation_file}) -ge 2 ]]; then
            tail -n +2 ${annotation_file} | cut -d',' -f3 | sort | uniq > paired_samples.txt
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracted \$(wc -l < paired_samples.txt) paired samples"
        else
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: No paired samples found, creating empty file"
            touch paired_samples.txt
        fi
        """
}

process GT_EMIT_SINGLE_SAMPLES {
    
    tag "09_GT | Extracting single sample IDs"
    label 'process_low'

    input:
        path annotation_file

    output:
        path "single_samples.txt", emit: samples

    when:
        annotation_file

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracting single sample IDs"
        
        if [[ \$(wc -l <${annotation_file}) -ge 2 ]]; then
            tail -n +2 ${annotation_file} | cut -d',' -f3 | sort | uniq > single_samples.txt
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracted \$(wc -l < single_samples.txt) single samples"
        else
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: No single samples found, creating empty file"
            touch single_samples.txt
        fi
        """
}

process GT_CREATE_SAMPLE_ANNOTATION_PAIRED {
    
    tag "10_GT | Sample annotation: ${sample_name_id}"
    label 'process_low'

    conda "${baseDir}/env/renv.yaml"

    publishDir "${params.outdir}/3.0_sample_annotation/paired", mode: 'copy', overwrite: true, pattern: "${sample_name_id}_*.tsv"

    input:
        path annotation_file
        val sample_name_id

    output:
        path "${sample_name_id}_1.tsv", emit: samplestab
        val "${params.outdir}/4.0_sample_annotation/paired", emit: outdir

    when:
        annotation_file && sample_name_id

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Creating annotation for paired sample: ${sample_name_id}"
        
        ${projectDir}/bin/qc/create_annSample_run.R --sample_name ${sample_name_id} --ann_file ${annotation_file} --outf ./
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Sample annotation created for ${sample_name_id}"
        """
}

process GT_CREATE_SAMPLE_ANNOTATION_SINGLE {
    
    tag "10_GT | Sample annotation: ${sample_name_id}"
    label 'process_low'

    conda "${baseDir}/env/renv.yaml"

    publishDir "${params.outdir}/3.0_sample_annotation/single", mode: 'copy', overwrite: true, pattern: "${sample_name_id}_*.tsv"

    input:
        path annotation_file
        val sample_name_id

    output:
        path "${sample_name_id}_1.tsv", emit: samplestab
        val "${params.outdir}/4.0_sample_annotation/single", emit: outdir

    when:
        annotation_file && sample_name_id

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Creating annotation for single sample: ${sample_name_id}"
        
        ${projectDir}/bin/qc/create_annSample_run.R --sample_name ${sample_name_id} --ann_file ${annotation_file} --outf ./
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Sample annotation created for ${sample_name_id}"
        """
}
