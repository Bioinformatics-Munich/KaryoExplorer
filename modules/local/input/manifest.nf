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
        
        # Extract SNP positions from manifest using column names (robust approach)
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracting SNP positions from manifest (auto-detecting Chr and MapInfo columns)"
        sed -e '1,/\\[Assay\\]/d' -e '/\\[Controls\\]/,\$d' $manifest | \\
        gawk 'BEGIN{FS=",";OFS="\\t"} 
        NR==1 {
            # Find column indices by name
            for(i=1; i<=NF; i++) {
                if(\$i == "Chr") chr_col = i;
                if(\$i == "MapInfo") pos_col = i;
            }
            if(chr_col == 0 || pos_col == 0) {
                print "ERROR: Could not find Chr or MapInfo columns in manifest header" > "/dev/stderr";
                exit 1;
            }
            print "INFO: Found Chr at column " chr_col ", MapInfo at column " pos_col > "/dev/stderr";
            next;
        }
        NR > 1 {
            # Split line into array for dynamic field access
            split(\$0, fields, ",");
            chr = fields[chr_col];
            pos = fields[pos_col];
            
            # Validate and output
            if(chr != "XY" && chr != "MT" && chr != "0" && chr != "" && 
               chr+0 > 0 && chr+0 <= 24 && pos+0 > 0) {
                print chr, pos-1, pos;
            }
        }' > manifest.bed
        
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
