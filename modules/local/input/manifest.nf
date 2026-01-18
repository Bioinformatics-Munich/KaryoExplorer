nextflow.enable.dsl=2

/*
========================================================================================
    INPUT: MANIFEST PROCESSING
========================================================================================
    Processes for handling manifest files and reference allele extraction
----------------------------------------------------------------------------------------
*/

process MANIFEST_GET_REF_ALLELE {
    
    tag "02_INPUT (MANIFEST_GET_REF_ALLELE) | ${manifest.simpleName}"
    label 'process_low'

    publishDir "${params.outdir}/2.0_preprocess/2.1_manifest_reference", mode: 'copy', overwrite: true

    conda "${baseDir}/env/preproc.yaml"

    input:
        path manifest
        path fasta

    output:
        path "${manifest_name}.ref", emit: manifest_ref
        
    when:
        manifest && fasta

    script:
        manifest_name = manifest.simpleName
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting manifest reference allele extraction for ${manifest_name}"
        
        # Extract SNP positions from manifest
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracting SNP positions from manifest"
        sed -e '1,/\\[Assay\\]/d' -e '/\\[Controls\\]/,\$d' $manifest | \\
        gawk 'BEGIN{FS=",";OFS="\\t"} \$10!="XY" && \$10!="MT" && \$10!="0" && !/MapInfo/ {print \$10,\$11-1,\$11}' > manifest.bed
        
        # Get FASTA sequences
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracting FASTA sequences for SNP positions"
        bedtools getfasta -fi $fasta -bed manifest.bed > manifest.fa
        
        # Generate reference file
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Generating reference allele file"
        gawk 'BEGIN{RS=">";FS=":|-|\\n";OFS="\\t"}!/^\$/{gsub(/X/,"23",\$1); gsub(/Y/,"24",\$1); print \$1,\$3,toupper(\$4)}' manifest.fa | \\
        sort -k1,1 -k2,2n > ${manifest_name}.ref
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Manifest reference allele extraction completed successfully"
        echo "Reference file: ${manifest_name}.ref contains \$(wc -l < ${manifest_name}.ref) SNPs"
        """
}
