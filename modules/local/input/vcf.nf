nextflow.enable.dsl=2

/*
========================================================================================
    INPUT: VCF PROCESSING
========================================================================================
    Processes for VCF creation, correction, and preprocessing with BAF/LRR annotation
----------------------------------------------------------------------------------------
*/

process VCF_CREATE_FROM_PLINK {
    
    tag "03_VCF (VCF_CREATE_FROM_PLINK) | PLINK to VCF conversion"
    label 'process_low'

    publishDir "${params.outdir}/2.0_preprocess/2.2_plink", mode: 'copy', overwrite: true
    publishDir "${params.outdir}/0.0_information/0.2_versions/", mode: 'copy', overwrite: true, pattern: "plink.version.txt"

    conda "${baseDir}/env/preproc.yaml"

    input:
        path gsplink

    output:
        path "plink.vcf", emit: vcf
        path "plink.nosex", emit: nosex, optional: true
        path "plink.log", emit: log
        path "plink.version.txt", emit: version

    when:
        gsplink

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting PLINK to VCF conversion"
        
        # Convert PLINK files to VCF
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Converting PED/MAP files to VCF format"
        plink --ped `ls $gsplink/*.ped` --map `ls $gsplink/*.map` --recode vcf
        
        # Get PLINK version
        plink --version > plink.version.txt
        
        # Check if .nosex file exists, if not create empty one (only created when sex info is missing/ambiguous)
        if [ ! -f "plink.nosex" ]; then
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: No plink.nosex file generated (all samples have valid sex information)"
            touch plink.nosex
        fi
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: PLINK to VCF conversion completed successfully"
        echo "Output VCF contains \$(grep -v '^#' plink.vcf | wc -l) variants"
        """
}

process VCF_CORRECT_REF_ALT {
    
    tag "04_VCF (VCF_CORRECT_REF_ALT) | Reference allele correction"
    label 'process_low'

    publishDir "${params.outdir}/2.0_preprocess/2.3_plink_corrected", mode: 'copy', overwrite: true

    input:
        path vcf
        path manifest_ref

    output:
        path "plink_corrected.vcf", emit: vcf_corrected

    when:
        vcf && manifest_ref

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting VCF reference allele correction"
        
        # Extract header and body
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Processing VCF header"
        gawk 'BEGIN{FS="\\t";OFS="\\t"}/^#/ && !/ID=(0|25|26)/{print \$0}' plink.vcf | \\
        sed "s/\\t[0-9]\\+_/\\t/g" | \\
        awk 'BEGIN{FS="\\t";OFS="\\t"} 
        /^#CHROM/{
            # Fix PLINK sample names: if sample is NAME_NAME, keep just NAME
            for(i=10; i<=NF; i++){
                n=split(\$i, parts, "_");
                if(n>=2){
                    # Check if sample name is duplicated (e.g., "NA06993_R_NA06993_R")
                    first_half = "";
                    second_half = "";
                    for(j=1; j<=int(n/2); j++) first_half = first_half (j>1?"_":"") parts[j];
                    for(j=int(n/2)+1; j<=n; j++) second_half = second_half (j>int(n/2)+1?"_":"") parts[j];
                    if(first_half == second_half) \$i = first_half;
                }
            }
        }
        {print}' > plink.header
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Processing VCF body and sorting variants"
        gawk 'BEGIN{FS="\\t";OFS="\\t"}!/^#/ && \$1!=0 && \$1!=25 && \$1!=26 {print \$0}' plink.vcf | \\
        sort -k1,1 -k2,2n > plink.body.all
        
        # Filter VCF to only include positions in manifest (using AWK to handle duplicates correctly)
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Filtering VCF to match manifest positions"
        gawk 'BEGIN{FS="\\t";OFS="\\t"}
        NR==FNR{pos[\$1"_"\$2]=1; next}
        {if(\$1"_"\$2 in pos) print \$0}
        ' ${manifest_ref} plink.body.all > plink.body
        
        # Check counts
        manifest_lines=\$(wc -l < ${manifest_ref})
        vcf_lines=\$(wc -l < plink.body)
        vcf_all_lines=\$(wc -l < plink.body.all)
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Original VCF: \$vcf_all_lines variants"
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Manifest: \$manifest_lines variants"
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Filtered VCF: \$vcf_lines variants"
        
        if [[ \$manifest_lines == \$vcf_lines ]]; then
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Counts match - correcting reference alleles using manifest"
            paste ${manifest_ref} plink.body | \\
            gawk 'BEGIN{FS="\\t";OFS="\\t"}{
                if ((\$3==\$7) && (\$1==\$4) && (\$2==\$5)) {
                    print \$0
                } else if ((\$3!=\$7) && (\$1==\$4) && (\$2==\$5)) {
                    \$8=\$7; \$7=\$3; print \$0
                } else if ((\$1!=\$4) || (\$2!=\$5)) {
                    print "WARNING: " \$1,\$2 " in ref file does not match the vcf" > "/dev/stderr"
                }
            }' | cut -f4- > tmp
            
            cat plink.header tmp > plink_corrected.vcf
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: VCF reference allele correction completed successfully"
            echo "Final VCF contains \$(grep -v '^#' plink_corrected.vcf | wc -l) variants"
        else
            echo "[\$(date '+%Y-%m-%d %H:%M:%S')] ERROR: After filtering, manifest has \$manifest_lines but VCF has \$vcf_lines variants"
            exit 2
        fi
        """
}

process VCF_ANNOTATE_BAF_LRR {
    
    tag "05_VCF (VCF_ANNOTATE_BAF_LRR) | BAF/LRR annotation"
    label 'process_low'

    conda "${baseDir}/env/preproc.yaml"

    publishDir "${params.outdir}/2.0_preprocess/2.4_preprocess_vcf", mode: 'copy', overwrite: true
    publishDir "${params.outdir}/0.0_information/0.2_versions/", mode: 'copy', overwrite: true, pattern: "*.version.txt"

    input:
        path fullTable_filt
        path vcf_corrected
        path lrr_table
        path baf_table

    output:
        path 'data_BAF_LRR.vcf', emit: vcf_annotated
        path 'SNPs_QC.txt', emit: snps_qc
        path "bcftools.version.txt", emit: bcftools_version
        path "vcftools.version.txt", emit: vcftools_version

    when:
        fullTable_filt && vcf_corrected && lrr_table && baf_table

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting VCF annotation with BAF/LRR data"
        
        # Extract QC SNPs
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Extracting QC SNP list"
        cut -f2 ${fullTable_filt} | sed '1d' > SNPs_QC.txt
        echo "Extracted \$(wc -l < SNPs_QC.txt) QC SNPs"
        
        # Filter VCF with QC SNPs
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Filtering VCF with QC SNPs"
        vcftools --vcf ${vcf_corrected} --snps SNPs_QC.txt --recode --recode-INFO-all --out vcf_file_QC
        
        # Prepare BAF/LRR files for annotation
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Preparing BAF/LRR files for annotation"
        bgzip ${lrr_table}
        bgzip ${baf_table}
        
        tabix -s1 -S1 -b2 -e2 ${lrr_table}.gz
        tabix -s1 -S1 -b2 -e2 ${baf_table}.gz

        # Create annotation headers
        echo '##FORMAT=<ID=BAF,Number=1,Type=Float,Description="GS estimate of BAF">' > baf.hdr
        echo '##FORMAT=<ID=LRR,Number=1,Type=Float,Description="GS estimate of LRR">' > lrr.hdr
        
        # Annotate VCF with BAF
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Annotating VCF with BAF values"
        bcftools annotate -a ${baf_table}.gz -h baf.hdr -c CHROM,POS,ID,FMT/BAF -Ov -o output.vcf vcf_file_QC.recode.vcf
        
        # Annotate VCF with LRR
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Annotating VCF with LRR values"
        bcftools annotate -a ${lrr_table}.gz -h lrr.hdr -c CHROM,POS,ID,FMT/LRR -Ov -o data_BAF_LRR.vcf output.vcf

        # Remove duplicates
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Removing duplicate SNPs"
        mv data_BAF_LRR.vcf data_BAF_LRR_withdup.vcf
        gawk 'BEGIN{FS="\\t"; OFS="\\t"}!/^#/{print \$3}' data_BAF_LRR_withdup.vcf | uniq -d > dupl.list
        
        if [[ -s dupl.list ]]; then
            echo "Found \$(wc -l < dupl.list) duplicate SNPs, removing them"
            vcftools --vcf data_BAF_LRR_withdup.vcf --exclude dupl.list --recode-INFO-all --recode --out data_BAF_LRR
            mv data_BAF_LRR.recode.vcf data_BAF_LRR.vcf
        else
            echo "No duplicate SNPs found"
            mv data_BAF_LRR_withdup.vcf data_BAF_LRR.vcf
        fi

        # Update SNP QC list
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Updating SNP QC list"
        gawk 'BEGIN{FS="\\t";OFS="\\t"} !/^#/ {print \$1,\$2,\$3}' data_BAF_LRR.vcf > SNPs_QC.txt
        
        # Get software versions
        bcftools --version > bcftools.version.txt
        vcftools --version > vcftools.version.txt
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: VCF annotation completed successfully"
        echo "Final annotated VCF contains \$(grep -v '^#' data_BAF_LRR.vcf | wc -l) variants"
        """
}
